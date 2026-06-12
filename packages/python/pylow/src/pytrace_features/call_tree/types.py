from dataclasses import dataclass


@dataclass
class CallTreeRequest:
    """Input DTO for a call-tree capture."""
    target: str = ""
    pid: int = 0
    lang: str = ""            # override detected language
    filter: str = ""          # only frames matching this path/package fragment
    depth: int = 25
    duration: float = 15.0    # window for attach-mode backends
    out: str = ""             # output file (default pylow_calltree_<lang>.txt)
    args: str = ""            # program arguments (launch mode)

    def out_file(self, lang: str) -> str:
        return self.out or f"pylow_calltree_{lang}.txt"

    def arg_list(self) -> list:
        return self.args.split() if self.args else []
