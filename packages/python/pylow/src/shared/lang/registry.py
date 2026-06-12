"""Language + predicate registries (declarative guide rules 1 and 3).

LanguageRegistry: WHAT language is this → registry lookup, never if/elif.
PredicateRegistry: WHICH stage rule applies → named predicates evaluated
against a context, never inline conditionals in engines.

Adding a language touches only shared/lang/languages.py (a register() call).
"""
import os
import shutil
from dataclasses import dataclass

from shared.lang.specs import LanguageSpec, StageRule


@dataclass(frozen=True)
class StageContext:
    """Facts a predicate may consult — engines fill this once per call."""
    target: str = ""
    is_dir: bool = False


class PredicateRegistry:
    _predicates: dict = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._predicates[name] = fn
            return fn
        return decorator

    @classmethod
    def passes(cls, when: tuple, ctx: StageContext) -> bool:
        return all(cls._evaluate(term, ctx) for term in when)

    @classmethod
    def _evaluate(cls, term: str, ctx: StageContext) -> bool:
        name, _, arg = term.partition(":")
        predicate = cls._predicates.get(name, cls._predicates["never"])
        return predicate(ctx, arg)


@PredicateRegistry.register("never")
def _(ctx, arg):
    return False


@PredicateRegistry.register("is_dir")
def _(ctx, arg):
    return ctx.is_dir


@PredicateRegistry.register("is_file")
def _(ctx, arg):
    return not ctx.is_dir


@PredicateRegistry.register("tool")
def _(ctx, arg):
    return shutil.which(arg) is not None


@PredicateRegistry.register("has")
def _(ctx, arg):
    root = ctx.target if ctx.is_dir else "."
    return os.path.exists(os.path.join(root, arg))


@PredicateRegistry.register("ext")
def _(ctx, arg):
    return ctx.target.endswith(arg)


class LanguageRegistry:
    _specs: dict = {}
    _aliases: dict = {}
    _extensions: dict = {}

    @classmethod
    def register(cls, spec: LanguageSpec) -> LanguageSpec:
        cls._specs[spec.name] = spec
        for alias in spec.aliases:
            cls._aliases[alias] = spec.name
        for ext in spec.extensions:
            cls._extensions[ext] = spec.name
        return spec

    @classmethod
    def get(cls, name: str) -> LanguageSpec | None:
        canonical = cls._aliases.get(name.lower(), name.lower())
        return cls._specs.get(canonical)

    @classmethod
    def names(cls) -> tuple:
        return tuple(cls._specs)

    @classmethod
    def lang_for_extension(cls, path: str) -> str | None:
        return cls._extensions.get(os.path.splitext(path)[1].lower())

    @classmethod
    def lang_for_markers(cls, present_files: list) -> str | None:
        names = set(present_files)
        matches = (
            spec.name
            for spec in cls._specs.values()
            for marker in spec.markers
            if marker in names
        )
        return min(
            ((cls._marker_priority(spec_name), spec_name) for spec_name in matches),
            default=(None, None),
        )[1]

    @classmethod
    def _marker_priority(cls, spec_name: str) -> int:
        return list(cls._specs).index(spec_name)

    @classmethod
    def resolve_stage(cls, spec: LanguageSpec, stage: str, ctx: StageContext) -> StageRule | None:
        return next(
            (rule for rule in spec.stage_rules(stage) if PredicateRegistry.passes(rule.when, ctx)),
            None,
        )


def pick_tool(tools: tuple) -> str | None:
    """First installed binary from a priority-ordered tuple."""
    return next((t for t in tools if shutil.which(t)), None)


def format_argv(template: tuple, mapping: dict) -> list:
    """Expand argv templates: pure '{key}' tokens substitute (lists splice,
    empty values drop out); every other token passes through literally."""
    expanded: list = []
    for token in template:
        key = token[1:-1] if token.startswith("{") and token.endswith("}") else None
        if key is None:
            expanded.append(token)
            continue
        value = mapping.get(key, "")
        if isinstance(value, (list, tuple)):
            expanded.extend(str(v) for v in value)
        elif value:
            expanded.append(str(value))
    return expanded
