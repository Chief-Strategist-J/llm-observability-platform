import pathlib
from typing import List, Optional
import logging
from temporalio import activity

logger = logging.getLogger(__name__)

class FileDiscoveryManager:
    def __init__(self, search_paths: List[str], include_patterns: Optional[List[str]] = None):
        self.search_paths = search_paths
        self.include_patterns = include_patterns or ["*.log", "*.out", "*.txt"]

    def discover(self) -> List[str]:
        files = []
        for base_path in self.search_paths:
            p = pathlib.Path(base_path)
            if not p.exists():
                continue
            for pattern in self.include_patterns:
                for match in p.rglob(pattern):
                    if match.is_file():
                        files.append(str(match.resolve()))
        return files

@activity.defn
async def discover_log_files_activity(
    search_paths: List[str],
    include_patterns: Optional[List[str]] = None
) -> List[str]:
    return FileDiscoveryManager(search_paths, include_patterns).discover()

if __name__ == "__main__":
    manager = FileDiscoveryManager(["./logs", "/var/log"], ["*.log"])
    result = manager.discover()
    print(result)
