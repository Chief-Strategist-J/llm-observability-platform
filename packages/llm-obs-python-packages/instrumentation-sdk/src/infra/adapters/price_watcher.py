import os
import yaml
from typing import Any, Dict, List
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler


class PriceConfigHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        super().__init__()
        self.watcher = watcher

    def on_modified(self, event):
        if os.path.basename(event.src_path) == "model_prices.yaml":
            self.watcher.reload()


class PriceWatcherAdapter:
    def __init__(self):
        self._config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "config",
            "model_prices.yaml",
        )
        self._prices_ref = self._load()
        dir_to_watch = os.path.dirname(self._config_path)
        handler = PriceConfigHandler(self)
        try:
            self._observer = Observer()
            self._observer.schedule(handler, path=dir_to_watch, recursive=False)
            self._observer.start()
        except Exception:
            try:
                self._observer = PollingObserver()
                self._observer.schedule(handler, path=dir_to_watch, recursive=False)
                self._observer.start()
            except Exception:
                self._observer = None

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self._config_path, "r") as f:
                return yaml.safe_load(f) or []
        except Exception:
            return []

    def reload(self) -> None:
        new_prices = self._load()
        self._prices_ref = new_prices

    def get_prices(self) -> List[Dict[str, Any]]:
        return self._prices_ref
