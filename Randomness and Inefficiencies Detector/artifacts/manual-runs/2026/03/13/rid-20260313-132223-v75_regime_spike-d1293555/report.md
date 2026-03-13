# V75 Detector Report

## Executive verdict

- Verdict: `WeakEvidence`
- Recommended next step: `ContinueDescriptiveResearch`
- Run ID: `rid-20260313-132223-v75_regime_spike-d1293555`

## Dataset summary

- Dataset path: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/Randomness and Inefficiencies Detector/tests/fixtures/v75_regime_spike.csv`
- Row count: `12`

## Data quality summary

- Quality status: `Pass`
- Notes: None`

## Exploratory data analysis summary

- Return mean/std: `0.000940384897545857` / `0.0036577476883460115`
- Return skew/kurtosis: `3.25667664527694` / `10.712330334243568`
- Positive/negative ratio: `0.5454545454545454` / `0.45454545454545453`
- Rolling window `8` std median/max: `0.004287756549031491` / `0.00433473298873345`
- Highest-activity hours: 0: abs_return=0.001408

## Regime overview

- Classification status: `warning`
- Regime config: `default_v75_regime_scheme` (`677d06438c34`)
- Dimensions: direction, volatility, compression, shock
- Classified/warm-up/missing bars: `8` / `4` / `0`
- Dominant states: direction=range, volatility=calm, compression=compressed, shock=normal
- Coverage warnings: `5` (direction regime coverage warning: MissingState: downtrend; volatility regime coverage warning: MissingState: normal; compression regime coverage warning: MissingState: expanded; shock regime coverage warning: SparseCoverage: shock; shock regime coverage warning: DominantCoverage: normal)
- Use regime output as contextual segmentation only; sparse or dominant coverage lowers downstream confidence.

## Directional findings summary

- Directional predictability in full: `Supported` (lag1_autocorr=-0.1084, sign_agreement=0.9000, fdr_rejections=2, max_vr_deviation=1.3397, max_abs_beta=0.0000, rows_used=12/12)

## Volatility findings summary

- Volatility persistence in full: `Rejected` (abs_return_autocorr=-0.1031, fdr_rejections=0, arch_lm_pvalue=0.7265284545708147, rows_used=12/12)

## Tradability summary

- Tradability under baseline: `Supported` (gross_edge=1.3397, penalty=0.0075)
- Tradability under adverse: `Supported` (gross_edge=1.3397, penalty=0.0117)
- Tradability under stress: `Supported` (gross_edge=1.3397, penalty=0.0169)

## Stability summary

- Cross-era stability validation: `Rejected` (supported_directional_eras=1)

## Caveats and unsupported claims

- This tool does not prove fairness.
- This tool does not prove hidden generator design.
- This tool does not guarantee future tradability.

## Recommended next step

- `ContinueDescriptiveResearch`
