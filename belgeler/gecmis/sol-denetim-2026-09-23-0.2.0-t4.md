# Sol Kod Denetimi — 0.2.0 T4

Tarih: 2026-09-24
Kapsam: T0–T4 Teams/SharePoint kaynağı; salt-okunur GPT-6 Sol kod denetimi
Sonuç: **SONUC: ONAY**

## İlk T4 Denetimi

Sonuç: BULGULAR.

* Orta — `file.hashes` içindeki yanlış tür/null/boş değerler hash yokmuş gibi ele alınıp açık zayıf doğrulamaya düşebiliyordu. Açıkça mevcut boş `hashes` nesnesi ve mevcut QuickXorHash/SHA-1 alanlarının null, boş veya geçersiz değerleri doğrulama hatası verir; desteklenen hash alanı yoksa varsayılan kapalı kalır, yalnız açık weak ayarıyla zayıf yol seçilebilir.
* Düşük — HTTP tarih biçimli `Retry-After` yerel saat diliminde yorumlanıyordu. RFC HTTP tarih ayrıştırması UTC/zaman dilimi farkındalığıyla değiştirildi.

## Düzeltme Sonrası İncelemeler

* `$select=id,eTag,size,file` metadata yanıtında `name` bulunması gerekmiyor; adsız ama seçilen alanları içeren yanıt kabul ediliyor ve weak yolun id/eTag/size denetimi çalışıyor.
* Graph yönlendirme sayısı her URL'nin retry bütçesinden ayrıldı. `302 → 302 → 503 → 200` senaryosu geçiyor.
* Son test-stratejisi incelemesinde, weak doğrulama sayacı/uyarısının başarısız indirmeden önce artabildiği ve aynı eTag'e kayıtlı yerel SHA-256 uyuşmazlığının sessizce yeniden indirmeye dönüştüğü görüldü. Sayaç/başarı uyarısı yalnız doğrulanmış akış/atlama sonrası oluşuyor; kuru mod yalnız plan uyarısı üretir ve kabul sayacını artırmaz. Aynı eTag/size altındaki bozuk yerel PDF ve Markdown, durum kaydıyla birlikte fail-closed temizlenip `dogrulama_hatasi` üretiyor. Kuru mod hatayı raporlar ama dosyayı değiştirmez.
* Hashless weak kayıtla aynı eTag/size'a bağlı yerel SHA-256 uyuşmazlığı da test edildi: normal akış bozuk PDF/Markdown ve kayıt girdisini temizleyip `dogrulama_hatasi` veriyor; kuru akış dosyaya dokunmuyor.
* Hash formatı, UTC retry tarihi, metadata alan seçimi, weak sayaç zamanlaması ve bozuk durum alt-kaydı davranışları düzeltildi. Son testte hashes alanı/alt alanların absent, null, empty nesne/string ve yanlış tip durumları ayrı ayrı denetlendi. Sol'un final salt-okunur turu `SONUC: ONAY` verdi; yeni engelleyici bulgu yok.

## Denetim Kapsamı

* Graph/ön kimlikli URL köken-yol/host denetimleri; Authorization ayrımı; nextLink, sayfa ve öğe sınırları; hash bütünlüğü; weak eTag pre/post; yerel SHA-256; `.part`/atomik taşıma; GitHub geriye uyumu; TUI/JSON/sağlık eşliği; zamanlanmış görev eylem değişmezliği.
* Microsoft Graph `$select=id,eTag,size,file` yanıtında `name` olmaması; absent/null/empty/malformed hash değerleri; 429/5xx retry ile 302 yönlendirme birleşimi ve weak sayaç hata zamanlaması sahte yanıtlarla kontrol edildi.

## Test Kanıtı ve Operasyonel Sınır

* Geçici kopya: regresyon 423/423; T0 199/199; T1 Graph/QuickXor 220/220; T2 sahte Graph adaptörü/idempotans 57/57. Trace summary raporlanan uygulama modüllerinde %100 gösterdi.
* Gerçek proje: derleme exit 0; GitHub çekme `atlanan=2`, exit 0; `--saglik --ders dosya-organizasyonu --json` exit 0, kota `limit=60 kalan=43`; durum `Ready`; sürüm `0.2.0`; ayarlar ve ağsız sağlık JSON'u geçerli. Sol'un kendi salt-okunur Görev Zamanlayıcı sorgusu bu ortamda doğrulanamadı; gerçek kapı ve E2E üretim görevi kontrolü `Ready` durumunu ve görev değişmezliğini gösterdi.
* `TEAMS_TENANT_ID`, `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET` ortam değişkenleri tanımlı değil. Bu nedenle canlı Entra tokenı, Teams erişimi ve ayrı test görevi kabul testi yapılmadı. Sol T4 kod denetimi ONAY'ı ve kullanıcı kararıyla `v0.2.0` etiketi oluşturuldu; canlı Teams kabulü ayrı bir işletim adımı olarak beklemededir.
