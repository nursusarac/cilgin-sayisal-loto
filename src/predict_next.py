
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "draws.csv"

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]
WINDOW_SIZE = 20


def main():
    df = pd.read_csv(DATA_FILE)

    # Parse Turkish draw dates and sort chronologically.
    months = {
        "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4,
        "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8,
        "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12,
    }

    def parse_date(value):
        day, month, year = str(value).split()
        return pd.Timestamp(
            year=int(year),
            month=months[month],
            day=int(day),
        )

    df["parsed_date"] = df["date"].apply(parse_date)
    df = df.sort_values("parsed_date").reset_index(drop=True)

    if len(df) <= WINDOW_SIZE:
        raise ValueError("Not enough historical draws.")

    # Use the last 20 draws to rank numbers by frequency.
    recent_numbers = df.tail(WINDOW_SIZE)[NUMBER_COLS].to_numpy().ravel()
    frequency = (
        pd.Series(recent_numbers)
        .value_counts()
        .reindex(range(1, 91), fill_value=0)
    )

    # Deterministic tie-breaking: higher frequency first, then lower number.
    ranked_numbers = sorted(
        range(1, 91),
        key=lambda number: (-int(frequency[number]), number),
    )

    combination = sorted(ranked_numbers[:6])

    print("\n=== ÇILGIN SAYISAL LOTO ===")
    print(f"Historical draws used: {len(df)}")
    print(f"Frequency window: last {WINDOW_SIZE} draws")
    print("Selected combination:", " - ".join(map(str, combination)))
    print(
        "\nNote: This is a historical-frequency selection, "
        "not a reliable prediction of future results."
    )


if __name__ == "__main__":
    main()
