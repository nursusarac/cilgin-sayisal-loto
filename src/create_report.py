
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_FILES = {
    "Strategy Comparison": "strategy_comparison_summary.csv",
    "Window Selection": "window_selection_results.csv",
    "Final Holdout Test": "final_holdout_result.csv",
    "Data Quality": "data_quality_summary.csv",
}

sections = []

# 1. Project overview
sections.append(
    """
============================================================
LOTTERY DRAW DATA ANALYSIS
============================================================

Project overview
----------------
This project analyzes historical lottery draw data, compares
number-selection strategies, evaluates them using a holdout
test set, and checks selected records against manually
provided official results.

Important limitations
---------------------
- Lottery draws are random events.
- Historical number frequencies do not establish that a
  number is more likely to appear in a future draw.
- Strategy comparisons are retrospective and do not
  guarantee future performance.
- Official verification covers only the records included
  in the verification file; it does not validate the
  entire historical dataset.
"""
)

# 2. Include analysis result tables
for title, filename in REPORT_FILES.items():
    file_path = OUTPUT_DIR / filename

    sections.append(
        f"\n{'=' * 60}\n{title}\n{'=' * 60}\n"
    )

    if not file_path.exists():
        sections.append(f"Missing file: {filename}")
        continue

    try:
        data = pd.read_csv(file_path)
        sections.append(data.to_string(index=False))
    except Exception as error:
        sections.append(f"Could not read {filename}: {error}")

# 3. Add interpretation of the final holdout test
holdout_path = OUTPUT_DIR / "final_holdout_result.csv"

sections.append(
    f"\n{'=' * 60}\n"
    "Holdout Test Interpretation\n"
    f"{'=' * 60}\n"
)

if holdout_path.exists():
    try:
        holdout = pd.read_csv(holdout_path)

        if (
            "method" in holdout.columns
            and "average_hits" in holdout.columns
        ):
            sections.append(
                "Average hits are descriptive results from the "
                "holdout period. Small differences between "
                "strategies and a random baseline should not be "
                "interpreted as evidence of predictive power."
            )
        else:
            sections.append(
                "The holdout table does not contain the expected "
                "columns for an automated interpretation."
            )
    except Exception as error:
        sections.append(f"Could not interpret holdout results: {error}")

# 4. Add official-result verification
verification_path = OUTPUT_DIR / "official_verification.csv"

sections.append(
    f"\n{'=' * 60}\n"
    "Verification Against Supplied Official Results\n"
    f"{'=' * 60}\n"
)

if verification_path.exists():
    try:
        verification = pd.read_csv(verification_path)

        if "status" in verification.columns:
            statuses = (
                verification["status"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            total_checked = len(verification)
            matched = statuses.eq("EŞLEŞİYOR").sum()
            not_matched = total_checked - matched

            sections.append(
                f"Records checked: {total_checked}\n"
                f"Matching records: {matched}\n"
                f"Records requiring review: {not_matched}\n"
            )

            if total_checked:
                match_rate = matched / total_checked * 100
                sections.append(
                    f"Match rate among checked records: "
                    f"{match_rate:.1f}%\n"
                )

            sections.append(
                "\nScope note: This result applies only to the "
                "records in this verification file. It does not "
                "confirm the accuracy of all historical draws.\n"
            )

        sections.append("\nDetailed verification records:\n")
        sections.append(verification.to_string(index=False))

    except Exception as error:
        sections.append(
            f"Could not read verification results: {error}"
        )
else:
    sections.append(
        "Verification file not found. Run verify_draws.py first."
    )

# 5. Save report
report_text = "\n".join(sections)
report_path = OUTPUT_DIR / "project_report.txt"
report_path.write_text(report_text, encoding="utf-8")

print("Project report generated.")
print(f"Saved to: {report_path}")
print("\n" + report_text)
