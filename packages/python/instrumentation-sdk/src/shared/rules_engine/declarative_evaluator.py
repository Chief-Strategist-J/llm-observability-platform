import re
from typing import Any, List, TypedDict, Callable, Dict

class DeclarativeRuleSpec(TypedDict, total=False):
    id: str
    match_type: str  # "exact" | "contains" | "regex" | "in_list" | "default"
    patterns: List[str]
    value: Any
    priority: int

def normalize_text(text: Any) -> str:
    normalized = str(text or "").strip()
    normalized = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', normalized)
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    return normalized.lower()

MATCH_STRATEGIES: Dict[str, Callable[[str, List[str]], bool]] = {
    "exact": lambda inp, pats: inp in pats,
    "contains": lambda inp, pats: any(p in inp for p in pats),
    "in_list": lambda inp, pats: inp in pats,
    "regex": lambda inp, pats: any(re.search(p, inp) for p in pats),
    "default": lambda inp, pats: True,
}

class DeclarativeRulesEngine:
    def __init__(self, rules_data: List[DeclarativeRuleSpec]) -> None:
        self.rules = sorted(rules_data, key=lambda r: r.get("priority", 0), reverse=True)

    def evaluate(self, input_val: Any, default: Any = None) -> Any:
        normalized_input = normalize_text(input_val)
        
        def _match_rule(rule: DeclarativeRuleSpec) -> bool:
            match_type = rule.get("match_type", "exact")
            patterns = list(map(normalize_text, rule.get("patterns", [])))
            strategy = MATCH_STRATEGIES.get(match_type, MATCH_STRATEGIES["exact"])
            return strategy(normalized_input, patterns)

        matching_rules = list(filter(_match_rule, self.rules))
        return matching_rules[0].get("value") if matching_rules else default
