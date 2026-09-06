from __future__ import annotations

import sys
from pathlib import Path
import httpx

local_src = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(local_src))

for mod_name in list(sys.modules.keys()):
    if mod_name.split(".")[0] in ["shared", "features", "worker", "infra", "api"]:
        mod = sys.modules[mod_name]
        file_path = getattr(mod, "__file__", None)
        if file_path and not file_path.startswith(str(local_src)):
            del sys.modules[mod_name]

_orig_client_init = httpx.Client.__init__


def _patched_client_init(self, *args, **kwargs):
    kwargs.pop("app", None)
    _orig_client_init(self, *args, **kwargs)


httpx.Client.__init__ = _patched_client_init
