"""REST router placeholders."""


def health() -> dict[str, str]:
    return {"status": "ok"}
