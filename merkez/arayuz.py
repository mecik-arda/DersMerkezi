import msvcrt

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import ayarlar, gunluk, indirici, zamanlayici

KONSOL = Console()

GUN_ETIKET = [("PZT", "Pazartesi"), ("SAL", "Sali"), ("CAR", "Carsamba"), ("PER", "Persembe"),
              ("CUM", "Cuma"), ("CMT", "Cumartesi"), ("PAZ", "Pazar")]


def _tus():
    olay = msvcrt.getwch()
    if olay in ("\x00", "\xe0"):
        ikinci = msvcrt.getwch()
        return {"H": "yukari", "P": "asagi", "K": "geri", "M": "ileri"}.get(ikinci, "yok")
    if olay == "\r":
        return "enter"
    if olay == " ":
        return "bosluk"
    if olay == "\x1b":
        return "cikis"
    if olay == "\x03":
        raise KeyboardInterrupt
    return olay.lower()


def _bekle_enter():
    while True:
        if _tus() == "enter":
            return


def _secim(baslik, secenekler, aciklama=None):
    imlec = 0
    KONSOL.show_cursor(False)
    try:
        while True:
            KONSOL.clear()
            KONSOL.print(Panel.fit("[bold]{}[/bold]".format(baslik), border_style="cyan"))
            if aciklama:
                KONSOL.print("[dim]{}[/dim]".format(aciklama))
            KONSOL.print()
            for sira, secenek in enumerate(secenekler):
                im = "[bold green]>[/bold green] " if sira == imlec else "  "
                KONSOL.print(im + secenek)
            olay = _tus()
            if olay == "yukari":
                imlec = (imlec - 1) % len(secenekler)
            elif olay == "asagi":
                imlec = (imlec + 1) % len(secenekler)
            elif olay == "enter":
                return imlec
            elif olay == "cikis":
                return None
    finally:
        KONSOL.show_cursor(True)


def _coklu_secim(baslik, ogeler, secili_kume):
    imlec = 0
    secili = set(secili_kume)
    KONSOL.show_cursor(False)
    try:
        while True:
            KONSOL.clear()
            KONSOL.print(Panel.fit("[bold]{}[/bold]".format(baslik), border_style="cyan"))
            KONSOL.print("[dim]Bosluk: isaretle, Enter: kaydet, ESC: vazgec[/dim]\n")
            for sira, (kimlik, etiket) in enumerate(ogeler):
                im = "[bold green]>[/bold green] " if sira == imlec else "  "
                kutu = "[green][x][/green]" if kimlik in secili else "[ ]"
                KONSOL.print("{} {} {}".format(im, kutu, etiket))
            olay = _tus()
            if olay == "yukari":
                imlec = (imlec - 1) % len(ogeler)
            elif olay == "asagi":
                imlec = (imlec + 1) % len(ogeler)
            elif olay == "bosluk":
                kimlik = ogeler[imlec][0]
                if kimlik in secili:
                    secili.discard(kimlik)
                else:
                    secili.add(kimlik)
            elif olay == "enter":
                return secili
            elif olay == "cikis":
                return None
    finally:
        KONSOL.show_cursor(True)


def _cek_ekrani(anahtarlar):
    kilit = gunluk.Kilit()
    if not kilit.al():
        KONSOL.print("[yellow]Baska bir calisma suruyor; cekme atlandi.[/yellow]")
        _bekle_enter()
        return
    KONSOL.show_cursor(False)
    try:
        KONSOL.clear()
        KONSOL.print(Panel.fit("[bold]Ders icerikleri cekiliyor[/bold]", border_style="cyan"))
        for anahtar in anahtarlar:
            with Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(bar_width=None),
                          TextColumn("{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=KONSOL) as ilerleme:
                gorev = ilerleme.add_task(anahtar, total=100)

                def geri_bildirim(asama, etiket, okunan=0, toplam=0, _g=gorev, _i=ilerleme, _a=anahtar):
                    if asama == "liste":
                        _i.update(_g, description="{}: depo listeleniyor".format(escape(_a)), completed=2)
                    elif asama == "indir" and toplam:
                        _i.update(_g, description="{}: indiriliyor {}".format(escape(_a), escape(str(etiket))),
                                  completed=min(99.0, okunan / toplam * 100.0))
                    elif asama == "donustur":
                        _i.update(_g, description="{}: baglam uretiliyor {}".format(escape(_a), escape(str(etiket))),
                                  completed=99)

                try:
                    rapor = indirici.indir_ders(anahtar, ilerleme=geri_bildirim)
                    ilerleme.update(gorev, completed=100, description="{}: tamam (yeni={} guncel={} atlanan={} baglam={} hata={})".format(
                        escape(anahtar), rapor["yeni"], rapor["guncellenen"], rapor["atlanan"], rapor["baglam"],
                        rapor["dogrulama_hatasi"] + rapor["donusum_hatasi"]))
                    for hata in rapor["hatalar"]:
                        KONSOL.print("  [yellow]- {}[/yellow]".format(escape(str(hata))))
                except (indirici.IndirmeHatasi, RuntimeError, ValueError, OSError) as hata:
                    ilerleme.update(gorev, completed=100, description="{}: HATA".format(escape(anahtar)))
                    KONSOL.print("  [red]{}: {}[/red]".format(escape(anahtar), escape(str(hata))))
        KONSOL.print()
        KONSOL.print("[bold green]Islem tamamlandi.[/bold green]")
        _bekle_enter()
    finally:
        KONSOL.show_cursor(True)
        kilit.birak()


def _cek_menu():
    veri = ayarlar.yukle()
    secililer = [k for k, d in veri["dersler"].items() if d.get("secili", True)]
    if not secililer:
        KONSOL.print("[yellow]Cekilecek ders yok. Ayarlar menusunden isaretleyin.[/yellow]")
        _bekle_enter()
        return
    if Confirm.ask("{} ders cekilecek. Baslansin mi?".format(len(secililer)), default=True):
        _cek_ekrani(secililer)


def _ders_tablosu(veri):
    tablo = Table(title="Dersler")
    tablo.add_column("Kimlik")
    tablo.add_column("Ad")
    tablo.add_column("Depo")
    tablo.add_column("Cekilecek")
    tablo.add_column("Otomasyon")
    for kimlik, ders in veri["dersler"].items():
        oto = ders.get("otomasyon", {}) or {}
        if oto.get("aktif"):
            oto_metin = "{} {}".format(",".join(oto.get("gunler", [])), oto.get("saat", ""))
        else:
            oto_metin = "kapali"
        tablo.add_row(escape(str(kimlik)), escape(str(ders.get("ad", ""))), escape(str(ders.get("depo", ""))),
                      "evet" if ders.get("secili", True) else "hayir", escape(oto_metin))
    return tablo


def _ders_ekle_ekrani():
    KONSOL.clear()
    try:
        ad = Prompt.ask("Ders adi")
        depo = Prompt.ask("Depo (owner/repo)")
        dal = Prompt.ask("Dal", default="main")
        desen = Prompt.ask("Dosya deseni", default="Hafta*.pdf")
        kimlik = ayarlar.ders_ekle(ad, depo, dal, desen)
        KONSOL.print("[green]Eklendi: {}[/green]".format(escape(kimlik)))
    except ValueError as hata:
        KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
    _bekle_enter()


def _ders_sil_ekrani(veri):
    if not veri["dersler"]:
        KONSOL.print("[yellow]Kayitli ders yok.[/yellow]")
        _bekle_enter()
        return
    ogeler = [(k, "{} ({})".format(escape(str(d.get("ad", k))), k)) for k, d in veri["dersler"].items()]
    secim = _secim("Silinecek dersi sec", [etiket for _, etiket in ogeler] + ["Geri"])
    if secim is None or secim == len(ogeler):
        return
    kimlik = ogeler[secim][0]
    if Confirm.ask("'{}' kaydi silinsin mi? (indirilen dosyalar korunur)".format(kimlik), default=False):
        try:
            try:
                sorgu = zamanlayici.gorev_sorgu(kimlik)
            except RuntimeError as hata:
                raise RuntimeError("Gorev sorgulanamadi: {}".format(hata))
            if sorgu.get("var"):
                if not zamanlayici.gorev_bizim(kimlik):
                    raise RuntimeError("Gorev bu kuruluma ait degil; ders silinmedi")
                zamanlayici.gorev_kaldir(kimlik)
            ayarlar.ders_sil(kimlik)
            KONSOL.print("[green]Silindi: {}[/green]".format(escape(kimlik)))
        except (ValueError, RuntimeError) as hata:
            KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
        _bekle_enter()


def dersler_ekrani():
    while True:
        veri = ayarlar.yukle()
        KONSOL.clear()
        KONSOL.print(_ders_tablosu(veri))
        secim = _secim("Dersler", ["Yeni ders ekle", "Ders cikar", "Geri"])
        if secim is None or secim == 2:
            return
        if secim == 0:
            _ders_ekle_ekrani()
        else:
            _ders_sil_ekrani(veri)


def ayarlar_ekrani():
    veri = ayarlar.yukle()
    if not veri["dersler"]:
        KONSOL.print("[yellow]Once ders ekleyin.[/yellow]")
        _bekle_enter()
        return
    ogeler = [(k, "{} ({})".format(escape(str(d.get("ad", k))), k)) for k, d in veri["dersler"].items()]
    secili = {k for k, d in veri["dersler"].items() if d.get("secili", True)}
    sonuc = _coklu_secim("Cekilecek dersleri isaretle", ogeler, secili)
    if sonuc is None:
        return
    for kimlik in veri["dersler"]:
        ayarlar.isaretle(kimlik, kimlik in sonuc)
    KONSOL.print("[green]Kaydedildi.[/green]")
    _bekle_enter()


def _otomasyon_detay(kimlik):
    while True:
        veri = ayarlar.yukle()
        ders = veri["dersler"].get(kimlik, {})
        oto = ders.get("otomasyon", {}) or {}
        durum = "kapali"
        try:
            sorgu = zamanlayici.gorev_sorgu(kimlik)
            if sorgu.get("var"):
                durum = "kayitli ({})".format(sorgu.get("durum", ""))
        except RuntimeError:
            durum = "sorgulanamadi"
        KONSOL.clear()
        KONSOL.print("[bold]{}[/bold]".format(escape(str(ders.get("ad", kimlik)))))
        KONSOL.print("Tetik: {} {}".format(",".join(oto.get("gunler", [])) or "-", oto.get("saat", "")))
        KONSOL.print("Gorev durumu: {}".format(durum))
        KONSOL.print()
        secim = _secim("Otomasyon", ["Kur / guncelle", "Kaldir", "Geri"])
        if secim is None or secim == 2:
            return
        if secim == 0:
            ogeler = GUN_ETIKET
            mevcut = set(oto.get("gunler", []))
            mevcut_kisa = {k for k, ing in ayarlar.GUNLER.items() if ing in mevcut}
            secili_gunler = _coklu_secim("Haftalik gunleri sec", [(k, tam) for k, tam in ogeler], mevcut_kisa)
            if not secili_gunler:
                continue
            try:
                saat = Prompt.ask("Saat (SS:DD)", default=oto.get("saat", "09:00"))
                ayarlar.gun_listesi_coz(sorted(secili_gunler))
                if not ayarlar.saat_gecerli(saat):
                    raise ValueError("Saat SS:DD biciminde olmali")
                sonuc = zamanlayici.gorev_kur_guvenli(kimlik, sorted(secili_gunler), saat)
                KONSOL.print("[green]Gorev kuruldu: {} {}[/green]".format(",".join(sonuc.get("gunler", [])), escape(str(sonuc.get("saat", "")))))
            except (ValueError, RuntimeError) as hata:
                KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
            _bekle_enter()
        else:
            try:
                sorgu = zamanlayici.gorev_sorgu(kimlik)
                if sorgu.get("var") and not zamanlayici.gorev_bizim(kimlik):
                    raise RuntimeError("Gorev bu kuruluma ait degil; kaldirilmadi")
                zamanlayici.gorev_kaldir(kimlik)
                veri = ayarlar.yukle()
                oto = veri["dersler"].get(kimlik, {}).get("otomasyon", {}) or {}
                ayarlar.otomasyon_ayarla(kimlik, oto.get("gunler") or ["PZT"], oto.get("saat", "09:00"), False)
                KONSOL.print("[green]Gorev kaldirildi.[/green]")
            except (ValueError, RuntimeError) as hata:
                KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
            _bekle_enter()


def otomasyon_ekrani():
    while True:
        veri = ayarlar.yukle()
        if not veri["dersler"]:
            KONSOL.print("[yellow]Once ders ekleyin.[/yellow]")
            _bekle_enter()
            return
        etiketler = ["{} ({})".format(escape(str(d.get("ad", k))), k) for k, d in veri["dersler"].items()] + ["Geri"]
        secim = _secim("Otomasyon Ayarla", etiketler)
        if secim is None or secim == len(etiketler) - 1:
            return
        kimlik = list(veri["dersler"])[secim]
        _otomasyon_detay(kimlik)


def ana_menu():
    while True:
        KONSOL.clear()
        KONSOL.print(Panel.fit("[bold cyan]DersMerkezi[/bold cyan]\nCok dersli icerik cekme araci", border_style="cyan"))
        KONSOL.print()
        secim = _secim("Ana menu", ["Dersleri Cek", "Dersler", "Ayarlar", "Otomasyon Ayarla", "Cikis"],
                       "Yon tuslari + Enter")
        if secim is None or secim == 4:
            return 0
        if secim == 0:
            _cek_menu()
        elif secim == 1:
            dersler_ekrani()
        elif secim == 2:
            ayarlar_ekrani()
        elif secim == 3:
            otomasyon_ekrani()


def baslat():
    try:
        return ana_menu()
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            KONSOL.show_cursor(True)
        except Exception:
            pass
