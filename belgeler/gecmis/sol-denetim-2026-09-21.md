# Sol Bağımsız Denetimi - 2026-09-21

Rota: kanonik codex köprüsü, model `gpt-5.6-sol`, salt-okunur denetim (denetim sırasında dosya değiştirilmedi).
Kapsam: `dersmerkezi.py`, `merkez/` modülleri, `merkez/ps/` betikleri, `AGENTS.md`, `README.md`, `CHANGELOG.md`, plan belgesi.
Denetim sonucu: 9 bulgu (`SONUC: BULGULAR`).

## Tur 1 Bulguları ve Kapatma Durumu

1. Orta - `--otomasyon-kur` ders varlığını ve slug sınırını görev kurulumundan önce doğrulamıyordu; ayar yazımı başarısız olursa öksüz görev kalabiliyordu.
   Kapatıldı: `ders_getir` + slug 2-40 ön koşulu (Python ve `gorev_kur.ps1`); ayar yazımı başarısızsa sahipliği doğrulanan görev geri alınır.
2. Orta - Görev sahipliği yalnızca betik yolu alt dizesiyle belirleniyordu.
   Kapatıldı: execute + tam argüman birebir karşılaştırma; taklit/yabancı görev reddi test edildi.
3. Orta - `.part` indirmesi fsync olmadan nihai ada taşınıyordu.
   Kapatıldı: akış sonunda `flush` + `os.fsync`.
4. Orta - `gunluk.kayit` kilit alınamazsa yine de yazıyordu.
   Kapatıldı: fail-closed (10 sn bekleme, alınamazsa yazma yok); `RuntimeError` mesajı `--sessiz` dışında stderr'e yazılır.
5. Düşük - `yukle()` bozuk dosyayı kilitsiz karantinaya alıyordu.
   Kapatıldı: `_bozuk_yedekle` mutex altında; kilit alınamazsa karantina yapılmaz.
6. Düşük - URL depo girdisinde şema/ana makine doğrulanmıyordu.
   Kapatıldı: yalnızca `https` + `github.com`; kimlik, port, sorgu, parça ve fazla yol reddedilir.
7. Düşük - Ders adı kümesi tek tırnak kabul ediyordu; kabul kriteri tırnak reddi diyor.
   Kapatıldı: tırnak kümeden çıkarıldı.
8. Düşük - Görev güncellemesi öncesi XML yedeği alınmıyordu.
   Kapatıldı: `belgeler/gecmis/gorev_<slug>_onceki.xml` yazılır.
9. Düşük - Plan belgesindeki eski "tetikleme doğrulanamıyor" ifadeleri güncel sonuçla çelişiyordu.
   Kapatıldı: ilgili maddeler güncellendi.

Risk listesinden kapatılanlar: `Kilit.__enter__` fail-closed; 200 MB üstü dosya liste aşamasında reddedilir; `--sil` yalnızca bu kuruluma ait görevi kaldırır.

## Düzeltme Sonrası Kanıtlar

* Birim 98/98, akış 48/48, taşıma hata 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7 (geçici klasördeki proje kopyasında).
* Taklit görev (yol argümanda, execute farklı) ve yabancı görev reddi; yabancı görev varken `--sil` reddi.
* Üretim görevi yeni sahiplik kontrolüyle güncellendi; `gorev_dosya-organizasyonu_onceki.xml` yazıldı; doğrulama kapısı geçti (`atlanan=1`, `gorev=kayitli (Ready)`).

## Tur 2 Sonucu

1. Eksik — `--otomasyon-kur` için `ders_getir` ve slug 2-40 ön koşulları doğrulandı; ayar yazımı sonrası geri alma mevcut görevi eski XML'den geri yüklemiyor ve kesin sahiplik denetimi kullanmıyor.
2. Doğrulandı — `gorev_kur.ps1` mevcut görevin `Execute` alanını ve tam `Arguments` değerini birebir karşılaştırıyor.
3. Doğrulandı — `.part` akışı nihai ada taşınmadan önce `flush` ve `os.fsync` çağırıyor.
4. Doğrulandı — `gunluk.kayit` kilit alınamazsa dosya ve rotasyon yazımı yapmıyor; yakalanan `RuntimeError` sessiz mod dışında stderr'e yazılıyor.
5. Doğrulandı — `_bozuk_yedekle` mutex alıyor ve kilit alınamazsa karantina yazımı yapmıyor.
6. Doğrulandı — URL biçimli depo girdisi `https` ve `github.com` ile sınırlandırılmış; kimlik, port, sorgu, parça ve ikiden fazla anlamlı yol bileşeni reddediliyor.
7. Doğrulandı — ders adı güvenli karakter kümesi tek ve çift tırnağı reddediyor.
8. Doğrulandı — sahip olunan mevcut görev güncellenmeden önce `gorev_<slug>_onceki.xml` yazılıyor.
9. Eksik — planın güncel sonucu tetiklemenin doğrulandığını söylerken eski doğrulanamaz ifadeleri hâlâ korunuyor.
10. Doğrulandı — `Kilit.__enter__` kilit alınamazsa `RuntimeError` yükseltiyor; edinilmiş kilidi ikinci kez almıyor ve incelenen akışlarda kilit sızıntısı görülmedi.
11. Doğrulandı — 200 MB üstü meta boyutu indirme çağrısından önce reddediliyor; akış sırasında da üst sınır yeniden uygulanıyor.
12. Eksik — `--sil` ve TUI ders silme sahiplik kontrolü çağırıyor ancak ortak denetim tam eylem yerine alt dize eşleşmesi kullanıyor.

Yeni bulgular:

* Orta — `dersmerkezi.py:124-133`, `merkez/arayuz.py:274-283`: ayar yazımı başarısız olduğunda yeni kurulan görev ile güncellenmiş mevcut görev ayrılmadan görev siliniyor; geri alma hataları da yutuluyor. Bu, geçerli önceki görevin kaybına veya başarısız geri almanın gizlenmesine yol açabilir. Beklenen davranış: yeni görev sahiplik doğrulamasıyla kaldırılmalı, güncellenmiş görev XML yedeğinden geri yüklenmeli ve geri alma başarısızlığı görünür biçimde fail-closed raporlanmalı.
* Orta — `merkez/zamanlayici.py:48-55`, `dersmerkezi.py:90,128,141`, `merkez/arayuz.py:201,278,290`: `gorev_bizim` yalnızca betik yolu ve slug alt dizelerini arıyor; ayrıca `--otomasyon-kaldir` ile TUI kaldırma yolları bu denetimi çağırmadan görevi siliyor. Aynı adlı yabancı veya taklit görev yıkıcı akışlarda sahip olunan görev sayılabilir ya da doğrudan kaldırılabilir. Beklenen davranış: her kaldırma ve geri alma öncesinde `Execute` ile tam `Arguments` birebir doğrulanmalı ve denetim ile silme aynı fail-closed işlem zincirinde yürütülmeli.
* Düşük — `belgeler/plan/2026-09-21-dersmerkezi-cli.md:34,214`: bu satırlar görev tetiklemesinin doğrulanamadığını belirtirken aynı belge `:252` satırında elle, tek seferlik ve haftalık tetiklemenin doğrulandığını kaydediyor. Beklenen davranış: eski ifadeler güncel sonuçla uyumlu hale getirilmeli veya açıkça tarihsel ve geçersiz kılınmış olarak işaretlenmeli.

## Tur 2 Düzeltmeleri ve Doğrulama (Tur 3 öncesi)

Tur 2'de "eksik" işaretlenen maddeler ve yeni bulgular kapatıldı:

1. Eksik (madde 1) — Ayar yazımı başarısız olduğunda geri alma artık görev geçmişini ayırıyor: `gorev_kur_guvenli` önce `vardi = gorev_bizim(slug)` durumunu saklar; hata halinde yeni görev kaldırılır, mevcut görev `gorev_<slug>_onceki.xml` dosyasından `gorev_yukle.ps1` ile geri yüklenir. Geri alma hatası yutulmaz; ayar hatası + geri alma hatası tek `RuntimeError` olarak raporlanır.
2. Eksik (madde 9) — Plandaki 34 ve 214. satırlar güncellendi; eski "doğrulanamıyor/test edilemedi" ifadeleri tarihsel olarak işaretlendi ve güncel sonuca bağlandı.
3. Eksik (madde 12) — `gorev_bizim` artık `Execute` ve tam `Arguments` değerlerini birebir karşılaştırıyor (`gorev_sorgu.ps1` artık `execute` alanını döndürür). `--otomasyon-kaldir` ve TUI kaldırma yolları da sahiplik denetiminden geçiyor; ek olarak `gorev_kaldir.ps1` beklenen execute + argümanı zorunlu doğruluyor (denetim ile silme aynı fail-closed zincirde).
4. Yeni Orta bulgu — yukarıdaki 1 ve 3 ile kapatıldı.
5. Yeni Orta bulgu — 3 ile kapatıldı (`--sil`, `--otomasyon-kaldir`, TUI kaldırma, taşıma geri alma ve `gorev_kaldir.ps1` katmanı).
6. Yeni Düşük bulgu — plan ifadeleri güncellendi (madde 2).

Ek kanıtlar (geçici klasörde, üretim dosyalarına dokunulmadı):

* Birim 101/101 (yeni: mevcut görevin XML'den geri yüklenmesi, PS katmanı sahiplik reddi), akış 50/50 (yeni: taklit görev — yol argümanda; argümanı eksik taklit görev reddi), taşıma hata 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7.
* Üretim görevi: `gorev_bizim('dosya-organizasyonu')` = True (execute + argüman birebir), güncelleme çalıştı, doğrulama kapısı geçti (`atlanan=1`, `gorev=kayitli (Ready)`).

## Tur 3 Sonucu

* Doğrulandı — `merkez/zamanlayici.py:95-112`, `dersmerkezi.py:115-126` ve `merkez/arayuz.py:262-278`: kurulum akışları `gorev_kur_guvenli` kullanıyor; ayar yazımı hatasında yeni görev kaldırılıyor, mevcut görev XML yedeğinden geri yükleniyor ve geri alma hatası ayar hatasıyla birlikte `RuntimeError` olarak yükseltiliyor.
* Eksik (Orta) — `merkez/zamanlayici.py:52-61,95-106`: başlangıçtaki `gorev_bizim` sorgu hatalarını `False` değerine indirgediği için "görev yok" ile "sahiplik sorgulanamadı" ayrımı kayboluyor. İlk sorgu geçici olarak hata verip `gorev_kur` mevcut görevi güncelleyebildikten sonra ayar yazımı başarısız olursa mevcut görev yeni görev sanılarak kaldırılabilir. Beklenen davranış: ilk durum sorgusu hatası mutasyondan önce fail-closed yükseltilmeli ve yok/mevcut/hata durumları ayrılmalı.
* Eksik (Orta) — `merkez/ps/gorev_kaldir.ps1:3-5,16-24`: `BeklenenExecute` ve `BeklenenArguman` zorunlu değil; biri eksik bırakıldığında sahiplik karşılaştırması tamamen atlanıp aynı adlı görev silinebiliyor. Beklenen davranış: iki parametre de zorunlu ve boş olamaz olmalı, `Execute` ile tam `Arguments` karşılaştırması koşulsuz uygulanmalı.
* Eksik (Orta) — `merkez/ps/gorev_yukle.ps1:9-14` ve `merkez/zamanlayici.py:90-92,103-104`: XML geri yükleme PowerShell katmanında yedekteki eylemin beklenen execute ve tam argümanla eşleşmesini doğrulamıyor; değiştirilmiş veya yanlış bir yedek doğrudan kaydedilebilir. Beklenen davranış: geri yükleme betiği beklenen execute ve argümanı zorunlu almalı, XML eylemini kayıt öncesinde birebir doğrulamalı ve sonucu kayıt sonrasında yeniden denetlemeli.
* Doğrulandı — `merkez/zamanlayici.py:52-61,115-121`, `dersmerkezi.py:80-100,128-145`, `merkez/arayuz.py:184-208,279-290` ve `merkez/ps/gorev_sorgu.ps1:14-27`: Python çağrı yolları `Execute` ile tam argümanı karşılaştırıyor ve kaldırma çağrısına iki beklenen değeri iletiyor; ders silme ve otomasyon kaldırma yabancı/taklit görevi reddediyor.
* Doğrulandı — `belgeler/plan/2026-09-21-dersmerkezi-cli.md:34,214,252`: eski doğrulanamama ifadeleri tarihsel olarak işaretlenmiş ve sonraki fiili tetikleme kanıtına bağlanmış.
* Doğrulandı — incelenen çağrı yollarında kilit akışı korunuyor; PowerShell çağrıları bağımsız argümanlarla `-File` üzerinden yapılıyor, slug/gün/saat girdileri kapalı doğrulamadan geçiyor ve yeni bir komut enjeksiyonu yolu görülmedi.

Doğrulama yalnızca belirtilen dosyaların statik kod incelemesidir; bildirilen test paketleri talimat gereği yeniden çalıştırılmadı. Geri alma ayrımı ile Python çağrı yollarındaki sahiplik denetimi büyük ölçüde düzeltilmiş olsa da yukarıdaki fail-closed boşluklar nedeniyle değişmezler henüz tam karşılanmıyor.

SONUC: BULGULAR

## Tur 3 Düzeltmeleri ve Doğrulama (Tur 4 öncesi)

1. Sorgu hatası ayrımı — `merkez/zamanlayici.py` içine `gorev_durumu(slug)` eklendi: sorgu hatası yükseltilir (fail-closed), sonuç `yok` / `bizim` / `yabanci` olarak ayrılır. `gorev_kur_guvenli` mutasyondan önce bu durumu sorgular; `yabanci` ise görev kurulmadan `RuntimeError` verir; `bizim` ise geri alma yolu XML'den yükleme yapar.
2. Zorunlu sahiplik parametreleri — `merkez/ps/gorev_kaldir.ps1` içinde `BeklenenExecute` ve `BeklenenArguman` artık `Mandatory`; boş olamaz ve karşılaştırma koşulsuz uygulanır.
3. Yedek doğrulaması — `merkez/ps/gorev_yukle.ps1` beklenen execute + tam argümanı zorunlu alır; yedeği kaydettikten sonra görevin eylemini birebir karşılaştırır; uyuşmazsa görevi kaldırıp geri yüklemeyi iptal eder.

Ek kanıtlar (geçici klasörde): birim 102/102 (yeni: bozuk/taklit yedek geri yüklenmez), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; üretim görevi `gorev_durumu` = `bizim`, `--otomasyon-kur` güncellemesi ve doğrulama kapısı geçti.

SONUC: BULGULAR (Tur 4 denetimi bekleniyor)

## Tur 4 Sonucu

* Kısmen doğrulandı — `merkez/zamanlayici.py:66-70,109-123`: `gorev_durumu` mutasyondan önce çağrılıyor, `yok` / `bizim` / `yabanci` ayrımını yapıyor, yabancı görevi reddediyor ve sahip olunan önceki görevi XML'den geri yüklüyor; diğer çağrı yollarındaki `gorev_bizim` korumaları da duruyor.
* Doğrulandı — `merkez/ps/gorev_kaldir.ps1:3-23`: `BeklenenExecute` ve `BeklenenArguman` zorunlu, boş değerler reddediliyor ve silmeden önce iki alanın karşılaştırması koşulsuz uygulanıyor.
* Eksik (Orta) — `merkez/ps/gorev_sorgu.ps1:9-12`, `merkez/ps/gorev_kaldir.ps1:12-15` ve `merkez/zamanlayici.py:58-63,122-128`: `Get-ScheduledTask -ErrorAction SilentlyContinue` sorgu hatalarını görev yok sonucuna, `gorev_bizim` ise sorgu hatasını `False` değerine indirebilir. Böylece yeni görev geri alınmadan kalabilir veya kaldırma gerçekte sorgulanamadığı hâlde başarılı/yok sayılabilir. Beklenen davranış: yalnız gerçek bulunamama `yok` sayılmalı, diğer sorgu hataları yükseltilmeli ve geri alma yolu sıkı durum sorgusunu kullanarak hatayı ayar hatasıyla birlikte raporlamalı.
* Eksik (Orta) — `merkez/ps/gorev_yukle.ps1:14-24`, `merkez/ps/gorev_sorgu.ps1:16-27` ve `merkez/ps/gorev_kaldir.ps1:17-22`: XML, eylem doğrulanmadan önce kaydediliyor ve sahiplik denetimi yalnız ilk eylemi inceliyor. Beklenen ilk eylemin yanına eklenmiş ikinci bir eylem denetimi geçebilir; uyumsuz XML de kaldırılmadan önce sisteme kaydedilmiş olur. Beklenen davranış: XML kayıt öncesinde ayrıştırılıp tam olarak tek eylem içerdiği ve bu eylemin beklenen execute ile tam argümana eşit olduğu doğrulanmalı; kayıt sonrasında da aynı eylem sayısı ve içerik yeniden denetlenmeli.
* Bildirilen 102/102, 50/50, 11/11, 4/4, 3/3 ve 7/7 sonuçları ile üretim doğrulaması not edildi; talimat gereği testler yeniden çalıştırılmadı. Kritik bulgu sayısı 0, genel sağlık 6/10; iki fail-closed değişmezi eksik olduğundan kod bu kapsamda gönderime hazır değil.

SONUC: BULGULAR

## Tur 4 Düzeltmeleri ve Doğrulama (Tur 5 öncesi)

1. Sorgu hatası / görev yok ayrımı — `merkez/ps/gorev_sorgu.ps1` artık `Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask` ile varlık sorgular; yalnızca gerçek bulunamama (`var=false`) döner, diğer sorgu hataları `ok=false` olarak yükseltilir. `gorev_durumu` da sorgu hatasını yükseltir; `gorev_kur_guvenli` geri alma dalında `gorev_durumu` kullanır ve beklenmedik durumu (yabancı) ayrı hata olarak raporlar.
2. Tek eylem şartı — `gorev_sorgu.ps1` `eylemSayisi` döndürür; Python `_sorgu_bizim` yalnızca tek eylemli görevi sahiplenir. `gorev_kur.ps1` ve `gorev_kaldir.ps1` mevcut görevi yalnızca tek eylemliyse günceller/kaldırır. `gorev_yukle.ps1` XML'i kayıt öncesinde namespace ile ayrıştırır: tam olarak tek `Exec` eylemi ve beklenen execute + tam argüman şartı; kayıt sonrasında eylem sayısı ve içeriği yeniden doğrulanır, uyuşmazsa görev kaldırılır.

Ek kanıtlar (geçici klasörde): birim 104/104 (yeni: çok eylemli taklit görev sahiplenilmez ve reddedilir; bozuk yedek geri yüklenmez), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; üretim görevi `gorev_durumu` = `bizim`, güncelleme ve doğrulama kapısı geçti.

SONUC: BULGULAR (Tur 5 denetimi bekleniyor)

## Tur 5 Sonucu

* Doğrulandı — `merkez/ps/gorev_sorgu.ps1:9-33` ve `merkez/zamanlayici.py:52-72,111-134`: varlık sorgusu yalnız gerçek bulunamamayı `var=false` döndürüyor; CIM veya sonraki görev sorgusu hataları `ok=false` ve çıkış kodu 1 üzerinden Python'da yükseltiliyor. Güvenli kurulum başlangıçta ve yeni görev geri alma dalında sıkı `gorev_durumu` kullanıyor; `yabanci` durumu ayrıca raporlanıyor.
* Doğrulandı — `merkez/ps/gorev_sorgu.ps1:17-29`, `merkez/zamanlayici.py:52-57`, `merkez/ps/gorev_kur.ps1:27-35` ve `merkez/ps/gorev_kaldir.ps1:17-24`: eylem sayısı taşınıyor ve yalnız tam bir eylem ile beklenen execute + tam argüman eşleşmesi sahipleniliyor; çok eylemli mevcut görev kurma ve kaldırmada reddediliyor. `merkez/ps/gorev_yukle.ps1:26-39` kayıt sonrasında eylem sayısını ve içeriğini yeniden doğrulayıp uyuşmazlığı kaldırıyor.
* Orta — `merkez/ps/gorev_kur.ps1:25-35,48` ve `merkez/ps/gorev_kaldir.ps1:12-15`: mutasyon katmanlarındaki `Get-ScheduledTask -ErrorAction SilentlyContinue`, sorgu hatasını hâlâ görev yok sonucuna indirebilir. Kurma yolu bu durumda `-Force` ile kayıt yapabilir; kaldırma yolu ise görev dururken başarılı bir `silindi=false` sonucu döndürebilir. Beklenen davranış: bu iki betikte yalnız kesin bulunamama yok sayılmalı, diğer sorgu hataları mutasyondan veya başarı çıktısından önce fail-closed yükseltilmelidir.
* Orta — `merkez/ps/gorev_yukle.ps1:19-25`: kayıt öncesi denetim yalnız `Exec` düğümlerini sayıyor; bir `Exec` yanında `ComHandler` gibi başka bir eylem bulunan XML ön denetimi geçip kayıt edilebilir ve ancak kayıt sonrası kaldırılır. Beklenen davranış: kayıt öncesinde `Actions` altındaki tüm eylem düğümleri sayılmalı, tam bir düğüm bulunmalı ve bu düğümün `Exec` olduğu doğrulanmadan `Register-ScheduledTask` çağrılmamalıdır.
* Bildirilen 104/104, 50/50, 11/11, 4/4, 3/3 ve 7/7 sonuçları ile üretim doğrulaması not edildi; talimat gereği yeniden çalıştırılmadı. Kritik bulgu sayısı 0, genel sağlık 7/10; iki kalan fail-closed boşluk nedeniyle kod bu kapsamda gönderime hazır değil.

SONUC: BULGULAR

## Tur 5 Düzeltmeleri ve Doğrulama (Tur 6 öncesi)

1. Mutasyon katmanlarında sıkı varlık sorgusu — `merkez/ps/gorev_kur.ps1` ve `merkez/ps/gorev_kaldir.ps1` artık `Get-ScheduledTask -ErrorAction SilentlyContinue` yerine `Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask` ile varlık sorgular; yalnızca gerçek bulunamama "yok" sayılır, sorgu hatası mutasyondan önce fail-closed yükseltilir. Görev bulunduğunda ayrıntılar `Get-ScheduledTask -ErrorAction Stop` ile alınır.
2. XML ön denetimi tüm eylem düğümleri — `merkez/ps/gorev_yukle.ps1` artık `//t:Actions/*` ile tüm eylem düğümlerini sayar; tam olarak tek düğüm ve bu düğümün `Exec` olması şartı aranır. `Exec` + `ComHandler` gibi karışık yedekler `Register-ScheduledTask` çağrılmadan reddedilir.

Ek kanıtlar (geçici klasörde): birim 106/106 (yeni: Exec+ComHandler yedeği reddedilir ve kaydedilmez), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; üretim görevi `gorev_durumu` = `bizim`, güncelleme ve doğrulama kapısı (`atlanan=1`, `gorev=kayitli (Ready)`) geçti.

SONUC: BULGULAR (Tur 6'da kapatıldı ve onaylandı)

## Tur 6 Sonucu

* Doğrulandı — `merkez/ps/gorev_kur.ps1:25-49` ve `merkez/ps/gorev_kaldir.ps1:12-26`: varlık sorgusu `Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask -ErrorAction Stop` ile yapılıyor; yalnızca tam sıfır sonuç görev yok kabul ediliyor, sorgu hataları yakalanıp başarısızlık olarak yükseltiliyor ve görev bulunduğunda ayrıntılar `Get-ScheduledTask -ErrorAction Stop` ile alınıyor.
* Doğrulandı — `merkez/ps/gorev_yukle.ps1:19-40`: kayıt öncesinde `//t:Actions/*` ile tüm eylem düğümleri sayılıyor; tam bir düğüm ve `Exec` türü doğrulanmadan `Register-ScheduledTask` çağrılmıyor. Kayıt sonrasında tek eylem ile beklenen execute ve tam argüman denetimi korunuyor; uyuşmazlıkta kayıt kaldırılıp hata yükseltiliyor.
* Bildirilen birim 106/106, akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3 ve TUI 7/7 sonuçları ile üretim görevi ve doğrulama kapısı kanıtları not edildi; talimat gereği testler yeniden çalıştırılmadı.

İncelenen akışlarda Tur 5'teki iki fail-closed boşluk kayıt veya mutasyon öncesinde kapatılmıştır. Yeni regresyon ya da kalan fail-closed boşluk görülmedi.

SONUC: ONAY
