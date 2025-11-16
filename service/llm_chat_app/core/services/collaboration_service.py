"""
Real-time Collaboration Service
Enables multiple users to share chat sessions and collaborate
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)

# Collaboration data storage
_COLLAB_DIR = Path.cwd() / "collaboration_sessions"
_COLLAB_DIR.mkdir(parents=True, exist_ok=True)

# In-memory active sessions (in production, use Redis)
_ACTIVE_SESSIONS: Dict[str, "CollaborationSession"] = {}
_SESSION_LOCK = threading.RLock()


@dataclass
class CollaborationMessage:
    """Represents a message in a collaborative session"""
    id: str
    user: str
    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborationSession:
    """Represents a collaborative chat session"""
    session_id: str
    name: str
    created_by: str
    created_at: float
    participants: Set[str]
    messages: List[CollaborationMessage]
    settings: Dict[str, Any]
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "participants": list(self.participants),
            "message_count": len(self.messages),
            "settings": self.settings,
            "is_active": self.is_active
        }


class CollaborationService:
    """Service for managing collaborative sessions"""
    
    @staticmethod
    def create_session(
        name: str,
        created_by: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new collaborative session
        
        Args:
            name: Session name
            created_by: User creating the session
            settings: Session settings (model, etc.)
            
        Returns:
            Session information
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().timestamp()
        
        session = CollaborationSession(
            session_id=session_id,
            name=name,
            created_by=created_by,
            created_at=now,
            participants={created_by},
            messages=[],
            settings=settings or {"model": "default"},
            is_active=True
        )
        
        with _SESSION_LOCK:
            _ACTIVE_SESSIONS[session_id] = session
        
        # Persist to disk
        _save_session(session)
        
        logger.info("event=collab_session_created session_id=%s created_by=%s", session_id, created_by)
        
        return {
            "success": True,
            "session_id": session_id,
            "session": session.to_dict()
        }
    
    @staticmethod
    def join_session(session_id: str, user: str) -> Dict[str, Any]:
        """
        Join an existing collaborative session
        
        Args:
            session_id: Session to join
            user: User joining
            
        Returns:
            Session information
        """
        with _SESSION_LOCK:
            if session_id not in _ACTIVE_SESSIONS:
                # Try to load from disk
                session = _load_session(session_id)
                if not session:
                    logger.warning("event=collab_session_not_found session_id=%s", session_id)
                    return {"success": False, "error": "Session not found"}
                _ACTIVE_SESSIONS[session_id] = session
            
            session = _ACTIVE_SESSIONS[session_id]
            
            if not session.is_active:
                logger.warning("event=collab_session_inactive session_id=%s", session_id)
                return {"success": False, "error": "Session is inactive"}
            
            session.participants.add(user)
        
        _save_session(session)
        
        logger.info("event=collab_user_joined session_id=%s user=%s participants=%s", 
                   session_id, user, len(session.participants))
        
        return {
            "success": True,
            "session_id": session_id,
            "session": session.to_dict(),
            "messages": [msg.to_dict() for msg in session.messages]
        }
    
    @staticmethod
    def add_message(
        session_id: str,
        user: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a collaborative session
        
        Args:
            session_id: Session ID
            user: User sending message
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message information
        """
        with _SESSION_LOCK:
            if session_id not in _ACTIVE_SESSIONS:
                session = _load_session(session_id)
                if not session:
                    return {"success": False, "error": "Session not found"}
                _ACTIVE_SESSIONS[session_id] = session
            
            session = _ACTIVE_SESSIONS[session_id]
            
            if user not in session.participants:
                logger.warning("event=collab_user_not_in_session session_id=%s user=%s", session_id, user)
                return {"success": False, "error": "User not in session"}
            
            msg_id = str(uuid.uuid4())
            now = datetime.now().timestamp()
            
            message = CollaborationMessage(
                id=msg_id,
                user=user,
                role=role,
                content=content,
                timestamp=now,
                metadata=metadata or {}
            )
            
            session.messages.append(message)
        
        _save_session(session)
        
        logger.info("event=collab_message_added session_id=%s user=%s msg_id=%s", 
                   session_id, user, msg_id)
        
        return {
            "success": True,
            "message": message.to_dict()
        }
    
    @staticmethod
    def get_session(session_id: str) -> Dict[str, Any]:
        """
        Get session information
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information
        """
        with _SESSION_LOCK:
            if session_id not in _ACTIVE_SESSIONS:
                session = _load_session(session_id)
                if not session:
                    return {"success": False, "error": "Session not found"}
                _ACTIVE_SESSIONS[session_id] = session
            
            session = _ACTIVE_SESSIONS[session_id]
        
        return {
            "success": True,
            "session": session.to_dict(),
            "messages": [msg.to_dict() for msg in session.messages]
        }
    
    @staticmethod
    def list_sessions(user: str) -> Dict[str, Any]:
        """
        List all sessions for a user
        
        Args:
            user: User to list sessions for
            
        Returns:
            List of sessions
        """
        sessions = []
        
        with _SESSION_LOCK:
            for session in _ACTIVE_SESSIONS.values():
                if user in session.participants:
                    sessions.append(session.to_dict())
        
        # Also check disk for archived sessions
        try:
            for session_file in _COLLAB_DIR.glob("*.json"):
                session = _load_session(session_file.stem)
                if session and user in session.participants:
                    if session.session_id not in [s["session_id"] for s in sessions]:
                        sessions.append(session.to_dict())
        except Exception as e:
            logger.error("event=collab_list_sessions_error error=%s", str(e))
        
        logger.info("event=collab_list_sessions user=%s count=%s", user, len(sessions))
        
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    
    @staticmethod
    def leave_session(session_id: str, user: str) -> Dict[str, Any]:
        """
        Leave a collaborative session
        
        Args:
            session_id: Session ID
            user: User leaving
            
        Returns:
            Operation result
        """
        with _SESSION_LOCK:
            if session_id not in _ACTIVE_SESSIONS:
                session = _load_session(session_id)
                if not session:
                    return {"success": False, "error": "Session not found"}
                _ACTIVE_SESSIONS[session_id] = session
            
            session = _ACTIVE_SESSIONS[session_id]
            
            if user not in session.participants:
                return {"success": False, "error": "User not in session"}
            
            session.participants.discard(user)
            
            # Close session if no participants
            if not session.participants:
                session.is_active = False
        
        _save_session(session)
        
        logger.info("event=collab_user_left session_id=%s user=%s remaining=%s", 
                   session_id, user, len(session.participants))
        
        return {
            "success": True,
            "session_id": session_id
        }
    
    @staticmethod
    def get_participants(session_id: str) -> Dict[str, Any]:
        """
        Get list of participants in a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of participants
        """
        with _SESSION_LOCK:
            if session_id not in _ACTIVE_SESSIONS:
                session = _load_session(session_id)
                if not session:
                    return {"success": False, "error": "Session not found"}
                _ACTIVE_SESSIONS[session_id] = session
            
            session = _ACTIVE_SESSIONS[session_id]
            participants = list(session.participants)
        
        return {
            "success": True,
            "session_id": session_id,
            "participants": participants,
            "count": len(participants)
        }


def _save_session(session: CollaborationSession) -> None:
    """Save session to disk"""
    try:
        session_file = _COLLAB_DIR / f"{session.session_id}.json"
        
        data = {
            "session_id": session.session_id,
            "name": session.name,
            "created_by": session.created_by,
            "created_at": session.created_at,
            "participants": list(session.participants),
            "messages": [msg.to_dict() for msg in session.messages],
            "settings": session.settings,
            "is_active": session.is_active
        }
        
        session_file.write_text(json.dumps(data, indent=2))
        logger.debug("event=collab_session_saved session_id=%s", session.session_id)
        
    except Exception as e:
        logger.error("event=collab_session_save_failed error=%s", str(e))


def _load_session(session_id: str) -> Optional[CollaborationSession]:
    """Load session from disk"""
    try:
        session_file = _COLLAB_DIR / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        data = json.loads(session_file.read_text())
        
        messages = [
            CollaborationMessage(**msg) for msg in data.get("messages", [])
        ]
        
        session = CollaborationSession(
            session_id=data["session_id"],
            name=data["name"],
            created_by=data["created_by"],
            created_at=data["created_at"],
            participants=set(data.get("participants", [])),
            messages=messages,
            settings=data.get("settings", {}),
            is_active=data.get("is_active", True)
        )
        
        logger.debug("event=collab_session_loaded session_id=%s", session_id)
        return session
        
    except Exception as e:
        logger.error("event=collab_session_load_failed session_id=%s error=%s", session_id, str(e))
        return None
