# Sales Analyst Agent

A small analytics app for a retail dataset. You can look at KPIs, find risky products, and ask questions in plain English. A free LLM turns the question into SQL, the SQL is checked, then run on a read-only database, and the answer is explained using only the returned numbers.


<img width="2284" height="1444" alt="dashboard" src="https://github.com/user-attachments/assets/dc39ac6c-296f-4ff9-a2a7-400da19a6b3e" />


## Stack
SQLite, Python (pandas), Streamlit, Plotly, Power BI, a free LLM (Ollama locally or Gemini free tier).

## How it works
question -> LLM writes SQL -> validator -> read-only SQLite -> result table -> LLM explains from that table

- `src/validator.py`: only a single SELECT/WITH on `v_sales`, no comments, blocked keywords, auto LIMIT
- `src/agent.py`: retries when the SQL fails, passes the error back to the model
- `src/queries.py`: fixed queries (MoM with LAG, margins, discount bands) used for the profit investigation so the evidence does not depend on the model
- `src/anomaly.py`: z-score on monthly profit and margin

## Setup
```
pip install -r requirements.txt
# download Superstore CSV (Kaggle "Sample - Superstore") into data/superstore.csv
python -m src.db data/superstore.csv
ollama pull qwen2.5-coder:7b       # or set LLM_PROVIDER=gemini and a key
streamlit run app.py
pytest
```

## Assumptions
- Discount is a fraction (0.2 = 20%) and profit is already after discount.
- Duplicates are dropped; one row per order line.
- Months are calendar months from order date.

## Findings
(TODO: write your own after running it, e.g. margin by discount band, worst sub-categories, anomaly months)

## Limitations
- Small local models sometimes write wrong SQL. The retry helps but does not fix everything.
- The explanation can suggest reasons the data cannot prove; the evidence tables are shown next to it for that reason.
- Observational data only, so no causal claims.

## Screenshots
(TODO: add dashboard + app screenshots)
