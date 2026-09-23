# Sol Kod Denetimi — 0.2.0 T4

Tarih: 2026-09-23
Kapsam: T0–T4 Teams/SharePoint kaynağı; salt-okunur GPT-6 Sol kod denetimi
Sonuç: **SONUC: ONAY**

## İlk T4 Denetimi

Sonuç: BULGULAR.

* Orta — `file.hashes` içindeki yanlış tür/boş değerler hash yokmuş gibi ele alınabiliyor ve açık zayıf doğrulamaya düşebiliyordu. `None`/eksik değer ile var ama geçersiz değer ayrıldı; boş `quickXorHash` veya `sha1Hash` doğrulama hatası veriyor, weak yola düşmüyor.
* Düşük — HTTP tarih biçimli `Retry-After` yerel saat diliminde yorumlanıyordu. RFC HTTP tarih ayrıştırması UTC/zaman dilimi farkındalığıyla değiştirildi.

## Düzeltme Sonrası Son Tur

Sonuç: **SONUC: ONAY**.

* Metadata isteği planlanan `$select=id,eTag,size,file` ile sınırlıdır; dönüşüm artık Graph yanıtında `name` bulunmasını gerektirmez. Seçilen alanlara uygun sahte yanıtla test edildi.
* Graph yönlendirme sayısı, her URL için ayrı sınırlı tekrar bütçesiyle yönetilir. `302 → 302 → 503 → 200` senaryosu ve yönlendirme bütçesi test edildi.
* Önceki hash ve UTC Retry-After bulguları kapalı olarak yeniden doğrulandı.
* Graph/ön kimlikli URL köken-yol/host denetimleri, Authorization ayrımı, sayfalama/boyut sınırları, hash bütünlüğü, weak eTag pre/post, yerel SHA-256, `.part` atomik taşıma, GitHub geriye uyumu, TUI/JSON/sağlık eşliği ve görev eylemi kodu için ek blocker saptanmadı.

## Test Kanıtı ve Operasyonel Sınır

* Geçici kopya: regresyon 422/422; T0 199/199; T1 Graph/QuickXor 218/218; T2 sahte Graph adaptörü 39/39. Trace summary raporlanan uygulama modüllerinde %100 gösterdi.
* Gerçek proje: derleme exit 0; GitHub çekme `atlanan=2`, exit 0; durum `Ready`; sürüm `0.2.0`; ayarlar ve ağsız sağlık JSON'u geçerli.
* Sol'un kendi salt-okunur Görev Zamanlayıcı sorgusu bu ortamda doğrulanamadı. Uygulama gerçek kapısı ve E2E üretim görevi kontrolü `Ready` durumunu ve üretim görevi değişmezliğini başarılı doğruladı; görev eylem dosyalarında değişiklik yok.
* `TEAMS_TENANT_ID`, `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET` ortam değişkenleri tanımlı değil. Bu nedenle canlı Entra tokenı, Teams erişimi ve test görevi kabul testi yapılamadı. Bu kod bulgusu değil, kullanıcı işletim adımıdır; gerçek Teams kabulinden önce `v0.2.0` etiketi oluşturulmamalıdır.
