"""Flags months where profit or margin is far from normal (simple z-score)."""


def flag_anomalies(monthly, threshold=2.0):
    df = monthly.copy()
    for col in ["profit", "margin_pct"]:
        std = df[col].std()
        df[col + "_z"] = 0.0 if std == 0 else (df[col] - df[col].mean()) / std
    mask = (df["profit_z"].abs() >= threshold) | (df["margin_pct_z"].abs() >= threshold)
    out = df[mask][["month", "profit", "margin_pct", "profit_z", "margin_pct_z"]].round(2)
    return out.reset_index(drop=True)
