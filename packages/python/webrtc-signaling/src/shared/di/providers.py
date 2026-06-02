from src.features.signal_session.service import SessionManagerService
from src.infra.adapters.memory.session_store_adapter import MemorySessionStoreAdapter


def build_session_manager() -> SessionManagerService:
    store = MemorySessionStoreAdapter()
    return SessionManagerService(store=store)
