from typing import Tuple, Any
from .ports import PatternScannerPort

class PiiInjectionScanService:
    def __init__(self, scanner: PatternScannerPort):
        self._scanner = scanner

    def scan_prompt(self, prompt: Any) -> Tuple[bool, bool]:
        return self._scanner.scan(prompt)
