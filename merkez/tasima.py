import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from . import ayarlar, gunluk, indirici, zamanlayici

ESKI_KOK = Path(r"C:\Users\ardam\Desktop\dersler3-1\Dosya_Organizasyonu")
ESKI_KLASOR = ESKI_KOK / "haftalik"
ESKI_DURUM = ESKI_KOK / "otomasyon" / "indirilenler.json"
ESKI_GOREV = "DosyaOrganizasyonu_HaftalikCek"
SLUG = "dosya-organizasyonu"
AD = "Dosya Organizasyonu"
DEPO = "emirozturk/Dosya-Organizasyonu-2026"
DESEN = "Hafta*.pdf"


def _sha256(yol):
    ozet = hashlib.sha256()
    with open(yol, "rb") as akis:
        for parca in iter(lambda: akis.read(1 << 20), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def _manifest(klasor):
    kayitlar = []
    for yol in sorted(klasor.iterdir(), key=lambda p: p.name):
        if yol.is_file():
            kayitlar.append({"ad": yol.name, "boyut": yol.stat().st_size, "sha256": _sha256(yol)})
    return kayitlar


def _ps_cikti(komut):
    try:
        sonuc = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if sonuc.returncode != 0:
        return ""
    return sonuc.stdout or ""


def _kanit_klasoru():
    yol = ayarlar.KOK / "belgeler" / "gecmis"
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def _geri_al(slug, ders_eklendi, onceki_oto):
    if zamanlayici.gorev_bizim(slug):
        try:
            zamanlayici.gorev_kaldir(slug)
        except Exception:
            pass
    try:
        if ders_eklendi:
            ayarlar.ders_sil(slug)
        elif onceki_oto is not None:
            ayarlar.otomasyon_ayarla(slug, onceki_oto.get("gunler") or ["PZT"],
                                     onceki_oto.get("saat", "09:00"), bool(onceki_oto.get("aktif")))
    except Exception:
        pass


def calistir(kuru=False, onayla=False, gunler=("PZT",), saat="09:00"):
    satirlar = []

    def ekle(mesaj):
        satirlar.append(mesaj)
        gunluk.kayit("BILGI", "[tasima] " + mesaj)

    try:
        kanit = _kanit_klasoru()
        gorev_xml = _ps_cikti(["schtasks", "/Query", "/TN", ESKI_GOREV, "/XML"])
        if gorev_xml:
            (kanit / "eski-gorev.xml").write_text(gorev_xml, encoding="utf-8")
            ekle("Eski gorev XML'i kaydedildi: {}".format(ESKI_GOREV))
        else:
            ekle("UYARI: Eski gorev bulunamadi: {}".format(ESKI_GOREV))
        if ESKI_KLASOR.exists():
            manifest = _manifest(ESKI_KLASOR)
            (kanit / "haftalik-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ekle("Kaynak manifesti: {} dosya".format(len(manifest)))
        else:
            ekle("UYARI: Kaynak klasor yok: {}".format(ESKI_KLASOR))
            manifest = []
        if ESKI_DURUM.exists():
            shutil.copy2(ESKI_DURUM, kanit / "eski-indirilenler.json")
            ekle("Eski durum dosyasi kopyalandi")
        if kuru:
            ekle("KURU CALISMA: kopyalama, ders kaydi ve gorev islemleri yapilmadi.")
            (kanit / "tasima-dogrulama-kuru.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
            return {"ok": True, "satirlar": satirlar}

        hedef = ayarlar.KOK / "dersler" / SLUG
        hedef.mkdir(parents=True, exist_ok=True)
        yeni_manifest = []
        for kayit in manifest:
            kaynak = ESKI_KLASOR / kayit["ad"]
            varis = hedef / kayit["ad"]
            if varis.exists() and _sha256(varis) == kayit["sha256"]:
                ekle("Zaten ayni, kopyalanmadi: {}".format(kayit["ad"]))
            else:
                shutil.copy2(kaynak, varis)
                ekle("Kopyalandi: {}".format(kayit["ad"]))
            yeni_manifest.append({"ad": kayit["ad"], "boyut": varis.stat().st_size, "sha256": _sha256(varis)})
        eslesme = len(manifest) == len(yeni_manifest) and all(
            a["ad"] == b["ad"] and a["boyut"] == b["boyut"] and a["sha256"] == b["sha256"]
            for a, b in zip(manifest, yeni_manifest))
        if not eslesme:
            raise RuntimeError("Manifest karsilastirmasi basarisiz")
        (kanit / "yeni-manifest.json").write_text(
            json.dumps(yeni_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ekle("Manifest dogrulandi: {} dosya".format(len(yeni_manifest)))

        veri = ayarlar.yukle()
        onceki_oto = ((veri["dersler"].get(SLUG) or {}).get("otomasyon")) or None
        if SLUG not in veri["dersler"]:
            ayarlar.ders_ekle(AD, DEPO, "main", DESEN, SLUG)
            ders_eklendi = True
            ekle("Ders kaydi eklendi: {}".format(SLUG))
        else:
            ders_eklendi = False
            ekle("Ders kaydi zaten var: {}".format(SLUG))

        try:
            rapor = indirici.indir_ders(SLUG, secili_zorunlu=False)
            ekle("Cekme dogrulamasi: yeni={} guncellenen={} atlanan={} baglam={}".format(
                rapor["yeni"], rapor["guncellenen"], rapor["atlanan"], rapor["baglam"]))
            if rapor["yeni"] or rapor["guncellenen"]:
                ekle("NOT: Bazi dosyalar yeniden indirildi (blob SHA eslesmemis olabilir).")
            for hata in rapor["hatalar"]:
                ekle("UYARI: {}".format(hata))

            ayarlar.otomasyon_ayarla(SLUG, list(gunler), saat, True)
            zamanlayici.gorev_kur(SLUG, list(gunler), saat)
            sorgu = zamanlayici.gorev_sorgu(SLUG)
            if not sorgu.get("var"):
                raise RuntimeError("Yeni gorev dogrulanamadi")
            ekle("Yeni gorev dogrulandi: {} ({})".format(sorgu.get("gorev"), sorgu.get("durum", "")))
        except Exception:
            _geri_al(SLUG, ders_eklendi, onceki_oto)
            raise

        eski_var = bool(_ps_cikti(["schtasks", "/Query", "/TN", ESKI_GOREV]))
        if eski_var and onayla:
            zamanlayici.gorev_sil_genel(ESKI_GOREV)
            kaldi = bool(_ps_cikti(["schtasks", "/Query", "/TN", ESKI_GOREV]))
            if kaldi:
                raise RuntimeError("Eski gorev kaldirilamadi: {}".format(ESKI_GOREV))
            ekle("Eski gorev kaldirildi: {}".format(ESKI_GOREV))
        elif eski_var:
            ekle("Eski gorev duruyor (kaldirmak icin --onayla kullanin): {}".format(ESKI_GOREV))
        else:
            ekle("Eski gorev zaten yok.")

        (kanit / "tasima-dogrulama.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        return {"ok": True, "satirlar": satirlar}
    except Exception as hata:
        ekle("HATA: {}".format(hata))
        try:
            (ayarlar.KOK / "belgeler" / "gecmis" / "tasima-dogrulama.txt").write_text(
                "\n".join(satirlar) + "\n", encoding="utf-8")
        except OSError:
            pass
        return {"ok": False, "satirlar": satirlar}
