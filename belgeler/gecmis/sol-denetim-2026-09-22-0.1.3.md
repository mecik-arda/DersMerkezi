# Sol Denetim Raporu — CLI Ayar Dilimi 0.1.3 (2026-09-22)

Kapsam: "Öncelik 4 - CLI Ayar Görünümü ve Seçim (0.1.3)" diliminin uygulanması (Sol danışma kararı doğrultusunda). İnceleme; `--ayarlar`, `--secili`, ortak işlevler, matris, eşlik, doküman ve kanıtlar üzerinden yapılır. Bu dosyaya yalnızca denetim turu sonuçları eklenir.

## Tur 1

Denetim, bağlayıcı eşlik listesi, bayrak matrisi, Öncelik 4, Uygulama Sırası 7 ve Kapsam Dışı kararlarıyla karşılaştırılarak yapıldı. Talimat gereği test, build veya script çalıştırılmadı. 403 toplamının `189 + 153 + 47 + 14` dağılımı, `133/133` fonksiyon ve `%81` ifade satırı iddiaları plan ile CHANGELOG arasında tutarlıdır; bunlar bu turda yeniden yürütülmüş çalışma kanıtı değildir.

1. **Orta — Salt-okunur hata yolu günlük dosyasına yazıyor — `dersmerkezi.py:293`, `dersmerkezi.py:295`, `merkez/ayarlar.py:309`, `merkez/ayarlar.py:312`.** `ayarlar.gorunum` bozuk `ayarlar.json` için `RuntimeError` yükseltiyor; genel çalışma hatası yakalayıcısı exit 1 dönmeden önce koşulsuz `gunluk.kayit` çağırıyor. Böylece `--ayarlar` görünümü bozuk ayarda karantina yapmasa da günlük oluşturma, günlük yazma veya rotasyon izi bırakabiliyor; bu davranış planın `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:187` ve `:192` satırlarındaki yazımsızlık kabulüyle ve `belgeler/kurulum.md:122` ile çelişiyor. **Beklenen düzeltme:** `ayarlar` salt-okunur görünümündeki çalışma hatalarını disk günlüğüne uğratmadan stderr/JSON kanal politikasına göre döndür; başarılı ve hatalı görünümde günlük, yedek, geçici dosya ve rotasyon izinin oluşmadığını doğrula.

2. **Orta — TUI Ayarlar ekranı bozuk dosyayı ortak fail-closed yola ulaşmadan karantinaya alıyor — `merkez/arayuz.py:244`, `merkez/arayuz.py:245`, `merkez/ayarlar.py:211`, `merkez/ayarlar.py:217`, `merkez/ayarlar.py:220`, `merkez/ayarlar.py:224`.** TUI ekranı başlangıç verisini `yukle_salt` veya `gorunum` yerine mutasyonlu `ayarlar.yukle` ile alıyor. Bozuk JSON, geçersiz kök veya desteklenmeyen sürüm bu aşamada taşınıp boş veriyle değiştiriliyor; dolayısıyla TUI'nin `isaretle -> secili_ayarla` delegasyonu sağlam dosyada doğru olsa da bozuk ayarda “dosya değişmez” ve aynı fail-closed ortak yol koşulları sağlanmıyor. **Beklenen düzeltme:** TUI görünümünü `yukle_salt`/`gorunum` üzerinden kur, okuma hatasını dosyaya dokunmadan Türkçe ve kaçışlı göster, yalnız gerçek seçim mutasyonlarını `isaretle -> secili_ayarla` yoluna gönder.

3. **Orta — Seçim mutasyonunda yedek zorunluluğu fail-closed değil — `merkez/ayarlar.py:249`, `merkez/ayarlar.py:252`, `merkez/ayarlar.py:254`, `merkez/ayarlar.py:255`, `merkez/ayarlar.py:257`.** `kaydet`, mevcut ayarı tek nesil yedeğe kopyalarken oluşan bütün `OSError` hatalarını yutuyor ve ana ayarı atomik olarak güncellemeye devam ediyor. Bu nedenle `secili_ayarla` mutex ve atomik ana dosya yazımını kullansa da planın `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:188` satırında bağlayıcı olan “yedek + atomik” zinciri yedek oluşturulamayan durumda sessizce atlanıyor. **Beklenen düzeltme:** Mevcut ayar dosyası varsa doğrulanmış yedek başarıyla oluşturulmadan ana dosya değişikliğine geçme; yedek hatasında ana dosyayı değiştirmeden exit 1 üret ve geçici yedek kalıntılarını temizle.

4. **Düşük — CLI ve JSON dokümantasyon listeleri 0.1.3 yüzeyini eksik gösteriyor — `README.md:50`, `belgeler/kurulum.md:91`, `belgeler/mimari.md:41`, `belgeler/mimari.md:48`.** Parser `--ayarlar` modunu ve bu modda `--json` kullanımını kabul ettiği halde README ve kurulumdaki JSON mod listelerinde `--ayarlar` yok; mimari mod matrisi `--ayarlar`ı, arayüz eşliği listesi de `ayarlar.gorunum`/`ayarlar.secili_ayarla` ortak yolunu içermiyor. Aynı belgelerin başka satırları özelliği anlattığı için kullanıcı ve mimari sözleşme kendi içinde çelişkili. **Beklenen düzeltme:** JSON mod listelerine `--ayarlar`ı ekle; mimari mod ve ortak işlev listelerini Öncelik 4 ile aynı kanonik yüzeyi gösterecek biçimde güncelle.

5. **Düşük — Plan durum bilgisi uygulanmış dilimle çelişiyor — `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:4`, `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:195`, `README.md:12`, `CHANGELOG.md:3`.** Plan üst bilgisi ve README bağlantı açıklaması belgeyi hâlâ “uygulanmadı” olarak tanımlarken aynı plan 0.1.3 kanıtını kaydediyor ve CHANGELOG sürümü yayımlanmış gösteriyor. **Beklenen düzeltme:** Plan durumunu uygulanan dilimleri açıkça gösterecek biçimde güncelle ve README açıklamasındaki “uygulanmadı” ifadesini kaldır veya yalnız kalan uygulanmamış maddelerle sınırla.

Doğrulanan uyumlu alanlar: `--ayarlar` bağımsız modu, `--secili evet|hayir` kapalı değer kümesi, `--ders` zorunluluğu, mod/bayrak dışlamaları, bilinmeyen ders için exit 2, boş liste için exit 0, kanonik başarı JSON şeması, mutasyon sonrası yeni durumun okunması, `--sessiz` ile JSON stdout'un korunması, `isaretle` delegasyonu, 200 MB sınırının CLI katmanında korunması ve mutex/atomik ana dosya yazım yolu. Sağlanan bağlamda sürüm kaynağının ve UA/görev eylemi türetiminin uygulama dosyaları bulunmadığından bu üç iddia yalnız çağrı ve belge tutarlılığı düzeyinde değerlendirilebildi.

Genel sonuç: 0 kritik, 3 orta, 2 düşük bulgu. Sağlık skoru 72/100. Salt-okunurluk ve fail-closed yedek sözleşmeleri düzeltilmeden dilim gönderilebilir değildir.

SONUC: BULGULAR

## Tur 2

İnceleme yalnız izin verilen kaynak ve belge dosyalarının salt-okunur karşılaştırmasıyla yapıldı; test, build veya script çalıştırılmadı. Bildirilen 410/410 sonuç ile gerçek proje kontrolleri bu turda yeniden üretilmiş kanıt değil, ana orkestratörün sağladığı güncel kanıt olarak değerlendirildi.

1. **Kapatıldı — Salt-okunur hata günlüğü (orta).** `dersmerkezi.py:131-138`, `ayarlar.gorunum` kaynaklı `RuntimeError`ı genel yakalayıcıdan önce ele alıyor; JSON hata nesnesini doğrudan stderr'e yazıyor, insan satırını yalnız sessiz değilken gösteriyor ve bu dalda `gunluk.kayit` çağırmadan exit 1 dönüyor. Böylece bozuk ayardaki salt-okunur görünüm günlük yazma ve rotasyon yoluna girmiyor; bildirilen günlük boyutu değişmezliği kod akışıyla uyumlu.

2. **Kapatıldı — TUI karantina (orta).** `merkez/arayuz.py:244-250`, başlangıç görünümünü `ayarlar.gorunum()` üzerinden alıyor; bu işlev `yukle_salt` kullandığı için bozuk ayarı karantinaya almıyor. `RuntimeError` metni `escape` ile kaçışlanıp Türkçe olarak gösteriliyor ve ekran geri dönüyor. Seçim mutasyonu `merkez/arayuz.py:260-264` ile `isaretle`ye, oradan `merkez/ayarlar.py:353-354` üzerinden `secili_ayarla`ya devrediliyor.

3. **Kapatıldı — Yedek fail-closed (orta).** `merkez/ayarlar.py:252-266`, mevcut ana dosyayı önce `.yedek.tmp` dosyasına `shutil.copy2` ile yazıyor, ardından `_replace_tekrar` ile atomik olarak yedeğe taşıyor. Herhangi bir `OSError` durumunda geçici yedek temizlenip hata yeniden yükseltiliyor; ana dosyanın `_json_yaz` çağrısı ancak yedek zinciri başarıyla tamamlandıktan sonra çalışıyor. Bildirilen hata enjeksiyonu sonucu bu akışla tutarlı.

4. **Açık — Doküman JSON listeleri (düşük).** README JSON listesi ile `belgeler/mimari.md` mod matrisi ve ortak işlev listesi istenen 0.1.3 yüzeyini içeriyor. Ancak `belgeler/kurulum.md:91` içinde `--ayarlar` art arda iki kez yazılmış; kanonik JSON mod listesi hâlâ hatalı. **Beklenen düzeltme:** Yinelenen ikinci `--ayarlar` girdisini kaldır ve listeyi her desteklenen modu bir kez içerecek biçimde bırak.

5. **Açık — Durum bilgisi (düşük).** Plan üst bilgisi, README açıklaması ve `AGENTS.md` plan notu 0.1.2 ile 0.1.3 dilimlerinin uygulandığını bildiriyor. Buna karşın `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:12`, maddelerin gelecekte uygulanacağını söylemeye devam ediyor ve `Durum: Uygulandı` üst bilgisiyle çelişiyor. **Beklenen düzeltme:** Bu cümleyi planın tarihsel niteliğini ve maddelerin uygulandığını anlatan geçmiş zamanlı ifadeyle güncelle.

**Kalan çelişki — Orta — Yedekleme hatası TUI menü yaşam döngüsünü bozuyor — `merkez/ayarlar.py:260-265`, `merkez/arayuz.py:260-266`.** `ayarlar.kaydet` artık yedekleme hatasında tasarlandığı gibi `OSError` yükseltiyor; ancak TUI Ayarlar ekranı seçim mutasyonunda yalnız `ValueError` ve `RuntimeError` yakalıyor. Yedek oluşturma veya atomik taşıma hatası TUI'de Türkçe/kaçışlı iletiye çevrilmeden menü döngüsünden dışarı taşar. **Beklenen düzeltme:** Seçim mutasyonu yakalayıcısına `OSError` ekle, metni mevcut `escape` yoluyla göster ve menü döngüsünün korunduğunu denetle.

Genel sonuç: 0 kritik, 1 orta ve 2 düşük açık bulgu; Tur 1'in üç bulgusu kapandı, iki bulgusu artık çelişkiler nedeniyle açık kaldı. Sağlık skoru 84/100. Orta önem düzeyindeki TUI hata yolu ve iki belge tutarsızlığı giderilmeden sürüm gönderilebilir değildir.

SONUC: BULGULAR

## Tur 3

İnceleme yalnız izin verilen kaynak ve belge dosyalarının salt-okunur karşılaştırmasıyla yapıldı; test, build veya script çalıştırılmadı. Bildirilen 418/418 kontrol ile gerçek proje sonuçları ana orkestratörün sağladığı güncel kanıt olarak değerlendirildi.

1. **Kapatıldı — Doküman JSON listesi (düşük).** `belgeler/kurulum.md:91` kanonik listeyi `--durum`, `--listele`, `--cek`, `--saglik`, `--surum`, `--oto-tamamlama`, `--ayarlar` biçiminde ve her modu bir kez içerecek şekilde gösteriyor. Sağlanan 418/418 kanıtı, tüm belgelerde ardışık `--ayarlar`, `--ayarlar` yinelenmesini engelleyen kontrolü de içeriyor.

2. **Kapatıldı — Durum bilgisi (düşük).** `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:12` giriş cümlesi maddeleri uygulanmış olarak tanımlıyor; planda `öneri listesidir` ve `uygulanacaktır` ifadeleri kalmamış. Sağlanan test kanıtı bu durum sözleşmesini koruyor.

3. **Kapatıldı — TUI `OSError` yolu (orta).** `merkez/arayuz.py:264` seçim mutasyonunda, `:206` ders eklemede, `:225` ders silmede ve `:321` ile `:334` otomasyon kurma/kaldırma yollarında `OSError` yakalanıyor. Ayarlar seçimi hatası `escape(str(hata))` ile güvenli biçimde gösterilip üst menü yaşam döngüsüne dönüyor; `secili_ayarla` için enjekte edilen `OSError` testinin menü döngüsünün korunduğunu ve kaçışlı Türkçe `disk dolu` iletisinin gösterildiğini doğruladığı bildirildi.

Kalan çelişki yoktur. Tur 2'de açık kalan 1 orta ve 2 düşük bulgunun tamamı kapatıldı. Sağlanan güncel kanıtta 418/418 kontrol başarılıdır; `--surum` 0.1.3, `--cek --sessiz` sonucu `atlanan=1`, `--ayarlar --json` çıkış kodu 0 ve `--durum` sonucu Ready olup üretim görevi değişmemiştir.

SONUC: ONAY
