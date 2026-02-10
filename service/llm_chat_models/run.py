import sys
import os
SERVICE_ROOT = os.path.dirname(os.path.abspath(__file__))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)
import uvicorn
from config.settings import API_HOST, API_PORT
from gateway.app import create_app
app = create_app()
if __name__ == '__main__':
    import asyncio
    import signal
    from config.settings import API_HOST, API_PORT, GRACEFUL_SHUTDOWN_TIMEOUT
    from logic.workflows.engine import WorkflowEngine
    from telemetry.logger import log_event
    engine = WorkflowEngine()

    async def main():
        config = uvicorn.Config(app, host=API_HOST, port=API_PORT, reload=True, reload_dirs=[SERVICE_ROOT])
        server = uvicorn.Server(config)
        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()

        def signal_handler():
            log_event('shutdown_signal_received')
            shutdown_event.set()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        server_task = asyncio.create_task(server.serve())
        await shutdown_event.wait()
        log_event('shutdown_sequence_start')
        server.should_exit = True
        await server_task
        await engine.drain(timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
        engine.close()
        log_event('shutdown_sequence_complete')
    asyncio.run(main())