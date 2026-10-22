import pytest
from src.validator import validate_sql
from src import agent


def test_select_gets_limit():
    assert validate_sql("SELECT * FROM v_sales").endswith("LIMIT 200")


def test_cte_allowed():
    validate_sql("WITH m AS (SELECT category, SUM(sales) s FROM v_sales GROUP BY 1) SELECT * FROM m")


@pytest.mark.parametrize("bad", [
    "DROP TABLE orders",
    "SELECT * FROM v_sales; DELETE FROM orders",
    "SELECT * FROM customers",
    "UPDATE v_sales SET profit = 0",
    "SELECT * FROM v_sales -- hi",
    "PRAGMA table_info(orders)",
])
def test_bad_sql_rejected(bad):
    with pytest.raises(ValueError):
        validate_sql(bad)


def test_agent_retries_after_bad_sql(monkeypatch):
    answers = iter(["DROP TABLE orders", "SELECT category, SUM(profit) AS p FROM v_sales GROUP BY 1"])
    monkeypatch.setattr(agent, "ask_llm", lambda prompt: next(answers))
    out = agent.ask_data("profit by category?")
    assert out["error"] is None and len(out["table"]) > 0
