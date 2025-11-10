import os
import glob
from typing import List
from abc import ABC, abstractmethod
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import LogDiscoveryConfig

class AbstractLogDiscoveryService(ABC):
    @abstractmethod
    def discover(self) -> List[str]:
        ...

class LocalLogDiscoveryService(AbstractLogDiscoveryService):
    def __init__(self, config: LogDiscoveryConfig):
        self.cfg = config.discovery

    def discover(self) -> List[str]:
        result = []

        for base in self.cfg.search_paths:
            if not os.path.isdir(base):
                continue

            for pattern in self.cfg.include_patterns:
                path_pattern = (
                    os.path.join(base, "**", pattern)
                    if self.cfg.recursive
                    else os.path.join(base, pattern)
                )

                matches = glob.glob(path_pattern, recursive=self.cfg.recursive)

                for f in matches:
                    if not os.path.isfile(f):
                        continue

                    if any(f.endswith(x.replace("*", "")) for x in self.cfg.exclude_patterns):
                        continue

                    result.append(os.path.realpath(f) if self.cfg.follow_symlinks else f)

        return sorted(set(result))
