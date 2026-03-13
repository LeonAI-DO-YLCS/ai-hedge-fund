# Detecting Randomness and Inefficiencies in Deriv Volatility 75 Index 1‑Minute OHLC Data

## Overview

This report outlines a practical, Python‑oriented framework to test whether a large 1‑minute OHLC dataset for Deriv’s Volatility 75 Index (V75) behaves like a random, fair synthetic market, or whether there is short‑horizon predictability that could be traded.

The goal is not to "prove" true randomness in the strict mathematical sense, which is impossible with finite data, but to systematically search for statistically robust deviations from an IID (independent, identically distributed) innovation process and a martingale‑like price evolution.

The design assumes a very large dataset (5+ years of 1‑minute candles) and focuses on short‑term predictability (next few minutes) and micro‑inefficiencies.

## What Volatility 75 Is (and Is Not)

Deriv’s synthetic indices, including Volatility 75, are algorithm‑based instruments designed to simulate market‑like price action with fixed volatility levels and no link to real‑world assets or news.[^1][^2][^3]

Public descriptions state that synthetic indices are generated via random number generators with statistically consistent volatility conditions and are audited by third parties for fairness, meaning that under the intended design, tick‑to‑tick moves should be random conditional on the specified volatility regime.[^2][^4][^5][^1]

Volatility 75 in particular is advertised as a synthetic index that mimics a market with constant 75% volatility, driven purely by an algorithm rather than order flow or macro events.[^6][^4][^3]

Implication: if Deriv’s RNG and transformation algorithm are correctly implemented and audited, the index should be very close to a fair, memoryless process at the tick/1‑minute level, although long apparent trends and complex price patterns will still emerge purely from random walks.

## Conceptual Target: What “Random” Means Here

For this analysis, "truly random" is operationalised as:

- Price process: behaves like a random walk or martingale with no predictable drift after conditioning on past information.
- Return process: 1‑minute log returns \(r_t = \ln(P_t) - \ln(P_{t-1})\) are:
  - Approximately stationary over time (no long‑term deterministic trend in the mean),
  - Having stable unconditional variance around the design level,
  - Showing no exploitable serial dependence (linear or nonlinear) in returns at short lags.

Departures from this ideal can still be consistent with the index design (for example, volatility clustering from a GARCH‑like generator), but from a trading perspective, any stable, out‑of‑sample exploitability in direction, magnitude, or volatility constitutes an inefficiency.

## High‑Level Analysis Pipeline

The tool can be structured as a sequential pipeline that can be run on any OHLC dataset for V75 (or other Deriv synthetics):

1. Data ingestion and integrity checks.
2. Basic EDA and summary statistics.
3. Distributional analysis of returns.
4. Linear and nonlinear dependence tests.
5. Volatility clustering and conditional heteroskedasticity tests.
6. Regime and structural‑break detection.
7. Micro‑structure and intraday‑pattern analysis (if timestamps include session information).
8. Probe strategies and walk‑forward backtests as "inefficiency detectors".
9. Statistical consolidation: p‑values, effect sizes, multiple‑testing control, and robustness.

The following sections break these down with concrete tests and the Python components needed to implement them.

## 1. Data Ingestion and Integrity Checks

### 1.1 Expected Input Format

Design the tool around a standard long‑format time series table with at least:

- `timestamp` (timezone‑aware, 1‑minute frequency, no duplicates),
- `open`, `high`, `low`, `close`,
- Optionally `volume` (if available; for most Deriv synthetics, this may be missing or synthetic).

### 1.2 Cleaning and Sanity Checks

The ingestion module should:

- Parse timestamps and sort by time.
- Remove duplicates or overlapping bars.
- Check for missing minutes (gaps) and either:
  - Forward‑fill prices only for diagnostic statistics (not for trading tests), or
  - Drop incomplete segments, depending on configuration.
- Check price constraints:
  - `low ≤ min(open, close) ≤ max(open, close) ≤ high` for all bars,
  - Discard or flag bars with obvious glitches (e.g., zero, negative, or astronomically large values far outside historical range).

### 1.3 Derived Fields

Add the following series:

- Mid price: \(m_t = (high_t + low_t)/2\).
- Log price: \(p_t = \ln(close_t)\).
- Log return: \(r_t = p_t - p_{t-1}\).
- Absolute and squared returns: \(|r_t|\), \(r_t^2\).

These become the core inputs to all downstream analyses.

## 2. Basic EDA and Summary Statistics

The EDA module should quickly characterise the series:

- Global statistics on returns (mean, median, standard deviation, skewness, kurtosis) overall and by year.
- Rolling statistics (e.g., 1‑month rolling mean and volatility of returns) to detect drift or slow changes.
- Price‑level diagnostics:
  - Long‑term drift in log prices (regression of \(p_t\) on time),
  - Maximum drawdowns and run‑ups over multi‑month windows.

Visualisations (for manual inspection, even if the automated tool only computes stats):

- Time series plot of price (log‑scaled),
- Time series of returns,
- Rolling volatility plot,
- Histogram and kernel density estimate of returns.

None of these alone proves or refutes randomness, but they give context on whether the generator seems to maintain a stable volatility regime, as Deriv claims.[^1][^2]

## 3. Distributional Properties of Returns

### 3.1 Static Distribution Tests

Key questions:

- Are 1‑minute returns symmetric around zero?
- Are tails heavier than Gaussian?
- Are there outliers inconsistent with the advertised constant volatility (e.g., occasional "jumps")?

Recommended tests:

- Jarque–Bera test for normality of \(r_t\).
- Anderson–Darling or Kolmogorov–Smirnov tests versus normal and potentially a t‑distribution.
- Empirical quantiles vs theoretical (QQ‑plots) against normal and t.

Heavy tails and skewness are not, by themselves, inefficiencies but may indicate non‑Gaussian innovations in the synthetic generator.

### 3.2 Conditional Distribution Stability

To check for non‑stationarity in the distribution:

- Split the sample into several subperiods (e.g., yearly blocks).
- For each block, recompute mean, variance, skewness, kurtosis.
- Run two‑sample tests (KS, Cramér–von Mises) between early and late periods.

If the generator is fully time‑homogeneous, there should be no systematic drift in these statistics across years, apart from sampling noise.

## 4. Linear Dependence and Predictability in Returns

Short‑horizon predictability is primarily about whether \(r_{t+1}\) depends on past returns.

### 4.1 Autocorrelation Structure

Compute and test:

- ACF and PACF of \(r_t\) for lags 1–100.
- ACF of \(|r_t|\) and \(r_t^2\) for volatility clustering.

Apply portmanteau tests:

- Ljung–Box test on \(r_t\) (e.g., lags 5, 10, 20, 60),
- Ljung–Box on \(|r_t|\) and \(r_t^2\).

Significant autocorrelation in \(r_t\) at small lags might be exploitable via momentum or mean‑reversion strategies, depending on sign.

### 4.2 Simple Linear Forecasts

Estimate predictive regressions of the form:

\[ r_{t+1} = \alpha + \sum_{k=1}^K \beta_k r_{t+1-k} + \varepsilon_{t+1}, \]

with small K (1–5) to avoid overfitting.

Analyse:

- Are \(\beta_k\) coefficients statistically significant after robust (HAC) standard errors?
- Is \(R^2\) materially above zero?
- Does a sign‑based predictor (e.g., `sign_hat = sign(β̂_1 r_t)`) achieve out‑of‑sample accuracy meaningfully above 50%?

If any of these survive out‑of‑sample and multiple‑testing corrections, they suggest linear predictability.

## 5. Nonlinear Dependence and Volatility Dynamics

Even if \(r_t\) itself looks uncorrelated, synthetic generators often introduce conditional heteroskedasticity (volatility clustering) to mimic real markets. This is not necessarily tradable, but volatility forecasts may be.[^2][^1]

### 5.1 ARCH/GARCH Effects

Run Engle’s ARCH LM test on \(r_t\) to detect conditional heteroskedasticity.

If significant, fit models such as:

- GARCH(1,1),
- EGARCH(1,1),
- Possibly GJR‑GARCH for leverage‑type effects, though these may not exist in symmetric synthetic indices.

Key diagnostics:

- Whether GARCH parameters are stable across subsamples,
- Whether standardized residuals are IID (no remaining autocorrelation in residuals or squared residuals).

If volatility is forecastable from past returns (e.g., high \(|r_t|\) today predicts higher \(|r_{t+1}|\)), there may be opportunities for position sizing, volatility targeting, or options on synthetics.

### 5.2 Nonlinear Independence Tests

Apply more general nonlinearity tests on \(r_t\):

- BDS test on residuals from a linear AR model,
- Runs test for independence (sign sequence of returns),
- Higher‑order moment dependence (cross‑correlations of \(r_t\) and \(r_{t-k}^2\)).

Evidence of nonlinear dependence suggests that simple autocorrelation tests are insufficient and that nonlinear models (e.g., kernels or tree‑based methods) might extract weak predictability.

## 6. Long‑Memory, Trend, and Mean‑Reversion Diagnostics

To test for longer‑horizon structure beyond a few minutes:

- Unit root tests on log price: ADF and KPSS (
  - ADF to test for unit root / random walk,
  - KPSS to test for stationarity around a deterministic trend).
- Hurst exponent estimation via rescaled range or DFA to detect long‑memory (\(H ≠ 0.5\)).

If \(H\) is statistically different from 0.5 on returns or on aggregated returns over longer intervals (e.g., 5‑min, 15‑min), this could motivate momentum (\(H > 0.5\)) or mean‑reversion (\(H < 0.5\)) style probes.

## 7. Regime and Structural‑Break Analysis

Deriv offers products such as Volatility Switch Indices, which explicitly change volatility regimes; these are distinct from constant‑vol indices but show how synthetic indices can encode regime changes algorithmically.[^7][^8][^1]

It is therefore reasonable to test whether V75 exhibits unannounced structural changes or implicit regimes:

- Structural break tests on return variance (e.g., Bai–Perron multiple break tests on \(r_t^2\)).
- Change‑point detection on volatility measures (e.g., rolling standard deviation or realized volatility).
- Hidden Markov Models (HMMs) fitted to \(|r_t|\) or \(r_t^2\) to infer latent high‑vol / low‑vol states.

If regimes exist and transition probabilities are stable, regime‑conditioned strategies could be built (for example, different leverage in high‑ and low‑vol states), though directionality may remain unpredictable.

## 8. Micro‑Structure and Intraday Patterns

Since V75 is available 24/7 and not tied to any real‑world session structure, there should be no strong time‑of‑day effects analogous to equity market opens/closes.[^1][^2]

Nonetheless, for completeness, compute:

- Average return and volatility by minute‑of‑day (1440 buckets) or by coarser buckets (e.g., 15‑minute slots),
- Frequency and size of extreme returns by bucket.

If the generator is truly time‑homogeneous, all such patterns should be indistinguishable from noise. Any persistent pattern (for example, slightly elevated volatility in certain minutes) might be exploitable via time‑based position sizing, even if not directionally.

## 9. Probe Strategies as Inefficiency Detectors

Statistical tests alone do not answer the trading question. The tool should implement a family of extremely simple, low‑parameter strategies that directly reflect the presence or absence of exploitable structure.

### 9.1 Design Principles

- Use only a small number of parameters (ideally 0–2) to reduce overfitting.
- Separate data into training, validation, and out‑of‑sample test segments in chronological order.
- Fix transaction‑cost assumptions (spread, commissions, slippage) realistically high so that marginal edges are filtered out.
- Evaluate not only raw PnL but also Sharpe ratio, maximum drawdown, hit rate, and turnover.

### 9.2 Example Probe Strategies

1. **Lag‑1 sign momentum**
   - Rule: Go long if \(r_t > 0\), short if \(r_t < 0\), exit/flat otherwise.
   - Evaluate 1‑minute holding, and 2–5 minute holding horizons.

2. **Lag‑1 mean reversion**
   - Rule: Go short if \(r_t > \theta\), long if \(r_t < -\theta\), where \(\theta\) is a multiple of recent volatility.

3. **MA‑based micro‑trend**
   - Short MA vs long MA on 1‑minute closes (e.g., 5 vs 20 bars), entering in the direction of the cross.

4. **Volatility‑conditioned flatting**
   - Use a volatility forecast (e.g., from GARCH) to reduce exposure in predicted high‑vol regimes and increase in low‑vol regimes.

All strategies should be run as pure probes: if none delivers performance meaningfully above what would be expected from noise (given the sample size), this is strong evidence that the market is effectively random at the tested horizon.

### 9.3 Statistical Significance of PnL

Given many probe strategies and parameter choices, the multiple‑testing problem is real.

The tool should:

- Record all tested strategies and parameters.
- Use bootstrap or analytical approximations to estimate the distribution of Sharpe ratios under a null of IID returns.
- Apply corrections such as Bonferroni or false discovery rate (FDR) to avoid over‑interpreting one lucky strategy.

## 10. Python Tool Architecture

Below is a suggested modular architecture for the Python analysis tool.

### 10.1 Package Layout

```text
v75_randomness_checker/
  __init__.py
  config.py
  data_loader.py
  features.py
  eda.py
  tests_linear.py
  tests_nonlinear.py
  volatility_models.py
  regimes.py
  microstructure.py
  probe_strategies.py
  evaluation.py
  cli.py or notebook.ipynb
```

### 10.2 Core Modules and Responsibilities

- `data_loader.py`
  - Functions to read CSV/Parquet, clean timestamps, enforce OHLC constraints, compute derived fields.

- `features.py`
  - Helpers for computing returns, rolling stats, Hurst exponent, etc.

- `eda.py`
  - Summary statistics and basic plots (if running in notebook mode).

- `tests_linear.py`
  - ACF/PACF computations, Ljung–Box tests, AR regressions, sign‑accuracy of linear forecasts.

- `tests_nonlinear.py`
  - Runs test, BDS test, nonlinear dependence diagnostics.

- `volatility_models.py`
  - ARCH/GARCH fitting and diagnostics, volatility forecast series.

- `regimes.py`
  - Structural break tests, HMM regime inference.

- `microstructure.py`
  - Time‑of‑day and bucketed analysis.

- `probe_strategies.py`
  - Implementations of a small, curated set of momentum, mean‑reversion, and volatility‑based probes.

- `evaluation.py`
  - Backtest engine, PnL metrics, Sharpe ratio, drawdown, significance assessment, multiple‑testing corrections.

- `cli.py` / notebook
  - User interface that wires everything together into a single run: ingest data, run all tests, run probe strategies, emit a human‑readable report (JSON/Markdown).

### 10.3 Key Libraries

Recommended stack:

- `pandas`, `numpy` for data handling.
- `scipy.stats` for distribution tests.
- `statsmodels` for AR, Ljung–Box, ARCH LM, unit‑root tests.
- `arch` for GARCH family models.
- `hmmlearn` or similar for HMMs.
- `numba` (optional) to accelerate backtests on very large datasets.
- `matplotlib` / `seaborn` / `plotly` for visual EDA.

## 11. Decision Criteria: When to Discard the Market

The tool should aggregate its findings into a small set of clear indicators that can be used to decide whether to discard V75 as "effectively random" for the tested horizon.

Reasonable discard criteria (for short‑term directional trading) include:

- No statistically significant linear or nonlinear dependence in \(r_t\) that survives out‑of‑sample validation and multiple‑testing corrections.
- Probe strategies show:
  - Out‑of‑sample Sharpe ratios consistent with what would be expected under IID noise at the tested sample size,
  - No robust edge after realistic transaction costs.
- Volatility is forecastable (e.g., GARCH works) but this does not translate into economically meaningful improvements in risk‑adjusted returns for reasonable strategies.

If these hold over many years of data, V75 can be treated, for practical purposes, as an efficient, random synthetic market at the 1‑minute level, suitable for benchmarking but not for systematic alpha extraction at that horizon.

Conversely, any persistent, cross‑validated edge (even small) flagged by this framework would justify deeper model building and strategy optimisation.

---

## References

1. [Synthetic Indices on Deriv – trading derived markets](https://deriv.com/blog/posts/an-introduction-to-synthetic-indices-trading) - Deriv's synthetic indices are algorithm-based instruments that maintain statistically consistent vol...

2. [Guide to understanding Volatility Indices | Deriv Academy](https://traders-academy.deriv.com/trading-guides/guide-to-understanding-volatility-indices) - Volatility Indices are synthetic instruments created by Deriv to replicate market-like price movemen...

3. [The ULTIMATE Volatility 75 Index Trading Strategy (Full Course)](https://www.youtube.com/watch?v=_wRda3hgao0) - Get Inside Our 3 Day Masterclass For Beginners https://tradingwiththan.com/forex/ My name is Courage...

4. [Volatility 75 Index Trading Strategy PDF | PDF | Vix - Scribd](https://www.scribd.com/document/960302413/71334298165) - V75 is a synthetic index offered by Deriv, a well-known forex broker. The index mimics a market with...

5. [I made Deriv V75 Simple (Making $500 Weekly) - YouTube](https://www.youtube.com/watch?v=WkCTSP2E8-I) - I made Deriv V75 Simple (Making $500 Weekly). 9.8K views · 4 ... Simple Top Down Analysis For Synthe...

6. [Volatility 75 index - How to trade VIX 75 - ForexBee](https://forexbee.co/volatility-75-index/) - Volatility 75 index refers to a synthetic index that is a simulation-based index and has 75% of real...

7. [[PDF] How to Trade Synthetic Indices - Deriv](https://docs.deriv.com/marketing/2025/ebook-synthetics-en-hq.pdf) - Deep liquidity: Deriv has constant deep liquidity, allowing you to buy or sell in large market sizes...

8. [Volatility Switch Indices: What they are, strategies and risks](https://traders-academy.deriv.com/trading-guides/volatility-switch-indices-guide) - In this guide, you'll learn what VSI is, how it works, how it differs from other volatility indices ...

