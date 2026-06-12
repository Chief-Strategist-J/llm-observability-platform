from dataclasses import dataclass


@dataclass
class DebugRequest:
    """Input DTO for interactive debugging and step-snapshot runs."""
    target: str = ""
    breaks: tuple = ()        # "file:line" or function names
    watches: tuple = ()       # expressions captured at every stop
    lang: str = ""            # override detected language
    out: str = "pylow_steps"  # snapshot directory
    max_steps: int = 50
    args: str = ""

    def arg_list(self) -> list:
        return self.args.split() if self.args else []
