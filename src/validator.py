"""Checks SQL written by the LLM before it touches the database."""
import re

ALLOWED_TABLES = {"v_sales"}   # the agent only gets the joined view
BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|reindex|truncate)\b", re.I)


def validate_sql(sql, max_rows=200):
    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise ValueError("empty query")
    if ";" in sql:
        raise ValueError("only one statement allowed")
    if "--" in sql or "/*" in sql:
        raise ValueError("comments not allowed")
    if not re.match(r"^(select|with)\b", sql, re.I):
        raise ValueError("query must start with SELECT or WITH")
    if BLOCKED.search(sql):
        raise ValueError("query contains a blocked keyword")

    # names defined by CTEs (WITH x AS (...)) are fine to select from
    ctes = {m.lower() for m in re.findall(r"\b(\w+)\s+as\s*\(", sql, re.I)}
    used = {t.lower() for t in re.findall(r"\b(?:from|join)\s+([A-Za-z_]\w*)", sql, re.I)}
    bad = used - ALLOWED_TABLES - ctes
    if bad:
        raise ValueError(f"table not allowed: {', '.join(sorted(bad))}")

    if not re.search(r"\blimit\s+\d+", sql, re.I):
        sql += f" LIMIT {max_rows}"
    return sql
