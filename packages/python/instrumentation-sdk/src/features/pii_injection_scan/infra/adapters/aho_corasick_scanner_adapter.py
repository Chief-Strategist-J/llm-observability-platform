import os
import re
import yaml
from typing import Tuple, List, Dict, Any, Set
from ...ports import PatternScannerPort
from .aho_corasick import AhoCorasickAutomaton

class AhoCorasickScannerAdapter(PatternScannerPort):
    def __init__(self) -> None:
        self._automaton = AhoCorasickAutomaton()
        self._regex_patterns: List[Tuple[re.Pattern, str, str]] = []
        self._load_patterns()

    def _get_patterns_file_path(self) -> str:
        path = "/etc/llm-obs/patterns.yaml"
        if os.path.exists(path):
            return path
        env_path = os.getenv("LLM_OBS_PATTERNS_FILE")
        if env_path and os.path.exists(env_path):
            return env_path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sdk_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
        local_path = os.path.join(sdk_root, "config", "patterns.yaml")
        if os.path.exists(local_path):
            return local_path
        return path

    def _load_patterns(self) -> None:
        path = self._get_patterns_file_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            patterns = data.get("patterns", [])
            for pattern in patterns:
                p_name = pattern.get("name", "")
                p_type = pattern.get("type", "")
                regex_str = pattern.get("regex")
                phrases = pattern.get("phrases", [])
                phrase = pattern.get("phrase")
                if phrase:
                    phrases.append(phrase)
                for ph in phrases:
                    self._automaton.add_keyword(ph.lower(), p_type)
                if regex_str:
                    try:
                        compiled = re.compile(regex_str)
                        self._regex_patterns.append((compiled, p_type, p_name))
                    except Exception:
                        pass
            self._automaton.build()
        except Exception:
            pass

    def _extract_text(self, prompt: Any) -> List[str]:
        if isinstance(prompt, str):
            return [prompt]
        if isinstance(prompt, list):
            texts = []
            for msg in prompt:
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str):
                        texts.append(content)
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                txt = part.get("text")
                                if isinstance(txt, str):
                                    texts.append(txt)
            return texts
        return []

    def scan(self, prompt: Any) -> Tuple[bool, bool]:
        texts = self._extract_text(prompt)
        pii_detected = False
        injection_attempt = False
        for text in texts:
            lowered_text = text.lower()
            matched_types = self._automaton.search(lowered_text)
            if "PII_STRUCTURAL" in matched_types or "FORBIDDEN_TOPIC" in matched_types:
                pii_detected = True
            if "JAILBREAK_PHRASE" in matched_types or "INJECTION_ATTEMPT" in matched_types:
                injection_attempt = True
            for regex_pat, p_type, p_name in self._regex_patterns:
                if regex_pat.search(text):
                    if p_type in ("PII_STRUCTURAL", "FORBIDDEN_TOPIC"):
                        pii_detected = True
                    if p_type in ("JAILBREAK_PHRASE", "INJECTION_ATTEMPT"):
                        injection_attempt = True
        return pii_detected, injection_attempt
