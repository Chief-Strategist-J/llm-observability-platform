import os
import pytest
import tempfile
import yaml
from services.shared.config_loader import load_yaml_config
from services.shared.exceptions import ConfigNotFoundError


def _write_tmp_config(content: dict, relative_to_root: str, tmp_path) -> str:
    abs_path = tmp_path / relative_to_root
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "w") as f:
        yaml.dump(content, f)
    return relative_to_root


def test_load_valid_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "services.shared.config_loader._project_root",
        lambda: str(tmp_path),
    )
    cfg_file = tmp_path / "configs" / "test.yaml"
    cfg_file.parent.mkdir(parents=True)
    cfg_file.write_text("model:\n  id: test-model\n  provider: fake\n")

    result = load_yaml_config("configs/test.yaml")

    assert result["model"]["id"] == "test-model"
    assert result["model"]["provider"] == "fake"


def test_load_empty_yaml_returns_empty_dict(tmp_path, monkeypatch):
    monkeypatch.setattr("services.shared.config_loader._project_root", lambda: str(tmp_path))
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")

    result = load_yaml_config("empty.yaml")

    assert result == {}


def test_missing_file_raises_config_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("services.shared.config_loader._project_root", lambda: str(tmp_path))

    with pytest.raises(ConfigNotFoundError) as exc_info:
        load_yaml_config("does/not/exist.yaml")

    assert "does/not/exist.yaml" in str(exc_info.value)


def test_nested_yaml_structure(tmp_path, monkeypatch):
    monkeypatch.setattr("services.shared.config_loader._project_root", lambda: str(tmp_path))
    cfg_file = tmp_path / "nested.yaml"
    cfg_file.write_text("model:\n  parameters:\n    temperature: 0.9\n    max_tokens: 256\n")

    result = load_yaml_config("nested.yaml")

    assert result["model"]["parameters"]["temperature"] == 0.9
    assert result["model"]["parameters"]["max_tokens"] == 256
