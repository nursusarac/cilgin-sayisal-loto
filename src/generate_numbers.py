
from pathlib import Path
import random
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "draws.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

NUMBER_COLUMNS = ["n1", "n2", "n3", "n4", "n5", "n6"]

# Load and validate historical draw data
df = pd.read_csv(DATA_FILE)

for column in NUMBER_COLUMNS:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=NUMBER_COLUMNS).copy()

valid = (
    df[NUMBER_COLUMNS].ge(1).all(axis=1)
    & df[NUMBER_COLUMNS].le(90).all(axis=1)
    & df[NUMBER_COLUMNS].nunique(axis=1).eq(6)
)
df = df.loc[valid].copy()

# Sort draws chronologically using Turkish date strings
if "date" in df.columns:
    month_names = {
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

    def parse_turkish_date(date_string):
        parts = str(date_string).strip().lower().split()

        if len(parts) != 3:
            return pd.NaT

        day, month_name, year = parts
        month = month_names.get(month_name)

        if month is None:
            return pd.NaT

        return pd.to_datetime(
            f"{day}.{month}.{year}",
            format="%d.%m.%Y",
            errors="coerce"
        )

    df["_date_sort"] = df["date"].apply(parse_turkish_date)

    if df["_date_sort"].isna().any():
        raise ValueError(
            "Some dates could not be parsed. Please check the date column."
        )

    df = df.sort_values("_date_sort")

elif "draw_id" in df.columns:
    df = df.sort_values("draw_id")
else:
    raise ValueError("Neither a date column nor draw_id is available.")

df = df.reset_index(drop=True)

df = df.reset_index(drop=True)

if len(df) < 20:
    raise ValueError("At least 20 valid draws are required.")

# Calculate frequencies in the most recent 20 draws
recent_draws = df.tail(20)[NUMBER_COLUMNS].to_numpy().flatten()

counts = (
    pd.Series(recent_draws)
    .value_counts()
    .reindex(range(1, 91), fill_value=0)
)

# Select the six most frequent numbers.
# Ties are resolved by choosing the smaller number first.
recent_pick = sorted(
    range(1, 91),
    key=lambda number: (-counts[number], number)
)[:6]

# Generate a uniformly random combination
rng = random.Random()
random_pick = sorted(rng.sample(range(1, 91), 6))

combinations = {
    "recent_20_frequency": recent_pick,
    "random": random_pick,
}

# Build a comparison report
rows = []

for method, selected_numbers in combinations.items():
    rows.append({
        "method": method,
        "n1": selected_numbers[0],
        "n2": selected_numbers[1],
        "n3": selected_numbers[2],
        "n4": selected_numbers[3],
        "n5": selected_numbers[4],
        "n6": selected_numbers[5],
        "odd_count": sum(n % 2 for n in selected_numbers),
        "even_count": sum(n % 2 == 0 for n in selected_numbers),
        "sum_of_numbers": sum(selected_numbers),
        "recent_20_frequency_total": sum(
            int(counts[n]) for n in selected_numbers
        ),
    })

results = pd.DataFrame(rows)
results.to_csv(
    OUTPUT_DIR / "generated_combinations.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 52)
print("LOTTERY COMBINATION ANALYSIS")
print("=" * 52)
print(f"Valid historical draws: {len(df)}")
print("Frequency window: most recent 20 draws")

for method, selected_numbers in combinations.items():
    title = (
        "RECENT-FREQUENCY STRATEGY"
        if method == "recent_20_frequency"
        else "RANDOM BASELINE"
    )

    print(f"\n{title}")
    print("Numbers:", " - ".join(map(str, selected_numbers)))

print("\nResults saved to:")
print(OUTPUT_DIR / "generated_combinations.csv")

print(
    "\nLimitations: Historical frequencies do not reliably predict "
    "future lottery outcomes. No strategy guarantees a win."
)
