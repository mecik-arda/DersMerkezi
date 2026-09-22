import json

from . import ayarlar, zamanlayici


def _durum_ozeti(kimlik):
    yol = ayarlar.KOK / "dersler" / kimlik / "indirilenler.json"
    ozet = {"dosya": 0, "bayt": 0, "guncelleme": None, "hata": None}
    if not yol.exists():
        ozet["hata"] = "durum dosyası yok"
        return ozet
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        dosyalar = veri.get("dosyalar") or {}
        if not isinstance(dosyalar, dict):
            raise ValueError("dosyalar bölümü geçersiz")
        ozet["dosya"] = len(dosyalar)
        ozet["bayt"] = sum(int((kayit or {}).get("boyut") or 0) for kayit in dosyalar.values())
        ozet["guncelleme"] = veri.get("guncelleme") or None
    except (OSError, ValueError, TypeError):
        ozet["hata"] = "durum dosyası okunamadı"
    return ozet


def _gorev_bilgisi(kimlik, ayrintili):
    gorev = {"durum": "yok", "sonCalisma": None, "sonSonuc": None}
    if ayrintili:
        gorev["eylem"] = None
    try:
        sorgu = zamanlayici.gorev_sorgu(kimlik)
    except RuntimeError:
        gorev["durum"] = "sorgulanamadı"
        return gorev
    if sorgu.get("var"):
        gorev["durum"] = str(sorgu.get("durum") or "kayıtlı")
        gorev["sonCalisma"] = sorgu.get("sonCalisma") or None
        try:
            gorev["sonSonuc"] = int(sorgu.get("sonSonuc"))
        except (TypeError, ValueError):
            gorev["sonSonuc"] = None
        if ayrintili:
            gorev["eylem"] = sorgu.get("eylem") or None
    return gorev


def _uret(veri, ayrintili=False, ders=None):
    sonuc = []
    for kimlik, kayit in veri["dersler"].items():
        if ders and kimlik != ders:
            continue
        oto = kayit.get("otomasyon", {}) or {}
        kayit_verisi = {
            "kimlik": kimlik,
            "ad": str(kayit.get("ad", "")),
            "depo": str(kayit.get("depo", "")),
            "secili": bool(kayit.get("secili", True)),
            "otomasyon": {
                "aktif": bool(oto.get("aktif")),
                "gunler": list(oto.get("gunler") or []),
                "saat": str(oto.get("saat", "09:00")),
                "gorev": _gorev_bilgisi(kimlik, ayrintili),
            },
        }
        if ayrintili:
            kayit_verisi["durum_dosyasi"] = _durum_ozeti(kimlik)
        sonuc.append(kayit_verisi)
    return sonuc


def kayitlar(ayrintili=False, ders=None):
    return _uret(ayarlar.yukle(), ayrintili, ders)


def kayitlar_salt(ayrintili=False):
    veri, hata = ayarlar.yukle_salt()
    if hata:
        return None, hata
    return _uret(veri, ayrintili), None
