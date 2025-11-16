import os
import sys
import yaml
import tempfile
import shutil
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(h)


@dataclass(frozen=True)
class DiscoverySection:
    search_paths: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    recursive: bool = True
    follow_symlinks: bool = False


@dataclass(frozen=True)
class LabelsSection:
    values: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchSection:
    enabled: bool = True
    size: int = 100
    flush_interval_seconds: int = 5


@dataclass(frozen=True)
class ShipSection:
    protocol: str = "loki"
    endpoint: str = "http://localhost:3100"
    timeout_seconds: int = 10


@dataclass(frozen=True)
class LogDiscoveryConfig:
    version: int
    discovery: DiscoverySection
    labels: LabelsSection
    batch: BatchSection
    ship: ShipSection


class ConfigStore(ABC):
    @abstractmethod
    def ensure_exists(self) -> LogDiscoveryConfig:
        ...

    @abstractmethod
    def load(self) -> LogDiscoveryConfig:
        ...

    @abstractmethod
    def save(self, config: LogDiscoveryConfig) -> None:
        ...

    @abstractmethod
    def update(self, updates: Dict[str, Any]) -> LogDiscoveryConfig:
        ...

    @abstractmethod
    def delete(self) -> None:
        ...

    @abstractmethod
    def validate_raw(self, raw: Dict[str, Any]) -> Tuple[bool, List[str]]:
        ...

    @abstractmethod
    def default_config(self) -> LogDiscoveryConfig:
        ...


def deep_merge_dicts(a: dict, b: dict) -> dict:
    result = {**a}
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge_dicts(result[k], v)
        else:
            result[k] = v
    return result


class FileConfigStore(ConfigStore):
    DEFAULT_PATH = Path("infrastructure/observability_platform/ingest/config/log_discovery_config.yaml")

    def __init__(self, config_path: Optional[str] = None):
        self.path = Path(config_path) if config_path else self.DEFAULT_PATH

    def ensure_parent_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("ensured parent dir exists: %s", str(self.path.parent))

    def default_config(self) -> LogDiscoveryConfig:
        return LogDiscoveryConfig(
            version=1,
            discovery=DiscoverySection(
                search_paths=["/var/log", "./logs"],
                include_patterns=["*.log", "*.out", "*.txt"],
                exclude_patterns=["*.gz", "*.zip"],
                recursive=True,
                follow_symlinks=False,
            ),
            labels=LabelsSection(values={"environment": "development", "source": "application_stdout"}),
            batch=BatchSection(enabled=True, size=200, flush_interval_seconds=5),
            ship=ShipSection(protocol="loki", endpoint="http://localhost:3100", timeout_seconds=10),
        )

    def ensure_exists(self) -> LogDiscoveryConfig:
        self.ensure_parent_dir()
        if not self.path.exists():
            cfg = self.default_config()
            self.save(cfg)
            return cfg
        cfg = self.load()
        if not getattr(cfg, "ship", None):
            default = self.default_config()
            merged = {
                "version": cfg.version,
                "discovery": asdict(cfg.discovery),
                "labels": cfg.labels.values,
                "batch": asdict(cfg.batch),
                "ship": asdict(default.ship),
            }
            cfg = self._dict_to_dataclass(merged)
            self.save(cfg)
        return cfg

    def load(self) -> LogDiscoveryConfig:
        self.ensure_parent_dir()
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found: {self.path}")
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        good, errs = self.validate_raw(raw)
        if not good:
            raise ValueError(f"Config validation failed: {errs}")
        return self._dict_to_dataclass(raw)

    def save(self, config: LogDiscoveryConfig) -> None:
        self.ensure_parent_dir()
        data = self._to_serializable_dict(config)
        fd, tmp_path = tempfile.mkstemp(dir=str(self.path.parent))
        os.close(fd)
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        shutil.move(tmp_path, str(self.path))
        logger.info("saved config to %s", str(self.path))

    def update(self, updates: Dict[str, Any]) -> LogDiscoveryConfig:
        self.ensure_parent_dir()
        existing = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        merged = deep_merge_dicts(existing, updates)
        good, errs = self.validate_raw(merged)
        if not good:
            raise ValueError(f"Update validation failed: {errs}")
        cfg = self._dict_to_dataclass(merged)
        self.save(cfg)
        return cfg

    def delete(self) -> None:
        if self.path.exists():
            self.path.unlink()
            logger.info("deleted config file %s", str(self.path))

    def validate_raw(self, raw: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if not isinstance(raw.get("version", None), int):
            errors.append("version must be an integer")
        return (len(errors) == 0), errors

    def _dict_to_dataclass(self, raw: Dict[str, Any]) -> LogDiscoveryConfig:
        return LogDiscoveryConfig(
            version=int(raw.get("version", 1)),
            discovery=DiscoverySection(**raw.get("discovery", {})),
            labels=LabelsSection(values=raw.get("labels", {})),
            batch=BatchSection(**raw.get("batch", {})),
            ship=ShipSection(**raw.get("ship", {})),
        )

    def _to_serializable_dict(self, config: LogDiscoveryConfig) -> Dict[str, Any]:
        out = asdict(config)
        return {
            "version": out["version"],
            "discovery": out["discovery"],
            "labels": out["labels"]["values"],
            "batch": out["batch"],
            "ship": out["ship"],
        }
