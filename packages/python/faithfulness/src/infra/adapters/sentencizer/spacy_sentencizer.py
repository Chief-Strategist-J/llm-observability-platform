from __future__ import annotations

from functools import cached_property


class SpacySentencizerAdapter:
    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        self._model_name = model_name

    @cached_property
    def _nlp(self):
        import spacy
        nlp = spacy.load(self._model_name, disable=["ner", "lemmatizer", "attribute_ruler"])
        return nlp

    def split(self, text: str, min_words: int) -> list[str]:
        doc = self._nlp(text)
        return [
            sent.text.strip()
            for sent in doc.sents
            if len(sent.text.strip().split()) >= min_words
        ]
