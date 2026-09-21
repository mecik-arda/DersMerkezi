#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from pypdf import PdfReader


def main() -> int:
    ayristirici = argparse.ArgumentParser(description="PDF dosyasını Markdown ders bağlamına dönüştürür.")
    ayristirici.add_argument("girdi", help="Kaynak PDF yolu")
    ayristirici.add_argument("cikti", help="Üretilecek Markdown yolu")
    ayristirici.add_argument("--kaynak", default="", help="Kaynak URL")
    ayristirici.add_argument("--sha", default="", help="Git blob SHA")
    ayristirici.add_argument("--tarih", default="", help="Dönüştürme zamanı")
    secenekler = ayristirici.parse_args()

    girdi = Path(secenekler.girdi)
    if not girdi.is_file():
        print(f"Girdi bulunamadı: {girdi}", file=sys.stderr)
        return 2

    try:
        okuyucu = PdfReader(str(girdi))
        sayfalar = list(okuyucu.pages)
    except Exception as hata:
        print(f"PDF okunamadı: {hata}", file=sys.stderr)
        return 3

    metinler = []
    metinli_sayfa = 0
    for numara, sayfa in enumerate(sayfalar, start=1):
        try:
            metin = (sayfa.extract_text() or "").strip()
        except Exception:
            metin = ""
        if metin:
            metinli_sayfa += 1
        metinler.append((numara, metin))

    satirlar = [
        f"# {girdi.stem} — Ders Bağlamı",
        "",
        f"> Kaynak: {secenekler.kaynak}",
        f"> Git blob SHA: {secenekler.sha}",
        f"> Dönüştürme: {secenekler.tarih}",
        f"> Sayfa: {len(sayfalar)} (metin içeren: {metinli_sayfa})",
        "",
        "---",
        "",
    ]
    if metinli_sayfa == 0:
        satirlar.append("> UYARI: PDF içinde çıkarılabilir metin katmanı bulunamadı; dosya görüntü tabanlı olabilir ve OCR gerektirir.")
        satirlar.append("")

    for numara, metin in metinler:
        satirlar.append(f"## Sayfa {numara}")
        satirlar.append("")
        satirlar.append(metin if metin else "_Bu sayfada çıkarılabilir metin bulunamadı._")
        satirlar.append("")

    cikti = Path(secenekler.cikti)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text("\n".join(satirlar), encoding="utf-8")
    print(f"Bağlam üretildi: {cikti.name} (sayfa: {len(sayfalar)}, metinli: {metinli_sayfa})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
