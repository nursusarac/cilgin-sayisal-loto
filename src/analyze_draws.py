
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. DOSYA YOLLARI
# ==========================================
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "draws.csv"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]
REQUIRED_COLS = ["draw_id", "date"] + NUMBER_COLS

# ==========================================
# 2. VERİYİ OKU
# ==========================================
if not DATA_FILE.exists():
    raise FileNotFoundError(f"Veri dosyası bulunamadı: {DATA_FILE}")

df = pd.read_csv(DATA_FILE)

missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
if missing_cols:
    raise ValueError(f"CSV dosyasında eksik sütunlar var: {missing_cols}")

numbers = df[NUMBER_COLS].apply(pd.to_numeric, errors="coerce")

print("=" * 55)
print("ÇILGIN SAYISAL LOTO - VERİ KALİTESİ VE ANALİZ RAPORU")
print("=" * 55)

# ==========================================
# 3. VERİ KALİTESİ KONTROLLERİ
# ==========================================
duplicate_ids = df["draw_id"].duplicated(keep=False)
missing_number_rows = numbers.isna().any(axis=1)
out_of_range_rows = (
    numbers.lt(1).any(axis=1) | numbers.gt(90).any(axis=1)
) & ~missing_number_rows

unique_number_rows = numbers.nunique(axis=1).eq(6)
complete_rows = numbers.notna().all(axis=1)
valid_range_rows = numbers.ge(1).all(axis=1) & numbers.le(90).all(axis=1)

# Tam geçerli bir çekiliş için altı sayı eksiksiz,
# 1-90 aralığında ve birbirinden farklı olmalıdır.
valid_mask = complete_rows & valid_range_rows & unique_number_rows

print(f"CSV satır sayısı: {len(df)}")
print(f"Tekrarlanan draw_id içeren satır: {int(duplicate_ids.sum())}")
print(f"Eksik ana sayı içeren satır: {int(missing_number_rows.sum())}")
print(f"Aralık dışı sayı içeren satır: {int(out_of_range_rows.sum())}")
print(f"Altı farklı ana sayısı olan satır: {int(unique_number_rows.sum())}")
print(f"Geçerli çekiliş satırı: {int(valid_mask.sum())}")
print(f"Geçersiz çekiliş satırı: {int((~valid_mask).sum())}")

# Aynı çekiliş ID'si birden fazla görünüyorsa ayrıca raporla.
# Otomatik silmiyoruz; önce kaydı incelemek daha güvenli.
duplicate_id_rows = df.loc[duplicate_ids].copy()
duplicate_id_rows.to_csv(
    OUTPUT_DIR / "duplicate_draw_ids.csv",
    index=False,
    encoding="utf-8-sig"
)

# Analizde geçerli satırları kullan.
clean_numbers = numbers.loc[valid_mask].astype(int)

if clean_numbers.empty:
    raise ValueError("Analiz edilecek geçerli çekiliş bulunamadı.")

# ==========================================
# 4. AYNI SAYI KÜMESİNE SAHİP SATIRLAR
# ==========================================
# Farklı çekiliş ID'lerinde aynı altı ana sayı varsa işaretle.
# Bu tek başına hata kanıtı değildir; yalnızca kontrol işaretidir.
sorted_combinations = clean_numbers.apply(
    lambda row: tuple(sorted(row.tolist())),
    axis=1
)

same_combination = sorted_combinations.duplicated(keep=False)

same_combination_rows = df.loc[clean_numbers.index[same_combination]].copy()
same_combination_rows.to_csv(
    OUTPUT_DIR / "repeated_number_combinations.csv",
    index=False,
    encoding="utf-8-sig"
)

print(
    "Aynı altı ana sayı kombinasyonunu paylaşan geçerli satır:",
    int(same_combination.sum())
)

# ==========================================
# 5. SAYI FREKANSLARI
# ==========================================
all_numbers = clean_numbers.to_numpy().ravel()

frequency = (
    pd.Series(all_numbers)
    .value_counts()
    .reindex(range(1, 91), fill_value=0)
    .rename_axis("number")
    .reset_index(name="count")
)

draw_count = len(clean_numbers)
expected_frequency = draw_count * 6 / 90

frequency["expected"] = expected_frequency
frequency["difference"] = frequency["count"] - expected_frequency
frequency["frequency_per_draw"] = frequency["count"] / draw_count

frequency = frequency.sort_values("number")

frequency.to_csv(
    OUTPUT_DIR / "number_frequency.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nEN SIK GÖRÜLEN 10 SAYI")
print(
    frequency.sort_values(
        ["count", "number"], ascending=[False, True]
    ).head(10).to_string(index=False)
)

print("\nEN AZ GÖRÜLEN 10 SAYI")
print(
    frequency.sort_values(
        ["count", "number"], ascending=[True, True]
    ).head(10).to_string(index=False)
)

print(f"\nSayı başına beklenen frekans: {expected_frequency:.2f}")

# ==========================================
# 6. FREKANS GRAFİĞİ
# ==========================================
plt.figure(figsize=(15, 6))
plt.bar(frequency["number"], frequency["count"])
plt.axhline(
    expected_frequency,
    linestyle="--",
    label="Adil çekilişte beklenen frekans"
)
plt.xlabel("Ana sayı")
plt.ylabel("Görülme sayısı")
plt.title(f"Sayı frekansları - {draw_count} geçerli çekiliş")
plt.xticks(range(1, 91, 5))
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "number_frequency.png", dpi=150)
plt.close()

# ==========================================
# 7. TEK-ÇİFT DAĞILIMI
# ==========================================
odd_even_rows = []

for row in clean_numbers.to_numpy():
    odd_count = sum(number % 2 != 0 for number in row)
    even_count = 6 - odd_count

    odd_even_rows.append({
        "odd": odd_count,
        "even": even_count
    })

odd_even_df = pd.DataFrame(odd_even_rows)

odd_even_summary = (
    odd_even_df.groupby(["odd", "even"])
    .size()
    .reset_index(name="draw_count")
    .sort_values(["odd", "even"])
)

odd_even_summary.to_csv(
    OUTPUT_DIR / "odd_even_distribution.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nTEK-ÇİFT DAĞILIMI")
print(odd_even_summary.to_string(index=False))

# ==========================================
# 8. VERİ KALİTESİ ÖZETİ
# ==========================================
summary = pd.DataFrame([{
    "total_rows": len(df),
    "valid_draws": int(valid_mask.sum()),
    "excluded_draws": int((~valid_mask).sum()),
    "duplicate_draw_id_rows": int(duplicate_ids.sum()),
    "missing_number_rows": int(missing_number_rows.sum()),
    "out_of_range_rows": int(out_of_range_rows.sum()),
    "same_combination_rows": int(same_combination.sum()),
    "expected_frequency_per_number": expected_frequency,
    "source_file": str(DATA_FILE)
}])

summary.to_csv(
    OUTPUT_DIR / "data_quality_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nAnaliz tamamlandı.")
print("Oluşturulan dosyalar:")
print("- outputs/number_frequency.csv")
print("- outputs/number_frequency.png")
print("- outputs/odd_even_distribution.csv")
print("- outputs/data_quality_summary.csv")
print("- outputs/duplicate_draw_ids.csv")
print("- outputs/repeated_number_combinations.csv")
