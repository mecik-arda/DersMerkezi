# DersMerkezi - Ajan Kuralları ve Proje Bağlamı

Bu dosya, bu projede çalışan tüm kod ajanları için bağlayıcı bağlam ve kuralları içerir. Değişiklik yapmadan önce okuyun.

## Proje Özeti

DersMerkezi, Windows masaüstünde çalışan Python + Rich tabanlı çok dersli içerik çekme aracıdır. GitHub depolarındaki haftalık ders içeriklerini (ör. `Hafta 1.pdf`) Git blob SHA-1 ile, Microsoft Teams/SharePoint kanal dosyalarını Microsoft Graph sağlayıcı hash'leriyle doğrular; pypdf ile Markdown bağlamı üretir ve ders bazında haftalık Windows Görev Zamanlayıcı görevleri kurar.

* Proje kökü: yerel çalışma kopyası (bu depo).
* Depo: `https://github.com/mecik-arda/DersMerkezi` (lisans: Apache-2.0) (tüm içerik Türkçe; sürüm kontrolü dışı: `dersler/`, `gunluk.log`, `ayarlar.json`, geçici/yedek dosyalar).
* Plan belgesi: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` (sonunda uygulama ve doğrulama kanıtları)
* CLI geliştirme önerileri: `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md` (öncelikli maddeler, mimari kararlar ve kaynaklar; Sol denetimlerinden ONAY aldı; 0.1.2 ve 0.1.3 dilimleri uygulandı)
* Teams kaynağı planı: `belgeler/plan/2026-09-23-teams-kaynagi-destegi.md` (T0-T4 kodu ve sahte Graph testleri tamamlandı; son T4 Sol denetimi ONAY aldı; canlı Graph kabulü ortam kimlik bilgilerine bağlı)
* Durum: M1-M5 uygulandı ve doğrulandı; bağımsız doğrulama turu ve 6 turluk Sol denetimi (toplam 19 bulgu kapatıldı, son turda ONAY) tamamlandı (sürüm 0.1.1). Görev tetiklemesi ve TUI iş mantığı test kapsamında doğrulandı; gerçek konsol/TUI ve takvim teyitleri 0.1.4'te tamamlandı; yalnızca üretim görevinin 28.09.2026 tarihli takvimli koşusu gunluk.log ile teyit edilecek.
* CLI genişletmesi (sürüm 0.1.2) uygulandı: mod/bayrak matrisi ve Türkçe doğrulama, `--json` kanal sözleşmesi, `--surum`, `--cek --kuru`, `--sil --onayla`, `--zorla/--zorla-md`, `--saglik/--ag/--ayrintili`, `--kilit-bekle`, `--sinir`, `--tetikle`, `--her-gun/--hafta-ici`, `--log`, `--oto-tamamlama` ve TUI eşliği; öneri planı Sol denetiminden ONAY aldı (tur 6). Uygulama sonrası Sol kod denetimi 3 turda tamamlandı (9 bulgu kapatıldı: kanal istisnası, kuru karantina, 200 MB guard, log yazılabilirlik/rotasyon, TUI salt-okunurluk ve eşlik, Rich kaçışları, üretilen betik); son turda ONAY alındı. Ayar dilimi (0.1.3) eklendi: `--ayarlar` salt-okunur görünüm ve `--ayarlar --ders X --secili evet|hayir` ile güvenli seçim değişikliği; TUI aynı ortak işlevi kullanır. Sol denetimi 3 turda ONAY aldı (5 bulgu kapatıldı). Gerçek konsol/TUI ve takvim teyitleri 0.1.4'te tamamlandı. Public hazırlığı (0.1.5): Apache-2.0 lisansı (`LICENSE`, `NOTICE`), "private" ifadelerinin kaldırılması ve kullanıcıya dönük belgelerde kişisel yolların genelleştirilmesi. Uçtan uca ve kapsam testi (2026-09-22): 374/374 kontrol (birim 164, fonksiyon kapsamı 150, uçtan uca 46, tetikleme 14), `trace` ile 131/131 fonksiyon kapsamı; gerçek görev yaşam döngüsü ve üretim görevi değişmezliği doğrulandı.
* Kayıtlı ders: `dosya-organizasyonu` (`emirozturk/Dosya-Organizasyonu-2026`, desen `Hafta*.pdf`); görev `DersMerkezi_dosya-organizasyonu` haftalık PZT 09:00.
* Teams sözleşmesi: `ayarlar.json` `SURUM=1` ve indirme durumu sürüm 2 kalır; `kaynak` yoksa `github` kabul edilir. `--ekle --kaynak teams` ile Teams/SharePoint kaydı açılır; Graph indirme ve sağlık kontrolü kaynak adaptöründen geçer. Tam `tenantId`/`driveId`/`itemId` yalnız `ayarlar.json`'da; görünüm, durum, Markdown kaynak URI'si ve günlüklerde kısaltılmış özet kullanılır. `TEAMS_CLIENT_SECRET` yalnız ortam değişkenindedir.
* T4 sürüm/test durumu: uygulama sürümü `0.2.0`; geçici kopyada regresyon 423/423 (206 birim/akış, 156 kapsam, 47 uçtan uca, 14 tetikleme), T0 199, T1 220, T2 57 kontrol. Sol T4 kod denetimi ONAY verdi ve `v0.2.0` etiketi bu onaya dayanarak yayımlandı. Gerçek Teams tenant uygulama kimlik bilgileri bu geliştirme ortamında tanımlı değil; canlı Graph tokenı ve test görevi kabulü kullanıcı ortam değişkenleriyle ayrıca yapılmalıdır.
* Eski PowerShell otomasyonu taşındı; eski `DosyaOrganizasyonu_HaftalikCek` görevi kaldırıldı.

## Ortam Gerçekleri

* Windows 11, PowerShell 5.1, Python 3.13.9 (Anaconda; `pythonw.exe` mevcut).
* Kurulu paketler: rich 14.2.0, requests 2.32.5, pypdf 6.12.2.
* Konsol kod sayfası gözlemi 857; başlatıcılar `chcp 65001` kullanır.
* Uzun yol desteği açık (LongPathsEnabled=1).
* Subagent köprüsü izinli kökü: projenin üst klasörü (bu proje izinlidir; eski proje klasörü değildir).

## Dosya Haritası

* `dersmerkezi.py`: Giriş noktası; mod işleyicileri, CLI argümanları ve TUI başlatma.
* `merkez/komut.py`: Argüman ayrıştırıcı, mod/bayrak matrisi doğrulaması, JSON çıktı sözleşmesi, Türkçe ayrıştırma hata eşlemesi.
* `merkez/ayarlar.py`: `ayarlar.json` şeması (sürüm=1), GitHub/Teams kaynak ve kimlik doğrulaması, `veri_dogrula`/`ders_dogrula`, `yukle_salt`/`gorunum` salt-okunur görünüm ve redaksiyon, `secili_ayarla` fail-closed seçim mutasyonu, atomik yazım ve tek nesil yedek.
* `merkez/teams.py`: Graph app-only tokenı, çocuk listeleme/sayfalama, Graph ve ön kimlikli indirme yönlendirme denetimleri, QuickXorHash ve akışlı dosya aktarımı.
* `merkez/indirici.py`: GitHub Contents/Teams Graph kaynak adaptörleri, akışlı indirme (`.part`), Git blob veya sağlayıcı hash doğrulama, Markdown üretimi, kuru/zorlama modları ve durum şeması v2.
* `merkez/durum.py`: Ders/görev durum kayıtları ve ayrıntılı durum (CLI + TUI ortak).
* `merkez/saglik.py`: Salt-okunur sağlık denetimi; `--ders`/`--ag` kaynak türüne göre sınırlı GitHub/Graph ağ çağrısı, `--ayrintili` sınırlı görev sorgusu.
* `merkez/tamamlama.py`: PowerShell tamamlama betiği üretimi (`tamamlama/`, gitignore).
* `merkez/zamanlayici.py`: PowerShell köprüsü (`gorev_kur`, `gorev_kaldir`, `gorev_sorgu`, `gorev_tetikle`, `gorev_yukle`, `gorev_sil`); sahiplik denetimi ve `ders_sil_guvenli`.
* `merkez/tasima.py`: Eski otomasyonun güvenli taşınması (kanıt, manifest, doğrulama).
* `merkez/arayuz.py`: Rich + msvcrt TUI (menü, çoklu seçim, canlı ilerleme, kuru önizleme, Durum/Sağlık, tetikleme).
* `merkez/gunluk.py`: `gunluk.log` (UTF-8, 1 MB rotasyon), doğrulanmış alternatif `--log` yolu ve `Local\DersMerkezi` mutex'i.
* `merkez/ps/*.ps1`: Sabit PowerShell betikleri; Python bunları `-File` ve bağlanan parametrelerle çağırır.
* `dersler/<slug>/`: İndirilen içerik ve `indirilenler.json`.
* `belgeler/`: plan, referans (eski otomasyon kopyaları), gecmis (taşıma ve denetim kanıtları), kurulum.md, mimari.md.

## Kod Kuralları

* Yorum satırı yazma; mevcut kod kendini açıklayıcı stilde kalır.
* Python ve Markdown dosyaları UTF-8 (BOM'suz); Türkçe karakterler doğru kullanılır.
* PowerShell betiklerinde kullanıcı metinleri ASCII'ye indirgenir (kod sayfası uyumsuzluğu).
* Kullanıcıya dönük tüm metinler Türkçe.
* Girdi doğrulaması zorunlu: slug `^[a-z0-9]+(?:-[a-z0-9]+)*$` (2-40); depo `owner/repo` deseni (URL biçimli girdiler yalnızca `https://github.com/owner/repo[.git]` olarak ayrıştırılır); dal `..` ve boşluk yasak; desen 64 karakter, yol ayracı yasak; ders adı 2-120 karakter ve güvenli karakter kümesi (tırnak ve enjeksiyon karakterleri reddedilir); saat `SS:DD` (00:00-23:59); gün kapalı küme; dosya adlarında yol kaçışı, ayrılmış aygıt adı ve 180+ karakter reddi; liste meta verisinde 200 MB üstü dosyalar indirilmeden reddedilir.
* Teams kimlikleri güvenli karakter kümesi/uzunlukla doğrulanır (`driveId`/`itemId` 8-200, `tenantId` 2-128); tam kimlikler hata mesajına/günlüğe yazılmaz. `zayif_dogrulama` yalnız Teams kaydında bool olarak kabul edilir.
* Görev ayarları: `StartWhenAvailable`, `MultipleInstances IgnoreNew`, 30 dakika zaman aşımı, pilde çalışma (`AllowStartIfOnBatteries`, `DontStopIfGoingOnBatteries`) ve zamanlanmış koşularda `pythonw.exe`.
* Zamanlanmış görev eylemlerine kullanıcı metni gömülmez; yalnızca doğrulanmış slug ve sistem yolları bulunur; PowerShell çağrıları `-File` ve adlandırılmış parametrelerledir.
* Görev güncellemesi, kaldırma ve geri alma yalnızca eylem (execute + tam argüman) birebir eşleşiyorsa ve görev tam olarak tek eylem içeriyorsa yapılır; bu denetim Python ve PowerShell katmanında uygulanır; mutasyondan önce görev durumu (yok/bizim/yabancı) sorgulanır, yalnızca gerçek bulunamama "yok" sayılır ve sorgu hatası fail-closed yükseltilir; güncelleme öncesi mevcut görev XML'i `belgeler/gecmis/gorev_<slug>_onceki.xml` olarak saklanır, geri alma gerekirse görev bu XML'den yüklenir ve yüklenen görevin eylemi birebir doğrulanır (uyuşmazsa geri yükleme iptal edilip görev kaldırılır); ders silme yalnızca bu kuruluma ait görevi kaldırır.
* Ağ çağrıları yalnızca HTTPS; token loglanmaz, hata mesajlarında redakte edilir; 429/5xx için sınırlı tekrar uygulanır. Graph sayfalama en fazla 50 sayfa/10.000 öğe; Graph nextLink/meta yönlendirmesi köken/yol denetimli. Ön kimlikli `/content` yönlendirmesi yalnız izinli Microsoft alan adlarına HTTPS ile gider, Authorization taşımaz ve URL hiçbir kalıcı alana yazılmaz.
* Dosya yazımları atomik: aynı dizinde `.tmp`/`.part`, flush, `os.fsync`, `os.replace` (kilitli hedefte 3 deneme, artan bekleme); başarısızlıkta geçici dosya temizlenir.
* `ayarlar.json` ve durum dosyası yazımları, oku-değiştir-yaz işlemleri ve günlük rotasyonu `Local\DersMerkezi` mutex'i altında yapılır; TUI çekme akışı da kilidi alır; kilit alınamazsa günlük yazımı atlanır (fail-closed).

## Değişmezler

* İkinci koşuda durum dosyasına güvenilmez: yerel varlık, boyut ve Git blob SHA yeniden doğrulanır.
* Markdown bağlamı durum kaydındaki `md_sha`/`md_boyut` ile doğrulanır; md eksik veya bozuksa yeniden üretilir.
* Git blob SHA'sı `blob <boyut>\0<veri>` biçiminde streaming hesaplanır; SHA doğrulanmadan dosya nihai adına taşınmaz.
* Markdown şablonu korunur: başlık, kaynak/SHA/tarih/sayfa satırları, `---`, `## Sayfa N`, OCR uyarısı.
* Eski proje klasörü (yerel referans; kodda `tasima.ESKI_KOK`) yalnızca referanstır; üzerinde değişiklik yapılmaz.
* `--tasima --onayla` bir kez çalıştırıldı (eski görev kaldırıldı); normal koşullarda yeniden çalıştırılmaz; `--tasima --kuru` çıktısı `tasima-dogrulama-kuru.txt` dosyasına yazılır ve gerçek kanıtı ezmez.
* Görev adı şeması: `DersMerkezi_<slug>`; zamanlanmış koşular `pythonw.exe` ile ve `--otomatik --ders <slug> --sessiz` argümanlarıyla çalışır.
* Ders kaydı silinirken varsa `DersMerkezi_<slug>` görevi de kaldırılır; görev kaldırılamazsa ders silinmez.
* Taşıma hata halinde geri alınır: yeni kurulan görev (bu kuruluma aitse) ve yeni ders kaydı silinir, mevcut kaydın otomasyon ayarı eski değerine döner; eski görev çalışır kalır.
* Otomasyon güncellemesinde ayar yazımı başarısız olursa yeni görev kaldırılır, güncellenmiş mevcut görev XML yedeğinden geri yüklenir; geri alma hatası gizlenmez (fail-closed).
* Çıkış kodları: 0 başarı, 1 hata, 2 kullanım hatası.

## Doğrulama Kapısı

Her değişiklikten sonra en az:

1. `python -m compileall merkez dersmerkezi.py`
2. `python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz` → logda `atlanan=2`, exit 0 (yeniden indirme olmamalı; üst depodaki eşleşen iki dosya)
3. `python dersmerkezi.py --durum`
4. Zamanlayıcı değiştiyse: test dersiyle `--otomasyon-kur` / `--otomasyon-kaldir` denenir ve `Get-ScheduledTask` / `schtasks /Query` ile doğrulanır.
5. Taşıma değiştiyse: yalnızca `--tasima --kuru` çalıştırılır; onaylı taşıma tekrarlanmaz.
6. Girdi doğrulaması değiştiyse: birim kontroller (slug, ders adı, depo/URL, dosya adı, saat, gün) yeniden çalıştırılır.
7. Markdown/durum şeması değiştiyse: `md_sha`/`md_boyut` alanları ve bozuk md yeniden üretimi doğrulanır.
8. Kilit/yazma davranışı değiştiyse: kilit dolu senaryosu ve özyinelemeli alma (kilit sızıntısı) kontrol edilir. Birim ve akış paketleri geçici klasördeki proje kopyasında koşturulur; repoya test dosyası eklenmez.

Başarısız doğrulama geçmiş sayılmaz; hata sınıfı (izin/şema/ağ/zaman aşımı) ayrıştırılır ve rapor edilir.

## Bilinen Sınırlamalar

* Görev Zamanlayıcı tetiklemesi test kapsamında doğrulandı: elle koşu, tek seferlik tetikleyici ve haftalık tetikleyici fiilen ateşlendi (`LastTaskResult=0`, `gunluk.log` satırı). İlk gözlemde tetiklenmemenin kök nedeni pil politikasıydı (`DisallowStartIfOnBatteries`); `gorev_kur.ps1` artık pilde çalışacak şekilde kayıt yapar ve üretim görevi elle tetiklemeyle fiilen koştu. Üretim görevinin kendi takvimli koşusu `gunluk.log` üzerinden teyit edilir; yapılandırma ve test göreviyle takvim ateşlemesi 2026-09-22'de doğrulandı (sonuç 0).
* TUI iş mantığı scriptli tuş girdisiyle (gezinme, çoklu seçim, çekme ekranı, kuru önizleme, Durum/Sağlık ekranı) doğrulandı; ayrıca gerçek konsolda (yeni pencere, chcp 65001) menü/Durum/Sağlık/çıkış akışı ve karakter kod noktaları doğrulandı (0.1.4).
* `--tetikle` akışı kontrollü test göreviyle doğrulanır: başarı (LastTaskResult=0), hiç çalışmama (267011), kuyrukta kalma, sonlandırılma, hızlı tamamlanma ve sorgu hatası senaryoları; yalnız kanıtlanan sonuç kodları yorumlanır (diğerleri ham/hex). Üretim görevi bu testlerde değiştirilmez.
* Antigravity/Gemini web rotası `web_evidence_invalid` verir; DeepSeek workspace yalnızca bu proje kökünde çalışır.

## Sık Kullanılan Komutlar

* TUI: `baslat.cmd` veya masaüstü `DersMerkezi.bat`
* Yeni ders: `python dersmerkezi.py --ekle --ad "<ad>" --depo <owner/repo> [--desen "<desen>"]`
* Teams kaydı: `python dersmerkezi.py --ekle --ad "<ad>" --kaynak teams --teams-drive <driveId> --teams-item <itemId> [--teams-tenant <tenantId>] [--zayif-dogrulama]`
* Teams çekme/sağlık: `python dersmerkezi.py --cek --ders <teams-slug> --sessiz`; `python dersmerkezi.py --saglik --ders <teams-slug>` (Graph app-only ortam değişkenleri gereklidir).
* Çekme: `python dersmerkezi.py --cek [--ders <slug>] --sessiz` (kuru: `--kuru`, zorla: `--zorla`/`--zorla-md`, sınır: `--sinir <MB>`, bekleme: `--kilit-bekle <sn>`)
* Görev kur: `python dersmerkezi.py --otomasyon-kur --ders <slug> --gunler PZT,CAR --saat 09:00` (kısayol: `--her-gun`/`--hafta-ici`, hemen dene: `--tetikle`)
* Durum: `python dersmerkezi.py --durum [--ayrintili] [--json]`
* Sağlık: `python dersmerkezi.py --saglik [--ders <slug>|--ag|--ayrintili] [--json]`
* Sürüm/JSON: `python dersmerkezi.py --surum`; diğer JSON modları `--durum`, `--listele`, `--cek`, `--saglik`, `--oto-tamamlama`
* Tamamlama: `python dersmerkezi.py --oto-tamamlama` → `tamamlama/dersmerkezi-tamamlama.ps1`
* Ayar görünümü/seçim: `python dersmerkezi.py --ayarlar [--ders <slug>] [--secili evet|hayir] [--json]`
* Silme (onaylı): `python dersmerkezi.py --sil --ders <slug> --onayla`
* Günlükler: `gunluk.log` ve `dersler/<slug>/indirilenler.json`
