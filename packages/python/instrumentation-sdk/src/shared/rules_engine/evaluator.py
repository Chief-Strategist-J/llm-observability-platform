from typing import Callable, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Rule:
    name: str
    condition: Callable[[Any], bool]
    action: Callable[[Any], Any]
    priority: int = 0

class RulesEngine:
    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        self.rules: List[Rule] = sorted(rules or [], key=lambda r: r.priority, reverse=True)

    def register(self, rule: Rule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def evaluate_first(self, ctx: Any, default: Any = None) -> Any:
        for rule in self.rules:
            if rule.condition(ctx):
                return rule.action(ctx)
        return default

    def evaluate_all(self, ctx: Any) -> List[Any]:
        results = []
        for rule in self.rules:
            if rule.condition(ctx):
                results.append(rule.action(ctx))
        return results
