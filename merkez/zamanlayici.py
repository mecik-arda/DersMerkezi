import json
import subprocess
import sys
from pathlib import Path

from . import ayarlar, gunluk

PS_KLASOR = Path(__file__).resolve().parent / "ps"
POWERSHELL = "powershell.exe"
SLUG_DESENI = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def python_yolu():
    aday = Path(sys.executable)
    pythonw = aday.with_name("pythonw.exe")
    return str(pythonw if pythonw.exists() else aday)


def _ps(betik, parametreler):
    komut = [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(PS_KLASOR / betik)]
    for anahtar, deger in parametreler.items():
        komut.extend(["-" + anahtar, str(deger)])
    try:
        sonuc = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired) as hata:
        raise RuntimeError("PowerShell çalıştırılamadı: {}".format(hata)) from hata
    veri = {}
    for satir in reversed((sonuc.stdout or "").splitlines()):
        satir = satir.strip()
        if satir.startswith("{"):
            try:
                veri = json.loads(satir)
                break
            except ValueError:
                continue
    if not veri.get("ok"):
        mesaj = veri.get("hata") or (sonuc.stderr or "").strip() or "Görev işlemi başarısız (kod {})".format(sonuc.returncode)
        raise RuntimeError(mesaj)
    return veri


def _slug_dogrula(slug):
    import re
    if not re.match(SLUG_DESENI, slug or "") or not 2 <= len(slug) <= 40:
        raise ValueError("Geçersiz ders kimliği: {}".format(slug))


def beklenen_arguman(slug):
    return '"{0}" --otomatik --ders {1} --sessiz'.format(ayarlar.KOK / "dersmerkezi.py", slug)


def _sorgu_bizim(sorgu, slug):
    execute = str(sorgu.get("execute") or "").strip().lower()
    eylem = str(sorgu.get("eylem") or "").strip()
    if int(sorgu.get("eylemSayisi") or 0) != 1:
        return False
    return execute == python_yolu().strip().lower() and eylem == beklenen_arguman(slug)


def gorev_bizim(slug):
    try:
        sorgu = gorev_sorgu(slug)
    except Exception:
        return False
    return bool(sorgu.get("var")) and _sorgu_bizim(sorgu, slug)


def gorev_durumu(slug):
    sorgu = gorev_sorgu(slug)
    if not sorgu.get("var"):
        return "yok"
    return "bizim" if _sorgu_bizim(sorgu, slug) else "yabanci"


def gorev_yedek_yolu(slug):
    return ayarlar.KOK / "belgeler" / "gecmis" / "gorev_{}_onceki.xml".format(slug)


def gorev_kur(slug, gunler, saat):
    _slug_dogrula(slug)
    gun_adlari = ayarlar.gun_listesi_coz(gunler)
    if not ayarlar.saat_gecerli(saat):
        raise ValueError("Saat SS:DD biçiminde olmalı")
    betik = str(ayarlar.KOK / "dersmerkezi.py")
    yedek = gorev_yedek_yolu(slug)
    try:
        yedek.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return _ps("gorev_kur.ps1", {
        "GorevAdi": "DersMerkezi_" + slug,
        "PythonYolu": python_yolu(),
        "BetikYolu": betik,
        "Ders": slug,
        "Gunler": ",".join(gun_adlari),
        "Saat": saat,
        "YedekYolu": str(yedek),
    })


def gorev_geri_yukle(slug, xml_yolu):
    _slug_dogrula(slug)
    return _ps("gorev_yukle.ps1", {
        "GorevAdi": "DersMerkezi_" + slug,
        "XmlYolu": str(xml_yolu),
        "BeklenenExecute": python_yolu(),
        "BeklenenArguman": beklenen_arguman(slug),
    })


def gorev_kur_guvenli(slug, gunler, saat):
    durum = gorev_durumu(slug)
    if durum == "yabanci":
        raise RuntimeError("Ayni adli gorev bu kuruluma ait degil: {}".format(slug))
    vardi = durum == "bizim"
    sonuc = gorev_kur(slug, gunler, saat)
    try:
        ayarlar.otomasyon_ayarla(slug, gunler, saat, True)
    except Exception as hata_ayar:
        geri_hata = None
        try:
            if vardi:
                gorev_geri_yukle(slug, gorev_yedek_yolu(slug))
            else:
                durum_sonra = gorev_durumu(slug)
                if durum_sonra == "bizim":
                    gorev_kaldir(slug)
                elif durum_sonra == "yabanci":
                    geri_hata = RuntimeError("Gorev durumu beklenmedik (yabanci); geri alma yapilmadi")
        except Exception as hata_geri:
            geri_hata = hata_geri
        if geri_hata is not None:
            raise RuntimeError("Ayar yazilamadi ve gorev geri alinamadi: {} / {}".format(hata_ayar, geri_hata)) from hata_ayar
        raise
    return sonuc


def gorev_kaldir(slug):
    _slug_dogrula(slug)
    return _ps("gorev_kaldir.ps1", {
        "GorevAdi": "DersMerkezi_" + slug,
        "BeklenenExecute": python_yolu(),
        "BeklenenArguman": beklenen_arguman(slug),
    })


def gorev_sorgu(slug):
    _slug_dogrula(slug)
    return _ps("gorev_sorgu.ps1", {"GorevAdi": "DersMerkezi_" + slug})


def gorev_sil_genel(ad):
    import re
    if not re.match(r"^[A-Za-z0-9_-]{1,120}$", ad or ""):
        raise ValueError("Geçersiz görev adı: {}".format(ad))
    return _ps("gorev_sil.ps1", {"GorevAdi": ad})
