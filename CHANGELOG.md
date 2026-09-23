# Changelog

## 0.2.0 - 2026-09-23

### Eklendi

* Microsoft Teams/SharePoint kanal dosyaları için Graph client-credentials istemcisi; `TEAMS_TENANT_ID`, `TEAMS_CLIENT_ID` ve `TEAMS_CLIENT_SECRET` ortam değişkenleriyle kimlik doğrulama.
* Teams klasör listeleme/sayfalama, çocuk öğe kimliğiyle indirme, QuickXorHash ve SHA-1 sağlayıcı doğrulaması; yalnız açık ders ayarıyla eTag ve yerel SHA-256 tabanlı zayıf doğrulama.
* CLI/TUI kaynak seçimi, Teams sağlık yoklaması, redakte kaynak görünümleri ve `--cek --json` zayıf doğrulama sayacı.

### Güvenlik

* Graph sayfalama bağlantıları HTTPS/köken/yol sınırlarında doğrulanır. Ön kimlikli indirme yönlendirmeleri yalnız izinli Microsoft depolama alan adlarına gider ve Authorization başlığı taşımaz; bu URL'ler hata, günlük, durum kaydı ve Markdown'a yazılmaz.
* Teams kimlikleri yalnız `ayarlar.json` içinde saklanır; görünümlerde ve `teams://` kaynak gösteriminde kısaltılır. `ayarlar.json` sürümü 1 ve indirme durumu sürüm 2 olarak kaldı.

### Doğrulama

* Geçici kopya regresyon paketi 422/422 (206 birim/akış + 155 kapsam + 47 uçtan uca + 14 tetikleme/sahiplik); T0 şema/CLI/görünüm/sağlık paketi 199 kontrol; T1 Graph güvenlik ve QuickXor karşılaştırma paketi 218 kontrol; T2 Graph sahte yanıt/idempotans paketi 39 kontrol.
* Gerçek proje kapısı: `compileall` exit 0; `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`); `--durum` (`Ready`); `--surum` `DersMerkezi 0.2.0`; `--ayarlar --json` başarılı. GitHub anonim API kotası yenilendikten sonra çekme/E2E kapısı tekrarlandı ve geçti.
* Yerel T1-T3 testleri sahte Graph yanıtları ve bağımsız QuickXor referansıyla geçti. Bu ortamda Teams Entra kimlik bilgileri bulunmadığından gerçek tenant tokenı/Teams test göreviyle kimlik doğrulama yapılmadı; işletimsel canlı kabul için kullanıcı ortam değişkenleriyle doğrulama gerekir.

## 0.1.5 - 2026-09-22

### Eklendi

* Apache-2.0 lisansı (`LICENSE`) ve `NOTICE` dosyası; README ve kurulum rehberine lisans bölümü.

### Değişti

* Public hazırlığı: "private depo" ifadeleri kaldırıldı; kullanıcıya dönük belgelerde (README, `belgeler/kurulum.md`, `AGENTS.md`, `CHANGELOG.md`) kişisel mutlak yollar genelleştirildi; tarihsel kanıt dosyaları (belgeler/gecmis) değiştirilmedi.
* Depo 2026-09-22'de public yapıldı; secret scanning, push protection, Dependabot güvenlik güncellemeleri ve özel güvenlik bildirimi etkinleştirildi.

### Doğrulama

* Son kod haliyle 418/418 kontrol (204 birim/akış + 153 fonksiyon kapsamı + 47 uçtan uca + 14 tetikleme/sahiplik) geçti. Gerçek proje kapısı: `compileall` exit 0; `--surum` → `DersMerkezi 0.1.5`; `--cek --ders dosya-organizasyonu --sessiz` exit 0; `--durum` (Ready); `--ayarlar --json` ve `--saglik --ders dosya-organizasyonu --json` exit 0. Secret taraması (içerik + geçmiş) temiz; izlenen dosyalarda hassas dosya yok.

## 0.1.4 - 2026-09-22

### Düzeltildi

* TUI ana menüsünde sürüm satırı kalıcı hale getirildi: menü ekranı kendini temizlediği için önceki sürüm paneli görünmüyordu; sürüm bilgisi menü açıklama satırına taşındı (gerçek konsol doğrulamasında saptandı).

### Doğrulama

* Gerçek konsolda (yeni pencere, `chcp 65001`) TUI ana menü, Durum listesi, Sağlık akışı ve çıkış doğrulandı; konsol tamponundaki karakter kod noktaları birebir denetlendi (ü=U+00FC, ş=U+015F, ─=U+2500); bozuk karakter yok. Tampon okuma bu ortamda yalnız ekranın bir bölümünü yakalayabildiği için satır satır görsel inceleme yerine kod noktası + akış kanıtı kullanıldı.
* Doğrulama kapısı (0.1.4 son kod): `compileall` exit 0; geçici kopyada son kod haliyle 418/418 kontrol (204 birim/akış + 153 fonksiyon kapsamı + 47 uçtan uca + 14 tetikleme/sahiplik) geçti; gerçek proje kapısı: `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`), `--surum` 0.1.4, `--ayarlar --json`, `--durum` (Ready) ve `--saglik --ders dosya-organizasyonu --json` exit 0; üretim görevi değişmedi.
* Üretim görevi takvimi teyit edildi: XML tetikleyicisi (haftalık Pazartesi 09:00, seri başlangıcı 21.09.2026), `MultipleInstances=IgnoreNew`, `StartWhenAvailable=true`, pilde çalışma, 30 dk zaman aşımı, `pythonw.exe` ve dondurulmuş argümanlar; `NextRunTime=28.09.2026 09:00`, `LastTaskResult=0`. Ayrıca test göreviyle gerçek takvim tetiklemesi ateşlendi (20:35:00, `LastTaskResult=0`, `gunluk.log` satırı) ve test görevi/kaydı temizlendi.

## 0.1.3 - 2026-09-22

### Eklendi

* `--ayarlar` bağımsız modu: ders ayarlarını (ad, depo, dal, desen, seçili durumu, otomasyon özeti) salt-okunur gösterir; `--ders` ile tek ders, `--json` ile kanonik JSON çıktısı.
* `--ayarlar --ders <kimlik> --secili evet|hayir`: çekilme işaretini CLI'dan değiştirir; `ayarlar.secili_ayarla` fail-closed ortak işlevi (mutex, atomik yazım, yedek) kullanılır; `ayarlar.isaretle` ve TUI aynı yolu çağırır.
* Görünüm ve mutasyon bozuk `ayarlar.json` dosyasını karantinaya almaz; görünüm sırasında ağ/görev/indirme izi oluşmaz.

### Doğrulama

* Sol bağımsız denetimi 3 turda tamamlandı (3 orta + 2 düşük bulgu kapatıldı; rapor `belgeler/gecmis/sol-denetim-2026-09-22-0.1.3.md`, son tur `SONUC: ONAY`).
* Geçici kopyada 418/418 kontrol (204 birim/akış + 153 fonksiyon kapsamı + 47 uçtan uca + 14 tetikleme/sahiplik) geçti; `trace` ile 133/133 fonksiyon çağrıldı (ifade satırı %81). Gerçek projede `--ayarlar` görünümü ve `--cek --sessiz` (atlanan=1) doğrulandı; üretim görevi Ready kaldı. Ayrıntılar `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md` "Öncelik 4" ve kanıt bölümünde.

## 0.1.2 - 2026-09-22

### Eklendi

* `--json`: `--durum`, `--listele`, `--cek`, `--saglik`, `--surum` ve `--oto-tamamlama` için tek JSON nesnesi çıktısı (`json_surum`, `komut`, `uygulama_surum`; hata durumunda stderr'de `{json_surum, komut, hata:{sinif, mesaj}}`).
* `--cek --kuru`: indirme yapmadan planlanan işi gösterir (yeni/güncellenecek/atlanan, planlanan bayt); hiçbir dosya, `.part` veya durum dosyası yazılmaz; bozuk durum karantinaya alınmaz.
* `--surum`: sürüm tek kaynaktan (`merkez.__version__`) yazılır; `indirici.UA` bu değerden türetilir.
* `--sil --onayla`: geri dönüşsüz ders silme CLI'da açık onaya bağlandı; onaysız çağrı exit 2 (TUI `Confirm` akışı korunur).
* Kombinasyon doğrulaması: mod dışlaması ve bayrak-mod matrisi `merkez/komut.py` içindeki `dogrula` ile uygulanır; moda özgü seçenekler `None` varsayılanla ayrıştırılıp gerçek varsayılanlar doğrulama sonrası uygulanır; ayrıştırma hataları Türkçe şablonlara çevrilir.
* `--zorla` (indirme + bağlam) ve `--zorla-md` (yalnız bağlam) seçenekleri; doğrulama zinciri (blob SHA, `md_sha`/`md_boyut`) korunur.
* `--saglik`: ağsız varsayılan ortam ön kontrolü (Python/paket sürümleri, ayar şeması, ders kayıtları, kilit, günlük/durum erişimi); `--ders` tek depo çağrısı, `--ag` ilk 10 ders; sorun varsa exit 1. Sağlık hiçbir dosya/dizin/yedek/günlük oluşturmaz.
* `--durum --ayrintili`: `sonCalisma`, `sonSonuc`, `eylem` ve durum dosyası özeti (dosya, bayt, güncelleme).
* `--kilit-bekle <sn>` (0-3600): kilit doluyken sınırlı bekleme; süre aşımında mevcut "atlandı" davranışı ve ek bloklama yapmayan fail-closed günlük.
* `--sinir <MB>` (1-200): indirme boyut üst sınırı yalnız düşürülebilir; 200 MB değişmezi korunur.
* `--otomasyon-kur --tetikle`: kurulum sonrası görev bir kez çalıştırılır; `LastTaskResult` yalnız kanıtlanan değerlerle yorumlanır (0 başarılı, 267011 hiç çalışmadı; diğerleri ham/hex), zaman aşımında koşul teşhisi ve exit 1.
* `--her-gun` / `--hafta-ici`: otomasyon gün kısayolları; `--gunler` ile birlikte kullanılamaz.
* `--log <yol>`: proje kökü içinde alternatif günlük yolu; `realpath` + reparse denetimi, yazım anında yeniden doğrulama, aynı 1 MB `.old` rotasyonu.
* `--oto-tamamlama`: parser'dan türetilen bayrak listesiyle `tamamlama/dersmerkezi-tamamlama.ps1` (PowerShell 5.1 `Register-ArgumentCompleter`) üretir; klasör `.gitignore` dışındadır.
* TUI eşliği: Dersleri Çek menüsünde "Önizleme (kuru çalışma)" ve zorlama onayı, kilit doluyken "Bekle/Atla" sorusu, "Durum / Sağlık" ekranı (ayrıntılı durum + sağlık kontrolü), Otomasyon detayında "Kur ve hemen dene" ve gün kısayolları, ana menü başlığında sürüm.

### Düzeltildi

* Çıktı kanalı politikası çağrı kapsamlı: `--json` modunda insan-okur metinler stderr'e gider, JSON stdout'ta tek nesne kalır; global durum `try/finally` ile geri yüklenir.
* `--sil` zinciri `zamanlayici.ders_sil_guvenli` ortak işlevine alındı; CLI ve TUI aynı sahiplik denetimli silme akışını kullanır.
* Görev tetikleme öncesi tek-eylem sahipliği yeniden doğrulanır; sorgu hatası fail-closed, yabancı görev tetiklenmez; kurulum kesinleşme noktası ayar yazımının başarısıdır ve tetikleme hatası kurulumu geri almaz.

### Doğrulama

* Geçici klasördeki proje kopyasında 164 birim/akış + 14 tetikleme/sahiplik kontrolü geçti; sonuçlar `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md` "Uygulama ve Doğrulama Kanıtları (0.1.2)" bölümüne işlendi.
* Uçtan uca ve kapsam testi (2026-09-22): geçici kopyada 374/374 kontrol (164 birim/akış + 150 fonksiyon kapsamı + 46 uçtan uca + 14 tetikleme/sahiplik) geçti; `trace` ile 131/131 fonksiyon ve ifade satırlarının %81'i çağrıldı; gerçek ağ ve Görev Zamanlayıcı üzerinden tam görev yaşam döngüsü (`--her-gun`/`--hafta-ici` maskeleri, `--tetikle`, kaldırma, silme) doğrulandı; üretim görevi değişmedi.
* Sol bağımsız kod denetimi 3 turda tamamlandı (8 orta + 2 düşük bulgu açıldı; kanal istisnası, kuru karantina, 200 MB guard, `--log` yazılabilirlik/rotasyon, TUI salt-okunurluk ve eşlik, Rich kaçışları ve üretilen betik yorumsuzluğu düzeltildi); son turda `SONUC: ONAY` alındı; rapor `belgeler/gecmis/sol-denetim-2026-09-22-0.1.2.md`.
* Doğrulama kapısı: `compileall`, gerçek projede `--cek --sessiz` (`atlanan=1`), `--durum`, `--durum --ayrintili`, `--saglik`, test dersiyle `--otomasyon-kur --tetikle` / `--otomasyon-kaldir`.

## 0.1.1 - 2026-09-21

### Eklendi

* Türkçe dökümantasyon: `belgeler/kurulum.md` (kurulum, kullanım, sorun giderme) ve `belgeler/mimari.md` (modül haritası, veri akışı, şemalar, değişmezler); README döküman bağlantıları ve depo bilgisiyle güncellendi.
* Sürüm kontrolü dosyaları: `.gitignore` (dersler/, günlük, ayarlar ve geçici dosyalar hariç) ve `.gitattributes` (UTF-8/LF normalizasyonu, ikili dosyalar).
* GitHub deposu oluşturuldu: <https://github.com/mecik-arda/DersMerkezi>

### Düzeltildi

* Markdown bütünlüğü: durum dosyasına `md_sha` ve `md_boyut` alanları eklendi; ikinci koşuda md dosyası boyut ve SHA-256 ile doğrulanır, bozuk veya eksikse yeniden üretilir.
* Mutex kapsamı genişletildi: `ayarlar.json`/durum yazımları, oku-değiştir-yaz işlemleri ve günlük rotasyonu `Local\DersMerkezi` altında; TUI çekme ekranı kilidi alır; kilit sızıntısına yol açan çift alma düzeltildi.
* Atomik yazım: başarısız yazımda `.tmp` ve geçici md dosyaları temizlenir.
* Contents API listeleme: 429 ve 5xx yanıtlarında `Retry-After` destekli sınırlı tekrar (en fazla 3 deneme).
* `--otomasyon-kur`: önce görev kurulur, başarılıysa ayar güncellenir; görev kurulamazsa ayar `aktif` kalmaz.
* `--sil` ve TUI ders çıkarma: varsa zamanlanmış görev önce kaldırılır; görev kaldırılamazsa ders kaydı silinmez.
* `--tasima --kuru` artık gerçek taşıma kanıtını ezmez; ayrı `tasima-dogrulama-kuru.txt` yazar.
* Girdi doğrulama: ders adı 2-120 karakter ve güvenli karakter kümesiyle sınırlandı; slug alt sınırı 2 karaktere çekildi; dal adında boşluk yasaklandı; `https://github.com/owner/repo[.git]` biçimli depo adresleri ayrıştırılır.
* TUI: kullanıcı ve depo kaynaklı metinler Rich markup olarak yorumlanmaz (`rich.markup.escape`).
* Taşıma hatasında geri alma: yeni kurulan görev (yalnızca bu kuruluma aitse) ve yeni ders kaydı geri alınır, mevcut kaydın otomasyon ayarı eski değerine döner; eski görev çalışır kalır.
* Sol bağımsız denetimi bulguları kapatıldı: görev sahipliği execute + tam argüman birebir eşleşme (taklit görev reddi), güncelleme öncesi `gorev_<slug>_onceki.xml` yedeği, `.part` indirmesinde fsync, günlük yazımı fail-closed, bozuk dosya karantinası mutex altında, URL depo girdisinde yalnızca `https://github.com/owner/repo[.git]`, ders adında tırnak reddi, 200 MB üstü dosyanın liste aşamasında reddi, `--sil` için görev sahipliği kontrolü, `Kilit.__enter__` fail-closed, plandaki çelişen tetikleme ifadelerinin düzeltilmesi.
* Sol denetimi ikinci tur bulguları kapatıldı: otomasyon güncellemesinde ayar yazımı başarısızsa yeni görev kaldırılır, mevcut görev XML yedeğinden `gorev_yukle.ps1` ile geri yüklenir ve geri alma hatası gizlenmez; sahiplik denetimi `--otomasyon-kaldir`, TUI kaldırma ve `gorev_kaldir.ps1` katmanında da `Execute` + tam `Arguments` birebir karşılaştırmayla uygulanır.
* Sol denetimi üçüncü tur bulguları kapatıldı: mutasyon öncesi görev durumu yok/bizim/yabancı olarak sorgulanır ve sorgu hatası fail-closed yükseltilir; `gorev_kaldir.ps1` sahiplik parametrelerini zorunlu tutar; `gorev_yukle.ps1` kayıt sonrası eylemi beklenen execute + tam argümanla doğrular, uyuşmazsa geri yüklemeyi iptal edip görevi kaldırır.
* Sol denetimi dördüncü tur bulguları kapatıldı: görev sorgusu CIM üzerinden yapılır ve yalnızca gerçek bulunamama `yok` sayılır (sorgu hatası yükseltilir); görevler tek eylem şartına bağlanır (çok eylemli taklit görev reddedilir); XML geri yükleme kayıt öncesinde ayrıştırılıp tek eylem + beklenen execute/tam argüman doğrulanır, kayıt sonrasında eylem sayısı ve içeriği yeniden denetlenir.
* Sol denetimi beşinci tur bulguları kapatıldı: `gorev_kur.ps1` ve `gorev_kaldir.ps1` de varlık sorgusunu CIM ile yapar (yalnız gerçek bulunamama yok sayılır, sorgu hatası fail-closed); XML geri yükleme ön denetimi `Actions` altındaki tüm eylem düğümlerini sayar ve yalnızca tek `Exec` düğümünü kabul eder.
* Görev ayarları pilde çalışacak şekilde güncellendi (`-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries`); pildeyken görevin "Queued" kalıp hiç koşmamasına yol açan varsayılan politika giderildi ve üretim görevi elle tetiklemeyle fiilen doğrulandı.

### Doğrulama

* Sol bağımsız denetimi (kanonik codex köprüsü, GPT-5.6 Sol) 6 turda tamamlandı: toplam 9 + 3 + 3 + 2 + 2 bulgu kapatıldı, son turda `SONUC: ONAY` alındı; rapor `belgeler/gecmis/sol-denetim-2026-09-21.md`.
* Geçici klasörde çalıştırılan test paketleri: 106 birim + 51 akış + 11 taşıma hata senaryosu + 4 HTTP hata matrisi + 3 kapsam + 7 TUI iş mantığı kontrolü geçti; ardından gerçek projede doğrulama kapısı koşuldu.
* Görev Zamanlayıcı fiili yürütme doğrulandı: elle koşu, tek seferlik ve haftalık tetikleyici ateşlendi (`LastTaskResult=0`); test görevleri kaldırıldı.
* Ayrıntılar: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` içindeki "Uygulama ve Doğrulama Kanıtları" bölümü.

## 0.1.0 - 2026-09-21

### Eklendi

* Python + Rich tabanlı DersMerkezi CLI/TUI: ders ekleme/çıkarma/listeleme, çekilecek ders işaretleme, canlı animasyonlu çekme ekranı, otomasyon ekranı.
* `merkez/` çekirdek modülleri: `ayarlar`, `indirici`, `zamanlayici`, `arayuz`, `gunluk`, `tasima` ve sabit PowerShell betikleri (`merkez/ps/`).
* Headless komutlar: `--ekle`, `--sil`, `--listele`, `--cek`, `--durum`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--tasima [--kuru] [--onayla]`, `--otomatik`, `--sessiz`.
* Masaüstü başlatıcı `%USERPROFILE%\Desktop\DersMerkezi.bat` ve proje içi `baslat.cmd`.
* Güvenlik ve dayanıklılık: girdi doğrulama, atomik yazım (fsync + os.replace), `Local\DersMerkezi` mutex, Git blob SHA-1 doğrulaması, enjeksiyon sertleştirmesi, hata kategorileri.
* `AGENTS.md`, `CLAUDE.md`, `README.md` ve plan belgesi.

### Değişti

* Eski PowerShell otomasyonu (`otomasyon/` klasörü ve `DosyaOrganizasyonu_HaftalikCek` görevi) DersMerkezi kapsamına taşındı; eski görev kaldırıldı, içerik `dersler/dosya-organizasyonu/` altına alındı, kanıtlar `belgeler/gecmis/` altında.

### Doğrulama

* Ayrıntılar: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` içindeki "Uygulama ve Doğrulama Kanıtları" bölümü.
