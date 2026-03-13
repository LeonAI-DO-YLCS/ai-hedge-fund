# Fixture Datasets

- `v75_mini_valid.csv`: valid canonical sample with consecutive timestamps and low spread.
- `v75_mini_gapped.csv`: canonical sample with intentional missing-minute gaps.
- `v75_mini_invalid.csv`: canonical sample with an OHLC consistency violation.
- `v75_regime_trend.csv`: deterministic upward drift fixture for stable uptrend labeling.
- `v75_regime_range.csv`: bounded oscillation fixture for low-drift range labeling.
- `v75_regime_spike.csv`: calm baseline with a single volatility shock for shock-state coverage.
- `v75_regime_sparse.csv`: short, imbalanced fixture intended to trigger regime coverage warnings.
