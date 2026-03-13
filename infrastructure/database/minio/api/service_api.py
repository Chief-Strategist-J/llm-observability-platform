import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.minio.setup.minio_setup_activity import setup_minio_activity, teardown_minio_activity
from infrastructure.database.shared.base_service_api import create_database_service_app

app = create_database_service_app(
    service_name="minio",
    setup_fn=setup_minio_activity,
    teardown_fn=teardown_minio_activity
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8105)
