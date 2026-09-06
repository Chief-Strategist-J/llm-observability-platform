from typing import Protocol, Tuple, Any

class PatternScannerPort(Protocol):
    def scan(self, prompt: Any) -> Tuple[bool, bool]:
        pass
