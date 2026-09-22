# Sol Bağımsız Denetim Raporu — CLI Genişletmesi 0.1.2 (2026-09-22)

Kapsam: `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md` planının uygulanması (sürüm 0.1.2). İnceleme; plan maddeleri, "Kapsam İlkesi: Arayüz Eşliği", değişmezler ve doğrulama kanıtları üzerinden yapılır. Bu dosyaya yalnızca denetim turu sonuçları eklenir.

## Tur 1

İnceleme sonucu: 0 kritik, 6 orta ve 2 düşük bulgu. Genel sağlık skoru: 58/100. Bu haliyle gönderime hazır değil.

1. Orta — JSON çalışma hataları kanonik hata kanalına taşınmıyor.
   Kanıt: `dersmerkezi.py:146-155` sağlık sorunlarında önce stdout'a normal sağlık nesnesini yazıp sonra exit 1 döndürüyor. `dersmerkezi.py:240-242` çekme doğrulama/dönüşüm hatalarında da stdout'a normal çekme nesnesi yazıp exit 1 döndürüyor. Ayrıca `dersmerkezi.py:257,273-278`, `--json --sessiz` çalışma hatasında zorunlu insan satırını bastırıyor. Bunlar plandaki “exit 1 → stdout boş; stderr'de JSON hata nesnesi ve insan satırı” sözleşmesine aykırı.
   Beklenen düzeltme: Sağlık ve çekme sonuçları çıkış kodu kesinleşene kadar tamponlanmalı; exit 1 durumunda stdout'a hiçbir şey yazılmadan stderr'e kanonik hata nesnesi ve Türkçe insan satırı yazılmalı. `--sessiz`, JSON çalışma hatasının zorunlu insan satırını kaldırmamalı.

2. Orta — Kuru çekme bozuk ayar dosyasını değiştirebiliyor.
   Kanıt: `merkez/indirici.py:284-302`, `kuru` dalına ulaşmadan önce `ayarlar.yukle()` çağırıyor. `merkez/ayarlar.py:211-225` bozuk veya desteklenmeyen `ayarlar.json` dosyasını `_bozuk_yedekle` ile karantinaya taşıyor. Böylece `indir_ders(kuru=True)` “hiçbir dosya yazılmaz/değiştirilmez” vaadini ayar bozukluğu senaryosunda ihlal ediyor.
   Beklenen düzeltme: Kuru akış, ayarları da karantina veya başka mutasyon yapmayan salt-okunur bir yükleyiciyle okumalı; bozuk ayarı hata olarak raporlayıp dosya sistemini değiştirmemeli.

3. Orta — 200 MB değişmezi ortak indirme işlevinde fail-closed korunmuyor.
   Kanıt: `merkez/komut.py:202-205` yalnız CLI `--sinir` değerini 1-200 aralığında doğruluyor; `merkez/indirici.py:284-285` ise ortak `indir_ders` işlevine verilen `ust_boyut` için üst sınır doğrulaması yapmıyor ve `merkez/indirici.py:337-340,364-365` çağıranın verdiği daha yüksek değeri doğrudan liste/akış sınırı olarak kullanıyor. CLI dışı ortak işlev çağrısı 200 MB üstünü açabiliyor.
   Beklenen düzeltme: `indir_ders` girişinde `1 <= ust_boyut <= UST_BOYUT` doğrulaması yapılmalı; liste ve akış katmanları hiçbir çağrı yolunda 200 MB üstü değer kabul etmemeli.

4. Orta — Yazılamayan alternatif günlük hedefi exit 1 yerine başarıyla sonuçlanabiliyor.
   Kanıt: `merkez/gunluk.py:103-112` hedefi ayarlarken yalnız yol/doğrulama ve dizin oluşturma yapıyor, yazılabilirliği kanıtlamıyor. `merkez/gunluk.py:121-129` rotasyon `OSError` hatalarını sessizce yutuyor; `merkez/gunluk.py:153-169` gerçek yazma hatasını yalnız uyarıya çevirip çağırana iletmiyor. `dersmerkezi.py:259-261` bu nedenle asıl modun başarı kodunu döndürebiliyor. Bu davranış plan ve kurulum belgesindeki “kök dışı exit 2, yazılamaz exit 1; OSError sessizce yutulmaz” sözleşmesini ihlal ediyor.
   Beklenen düzeltme: Çağrı kapsamlı günlük hedefi yazım anında yeniden doğrulanmalı; rotasyon ve yazma hataları çağırana taşınarak exit 1 üretilmeli. Kök dışı/dizin/reparse doğrulama hataları exit 2 olarak kalmalı.

5. Orta — TUI sağlık yolu bozuk ayarda salt-okunur değil ve sağlık ekranına ulaşamıyor.
   Kanıt: `merkez/arayuz.py:365-392` sağlık seçeneğini göstermeden önce `durum.kayitlar(ayrintili=True)` çağırıyor ve kayıt yoksa doğrudan dönüyor. `merkez/durum.py:46-48` bunun için mutasyonlu `ayarlar.yukle()` işlevini kullanıyor; `merkez/ayarlar.py:211-225` bozuk ayarı karantinaya taşıyor. Dolayısıyla CLI'daki salt-okunur `saglik.denetle` davranışı TUI sağlık girişinde korunmuyor.
   Beklenen düzeltme: Sağlık, durum kaydı yüklemesine bağlı olmayan doğrudan bir TUI menü girdisi olmalı ve bozuk ayarda da `saglik.denetle` çağrılmalı; sağlık yolunda karantina veya başka dosya mutasyonu yapılmamalı.

6. Orta — Arayüz eşliği `--zorla-md` ve ders-özel sağlık için eksik.
   Kanıt: `merkez/arayuz.py:152-171` çekme ekranında yalnız normal, kuru ve tam `zorla` seçeneklerini sunuyor; `zorla_md=True` ile ortak işlevi çağıran bir TUI yolu yok. `merkez/arayuz.py:339-346` sağlık ekranında yalnız varsayılan ve tüm dersler için `ag=True` seçenekleri var; bağlayıcı eşlik listesindeki `--saglik --ders <kimlik>` karşılığı bulunmuyor.
   Beklenen düzeltme: TUI çekme akışına “yalnız Markdown bağlamını yenile” seçeneği, sağlık akışına tek ders seçimi eklenmeli; iki yüzey de CLI ile aynı `indirici.indir_ders` ve `saglik.denetle` işlevlerini eşdeğer girdilerle çağırmalı.

7. Düşük — Bazı dinamik TUI metinleri Rich kaçışından geçirilmeden işaretleme olarak yorumlanıyor.
   Kanıt: `merkez/arayuz.py:270-271` ayar dosyasından gelen gün, saat ve görev durumu değerlerini doğrudan `KONSOL.print` içine yerleştiriyor. `merkez/ayarlar.py:211-226` normal yüklemede ders kayıtlarını `ders_dogrula` ile doğrulamadığı için bu alanların güvenli kapalı kümede olduğu garanti edilmiyor. Bu, bağlayıcı `rich.markup.escape` değişmezini ihlal ediyor.
   Beklenen düzeltme: Rich işaretlemesi içine giren tüm dinamik ayar ve görev değerleri `escape(str(...))` ile kaçırılmalı; güvenlik yalnız normal yazma yolundaki doğrulamaya bırakılmamalı.

8. Düşük — Üretilen PowerShell tamamlama kodu yasaklı yorum satırı içeriyor.
   Kanıt: `merkez/tamamlama.py:10-13`, üretilen betiğin ilk satırına `#` ile başlayan yorum ekliyor. Bu çıktı, AGENTS.md'nin kod içinde yorum satırı bulunmaması değişmezine aykırı.
   Beklenen düzeltme: Üretilen betikteki yorum satırı kaldırılmalı; parser kaynaklı bayrak üretimi ve atomik yazım davranışı korunmalı.

Doğrulanan ve ek bulgu saptanmayan alanlar: `merkez/komut.py:52-74,155-212` mod/bayrak matrisi ve aralıkları uyguluyor; moda özgü varsayılanlar doğrulama sonrasına bırakılıyor. `merkez/indirici.py:351-420` zorlama türlerini ve doğrulama zincirini ayırıyor. `dersmerkezi.py:222-239` kilit süresi aşımında ek bloklamadan atlıyor. `merkez/saglik.py:27-136` doğrudan çağrıda ağsız/salt-okunur temel denetimi, 10 ağ ve 20 görev sınırını koruyor ve kota meta verisinde secret döndürmüyor. `merkez/zamanlayici.py:187-213` ile `merkez/ps/gorev_tetikle.ps1:13-72` tetikleme öncesi sahipliği yeniden doğruluyor, 60 saniye yokluyor ve yalnız kanıtlanmış sonuç anlamlarını kesinleştiriyor. `merkez/tamamlama.py:33-50` bayrakları parser'dan türetip dosyayı geçici dosya, `fsync` ve atomik değiştirme ile yazıyor. `merkez/komut.py:6,245-248`, `merkez/indirici.py:11-15` ve `CHANGELOG.md:3` sürüm/UA/CHANGELOG bağlantısını tek kaynak kullanacak biçimde kuruyor.

SONUC: BULGULAR

## Tur 2

1. Kanal politikası — kapatıldı. `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:483-494` hata sayacı taşıyan kanonik mod sonuçlarını istisna yollarından açıkça ayırıyor. `dersmerkezi.py:146-155,242-244` sağlık ve çekme sonuçlarını JSON stdout'a yazıp sorun varsa exit 1 döndürüyor; `dersmerkezi.py:270-280` istisnalarda JSON hata nesnesini stderr'e her durumda yazıyor, insan satırını yalnız `--sessiz` bastırıyor ve stdout'a yazmıyor.

2. Kuru mutasyonsuzluk — kapatıldı. `merkez/ayarlar.py:229-245` mutasyonsuz `yukle_salt` ve `secili_dersler_salt` yollarını sağlıyor; `merkez/indirici.py:289-294` kuru çalışmada yalnız bu yükleyiciyi kullanıp bozuk ayarı `IndirmeHatasi` ile reddediyor. `dersmerkezi.py:212-218` ders belirtilmeyen kuru CLI yolunu da `secili_dersler_salt` üzerinden geçiriyor. Kayıtlı test kanıtı bozuk ayarda exit 1 ve karantina oluşmamasını kapsıyor.

3. 200 MB değişmezi — kapatıldı. `merkez/indirici.py:285-288` ortak `indir_ders` girişinde değeri tamsayıya çevirip `1 <= ust_boyut <= UST_BOYUT` koşulunu uyguluyor; `merkez/indirici.py:15` üst sınırı 200 MB olarak sabitliyor. Kayıtlı sınır testleri 0 ve 201 MB değerlerinin reddini kapsıyor.

4. `--log` yazılabilirliği — açık (orta). `merkez/gunluk.py:103-114` hedefi append modunda açarak ilk yazılabilirlik kontrolünü yapıyor ve hata `dersmerkezi.py:270-281` üzerinden exit 1'e dönüşüyor; `merkez/gunluk.py:155-168` özel günlükte sonradan oluşan yazma/doğrulama hatasını da `OSError` olarak yükseltiyor. Ancak `merkez/gunluk.py:123-131` rotasyon sırasında oluşan her `OSError` hatasını koşulsuz yutuyor. Bu, revizyondaki “özel günlükte yazım/rotasyon hatası OSError olarak yükseltilir” kararıyla çelişiyor ve kayıtlı “yazılamayan hedef” testi rotasyon hatası yolunu kanıtlamıyor. Beklenen düzeltme: `_rotasyon` hatası özel günlük hedefinde `OSError` olarak çağırana taşınmalı, yalnız varsayılan günlük için mevcut fail-closed atlama korunmalı; özel günlükte kilitli `.old`, silme ve yeniden adlandırma başarısızlıkları exit 1 ile doğrulanmalı.

5. TUI sağlık salt-okunurluğu — kapatıldı. `merkez/durum.py:74-78` durum verisini `ayarlar.yukle_salt` ile okuyor; `merkez/arayuz.py:389-420` ayar hatasında menüden dönmeyip sağlık seçeneğini erişilebilir tutuyor. `merkez/arayuz.py:346-370` sağlık ekranındaki ayar okumasını da salt-okunur yapıyor ve denetimi çağırıyor. Kayıtlı test kanıtı bozuk ayarda sağlık erişimi ile karantina oluşmamasını kapsıyor.

6. Arayüz eşliği — kapatıldı. `merkez/arayuz.py:151-176` çekme menüsünde “Zorla yeniden indir” ve “Yalnız bağlamı yenile” seçimlerini sırasıyla `zorla` ve `zorla_md` olarak ortak `indirici.indir_ders` yoluna iletiyor. `merkez/arayuz.py:346-370` tek ders seçimini `saglik.denetle(ders=...)` çağrısına bağlıyor. Kayıtlı TUI kontrolleri zorla-md ve tek ders sağlık yollarını kapsıyor.

7. Rich kaçışı — kapatıldı. `merkez/arayuz.py:274-277` gün, saat ve görev durumunu; `merkez/arayuz.py:302-310` görev kurulum ve tetikleme sonuçlarını `escape` ile kaçışlıyor. Kayıtlı markup enjeksiyonu kontrolü bu yüzeyleri kapsıyor.

8. Üretilen betik — kapatıldı. `merkez/tamamlama.py:10-29` tarafından üretilen PowerShell satırlarında yorum satırı bulunmuyor; `merkez/tamamlama.py:32-49` parser kaynaklı bayrak üretimini ve geçici dosya üzerinden atomik değiştirmeyi koruyor. Kayıtlı kontrol üretilen betiğin yorumsuz olduğunu doğruluyor.

Toplam: 7 bulgu kapatıldı; 1 orta bulgu açık kaldı. Kritik bulgu yoktur. Açık rotasyon hatası nedeniyle sürüm bu turda gönderime hazır değildir. İnceleme kullanıcı talimatı gereği test çalıştırılmadan, salt-okunur kaynak incelemesi ve planda kayıtlı 162 birim/akış ile 14 tetikleme/sahiplik kontrolü kanıtı üzerinden yapılmıştır.

SONUC: BULGULAR

## Tur 3

1. Özel günlük rotasyon hatası — kapatıldı. `merkez/gunluk.py:123-132` rotasyon sırasında oluşan `OSError` hatasını yalnız `LOG_YOLU == VARSAYILAN_LOG` durumunda yutuyor; özel günlük hedefinde yeniden yükseltiyor. `merkez/gunluk.py:156-169` bu yolu `kayit` içinden çağırıp özel hedefte `OSError` olarak çağırana taşıyor; `dersmerkezi.py:270-281` hatayı exit 1'e çeviriyor. `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:490` kararı aynı ayrımla güncelliyor. Geçici kopyadaki kilitli `.old`, 1 MB üstü özel günlük ve `--cek --kuru --log alt/rot.log` kontrolünün exit 1 dönmesi ve hedef dosyaları değiştirmemesi, Tur 2'de eksik kalan rotasyon hata yolunu doğrudan kanıtlıyor. Güncel 164 birim/akış ile 14 tetikleme/sahiplik kontrolünün geçtiği kayıtlıdır.

Kalan çelişki yoktur. Kritik bulgu sayısı 0, genel sağlık skoru 100/100; sürüm gönderime hazırdır.

SONUC: ONAY
