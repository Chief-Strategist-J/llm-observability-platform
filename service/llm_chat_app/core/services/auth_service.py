import os
import json
import hashlib
import secrets
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

_AUTH_DIR = Path.cwd() / "auth_data"
_AUTH_DIR.mkdir(parents=True, exist_ok=True)
_USERS_FILE = _AUTH_DIR / "users.json"
_SESSIONS_FILE = _AUTH_DIR / "sessions.json"
_RESET_TOKENS_FILE = _AUTH_DIR / "reset_tokens.json"

for file in [_USERS_FILE, _SESSIONS_FILE, _RESET_TOKENS_FILE]:
    if not file.exists():
        file.write_text("[]")


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    start = time.time()
    if salt is None:
        salt = secrets.token_hex(16)

    hashed = password + salt
    for _ in range(10000):
        hashed = hashlib.sha256(hashed.encode()).hexdigest()

    duration = int((time.time() - start) * 1000)
    logger.debug(f"event=password_hash duration_ms={duration} salt_length={len(salt)}")
    return hashed, salt


def _verify_password(password: str, hashed: str, salt: str) -> bool:
    start = time.time()
    computed_hash, _ = _hash_password(password, salt)
    ok = computed_hash == hashed
    duration = int((time.time() - start) * 1000)
    logger.debug(f"event=password_verify match={ok} duration_ms={duration}")
    return ok


def _generate_session_token() -> str:
    token = secrets.token_urlsafe(32)
    logger.debug(f"event=session_token_generated token_prefix={token[:8]}")
    return token


def _generate_reset_token() -> str:
    token = secrets.token_urlsafe(32)
    logger.debug(f"event=reset_token_generated token_prefix={token[:8]}")
    return token


def _load_json(file_path: Path) -> list:
    try:
        data = json.loads(file_path.read_text())
        logger.debug(f"event=json_load_success file={file_path.name} records={len(data)}")
        return data
    except Exception as e:
        logger.error(f"event=json_load_failed file={file_path.name} error={e}")
        return []


def _save_json(file_path: Path, data: list) -> bool:
    try:
        file_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"event=json_save_success file={file_path.name} records={len(data)}")
        return True
    except Exception as e:
        logger.error(f"event=json_save_failed file={file_path.name} error={e}")
        return False


def register_user(username: str, password: str, email: str) -> Dict[str, Any]:
    start = time.time()
    logger.info(f"event=register_attempt username={username} email={email}")

    if not username or len(username) < 3:
        logger.warning(f"event=register_failed username={username} reason=invalid_username")
        return {"success": False, "message": "Username must be at least 3 characters"}

    if not password or len(password) < 6:
        logger.warning(f"event=register_failed username={username} reason=weak_password")
        return {"success": False, "message": "Password must be at least 6 characters"}

    if not email or "@" not in email:
        logger.warning(f"event=register_failed username={username} reason=invalid_email")
        return {"success": False, "message": "Invalid email address"}

    users = _load_json(_USERS_FILE)

    if any(u["username"] == username for u in users):
        logger.warning(f"event=register_failed username={username} reason=username_exists")
        return {"success": False, "message": "Username already exists"}

    if any(u["email"] == email for u in users):
        logger.warning(f"event=register_failed email={email} reason=email_exists")
        return {"success": False, "message": "Email already registered"}

    hashed_password, salt = _hash_password(password)

    user = {
        "username": username,
        "email": email,
        "password_hash": hashed_password,
        "salt": salt,
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }

    users.append(user)

    if _save_json(_USERS_FILE, users):
        duration = int((time.time() - start) * 1000)
        logger.info(f"event=register_success username={username} duration_ms={duration}")
        return {"success": True, "message": "Registration successful"}
    else:
        logger.error(f"event=register_failed username={username} reason=save_error")
        return {"success": False, "message": "Failed to save user data"}


def sign_in(username: str, password: str) -> Dict[str, Any]:
    start = time.time()
    logger.info(f"event=signin_attempt username={username}")

    users = _load_json(_USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        logger.warning(f"event=signin_failed username={username} reason=user_not_found")
        return {"success": False, "message": "Invalid username or password"}

    if not user.get("is_active", True):
        logger.warning(f"event=signin_failed username={username} reason=inactive_account")
        return {"success": False, "message": "Account is deactivated"}

    if not _verify_password(password, user["password_hash"], user["salt"]):
        logger.warning(f"event=signin_failed username={username} reason=wrong_password")
        return {"success": False, "message": "Invalid username or password"}

    session_token = _generate_session_token()

    sessions = _load_json(_SESSIONS_FILE)
    sessions = [s for s in sessions if s["username"] != username]

    session = {
        "username": username,
        "token": session_token,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }

    sessions.append(session)
    _save_json(_SESSIONS_FILE, sessions)

    duration = int((time.time() - start) * 1000)
    logger.info(f"event=signin_success username={username} token_prefix={session_token[:8]} duration_ms={duration}")

    return {
        "success": True,
        "message": "Sign in successful",
        "session_token": session_token,
        "username": username
    }


def sign_out(session_token: str) -> Dict[str, Any]:
    logger.info(f"event=signout_attempt token_prefix={session_token[:8]}")

    sessions = _load_json(_SESSIONS_FILE)
    session = next((s for s in sessions if s["token"] == session_token), None)

    if not session:
        logger.warning(f"event=signout_failed token_prefix={session_token[:8]} reason=invalid_token")
        return {"success": False, "message": "Invalid session"}

    username = session["username"]
    sessions = [s for s in sessions if s["token"] != session_token]
    _save_json(_SESSIONS_FILE, sessions)

    logger.info(f"event=signout_success username={username} token_prefix={session_token[:8]}")
    return {"success": True, "message": "Signed out successfully"}


def validate_session(session_token: str) -> Optional[str]:
    logger.debug(f"event=session_validate_attempt token_prefix={session_token[:8]}")

    sessions = _load_json(_SESSIONS_FILE)
    session = next((s for s in sessions if s["token"] == session_token), None)

    if not session:
        logger.debug(f"event=session_invalid token_prefix={session_token[:8]} reason=not_found")
        return None

    expires_at = datetime.fromisoformat(session["expires_at"])

    if datetime.now() > expires_at:
        sessions = [s for s in sessions if s["token"] != session_token]
        _save_json(_SESSIONS_FILE, sessions)
        logger.info(f"event=session_expired username={session['username']} token_prefix={session_token[:8]}")
        return None

    logger.debug(f"event=session_valid username={session['username']} token_prefix={session_token[:8]}")
    return session["username"]


def request_password_reset(email: str) -> Dict[str, Any]:
    start = time.time()
    logger.info(f"event=reset_request email={email}")

    users = _load_json(_USERS_FILE)
    user = next((u for u in users if u["email"] == email), None)

    if not user:
        logger.warning(f"event=reset_request_unknown_email email={email}")
        return {"success": True, "message": "If the email exists, a reset token has been generated"}

    reset_token = _generate_reset_token()
    reset_tokens = _load_json(_RESET_TOKENS_FILE)

    reset_tokens = [t for t in reset_tokens if t["username"] != user["username"]]

    token_data = {
        "username": user["username"],
        "email": email,
        "token": reset_token,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
    }

    reset_tokens.append(token_data)
    _save_json(_RESET_TOKENS_FILE, reset_tokens)

    duration = int((time.time() - start) * 1000)
    logger.info(f"event=reset_token_created username={user['username']} token_prefix={reset_token[:8]} duration_ms={duration}")

    return {
        "success": True,
        "message": "Reset token generated",
        "reset_token": reset_token
    }


def reset_password(reset_token: str, new_password: str) -> Dict[str, Any]:
    start = time.time()
    logger.info(f"event=reset_password_attempt token_prefix={reset_token[:8]}")

    if not new_password or len(new_password) < 6:
        logger.warning(f"event=reset_password_failed token_prefix={reset_token[:8]} reason=weak_password")
        return {"success": False, "message": "Password must be at least 6 characters"}

    reset_tokens = _load_json(_RESET_TOKENS_FILE)
    token_data = next((t for t in reset_tokens if t["token"] == reset_token), None)

    if not token_data:
        logger.warning(f"event=reset_password_failed token_prefix={reset_token[:8]} reason=invalid_token")
        return {"success": False, "message": "Invalid or expired reset token"}

    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.now() > expires_at:
        logger.warning(f"event=reset_password_failed username={token_data['username']} reason=expired_token")
        return {"success": False, "message": "Reset token has expired"}

    users = _load_json(_USERS_FILE)
    user = next((u for u in users if u["username"] == token_data["username"]), None)

    if not user:
        logger.error(f"event=reset_password_failed token_prefix={reset_token[:8]} reason=user_missing")
        return {"success": False, "message": "User not found"}

    hashed_password, salt = _hash_password(new_password)
    user["password_hash"] = hashed_password
    user["salt"] = salt
    _save_json(_USERS_FILE, users)

    reset_tokens = [t for t in reset_tokens if t["token"] != reset_token]
    _save_json(_RESET_TOKENS_FILE, reset_tokens)

    sessions = _load_json(_SESSIONS_FILE)
    sessions = [s for s in sessions if s["username"] != token_data["username"]]
    _save_json(_SESSIONS_FILE, sessions)

    duration = int((time.time() - start) * 1000)
    logger.info(f"event=reset_password_success username={token_data['username']} duration_ms={duration}")

    return {"success": True, "message": "Password reset successful"}


def change_password(username: str, old_password: str, new_password: str) -> Dict[str, Any]:
    start = time.time()
    logger.info(f"event=change_password_attempt username={username}")

    if not new_password or len(new_password) < 6:
        logger.warning(f"event=change_password_failed username={username} reason=weak_new_password")
        return {"success": False, "message": "New password must be at least 6 characters"}

    users = _load_json(_USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        logger.error(f"event=change_password_failed username={username} reason=user_missing")
        return {"success": False, "message": "User not found"}

    if not _verify_password(old_password, user["password_hash"], user["salt"]):
        logger.warning(f"event=change_password_failed username={username} reason=wrong_old_password")
        return {"success": False, "message": "Current password is incorrect"}

    hashed_password, salt = _hash_password(new_password)
    user["password_hash"] = hashed_password
    user["salt"] = salt

    if _save_json(_USERS_FILE, users):
        duration = int((time.time() - start) * 1000)
        logger.info(f"event=change_password_success username={username} duration_ms={duration}")
        return {"success": True, "message": "Password changed successfully"}
    else:
        logger.error(f"event=change_password_failed username={username} reason=save_failed")
        return {"success": False, "message": "Failed to update password"}


def get_user_info(username: str) -> Optional[Dict[str, Any]]:
    logger.info(f"event=get_user_info username={username}")
    users = _load_json(_USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        logger.warning(f"event=get_user_info_failed username={username} reason=user_not_found")
        return None

    logger.info(f"event=get_user_info_success username={username}")
    return {
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
        "is_active": user.get("is_active", True)
    }
