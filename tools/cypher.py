# tools/cypher.py
from typing import Any, List
from graph import graph

def _fmt(rows: List[dict]) -> str:
    if not rows:
        return "No results."
    # pretty print small tables
    keys = list(rows[0].keys())
    header = " | ".join(keys)
    sep = "-|-".join("---" for _ in keys)
    body = "\n".join(" | ".join(str(r.get(k, "")) for k in keys) for r in rows)
    return header + "\n" + sep + "\n" + body

def cypher_qa(question: str) -> str:
    """
    Very simple heuristic:
    - If the question seems like a title search, do a CONTAINS on :Movie.title.
    - Else list a few movies as a fallback.
    Extend this later with an LLM->Cypher translator.
    """
    q = question.strip()

    # naive title capture between quotes
    title = None
    if '"' in q:
        try:
            title = q.split('"')[1]
        except Exception:
            title = None
    if "'" in q and title is None:
        try:
            title = q.split("'")[1]
        except Exception:
            title = None

    try:
        if title:
            rows = graph.query(
                """
                MATCH (m:Movie)
                WHERE toLower(m.title) CONTAINS toLower($q)
                RETURN m.title AS title, m.tagline AS tagline, m.released AS released
                ORDER BY m.released DESC
                LIMIT 5
                """,
                {"q": title},
            )
            return _fmt(rows)

        # generic fallback
        rows = graph.query(
            """
            MATCH (m:Movie)
            RETURN m.title AS title, m.released AS released
            ORDER BY m.released DESC
            LIMIT 5
            """
        )
        return _fmt(rows)
    except Exception as e:
        return f"Cypher error: {e}"
