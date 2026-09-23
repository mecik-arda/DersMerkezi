# Sol Kod Denetimi — 0.2.0 T0

Tarih: 2026-09-23
Kapsam: Yalnız T0 ayar dilimi; salt-okunur GPT-6 Sol denetimleri
Sonuç: **SONUC: ONAY**

## Tur 1

Sonuç: BULGULAR.

* Yüksek — `merkez/indirici.py` Teams guard'ı seçili kontrolünden sonra çalıştığından, seçili olmayan Teams dersi `atlanan=1` ve exit 0 ile sonuçlanabiliyordu. Guard ders kaydı bulunur bulunmaz, seçim ve dosya hazırlığı öncesine alındı. T0 paketi seçili olmayan Teams dersi için de exit 1'i doğruluyor.
* Düşük — `--listele` ve `--durum` insan çıktılarında kaynak/redakte özet gösterilmiyordu. Teams'e özgü `teams.ozet` görünümü üç insan-okur liste komutuna eklendi; GitHub insan çıktısı korunuyor. Kurulum belgesi bu davranışla eşitlendi.

## Tur 2

Sonuç: BULGULAR.

* Orta — `--saglik --ag` veya Teams dersi için ağ sağlık denetimi `depo` alanı bekleyip `KeyError` üretebilirdi. `merkez/saglik.py`, T0 süresince Teams için ağ isteği yapmadan T3'te gerçek sağlık yoklamasının geleceğini belirten uyarı üretir; GitHub ağ denetimi ve token kontrolü yalnız GitHub kayıtlarında sürer. T0 testleri toplu ağ denetiminde Teams için depo çağrısı olmadığını ve CLI Teams sağlık görünümünün çökmeden tamamlandığını doğrular.

## Tur 3

Sonuç: BULGULAR.

* Düşük — GitHub kaydında `teams: null` ve Teams kaydında `zayif_dogrulama: null` yasak alanlar/yanlış tipler olarak reddedilmiyordu. `merkez/ayarlar.py` artık anahtarın varlığını ve mantıksal tipini denetliyor; T0 paketi iki durumu da kapsıyor.
* Düşük — `--ekle` yardım metni depo zorunluymuş izlenimi veriyordu. `merkez/komut.py` açıklaması, ders kaynağına uygun bilgilerin gerekli olduğunu belirtecek şekilde düzeltildi; yardım yüzeyi testi eklendi.

## Son Tur

Sol; eski ve yeni bulguların kapatıldığını, T0 kapsamını engelleyen veya yeni bulgu bulunmadığını doğruladı ve **SONUC: ONAY** verdi.

Denetimde doğrulanan noktalar:

* `SURUM=1`; `kaynak` alanı olmayan GitHub kaydı geçerli ve görünüm/JSON davranışı additive.
* Teams kimliklerinde güvenli karakter kümesi ve uzunluk sınırları var; redakte özetler tam kimlikleri ve son karakteri açığa çıkarmıyor; hata metinleri tam kimlik içermiyor.
* CLI kaynak/bayrak matrisi ve geçersiz birleşimlerin mutasyondan önce reddi; zayıf doğrulamanın yalnız Teams kaydında kabulü.
* T0 Teams indirme koruması seçili olmayan ve kuru çağrılar dâhil önce çalışıyor; T2'de kaldırma ve test güncellemesi planda izleniyor.
* Sağlık denetimi T0 Teams kayıtlarında kontrollü T3 uyarısı veriyor; TUI işleyişi, mutex/atomik yazım deseni ve görev eylemi kodu korunuyor.

Canlı üretim görevinin durumu Sol'un salt-okunur görev sorgusunda erişim hatası nedeniyle yeniden teyit edilemedi. Uygulama doğrulama kapısı ve E2E paketi görev durumunu `Ready` olarak ve üretim görevi değişmezliğini başarılı doğruladı; görev eylemi dosyalarında değişiklik yok.
