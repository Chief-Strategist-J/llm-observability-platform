from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Type
from abc import ABC, abstractmethod

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerConfig:
    host: str
    queue: str
    port: int | None = None
    namespace: str | None = None
    max_concurrency: int | None = None


class BaseWorker(ABC):
    def __init__(self, config: WorkerConfig):
        self.config = config

    @property
    @abstractmethod
    def workflows(self) -> Sequence[Type]:
        pass

    @property
    @abstractmethod
    def activities(self) -> Sequence[object]:
        pass

    async def run(self) -> None:
        svc = self.__class__.__name__
        fn = f"{svc}.run"
        client: Optional[Client] = None
        try:
            if not self.config.host:
                raise ValueError("config.host is required")
            if not self.config.queue:
                raise ValueError("config.queue is required")
            if not self.workflows and not self.activities:
                raise ValueError("At least one workflow or activity must be defined")

            logger.info(
                "service=%s function=%s event=prepare_connection host=%s port=%s namespace=%s",
                svc, fn, self.config.host, self.config.port, self.config.namespace
            )

            host = self.config.host
            if self.config.port is not None:
                host = f"{host}:{self.config.port}"

            namespace = self.config.namespace or "default"

            logger.info(
                "service=%s function=%s event=connect host=%s namespace=%s",
                svc, fn, host, namespace
            )

            client = await Client.connect(host, namespace=namespace)

            logger.info(
                "service=%s function=%s event=initialize_worker queue=%s workflows=%s activities=%s max_concurrency=%s",
                svc, fn, self.config.queue, len(self.workflows), len(self.activities), self.config.max_concurrency
            )

            worker = Worker(
                client,
                task_queue=self.config.queue,
                workflows=self.workflows,
                activities=self.activities,
                max_concurrent_activities=self.config.max_concurrency,
            )

            logger.info("service=%s function=%s event=worker_start", svc, fn)
            await worker.run()
            logger.info("service=%s function=%s event=worker_stop", svc, fn)

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("service=%s function=%s event=shutdown_signal", svc, fn)
        except TimeoutError:
            logger.error("service=%s function=%s event=connection_timeout", svc, fn)
            raise
        except ValueError as e:
            logger.error("service=%s function=%s event=invalid_configuration error=%s", svc, fn, str(e))
            raise
        except Exception:
            logger.exception("service=%s function=%s event=unexpected_error", svc, fn)
            raise
        finally:
            if client:
                logger.info("service=%s function=%s event=client_closing", svc, fn)
                await client.shutdown()
                logger.info("service=%s function=%s event=client_closed", svc, fn)
