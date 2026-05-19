from collections import deque
from typing import Dict, Set, Optional

class AhoCorasickNode:
    def __init__(self) -> None:
        self.children: Dict[str, AhoCorasickNode] = {}
        self.fail: Optional[AhoCorasickNode] = None
        self.output: Set[str] = set()

class AhoCorasickAutomaton:
    def __init__(self) -> None:
        self.root = AhoCorasickNode()

    def add_keyword(self, keyword: str, pattern_name: str) -> None:
        if not keyword:
            return
        node = self.root
        for char in keyword:
            if char not in node.children:
                node.children[char] = AhoCorasickNode()
            node = node.children[char]
        node.output.add(pattern_name)

    def build(self) -> None:
        queue = deque()
        for char, child in self.root.children.items():
            child.fail = self.root
            queue.append(child)
        while queue:
            current = queue.popleft()
            for char, child in current.children.items():
                fail_state = current.fail
                while fail_state is not None and char not in fail_state.children:
                    fail_state = fail_state.fail
                child.fail = fail_state.children[char] if fail_state is not None else self.root
                child.output.update(child.fail.output)
                queue.append(child)

    def search(self, text: str) -> Set[str]:
        matched_patterns: Set[str] = set()
        node = self.root
        for char in text:
            while node is not None and char not in node.children:
                node = node.fail
            node = node.children[char] if node is not None else self.root
            if node.output:
                matched_patterns.update(node.output)
        return matched_patterns
