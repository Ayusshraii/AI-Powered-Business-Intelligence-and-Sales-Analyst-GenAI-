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

1. Growth
Revenue grew from 484,247 (2014) to 733,215 (2017), up about 51%.
Profit grew faster, from 49,544 to 93,439, up about 89%. Margin rose from 10.2% to 12.7%, peaking at 13.4% in 2016.
Revenue is highest in November (352,461), December (325,294), and September (307,650).

2. Heavy discounts are where the money is lost
Order lines with discounts of 20% or less earn 421,773 profit at a 21.8% margin.
Lines above 20% discount lose a combined 135,376: -35,817 at 21-40% and -99,559 at 40% and above.
Of the 156,131 lost on all loss-making lines, 138,515 (about 89%) come from lines discounted above 20%.
1,871 of 9,994 order lines (about 19%) are loss-making.

3. Furniture sells a lot but earns little
Furniture has 742,000 revenue but only 18,451 profit, a 2.5% margin. Office Supplies earns 17.0% and Technology 17.4%.
Tables lose 17,725 (-8.6% margin) at an average discount of 26.1%. Bookcases (-3,473) and Supplies (-1,189) also lose money.
Copiers earn 55,618 at a 37.2% margin with a 16.2% average discount. Labels have the highest margin, 44.4%, at only 6.9% average discount.

4. Regions differ, but discounts don’t explain it
East has the best margin (15.5%) and South the worst (7.5%).
Their average discounts are almost the same (15.1% vs 15.7%), so something else drives the South gap, such as product mix or shipping costs. This data can’t say which.

5. Risky products
The Cubify CubeX 3D Printer (double head) has revenue of 11,100 and profit of -8,880 (-80% margin). The triple head version has -48%.
The Lexmark MX611dhe printer has revenue of 16,830 and profit of -4,590.
The Cisco TelePresence System EX90 is the 3rd best seller by revenue but has a profit of -1,811.

6. Unusual months
January 2015 was the worst month (profit -3,281, margin -18%).
October 2016, December 2016, and March 2017 had unusually high profit.

## Limitations
- Small local models sometimes write wrong SQL. The retry helps but does not fix everything.
- The explanation can suggest reasons the data cannot prove; the evidence tables are shown next to it for that reason.
- Observational data only, so no causal claims.
