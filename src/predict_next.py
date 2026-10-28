
from pathlib import Path

import pandas as pd
import numpy as np

# Proje klasörünü bul
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "draws.csv"

# Geçmiş çekilişleri oku
df = pd.read_csv(DATA_FILE)

number_cols = [f"n{i}" for i in range(1, 7)]
numbers = df[number_cols].to_numpy().ravel()

# 1-90 arasındaki her sayının görülme sıklığı
frequency = (
    pd.Series(numbers)
    .value_counts()
    .reindex(range(1, 91), fill_value=0)
)

# Tahmin stratejisi: geçmiş frekanslarına göre ağırlıklı seçim
# Bu yöntem bir deneydir; geleceği bildiği anlamına gelmez.
weights = frequency.to_numpy(dtype=float)

# Her sayıya küçük bir başlangıç ağırlığı ver
weights = weights + 1

# Aynı kolonda 6 farklı sayı seç
rng = np.random.default_rng()
prediction = rng.choice(
    np.arange(1, 91),
    size=6,
    replace=False,
    p=weights / weights.sum()
)

prediction = sorted(prediction.tolist())

print("\n=== ÇILGIN SAYISAL LOTO TAHMİNİ ===")
print("Kullanılan geçmiş çekiliş sayısı:", len(df))
print("Önerilen 6 sayı:", " - ".join(map(str, prediction)))
print("\nNot: Bu bir istatistiksel denemedir; kazanma garantisi yoktur.")
