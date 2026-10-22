from dotenv import load_dotenv
load_dotenv()
import os
import re
import requests
import pandas as pd
from .db import connect_ro
from .validator import validate_sql
from . import queries

PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SCHEMA = """SQLite view v_sales (one row per order line):
order_id, order_date (YYYY-MM-DD text), ship_mode, customer_id, customer_name,
segment, region, state, product_id, product_name, category, sub_category,
sales (revenue), quantity, discount (0 to 1), profit.
Use strftime('%Y-%m', order_date) for months. Only use v_sales."""


def ask_llm(prompt):
    if PROVIDER == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        r = requests.post(url, headers={"x-goog-api-key": os.getenv("GEMINI_API_KEY", "")},
                          json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                      json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=180)
    r.raise_for_status()
    return r.json()["response"]


def extract_sql(text):
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    if m:
        text = m.group(1)
    m = re.search(r"\b(select|with)\b", text, re.I)
    return text[m.start():].strip() if m else text.strip()


def question_to_sql(question, last_error=None):
    prompt = (f"{SCHEMA}\n\nWrite ONE SQLite SELECT query that answers the question. "
              "Return only the SQL, no explanation, no markdown.\n")
    if last_error:
        prompt += f"Your previous query failed with: {last_error}. Fix it.\n"
    prompt += f"Question: {question}"
    return extract_sql(ask_llm(prompt))


def ask_data(question, retries=2):
    """Returns dict with sql, table, error."""
    error = None
    for _ in range(retries + 1):
        sql = ""
        try:
            sql = validate_sql(question_to_sql(question, error))
            con = connect_ro()
            try:
                table = pd.read_sql_query(sql, con)
            finally:
                con.close()
            return {"sql": sql, "table": table, "error": None}
        except Exception as e:      # validation error or SQL error, try again with the message
            error = str(e)
    return {"sql": sql, "table": None, "error": error}


def explain(question, table):
    """The LLM only sees the real result table and must stick to it."""
    prompt = (
        "You are a retail business analyst. Answer using ONLY the numbers in the table below. "
        "Do not invent figures. If the data does not prove a cause, say it is only a possible reason. "
        "Give a short answer, then 2-3 recommended actions.\n\n"
        f"Question: {question}\n\nData:\n{table.head(30).to_string(index=False)}"
    )
    return ask_llm(prompt)


def investigate_profit(month):
    """Fixed queries first, then the LLM explains. Evidence comes from SQL, not from the model."""
    changes = queries.category_change(month)
    bands = queries.discount_bands()
    evidence = (f"Category profit vs previous month:\n{changes.to_string(index=False)}\n\n"
                f"Profit by discount band (all time):\n{bands.to_string(index=False)}")
    prompt = (
        f"Why did profit change in {month}? Use ONLY the tables below, quote the numbers you rely on, "
        "say clearly whether discounts support the explanation or not, then give 2-3 actions.\n\n" + evidence)
    return changes, bands, ask_llm(prompt)
