
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    ("Data analysis", "src/analyze_draws.py"),
    ("Model backtest", "src/test_model.py"),
    ("Number generation", "src/generate_numbers.py"),
    ("Prediction experiment", "src/predict_next.py"),
    ("Report generation", "src/create_report.py"),
    ("Official result verification", "src/verify_draws.py"),
]


def main():
    print("=" * 60)
    print("LOTTERY PROJECT CHECKS")
    print("=" * 60)

    for label, script in SCRIPTS:
        script_path = ROOT / script

        if not script_path.exists():
            print(f"\nERROR: Script not found: {script}")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print(f"Running: {label}")
        print(f"{'=' * 60}")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=ROOT,
            check=False,
        )

        if result.returncode != 0:
            print(f"\nFAILED: {label}")
            print("The remaining checks were stopped.")
            sys.exit(result.returncode)

    print("\n" + "=" * 60)
    print("ALL CHECKS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
