from typing import Tuple, Any
from .service import PiiInjectionScanService
from .infra.adapters.aho_corasick_scanner_adapter import AhoCorasickScannerAdapter

_SCANNER = AhoCorasickScannerAdapter()
_SERVICE = PiiInjectionScanService(_SCANNER)

def scan_prompt(prompt: Any) -> Tuple[bool, bool]:
    return _SERVICE.scan_prompt(prompt)
