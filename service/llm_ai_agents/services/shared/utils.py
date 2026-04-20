import os


def project_root() -> str:
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def resolve_path(relative: str) -> str:
    return os.path.join(project_root(), relative)
