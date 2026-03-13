from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def summarize_eda(df: pd.DataFrame) -> dict[str, Any]:
    returns = np.log(df["close"]).diff().dropna()
    if returns.empty:
        return {
            "return_distribution": {},
            "time_of_day": {},
            "weekday": {},
            "rolling": {},
        }

    timestamped = df.iloc[1:].copy()
    timestamped["return"] = returns.to_numpy()
    timestamped["abs_return"] = timestamped["return"].abs()
    timestamped["hour"] = timestamped["timestamp"].dt.hour
    timestamped["weekday"] = timestamped["timestamp"].dt.day_name()

    hourly = (
        timestamped.groupby("hour")[["return", "abs_return"]]
        .agg({"return": "mean", "abs_return": "mean"})
        .round(6)
    )
    weekday = (
        timestamped.groupby("weekday")[["return", "abs_return"]]
        .agg({"return": "mean", "abs_return": "mean"})
        .round(6)
    )

    window = min(256, max(8, len(returns) // 20))
    rolling_mean = returns.rolling(window=window).mean().dropna()
    rolling_std = returns.rolling(window=window).std().dropna()

    return {
        "return_distribution": {
            "mean": float(returns.mean()),
            "std": float(returns.std()),
            "skew": float(returns.skew()),
            "kurtosis": float(returns.kurtosis()),
            "positive_ratio": float((returns > 0).mean()),
            "negative_ratio": float((returns < 0).mean()),
        },
        "time_of_day": {
            str(hour): {
                "mean_return": float(row["return"]),
                "mean_abs_return": float(row["abs_return"]),
            }
            for hour, row in hourly.to_dict("index").items()
        },
        "weekday": {
            str(name): {
                "mean_return": float(row["return"]),
                "mean_abs_return": float(row["abs_return"]),
            }
            for name, row in weekday.to_dict("index").items()
        },
        "rolling": {
            "window": int(window),
            "mean_min": float(rolling_mean.min()) if not rolling_mean.empty else None,
            "mean_max": float(rolling_mean.max()) if not rolling_mean.empty else None,
            "std_median": float(rolling_std.median())
            if not rolling_std.empty
            else None,
            "std_max": float(rolling_std.max()) if not rolling_std.empty else None,
        },
    }
