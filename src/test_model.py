
from pathlib import Path
import random
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "draws.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

SEED = 42
WINDOWS = [20, 50, 100, 200]
NUMBER_COLUMNS = ["n1", "n2", "n3", "n4", "n5", "n6"]

MONTHS = {
    "ocak": "01",
    "şubat": "02",
    "mart": "03",
    "nisan": "04",
    "mayıs": "05",
    "haziran": "06",
    "temmuz": "07",
    "ağustos": "08",
    "eylül": "09",
    "ekim": "10",
    "kasım": "11",
    "aralık": "12",
}


def parse_turkish_date(value):
    """Convert dates such as '03 Ağustos 2020' to timestamps."""
    parts = str(value).strip().lower().split()

    if len(parts) != 3:
        return pd.NaT

    day, month_name, year = parts
    month = MONTHS.get(month_name)

    if month is None:
        return pd.NaT

    return pd.to_datetime(
        f"{day}.{month}.{year}",
        format="%d.%m.%Y",
        errors="coerce",
    )


def get_frequency_pick(history, window=None):
    """Select six most frequent numbers from past draws."""
    selected_history = history if window is None else history[-window:]

    flattened = [
        number
        for draw in selected_history
        for number in draw
    ]

    counts = (
        pd.Series(flattened)
        .value_counts()
        .reindex(range(1, 91), fill_value=0)
    )

    # Deterministic tie-break: smaller number first.
    return sorted(
        range(1, 91),
        key=lambda number: (-counts[number], number),
    )[:6]


def count_hits(prediction, actual):
    return len(set(prediction) & set(actual))


# 1. Load and validate data
df = pd.read_csv(DATA_FILE)

missing_columns = [
    column for column in NUMBER_COLUMNS
    if column not in df.columns
]
if missing_columns:
    raise ValueError(f"Missing number columns: {missing_columns}")

for column in NUMBER_COLUMNS:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=NUMBER_COLUMNS).copy()

valid = (
    df[NUMBER_COLUMNS].ge(1).all(axis=1)
    & df[NUMBER_COLUMNS].le(90).all(axis=1)
    & df[NUMBER_COLUMNS].nunique(axis=1).eq(6)
)
df = df.loc[valid].copy()

# 2. Sort chronologically
if "date" in df.columns:
    df["_sort_date"] = df["date"].apply(parse_turkish_date)

    if df["_sort_date"].isna().any():
        bad_dates = df.loc[
            df["_sort_date"].isna(), "date"
        ].head(10).tolist()

        raise ValueError(
            "Some dates could not be parsed. "
            f"Example values: {bad_dates}"
        )

    df = df.sort_values("_sort_date")
    df = df.drop(columns=["_sort_date"])

elif "draw_id" in df.columns:
    df = df.sort_values("draw_id")
else:
    raise ValueError("No date or draw_id column is available.")

df = df.reset_index(drop=True)

draws = df[NUMBER_COLUMNS].astype(int).values.tolist()
total_draws = len(draws)

if total_draws < 250:
    raise ValueError(
        "At least 250 valid draws are required for this test."
    )

# 3. Chronological split:
# First 70% is initial history.
# Half of the remaining draws selects the window.
# The final half is the holdout test.
warmup = int(total_draws * 0.70)
remaining = total_draws - warmup
selection_end = warmup + remaining // 2

if warmup < max(WINDOWS):
    raise ValueError("Initial history must contain at least 200 draws.")

methods = {
    "All history": None,
    "Last 20 draws": 20,
    "Last 50 draws": 50,
    "Last 100 draws": 100,
    "Last 200 draws": 200,
}

# One random combination per target draw, shared across
# the strategy comparison for that target.
rng = random.Random(SEED)
records = []

for index in range(warmup, total_draws):
    history = draws[:index]
    actual = draws[index]
    period = "selection" if index < selection_end else "holdout"

    random_pick = sorted(rng.sample(range(1, 91), 6))

    for method, window in methods.items():
        prediction = get_frequency_pick(history, window)
        hits = count_hits(prediction, actual)

        records.append({
            "target_index": index,
            "period": period,
            "method": method,
            "test_date": (
                df.iloc[index]["date"]
                if "date" in df.columns else index
            ),
            "hits": hits,
            "draw_with_1_or_more": int(hits >= 1),
            "draw_with_2_or_more": int(hits >= 2),
        })

    random_hits = count_hits(random_pick, actual)

    records.append({
        "target_index": index,
        "period": period,
        "method": "Random selection",
        "test_date": (
            df.iloc[index]["date"]
            if "date" in df.columns else index
        ),
        "hits": random_hits,
        "draw_with_1_or_more": int(random_hits >= 1),
        "draw_with_2_or_more": int(random_hits >= 2),
    })

details = pd.DataFrame(records)
details.to_csv(
    OUTPUT_DIR / "strategy_comparison_detail.csv",
    index=False,
    encoding="utf-8-sig",
)


def summarize_period(data):
    return (
        data.groupby("method")
        .agg(
            test_draws=("hits", "count"),
            total_hits=("hits", "sum"),
            average_hits=("hits", "mean"),
            draws_with_1_or_more=("draw_with_1_or_more", "sum"),
            draws_with_2_or_more=("draw_with_2_or_more", "sum"),
        )
        .reset_index()
    )


# 4. Window selection: selection period only
selection = details[details["period"] == "selection"].copy()
selection_summary = summarize_period(selection)

selection_random_average = selection_summary.loc[
    selection_summary["method"] == "Random selection",
    "average_hits",
].iloc[0]

selection_summary["random_baseline"] = selection_random_average
selection_summary["difference_from_random"] = (
    selection_summary["average_hits"] - selection_random_average
)

selection_summary = selection_summary.sort_values(
    "average_hits", ascending=False
)

selection_summary.to_csv(
    OUTPUT_DIR / "window_selection_results.csv",
    index=False,
    encoding="utf-8-sig",
)

# 5. Select best frequency window using selection period only
frequency_candidates = selection_summary[
    selection_summary["method"] != "Random selection"
]

selected_method = frequency_candidates.iloc[0]["method"]
selected_average = frequency_candidates.iloc[0]["average_hits"]

# 6. Final holdout: selected strategy vs random baseline
holdout = details[details["period"] == "holdout"].copy()
holdout_methods = holdout[
    holdout["method"].isin([selected_method, "Random selection"])
]

holdout_summary = summarize_period(holdout_methods)

holdout_random_average = holdout_summary.loc[
    holdout_summary["method"] == "Random selection",
    "average_hits",
].iloc[0]

holdout_summary["random_baseline"] = holdout_random_average
holdout_summary["theoretical_random_average"] = 0.4
holdout_summary["difference_from_random"] = (
    holdout_summary["average_hits"] - holdout_random_average
)
holdout_summary["selected_window"] = selected_method

holdout_summary.to_csv(
    OUTPUT_DIR / "final_holdout_result.csv",
    index=False,
    encoding="utf-8-sig",
)

# 7. Create a consistent strategy comparison summary
# This summary uses the same selection period as window selection.
strategy_summary = selection_summary[
    selection_summary["method"].isin([
        "Last 20 draws",
        "Last 50 draws",
        "Last 100 draws",
        "Last 200 draws",
        "All history",
        "Random selection",
    ])
].copy()

strategy_summary.to_csv(
    OUTPUT_DIR / "strategy_comparison_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

# 8. Print results
print("\n" + "=" * 60)
print("LOTTERY STRATEGY BACKTEST")
print("=" * 60)
print(f"Valid draws: {total_draws}")
print(f"Initial history: {warmup}")
print(f"Selection test draws: {selection_end - warmup}")
print(f"Independent holdout draws: {total_draws - selection_end}")

print("\n--- WINDOW SELECTION PERIOD ---")
print(selection_summary.to_string(index=False))

print(f"\nSelected frequency strategy: {selected_method}")
print(f"Selection-period average hits: {selected_average:.3f}")

print("\n--- INDEPENDENT HOLDOUT TEST ---")
print(holdout_summary.to_string(index=False))

print("\nUpdated output files:")
print(OUTPUT_DIR / "strategy_comparison_detail.csv")
print(OUTPUT_DIR / "strategy_comparison_summary.csv")
print(OUTPUT_DIR / "window_selection_results.csv")
print(OUTPUT_DIR / "final_holdout_result.csv")

print(
    "\nNote: Historical backtests do not guarantee future results. "
    "The theoretical expected number of main-number hits for a "
    "uniform random 6/90 selection is 0.4 per draw."
)
