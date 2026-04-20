import pytest
from services.llm.registry import PROVIDER_REGISTRY
from services.llm.base.llm import BaseLLM


def test_registry_contains_all_expected_providers():
    expected = {"local", "openai", "anthropic", "gemini", "grok", "mistral", "huggingface"}
    assert expected == set(PROVIDER_REGISTRY.keys())


def test_all_registered_classes_are_subclasses_of_base_llm():
    for name, cls in PROVIDER_REGISTRY.items():
        assert issubclass(cls, BaseLLM), f"{name} does not extend BaseLLM"


def test_registry_values_are_classes_not_instances():
    for name, cls in PROVIDER_REGISTRY.items():
        assert isinstance(cls, type), f"{name} registry value is not a class"


def test_adding_new_provider_to_registry():
    from services.llm.base.llm import BaseLLM

    class TestProvider(BaseLLM):
        def generate(self, prompt, **kwargs): return ""
        def stream_generate(self, prompt, **kwargs): yield ""
        async def generate_async(self, prompt, **kwargs): return ""
        async def astream_generate(self, prompt, **kwargs): yield ""

    extended = {**PROVIDER_REGISTRY, "test": TestProvider}
    assert "test" in extended
    assert issubclass(extended["test"], BaseLLM)
