# Changelog

## 0.1.1 - 2026-09-21

### Eklendi

* Türkçe dökümantasyon: `belgeler/kurulum.md` (kurulum, kullanım, sorun giderme) ve `belgeler/mimari.md` (modül haritası, veri akışı, şemalar, değişmezler); README döküman bağlantıları ve depo bilgisiyle güncellendi.
* Sürüm kontrolü dosyaları: `.gitignore` (dersler/, günlük, ayarlar ve geçici dosyalar hariç) ve `.gitattributes` (UTF-8/LF normalizasyonu, ikili dosyalar).
* Private GitHub deposu oluşturuldu: <https://github.com/mecik-arda/DersMerkezi>

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
* Masaüstü başlatıcı `C:\Users\ardam\Desktop\DersMerkezi.bat` ve proje içi `baslat.cmd`.
* Güvenlik ve dayanıklılık: girdi doğrulama, atomik yazım (fsync + os.replace), `Local\DersMerkezi` mutex, Git blob SHA-1 doğrulaması, enjeksiyon sertleştirmesi, hata kategorileri.
* `AGENTS.md`, `CLAUDE.md`, `README.md` ve plan belgesi.

### Değişti

* Eski PowerShell otomasyonu (`otomasyon/` klasörü ve `DosyaOrganizasyonu_HaftalikCek` görevi) DersMerkezi kapsamına taşındı; eski görev kaldırıldı, içerik `dersler/dosya-organizasyonu/` altına alındı, kanıtlar `belgeler/gecmis/` altında.

### Doğrulama

* Ayrıntılar: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` içindeki "Uygulama ve Doğrulama Kanıtları" bölümü.
