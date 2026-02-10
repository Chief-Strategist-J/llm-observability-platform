import datetime
from typing import Any, Dict, List, Optional
from infrastructure.database.mongodb.client.mongodb_client import get_client, get_db, get_collection, create_document, find_one, find_many, update_document, delete_document, create_index, create_ttl_index
from config.settings import MONGO_URI, MONGO_DB_NAME
_client = None
_db = None

def _get_db():
    global _client, _db
    if _db is None:
        _client = get_client(MONGO_URI, appname='ai-agents-service')
        _db = get_db(_client, MONGO_DB_NAME)
    return _db

def _ensure_indexes():
    db = _get_db()
    wf_col = get_collection(db, 'ai_agent_workflows')
    create_index(wf_col, ['status'])
    create_index(wf_col, ['metadata.name'])
    steps_col = get_collection(db, 'ai_agent_steps')
    create_index(steps_col, ['workflow_id', 'step_name'], unique=True)
    events_col = get_collection(db, 'ai_agent_events')
    create_index(events_col, ['event_name', 'acknowledged'])
    create_ttl_index(events_col, 'created_at', 86400)
_indexes_created = False

def _init():
    global _indexes_created
    if not _indexes_created:
        _ensure_indexes()
        _indexes_created = True

class MongoWorkflowStore:

    def __init__(self):
        _init()
        self._db = _get_db()

    @property
    def workflows(self):
        return get_collection(self._db, 'ai_agent_workflows')

    @property
    def steps(self):
        return get_collection(self._db, 'ai_agent_steps')

    @property
    def events(self):
        return get_collection(self._db, 'ai_agent_events')

    def save_workflow(self, workflow_data: Dict[str, Any]) -> str:
        doc = {**workflow_data}
        if 'started_at' in doc and isinstance(doc['started_at'], datetime.datetime):
            doc['started_at'] = doc['started_at'].isoformat()
        if 'completed_at' in doc and isinstance(doc['completed_at'], datetime.datetime):
            doc['completed_at'] = doc['completed_at'].isoformat()
        existing = find_one(self.workflows, {'workflow_id': doc['workflow_id']})
        if existing:
            update_document(self.workflows, existing['_id'], doc)
            return existing['_id']
        return create_document(self.workflows, doc)

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return find_one(self.workflows, {'workflow_id': workflow_id})

    def list_workflows(self, status: Optional[str]=None, limit: int=100) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query['status'] = status
        return find_many(self.workflows, query, sort_by='created_at', sort_order=-1, limit=limit)

    def update_workflow_status(self, workflow_id: str, status: str, **extra_fields) -> bool:
        existing = find_one(self.workflows, {'workflow_id': workflow_id})
        if not existing:
            return False
        update_data = {'status': status, **extra_fields}
        return update_document(self.workflows, existing['_id'], update_data)

    def save_step_result(self, workflow_id: str, step_name: str, result: Any) -> str:
        existing = find_one(self.steps, {'workflow_id': workflow_id, 'step_name': step_name})
        doc = {'workflow_id': workflow_id, 'step_name': step_name, 'result': result, 'completed_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if existing:
            update_document(self.steps, existing['_id'], doc)
            return existing['_id']
        return create_document(self.steps, doc)

    def get_step_result(self, workflow_id: str, step_name: str) -> Optional[Any]:
        doc = find_one(self.steps, {'workflow_id': workflow_id, 'step_name': step_name})
        if doc:
            return doc.get('result')
        return None

    def get_completed_steps(self, workflow_id: str) -> Dict[str, Any]:
        docs = find_many(self.steps, {'workflow_id': workflow_id})
        return {doc['step_name']: doc.get('result') for doc in docs}

    def save_event(self, event_name: str, payload: Any=None) -> str:
        doc = {'event_name': event_name, 'payload': payload, 'acknowledged': False, 'created_at': datetime.datetime.now(datetime.timezone.utc)}
        return create_document(self.events, doc)

    def poll_event(self, event_name: str) -> Optional[Dict[str, Any]]:
        return find_one(self.events, {'event_name': event_name, 'acknowledged': False})

    def ack_event(self, event_id: str) -> bool:
        return update_document(self.events, event_id, {'acknowledged': True})

    def delete_workflow(self, workflow_id: str) -> bool:
        existing = find_one(self.workflows, {'workflow_id': workflow_id})
        if not existing:
            return False
        delete_document(self.workflows, existing['_id'])
        steps = find_many(self.steps, {'workflow_id': workflow_id})
        for s in steps:
            delete_document(self.steps, s['_id'])
        return True

    def close(self):
        global _client, _db, _indexes_created
        if _client:
            _client.close()
            _client = None
            _db = None
            _indexes_created = False