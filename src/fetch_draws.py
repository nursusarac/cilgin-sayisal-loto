
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://loto.gen.tr"
ARCHIVE_URL = f"{BASE_URL}/cilgin-sayisal/arsiv"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "draws.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Bir veya iki ek sayı içeren çekilişleri okuyabilir.
PATTERN = re.compile(
    r"#?\s*(\d+)\s+"
    r"(\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4})\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s*\+\s*"
    r"(\d{1,2})(?:\s+(\d{1,2}))?"
)

session = requests.Session()
session.headers.update(HEADERS)


def get_page(page):
    params = {"sayfa": page} if page > 1 else None

    response = session.get(
        ARCHIVE_URL,
        params=params,
        timeout=30
    )
    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def parse_page(soup):
    rows = []
    skipped = 0

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/cilgin-sayisal/cekilis/" not in href:
            continue

        text = link.get_text(" ", strip=True)
        match = PATTERN.search(text)

        if not match:
            print("Kontrol edilmeli:", text)
            skipped += 1
            continue

        values = match.groups()

        draw_id = values[0]
        date = values[1]
        main = [int(x) for x in values[2:8]]

        extra1 = int(values[8])
        extra2 = int(values[9]) if values[9] else None

        # Altı ana sayı birbirinden farklı ve 1-90 arasında olmalı.
        if (
            len(set(main)) != 6
            or any(n < 1 or n > 90 for n in main)
            or not 1 <= extra1 <= 90
            or (
                extra2 is not None
                and not 1 <= extra2 <= 90
            )
        ):
            print("Geçersiz kayıt:", text)
            skipped += 1
            continue

        if href.startswith("http"):
            source_url = href
        else:
            source_url = BASE_URL + href

        row = {
            "draw_id": draw_id,
            "date": date,
            "n1": sorted(main)[0],
            "n2": sorted(main)[1],
            "n3": sorted(main)[2],
            "n4": sorted(main)[3],
            "n5": sorted(main)[4],
            "n6": sorted(main)[5],
            "extra1": extra1,
            "extra2": extra2,
            "source_url": source_url
        }

        rows.append(row)

    return rows, skipped


def main():
    print("Arşiv inceleniyor...")

    first_page = get_page(1)
    page_text = first_page.get_text(" ", strip=True)

    match = re.search(r"Sayfa\s+1\s*/\s*(\d+)", page_text)

    if not match:
        raise RuntimeError(
            "Toplam sayfa sayısı bulunamadı. "
            "Arşiv sayfasının yapısı değişmiş olabilir."
        )

    total_pages = int(match.group(1))
    all_rows = []
    total_skipped = 0

    for page in range(1, total_pages + 1):
        try:
            soup = first_page if page == 1 else get_page(page)
            rows, skipped = parse_page(soup)

            all_rows.extend(rows)
            total_skipped += skipped

            print(
                f"{page}/{total_pages}. sayfa: "
                f"{len(rows)} kayıt, {skipped} atlanan"
            )

            if page > 1:
                time.sleep(0.4)

        except requests.RequestException as error:
            raise RuntimeError(
                f"{page}. sayfa alınamadı. "
                "Eksik veriyle devam edilmedi: {error}"
            ) from error

    if not all_rows:
        raise RuntimeError("Hiç çekiliş kaydı bulunamadı.")

    df = pd.DataFrame(all_rows)

    # Aynı çekiliş birden fazla kez geldiyse tek kayıt bırak.
    df = df.drop_duplicates(subset="draw_id")

    df["_sort_id"] = pd.to_numeric(
        df["draw_id"],
        errors="coerce"
    )

    df = (
        df.sort_values("_sort_id")
        .drop(columns="_sort_id")
        .reset_index(drop=True)
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=== TOPLAMA RAPORU ===")
    print("Kaydedilen kayıt:", len(df))
    print("Benzersiz çekiliş:", df["draw_id"].nunique())
    print("Kontrol için atlanan bağlantı:", total_skipped)
    print("İkinci ek sayısı boş kayıt:", int(df["extra2"].isna().sum()))
    print("Dosya:", OUTPUT.resolve())

    print("\nEn eski kayıt:")
    print(df.iloc[0][["draw_id", "date"]].to_string())

    print("\nEn yeni kayıt:")
    print(df.iloc[-1][["draw_id", "date"]].to_string())


if __name__ == "__main__":
    main()
