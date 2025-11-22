import asyncio
import json
import logging
import time
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Sequence, Type

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BaseTrigger(ABC):
    def __init__(
        self,
        host: str = "localhost:7233",
        namespace: str = "default",
        task_queue: str = "default-queue",
        service_name: str = "default-service",
        workflow_name: str = "DefaultWorkflow",
        max_concurrency: Optional[int] = None,
        web_ui_url: str = "http://localhost:8080",
        params: Optional[Dict[str, Any]] = None,
    ):
        self.host = host
        self.namespace = namespace
        self.task_queue = task_queue
        self.service_name = service_name
        self.workflow_name = workflow_name
        self.max_concurrency = max_concurrency
        self.web_ui_url = web_ui_url
        self.params = params or {}
        self._client: Optional[Client] = None
    
    @abstractmethod
    def get_workflows(self) -> Sequence[Type]:
        pass
    
    @abstractmethod
    def get_activities(self) -> Sequence[object]:
        pass
    
    async def run_worker(self) -> None:
        try:
            workflows = self.get_workflows()
            activities = self.get_activities()
            
            if not workflows and not activities:
                raise ValueError("At least one workflow or activity must be defined")
            
            logger.info(
                "service=%s event=connect host=%s namespace=%s queue=%s",
                self.service_name, self.host, self.namespace, self.task_queue
            )
            
            self._client = await Client.connect(self.host, namespace=self.namespace)
            
            worker = Worker(
                self._client,
                task_queue=self.task_queue,
                workflows=workflows,
                activities=activities,
                max_concurrent_activities=self.max_concurrency,
            )
            
            logger.info("service=%s event=worker_start", self.service_name)
            await worker.run()
            
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("service=%s event=shutdown", self.service_name)
        except Exception:
            logger.exception("service=%s event=error", self.service_name)
            raise
        finally:
            if self._client:
                await self._client.close()
    
    async def trigger_workflow(self, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        client = None
        try:
            logger.info(json.dumps({
                "event": "connect",
                "service": self.service_name,
                "host": self.host,
                "ts": int(time.time())
            }))
            
            client = await Client.connect(self.host)
            
            workflow_id = f"{self.service_name.replace('-', '_')}_{int(time.time())}"
            
            workflow_params = {**self.params, **(params or {})}
            if "service_name" not in workflow_params:
                workflow_params["service_name"] = self.service_name
            
            result = await client.start_workflow(
                self.workflow_name,
                workflow_params,
                id=workflow_id,
                task_queue=self.task_queue,
            )
            
            logger.info(json.dumps({
                "event": "workflow_started",
                "workflow_id": result.id,
                "service": self.service_name,
                "workflow_name": self.workflow_name,
                "task_queue": self.task_queue,
                "web_ui": self.web_ui_url,
                "ts": int(time.time())
            }))
            
            return result.id
            
        except Exception as e:
            logger.error(json.dumps({
                "event": "workflow_start_failed",
                "service": self.service_name,
                "error": str(e),
                "ts": int(time.time())
            }))
            return None
        finally:
            if client and hasattr(client, 'close'):
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(f"Error closing client: {e}")
    
    def run_as_worker(self) -> None:
        asyncio.run(self.run_worker())
    
    def run_as_trigger(self, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        return asyncio.run(self.trigger_workflow(params))