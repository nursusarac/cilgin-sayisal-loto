
from pathlib import Path
import pandas as pd

# ==========================================
# 1. DOSYA YOLLARI
# ==========================================
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "draws.csv"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]

# ==========================================
# 2. RESMÎ SİTEDEN KONTROL ETTİĞİMİZ 10 KAYIT
# ==========================================
# Bu değerleri senin gönderdiğin resmî sonuç
# listesinden aktarıyoruz.

official_draws = [
    # Ekim 2026
    {"date": "26.10.2026", "draw_no": 128, "numbers": [13, 22, 51, 52, 60, 80]},
    {"date": "24.10.2026", "draw_no": 127, "numbers": [10, 29, 43, 48, 69, 79]},
    {"date": "21.10.2026", "draw_no": 126, "numbers": [8, 33, 36, 53, 70, 80]},
    {"date": "19.10.2026", "draw_no": 125, "numbers": [52, 65, 78, 79, 86, 87]},
    {"date": "17.10.2026", "draw_no": 124, "numbers": [6, 19, 39, 59, 75, 85]},
    {"date": "14.10.2026", "draw_no": 123, "numbers": [1, 3, 65, 66, 79, 81]},
    {"date": "12.10.2026", "draw_no": 122, "numbers": [2, 16, 18, 38, 75, 79]},
    {"date": "10.10.2026", "draw_no": 121, "numbers": [14, 26, 35, 45, 47, 57]},
    {"date": "07.10.2026", "draw_no": 120, "numbers": [38, 40, 44, 48, 63, 77]},
    {"date": "05.10.2026", "draw_no": 119, "numbers": [13, 19, 29, 40, 42, 79]},

    # Eylül 2026
    {"date": "30.09.2026", "draw_no": 117, "numbers": [21, 24, 35, 36, 43, 80]},
    {"date": "28.09.2026", "draw_no": 116, "numbers": [1, 23, 57, 66, 88, 90]},
    {"date": "26.09.2026", "draw_no": 115, "numbers": [35, 42, 44, 64, 70, 87]},
    {"date": "23.09.2026", "draw_no": 114, "numbers": [10, 37, 54, 69, 82, 89]},
    {"date": "21.09.2026", "draw_no": 113, "numbers": [5, 30, 34, 53, 64, 84]},
    {"date": "19.09.2026", "draw_no": 112, "numbers": [3, 6, 9, 23, 50, 89]},
    {"date": "16.09.2026", "draw_no": 111, "numbers": [3, 4, 14, 24, 46, 76]},
    {"date": "14.09.2026", "draw_no": 110, "numbers": [35, 51, 54, 56, 66, 87]},
    {"date": "12.09.2026", "draw_no": 109, "numbers": [3, 10, 23, 24, 67, 75]},
    {"date": "09.09.2026", "draw_no": 108, "numbers": [8, 10, 24, 25, 34, 44]},
]


# ==========================================
# 3. CSV DOSYASINI OKU
# ==========================================
if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dosya bulunamadı: {DATA_FILE}")

df = pd.read_csv(DATA_FILE)

required_cols = ["date"] + NUMBER_COLS
missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    raise ValueError(f"Eksik sütunlar: {missing_cols}")

df["parsed_date"] = pd.to_datetime(
    df["date"],
    format="%d %B %Y",
    errors="coerce"
)

# Türkçe ay adlarını Python bazı Windows kurulumlarında
# otomatik tanımayabilir. Bu yüzden alternatif dönüşüm:
turkish_months = {
    "Ocak": "January",
    "Şubat": "February",
    "Mart": "March",
    "Nisan": "April",
    "Mayıs": "May",
    "Haziran": "June",
    "Temmuz": "July",
    "Ağustos": "August",
    "Eylül": "September",
    "Ekim": "October",
    "Kasım": "November",
    "Aralık": "December",
}

date_text = df["date"].astype(str).str.strip()

for turkish, english in turkish_months.items():
    date_text = date_text.str.replace(
        turkish, english, regex=False
    )

df["parsed_date"] = pd.to_datetime(
    date_text,
    format="%d %B %Y",
    errors="coerce"
)

for col in NUMBER_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ==========================================
# 4. TARİH VE SAYILARI KARŞILAŞTIR
# ==========================================
results = []

for official in official_draws:
    official_date = pd.to_datetime(
        official["date"], format="%d.%m.%Y"
    )

    matching_rows = df[df["parsed_date"] == official_date]

    if len(matching_rows) == 0:
        results.append({
            "date": official["date"],
            "official_draw_no": official["draw_no"],
            "status": "CSV'de tarih bulunamadı",
            "official_numbers": ",".join(map(str, official["numbers"])),
            "csv_numbers": "",
        })
        continue

    if len(matching_rows) > 1:
        results.append({
            "date": official["date"],
            "official_draw_no": official["draw_no"],
            "status": "CSV'de aynı tarihte birden fazla kayıt",
            "official_numbers": ",".join(map(str, official["numbers"])),
            "csv_numbers": "",
        })
        continue

    row = matching_rows.iloc[0]
    csv_numbers = sorted(int(row[col]) for col in NUMBER_COLS)
    official_numbers = sorted(official["numbers"])

    status = (
        "EŞLEŞİYOR"
        if csv_numbers == official_numbers
        else "UYUŞMAZLIK"
    )

    results.append({
        "date": official["date"],
        "official_draw_no": official["draw_no"],
        "status": status,
        "official_numbers": ",".join(map(str, official_numbers)),
        "csv_numbers": ",".join(map(str, csv_numbers)),
    })

# ==========================================
# 5. SONUÇLARI KAYDET VE GÖSTER
# ==========================================
results_df = pd.DataFrame(results)

output_file = OUTPUT_DIR / "official_verification.csv"
results_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 55)
print("RESMÎ SONUÇLARLA CSV KARŞILAŞTIRMASI")
print("=" * 55)
print(results_df.to_string(index=False))

matched = (results_df["status"] == "EŞLEŞİYOR").sum()
print(f"\nEşleşen kayıt: {matched}/{len(official_draws)}")
print(f"Rapor kaydedildi: {output_file}")
