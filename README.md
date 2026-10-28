# Lottery Draw Data Analysis

A Python-based data analysis project exploring historical Çılgın Sayısal Loto (6/90) results, examining number frequencies, validating data quality, and evaluating simple number-selection strategies through chronological backtesting.

## Project Overview

This project investigates historical lottery draw data to practice data collection, data cleaning, exploratory data analysis, and basic model evaluation.

The analysis compares historical-frequency strategies with a random-selection baseline and evaluates the selected strategy on a separate holdout period.

**Important:** Lottery draws are random. Historical frequencies do not establish that a number is more likely to appear in a future draw. This project is for analytical and educational purposes, not a reliable lottery prediction system.

## Objectives

- Collect and organize historical draw data.
- Validate number ranges, missing values, duplicate draw IDs, and repeated combinations.
- Explore number frequencies and odd/even distributions.
- Compare selection strategies using chronological backtesting.
- Evaluate a selected strategy against a random baseline on a holdout set.
- Verify a sample of historical records against manually supplied official results.

## Tools and Technologies

- Python
- Pandas
- Matplotlib
- Requests
- Beautiful Soup
- CSV data processing
- Exploratory data analysis
- Chronological backtesting

## Dataset and Data Quality

The current dataset contains **975 structurally valid draw records**.

The validation checks found no invalid main-number rows, duplicate draw IDs, or repeated six-number combinations in the dataset.

These checks establish structural consistency, not the accuracy of every historical result. A sample of 20 records was compared with official results supplied for verification; all 20 matched. The remaining historical records have not all been independently verified.

## Strategy Evaluation

The project compares historical-frequency selection using different lookback windows with a random-selection baseline.

The current chronological test uses:
- 682 draws as initial history
- 146 draws for strategy selection
- 147 draws for the final holdout test

On the final holdout set, the selected last-20-draw frequency strategy recorded 56 total main-number hits, while the random baseline recorded 55.

This small difference is descriptive and does **not** demonstrate predictive power or a reliable advantage over random selection.

For a uniform random selection of six distinct numbers from 1 to 90, the theoretical expected number of main-number matches per draw is 0.4.

## Project Outputs

The `outputs/` directory includes:
- Number-frequency analysis and chart
- Odd/even distribution
- Data-quality summary
- Strategy-comparison results
- Window-selection results
- Final holdout-test results
- Official-record verification
- Generated example combinations
- Text-based project report

## Project Structure

```text
cilgin-sayisal-loto/
├── data/
│   └── draws.csv
├── src/
│   ├── fetch_draws.py
│   ├── analyze_draws.py
│   ├── test_model.py
│   ├── generate_numbers.py
│   ├── create_report.py
│   └── verify_draws.py
├── outputs/
├── README.md
```

## Limitations

- Lottery outcomes are random and cannot be reliably predicted from historical frequencies.
- Historical archive data may contain inaccuracies.
- Official verification currently covers only a limited sample.
- Backtest results may vary depending on the dataset, testing period, and random baseline.
- The current random baseline uses one reproducible random combination per test draw, so it is subject to sampling variability.

## Future Improvements

- Expand verification against official historical results.
- Repeat random-baseline experiments to quantify variability.
- Add confidence intervals and statistical comparisons.
- Improve automated data-source validation.
- Create a more visual dashboard for exploratory analysis.

## Disclaimer

This project is an educational data-analysis exercise. It does not guarantee lottery winnings and should not be used as a basis for financial decisions.