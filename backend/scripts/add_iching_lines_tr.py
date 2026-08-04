"""384 yao (çizgi) pasajının Türkçe Rytho aktarımı (Revize İ1).

Kamu malı bir Türkçe I Ching çevirisi YOK; Wilhelm/Özşahin ve Huang
telifli. Bu dosya birebir çeviri değil, kamu malı Legge (1899) metni ve
klasik doktrin okunarak Rytho Türkçesiyle yazılmış AKTARIMDIR — imge
(ejderha, kırağı, kuyu) ve hüküm (talih/sakınca) korunur, cümle
aktarılmaz. Tetrabiblos TR aktarımıyla aynı disiplin; künye
knowledge/SOURCES.md'de. Telif RythoAI'ye aittir.

Sözlük biçimi bilinçli (add_iching_en.py deseni): içerik diff'te satır
satır gözden geçirilebilir kalır.

Kullanım: backend dizininden
    .venv/Scripts/python.exe scripts/add_iching_lines_tr.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_FILE = (Path(__file__).resolve().parent.parent
             / "data" / "hexagrams.json")

#: Heksagram no -> alttan üste 6 çizgi aktarımı.
CIZGILER: dict[int, list[str]] = {
    1: [
        "Ejderha derinde gizli yatar; eyleme geçmenin vakti değildir.",
        "Ejderha tarlada görünür; büyük insanla görüşmek kazanç getirir.",
        "Soylu insan gün boyu uyanık çalışır, akşam yine tetiktedir; tehlike vardır ama kusur yoktur.",
        "Ejderha sıçramayı dener, hâlâ derinliğin üstündedir; ilerlese de kusur olmaz.",
        "Ejderha gökte kanat açar; büyük insanla görüşmek kazanç getirir.",
        "Haddini aşan ejderha pişman olur; doruğun ötesi düşüştür.",
    ],
    2: [
        "Kırağıya basan ayak bilir: katı buz yakındır — küçük işaret büyük gidişi haber verir.",
        "Doğru, kare ve geniş ol; çaba gösterişsizken bile hiçbir şey kazançsız kalmaz.",
        "Yeteneğini örtük tut; devlet işine girsen de başarıyı sahiplenme, tamamlamakla yetin.",
        "Ağzı bağlanmış çuval gibi ol: ne övgü gelir ne suçlama — temkin kusuru önler.",
        "Sarı alt giysi gibi ölçülü asalet: en yüksek talih ortada durmasını bilendedir.",
        "Ejderhalar kırda savaşır, kanları mor ve sarı akar; yin haddini aşarsa çatışma doğar.",
    ],
    3: [
        "İlk adımda engel var: kayayı çevirip yerinde sağlam dur; doğru kalmak ve destek bulmak kazançlıdır.",
        "Atlar koşulur, sonra geri döner; zorla istenmez — kız on yıl bekler, sonra evlenir. Olgunlaşmamış bağa acele edilmez.",
        "Kılavuzsuz geyik kovalayan ormanda kaybolur; soylu insan vazgeçmeyi bilir, ısrar utanç getirir.",
        "Atlar koşulmuş bekler: ittifak arayışına gitmek doğrudur; ilerlemek talih getirir, kusur olmaz.",
        "Nimetini biriktirmek zorlaşır: küçükte doğruluk talih, büyükte zorlamak felaket getirir.",
        "Atlar koşulmuş ama yol yok; kan ve gözyaşı akar — çıkışsız ısrarın resmi budur.",
    ],
    4: [
        "Tomurcuğu açmak için disiplin gerekir; ceza yalnız yolu göstermek içindir, zincire dönüşürse utanç doğar.",
        "Toyluğu hoşgörüyle kucaklayan talihlidir; eve gelin almak hayırlıdır — oğul ocağı taşıyabilir.",
        "Altın gören kadını alma: kendini kaybedene bağlanmak hiçbir yerde kazanç bırakmaz.",
        "Toyluğun içine hapsolmak utançtır; gerçeklikten kopan öğrenci yalnız kalır.",
        "Saf ve alçakgönüllü toyluk talih getirir; öğrenmeye açık çocuk yolu bulur.",
        "Toyluğu cezalandırırken saldırgan olma; taşkını savuşturmak yeter — amaç kırmak değil korumaktır.",
    ],
    5: [
        "Kırda beklemek: sabrı bozmadan olağan işinde kal; kusur doğmaz.",
        "Kumsalda beklemek: küçük söylentiler çıkar ama sonu talihlidir.",
        "Çamurda beklemek düşmanı davet eder; dikkat yaralanmayı önler.",
        "Kan içinde beklemek: çukurdan çık — teslimiyet değil, yerini değiştirme vaktidir.",
        "Şarap ve yemekle beklemek: güç toplama molası da doğruluğun parçasıdır, talih getirir.",
        "Çukura düşülür; çağrılmamış üç konuk gelir — onları ağırlamasını bilen sonunda talihi bulur.",
    ],
    6: [
        "Davayı uzatma; küçük söz işitilir ama sonu talihe döner.",
        "Çekişmeyi kaldıramayacaksan geri çekil ve gizlen; kasabanın üç yüz hanesi böylece beladan kurtulur.",
        "Eski hakkınla geçin, doğru kal; tehlike sonunda talihe döner. Devlet işine girsen de başarıyı sahiplenme.",
        "Çekişmeye gücün yetmez; kadere dön, tavrını değiştir, doğrulukta huzur bul — talih gelir.",
        "Çekişmeyi büyük insanın önünde çözmek: en yüksek talih adil hakemdedir.",
        "Çekişmeyle kazanılan kemer sabah verilir, akşam üç kez geri alınır — dava ile gelen onur eğreti durur.",
    ],
    7: [
        "Ordu düzenle çıkar; düzen bozulursa zafer bile felakete döner.",
        "Komutan ordunun ortasında durur: talih ondadır, kusur doğmaz; hükümdar üç kez onur bahşeder.",
        "Ordu araba dolusu ceset taşır — ehil olmayana komuta vermenin sonu budur.",
        "Ordu geri çekilip konaklar; yenilgi değil, ölçülü manevradır — kusur yoktur.",
        "Tarlada av varsa yakalamak doğrudur; ama büyük oğul orduyu yönetirken küçüğe bırakılırsa cesetler taşınır.",
        "Zafer sonrası büyük hükümdar devletler kurar, aileler onurlandırır; küçük insana yetki verilmez.",
    ],
    8: [
        "İçtenlikle bağlan: toprak testi kadar sade bir samimiyet bile sonunda beklenmedik talih çeker.",
        "Birliğe içten, kendi merkezinden katıl; doğruluk talih getirir.",
        "Bağlanılmaması gerekenlerle birlik aramak — kayıp buradan başlar.",
        "Dışarıdakiyle de birlik kurulur; ehline bağlanmak doğrudur, talih getirir.",
        "Birliğin en parlak hali: kral avda üç yandan kuşatır, önden kaçana dokunmaz — gönüllü bağlılık zorla gelmez.",
        "Başsız birlik: ilk adımı atacak öncü yoksa sonu kötüdür.",
    ],
    9: [
        "Kendi yoluna geri dönmek: bunda ne kusur var ne engel — dönüş talihlidir.",
        "El birliğiyle dönüş: ortak istikamet talih getirir.",
        "Arabanın jant teli fırlar; karı koca birbirine ters bakar — küçük engel içeride gerilim doğurur.",
        "İçtenlik kanı uzaklaştırır, korkuyu dağıtır; kusur doğmaz.",
        "İçtenlik bağ kurar: komşusuyla zenginliğini paylaşan yalnız kalmaz.",
        "Yağmur yağdı, duruldu; erdem yüklü araba doldu. Küçüğün doruğunda ısrar kadını da soyluyu da tehlikeye sokar — ay dolunaya vardı, ileri gitme.",
    ],
    10: [
        "Sade ayakla yürü: gösterişsiz ilerleyen kusursuz gider.",
        "Düz ve sakin yolda yürüyen münzevi, doğruluğunda talihlidir.",
        "Tek gözlü görürüm der, topal yürürüm der; kaplanın kuyruğuna basar, ısırılır — gücünü aşan iddia savaşçıyı bile düşürür.",
        "Kaplanın kuyruğuna basar ama çekinerek, dikkatle; sonunda talih gelir.",
        "Kararlı yürüyüş: doğru olsa da tetikte ol — güvenli görünen adım da tehlike taşır.",
        "Yürüdüğün yola dön, işaretleri tart; devir tamamlanmışsa en yüksek talih gelir.",
    ],
    11: [
        "Ot sökülünce kökleri birlikte gelir: ehil biri yükselince benzerlerini de taşır — ilerleyiş talihlidir.",
        "Kaba olanı taşı, nehri sandalsız geç, uzağı unutma, hizbi bırak: ortada yürüyenin ödülü budur.",
        "Düzlük yok ki yokuşu olmasın, gidiş yok ki dönüşü olmasın; zorlukta doğru kalana kusur yazılmaz.",
        "Kanat çırpıp iner, zenginliğine yaslanmaz; komşusuyla içtenlikle bağ kurar.",
        "Hükümdar kız kardeşini gelin verir: alçalan yücelik en büyük talihi getirir.",
        "Sur hendeğe devrilir; ordu kullanma vakti değildir — emir kendi şehrinde duyurulur, ısrar utanç getirir.",
    ],
    12: [
        "Ot sökülünce kökleri birlikte gelir: tıkanıklık çağında doğrularla birlikte çekilmek talihtir.",
        "Küçük insan taşıyıp katlanır; büyük insan tıkanıklıkta bile ilkesinden ödün vermez — başarı budur.",
        "Utancı sırtında taşır: ehliyetsiz makam er geç yüz kızartır.",
        "Yukarının çağrısıyla davranan kusursuzdur; aynı tarlayı sürenler nimeti paylaşır.",
        "Tıkanıklık duruyor ama büyük insan tetikte: 'ya kopup düşerse' diye dut ağacının sürgünlerine bağlar.",
        "Tıkanıklık devrilir: önce kapanma, sonra sevinç — hiçbir kapanış sonsuz değildir.",
    ],
    13: [
        "Kapının hemen dışında dostluk: açık başlangıçta kusur olmaz.",
        "Yalnız kendi soyuyla dostluk kuran dar kalır; hizip utanç getirir.",
        "Pusuya silah gizler, tepeden gözetler; üç yıl kımıldayamaz — gizli niyet dostluğu dondurur.",
        "Surun üstüne çıkar ama saldırmaz; dönüşü talihe çevirir.",
        "Dostlar önce ağlar, sonra güler: büyük ordular buluşunca ayrılık biter.",
        "Kır açıklığında dostluk: yakınlık idealin gerisinde kalsa da pişmanlık doğmaz.",
    ],
    14: [
        "Zararlıyla teması olmayan zenginlik: başlangıçtaki temkin kusuru önler; zorluğu bilen hazırlıklı olur.",
        "Büyük araba yük taşır; nereye gidilse gidilsin kusur doğmaz — kapasite sorumluluğu karşılar.",
        "Prens hazinesini Göğün Oğlu'na sunar; küçük insan bunu beceremez — bolluk paylaşanın elinde büyür.",
        "Gücünü şişirmeden taşıyan komşusunu gölgelemez; kusur doğmaz.",
        "İçten ve vakur bağlılık: samimiyet saygıyla birleşince talih gelir.",
        "Gök yardım eder: bolluğun doruğunda bile alçakgönüllü kalan her yönden kazançlıdır.",
    ],
    15: [
        "Alçakgönüllünün alçakgönüllüsü soylu insan: büyük nehri bile böyle geçer, talihle.",
        "Alçakgönüllülük sese vurur: içtenlik duyulunca doğruluk talih getirir.",
        "Emeğiyle yükselen ama övünmeyen soylu insan işini sonuna taşır; talih ondadır.",
        "Alçakgönüllülüğü her hareketine sindir: hiçbir yönde kazançsız kalmaz.",
        "Zenginliğe yaslanmadan komşusunu yanına alır; gerekirse kararlı harekât da alçakgönüllülüğe sığar.",
        "Alçakgönüllülük sese vurmuşken ordu yürütülür — ama yalnız kendi şehrini düzeltmek için.",
    ],
    16: [
        "Coşkusunu ilan eden tükenir: gösterişli sevinç felaket çağırır.",
        "Kaya gibi sağlam duran, günü dolmadan işareti okur; doğruluğu talih getirir.",
        "Yukarı bakıp coşku bekleyen pişman olur; gecikmiş dönüş de pişmanlıktır.",
        "Coşkunun kaynağı olan büyük işler başarır; kuşkulanma — dostlar saç tokasının topladığı saç gibi çevrene toplanır.",
        "Süreğen bir dert: sıkıntı taşır ama öldürmez — coşku çağında hasta olan ayakta kalır.",
        "Karanlığa dönmüş coşku: tamamlanmışsa bile tavrını değiştirene kusur yazılmaz.",
    ],
}

CIZGILER.update({
    17: [
        "Görev değişir: kapından çık, karışık toplulukta bile ilkeli kal — çaba boşa gitmez.",
        "Küçük çocuğa bağlanan güçlü adamı kaybeder; iki bağ birden tutulmaz.",
        "Güçlü adama bağlanan çocuğu bırakır; aradığını bulur — doğrulukta kalmak yine de şarttır.",
        "İzleyenler artar, kazanç büyür; ama doğruluktan saparsan talih bile uğursuzlaşır. İçtenlik yolu aydın tutar.",
        "İyiye içtenlikle bağlılık: talih ondadır.",
        "Bağlılık zorla mühürlenir, iple sarılır; kral Batı Dağı'nda kurban sunar — bağın doruğu adanmışlıktır.",
    ],
    18: [
        "Babanın bozduğunu evlat onarır: ehil oğul varsa geçmişin kusuru silinir; tehlike sonunda talihe döner.",
        "Ananın bozduğunu onarırken katı olma; ölçülü doğruluk yeter.",
        "Babanın bozduğunu onarırken küçük pişmanlıklar olur ama büyük kusur doğmaz.",
        "Bozulmayı hoş görüp uzatan, ilerledikçe utanç bulur.",
        "Babanın bozduğunu onarmak övgüyle taçlanır: geçmişi düzelten ad kazanır.",
        "Krala da prense de hizmet etmez; kendi işini yüceltir — onarımın en yüksek hali kendi düzenini kurmaktır.",
    ],
    19: [
        "Ortak yaklaşım: doğrulukla yaklaşan talihlidir.",
        "Ortak yaklaşım talih getirir; hiçbir yönde kazançsız kalmaz.",
        "Tatlı dille yaklaşmak kazanç getirmez; ama yanlışı dert edinen kusurdan kurtulur.",
        "Tam yerinde, kusursuz bir yaklaşım: konum ehline denk düşer.",
        "Bilgece yaklaşım: büyük hükümdara yakışan, işi ehline bırakmaktır — talih ondadır.",
        "Cömert ve içten yaklaşım: talih getirir, kusur bırakmaz.",
    ],
    20: [
        "Çocuğun bakışı: küçük insana yakışır, soylu insana utançtır — yüzeysel bakış dar kalır.",
        "Kapı aralığından gözetleme: kadına yeterli sayılır ama geniş iş görmeye yetmez.",
        "Kendi hayatına bakıp ilerlemeye ya da çekilmeye karar vermek: dönüm noktası öz-bakıştan geçer.",
        "Ülkenin ışığına bakmak: hükümdara konuk olmak kazançlıdır — parlaklığı yerinde incele.",
        "Kendi hayatına bak: soylu insanın öz-denetimi kusuru önler.",
        "Başkaları onun hayatına bakar: örnek olana kusur yazılmaz — bakılan da sorumluluk taşır.",
    ],
    21: [
        "Ayakları tomruğa vurulur, parmakları kaybolur; küçük cezanın erken gelmesi büyük suçu önler.",
        "Yumuşak eti ısırırken burnu batırır: ceza kolay hedefte aşırıya kaçar ama kusur büyük değildir.",
        "Kurutulmuş et ısırırken zehre rastlar: eski hesap küçük utanç doğurur, kusur büyümez.",
        "Kemikli kuru eti ısırır, altın ok bulur: zorlukta doğru kalmak ödülü çıkarır.",
        "Kuru eti ısırır, sarı altın bulur: tehlikeyi bilerek doğru kalan kusursuz çıkar.",
        "Boyunduruk kulakları örter: uyarıyı duymayan sonunda kendini kaybeder.",
    ],
    22: [
        "Ayaklarını süsler, arabayı bırakıp yürür: gösterişten önce kendi adımı.",
        "Sakalını süsler: süs ancak taşıyanla birlikte hareket ederse anlam kazanır.",
        "Süslü ve parlak: sürekli doğruluk talihi korur — cila kalıcılık değildir.",
        "Süs mü sadelik mi? Beyaz atlı gelen yağmacı değil dünürdür; kuşku yersizdir.",
        "Tepedeki bahçede süs: hediyesi küçücük görünse de sonunda talih gelir — öz, kumaştan değerlidir.",
        "Beyaz süs: süssüzlük en yüksek süstür, kusur bırakmaz.",
    ],
    23: [
        "Yatağın ayağı soyulur: çürüme alttan başlar — doğruyu görmezden gelmek felakettir.",
        "Yatağın gövdesi soyulur: destek kalmadan ısrar, ayrım gözetmeyen kayıptır.",
        "Soyulanların arasında tek başına bağ kurar: çevresine rağmen doğruya bağlanan kusurdan kurtulur.",
        "Yatak deriye dayandı: zarar tene ulaştı — felaket artık yakındır.",
        "Balık dizisi gibi sıraya girer, saray kadınlarıyla lütuf taşır: teslimiyet düzene dönüşürse her şey kazanca döner.",
        "En büyük meyve yenmeden kalır: soylu insan arabayı alır, küçük insan kulübesini de soyar — çöküşte tohum saklıdır.",
    ],
    24: [
        "Yoldan uzaklaşmadan dönüş: pişmanlığa varmadan dönen en yüksek talihi bulur.",
        "Güzel bir dönüş: iyiye boyun eğerek dönmek talihlidir.",
        "Tekrar tekrar dönüş: tehlikelidir ama kusur yazılmaz — bocalama da yolun parçasıdır.",
        "Ortada yürürken tek başına dönüş: kalabalık ortasında yolunu bilen döner.",
        "Soylu bir dönüş: kendini sınayarak dönen pişmanlık bırakmaz.",
        "Şaşkın dönüş: yolu kaybetmiş dönüş felaket getirir; orduyla çıkılırsa hükümdar bile yenilir, on yıl toparlanamaz.",
    ],
    25: [
        "Yalın içtenlikle ilerle: hesapsız doğruluk talih getirir.",
        "Tarlayı sürerken hasadı hesaplama, üçüncü yılın verimini bekleme; o zaman ilerlemek kazançlıdır.",
        "Beklenmedik bela: bağlı inek yolcunun eline geçer, kasabalı suçlanır — kusursuz da kayba uğrayabilir.",
        "Doğru kalabilen kusurdan uzak durur.",
        "Beklenmedik hastalığa ilaç arama; kendi seyrinde geçer — müdahale bazen zehirdir.",
        "İçtenlik bile vakitsizce harekete dönerse felaket getirir; ilerlemenin yararı yoktur.",
    ],
    26: [
        "Tehlike var: durmasını bil — zapt edilen güç erken harcanmaz.",
        "Arabanın dingil bağları çözülür: ilerleyemezsin ama bu durak birikimdir.",
        "İyi atlar kovalar: zorluğu bilerek günlük talimle savunmayı öğren; o zaman ilerlemek kazançlıdır.",
        "Genç boğanın boynuzuna tahta vurulur: gücü zapt etmenin en erken hali en talihlisidir.",
        "İğdiş edilmiş domuzun dişi: saldırganlığı kaynağında dönüştürmek talih getirir.",
        "Göğün geniş yolu açılır: zapt edilen güç vakti gelince engelsiz akar.",
    ],
    27: [
        "Kendi kaplumbağanı bırakıp benim lokmama bakıyorsun: gıptayla beslenen aç kalır.",
        "Tepeden beslenme bekleyip yoldan sapan, ilerledikçe felaket bulur.",
        "Beslenme düzenine aykırı davranan on yıl kımıldayamaz; hiçbir yönde kazanç yoktur.",
        "Tepeden beslenmek burada talihlidir: kaplan gibi sabit ve aç bakan, ehil desteği çekmekte kusursuzdur.",
        "Düzenden sapmış olsa da doğrulukta sebat eden talihi bulur; ama büyük nehri geçmeye kalkmasın.",
        "Beslenmenin kaynağı olmak: sorumluluğun bilincinde olana tehlike bile talihe döner; büyük nehir geçilir.",
    ],
    28: [
        "Altına beyaz hasır sermek: aşırı yükte bile özenli temkin kusur bırakmaz.",
        "Kuru söğüt filiz verir, yaşlı adam genç eş alır: tükenmiş görünende yenilenme saklıdır.",
        "Kiriş ortasından çöker: taşınamayan yükte ısrar felakettir.",
        "Kiriş yukarı kavis alır: destek gelince yük taşınır; ama desteğe hesap karışırsa utanç doğar.",
        "Kuru söğüt çiçek açar, yaşlı kadın genç koca alır: ne suç ne övgü — meyvesiz gösteriş.",
        "Suyu geçerken sular başını aşar: fedakârlık felakete varsa da adanmışlığa kusur yazılmaz.",
    ],
    29: [
        "Çukurun içinde çukura düşmek: tehlikeye alışmak en derin kayıptır.",
        "Çukurda tehlike içinde küçük kazanımla yetin; büyük çıkışı zorlama.",
        "Her adım çukur: çıkış görünmüyorsa kımıldama — çırpınmak derinleştirir.",
        "Bir testi şarap, iki kap yemek, pencereden uzatılan sade sunu: darlıkta içtenlik töreni aşar; sonunda kusur kalmaz.",
        "Çukur ağzına kadar dolmaz, su düzlüğü bulunca durulur: taşmadan dolan kusursuz çıkar.",
        "İple bağlanmış, dikenler arasına kapatılmış: üç yıl yolu bulamaz — tehlikede yön kaybının bedeli budur.",
    ],
    30: [
        "Adımlar karışık ama saygı yerinde: dikkatli başlangıç kusuru önler.",
        "Sarı ışık: ölçülü parlaklık en yüksek talihtir.",
        "Batan günün ışığında testi çalıp şarkı söylemeyen, yaşlılığına ağıt yakar: geçen vakte direnmek felakettir.",
        "Ansızın parlayıp alev gibi sönen: yanışı da terk edilişi de ani olur.",
        "Gözyaşı sel, keder derin — ama tam da bu yas dönüşü getirir: talih.",
        "Kral sefere çıkar: elebaşılar alınır, sürüklenenler bağışlanır — ayrım gözeten sertlik kusursuzdur.",
    ],
    31: [
        "Etki ayak başparmağında: niyet var, adım yok — henüz kimse kımıldamaz.",
        "Etki baldırda: erken davranış felaket, yerinde bekleyiş talihtir.",
        "Etki kalçada: peşinden gitmeye ayarlı olmak utanç getirir — ilerleyiş kendi kararın olmalı.",
        "Kararlı doğruluk pişmanlığı siler; ama dur durak bilmeyen gel-gitli düşünceye yalnız yakın dostlar uyar.",
        "Etki sırtta: iradenin dışında kalan yüzeysel etki pişmanlık bırakmaz.",
        "Etki çenede ve dilde: yalnız söze dökülen etki en sığ olandır.",
    ],
    32: [
        "Süreklilik en başta derinlik ister: hemen kök isteyen ısrar felakettir.",
        "Pişmanlık kaybolur: gücü konumunu aşanın dengeyi ortada bulmasıyla.",
        "Erdemine süreklilik veremeyen utanç taşır; nereye varsa aynı sonuç.",
        "Avlanılacak av olmayan tarlada beklemek: yanlış yerde süreklilik kazandırmaz.",
        "Erdemi sürekli kılmak: kadına talih olan uysallık, erkeğe kural olursa felakettir — süreklilik role göre değişir.",
        "Sürekliliği sarsıntıda aramak: yerinde duramayan hep kaybeder.",
    ],
})

CIZGILER.update({
    33: [
        "Geri çekilişte kuyrukta kalmak tehlikelidir; hiçbir girişime kalkışma.",
        "Sarı öküz derisinden kayışla bağlanır: kararlı bağlılığı kimse çözemez.",
        "Bağlarla dolanmış çekiliş sıkıntılı ve tehlikelidir; hizmetkâr ve cariye beslemekte talih var — büyük iş bekleme.",
        "Sevdiklerine rağmen çekilmesini bilen soylu insan talihi bulur; küçük insan bunu beceremez.",
        "Takdire yaraşır bir çekiliş: yerinde ayrılış doğrulukla taçlanır.",
        "Zenginleşmiş, ferah bir çekiliş: gönül rahatlığıyla ayrılan her yönden kazançlıdır.",
    ],
    34: [
        "Güç ayak parmaklarında: en alttan zorlayan ilerleyiş felaket getirir.",
        "Doğrulukta kalan güç talih getirir.",
        "Küçük insan gücünü kullanır, soylu insan kullanmaz; koç çite toslar, boynuzları takılır — gösterilen güç tuzağa dönüşür.",
        "Doğru kalınca pişmanlık kaybolur: çit açılır, boynuz kurtulur; güç büyük arabanın dingiline vurur.",
        "Koçunu kolaylıkla kaybeder: yumuşak alanda güce gerek kalmayınca pişmanlık da kalmaz.",
        "Koç çite toslar: ne geri gider ne ilerler — zorluğu görüp durmasını bilen sonunda talihi bulur.",
    ],
    35: [
        "İlerlerken geri itilir: doğru kal; güven gelmese de geniş yürekli sükûnet kusuru önler.",
        "İlerleyiş hüzünlü ama doğruluk talih getirir; büyük ana-atadan gelen nimet kuşağı bulur.",
        "Herkes onaylar: ortak güven pişmanlığı siler.",
        "Sıçan gibi ilerlemek: gizli-saklı ilerleyiş tehlikelidir.",
        "Pişmanlık kaybolur: kayıp-kazanç hesabını bırak — ilerleyiş kendisi kazançtır.",
        "Boynuzlarla ilerlemek yalnız kendi şehrini düzeltmeye yarar: sertlik doğru olsa da dar alanda utanç payı taşır.",
    ],
    36: [
        "Yaralı ışık uçarken kanadını indirir; soylu insan üç gün aç yürür — gidecek yeri vardır, ev sahibi söylenir.",
        "Sol kalçadan yaralanır ama güçlü atla kurtulur: talih yardımcının gücündedir.",
        "Güneyde avda elebaşını yakalar; hemen düzeltmeye kalkma — karanlık çağın hastalığı acele kaldırılmaz.",
        "Sol karna girer, karanlık yönetimin kalbine ulaşır ve kapıdan avluya çıkar: içyüzünü gören terk eder.",
        "Prens Çi'nin duruşu: karanlıkta aklını gizleyen, doğruluğunu kaybetmez.",
        "Önce göğe yükselen, sonra yere gömülen karanlık: aydınlığı yutan sonunda kendi kuralını da yutar.",
    ],
    37: [
        "Evin içinde kurallı düzen: baştan konan sınır pişmanlığı siler.",
        "Kendi başına iş kovalamaz, içeride yemeği düzenler: görünmez emek evin dengesidir — doğruluk talih getirir.",
        "Ev halkı sertçe azarlanır: aşırılık pişmanlık doğursa da talih kalır; kadın ve çocuk kahkahaya boğulursa sonu utançtır.",
        "Evi zenginleştiren: bereketin ölçüsü büyük talihtir.",
        "Kral gibi evine yaklaşan: korku salmadan sevgiyle yönetmek talih getirir.",
        "İçtenlik ve vakar: sonunda talih, ev düzeninin son sözüdür.",
    ],
    38: [
        "Pişmanlık kaybolur: kaçan atı kovalama, kendi döner; kötü insanı görmek de kusur değildir — ayrılıkta soğukkanlılık.",
        "Efendisiyle dar sokakta karşılaşır: ters düşmüş yollar yan geçitte buluşur, kusur doğmaz.",
        "Arabası geri çekilir, öküzü durdurulur, saçı kesilir burnu yaralanır: kötü başlangıcın iyi sonu vardır.",
        "Ayrılık içinde yalnız kalan, ilk hâliyle içten buluşur: tehlike içinde bile kusur kalmaz.",
        "Pişmanlık kaybolur: akraba deriyi ısırır gibi içten kenetlenir; ilerleyişin nesi kusur olsun?",
        "Yalnız gezgin domuzu çamurda, arabayı hayalet dolusu görür; önce yayını gerer, sonra indirir — yağmacı değil dünürdür. Yağmur yağar, talih gelir.",
    ],
    39: [
        "İlerlemek zorluğa, durmak övgüye götürür: engel çağında bekleyiş erdemdir.",
        "Kralın hizmetkârı zorluk üstüne zorlukla boğuşur; kendi çıkarı için değil — kusur yazılmaz.",
        "İlerlemek zorluğa götürür; geri dönen sevinçle karşılanır.",
        "İlerlemek zorluğa, durmak dayanışmaya götürür: bekle ve bağ kur.",
        "En büyük zorlukta dostlar gelir: direnenin yardımı yolda olur.",
        "İlerlemek zorluğa, dönmek büyümeye götürür: büyük insanı görmek kazançtır — engelin sonunda rehber vardır.",
    ],
    40: [
        "Kurtuluşun başında söz gerekmez: kusursuz sükûnet yeter.",
        "Avda üç tilki vurulur, sarı ok bulunur: gizli fesat temizlenince doğruluk talih getirir.",
        "Yük taşıyan hamal arabaya kurulursa yağmacıyı davet eder: hak edilmemiş konum saldırı çeker; ısrar utançtır.",
        "Ayak başparmağından kurtul: uygunsuz bağlar çözülünce güvenilir dost gelir.",
        "Soylu insan bağını kendi çözer: kurtuluş içeriden gelirse küçük insanlar da çekilir.",
        "Prens yüksek surun tepesindeki şahini vurur: olgunlaşmış hamle her engeli düşürür.",
    ],
    41: [
        "İşini bitirip hızla gitmek kusursuzdur; ama vereceğini de tartarak azalt.",
        "Kendini eksiltmeden başkasını artır: doğruluk kazanır, vakitsiz hamle kaybettirir.",
        "Üç kişi yürürse biri eksilir; bir kişi yürürse dostunu bulur — azalış sadeleşince bağ netleşir.",
        "Hastalığını azaltan hızla sevince kavuşur; kusur doğmaz.",
        "On çift kaplumbağa kabuğu bile onun talihini çeviremez: artışı gök onaylamıştır.",
        "Eksiltmeden artırmak: kusursuz doğrulukla her ilerleyiş kazançlı olur; hizmetkâr değil, ev halkı kazanılır.",
    ],
    42: [
        "Büyük işlere girişmenin tam vakti: artış çağında cömert hamle en yüksek talihtir.",
        "On çift kaplumbağa kabuğu karşı koyamaz: artışa açık olana kalıcı doğruluk talih getirir; kral Tanrı'ya sunağında bile bunu sunar.",
        "Artış felaket işlerinde bile işe koşulur: içtenlikle ortada yürüyene, mühürlü asayla prense çıkana kusur yazılmaz.",
        "Ortada yürü, prense danış: başkentin taşınması gibi büyük işte bile sözün dinlenir.",
        "İçten bir kalple herkese iyilik: sorgusuz talih — iyiliğin erdem sayıldığı yerde soru sorulmaz.",
        "Kimseye artış vermeyen, üstelik vurulan: kalbini sabitleyememiş olana felaket dışarıdan gelmez.",
    ],
    43: [
        "Ayak parmaklarında güçle ilerlemek: yetmeyen güçle atılan adım kusur getirir.",
        "Korku çığlığı gece yarısı da gelse hazırlıklı olan korkmaz.",
        "Yüzdeki kararlılık: tek başına yürüyen yağmura tutulur, ıslanır, söylenilir — ama kusur yazılmaz.",
        "Kalçada deri yok, yürüyüş güç: koyun gibi yedekte götürülse pişmanlık silinir; ama söz dinlenmez.",
        "Semizotu gibi kolay kopan fesat: ortada yürüyen kararlılıkla temizler, kusur kalmaz.",
        "Çığlık atacak kimse kalmaz: son direnç sessizce düşer — ama gevşeyen sonunda felaketi bulur.",
    ],
    44: [
        "Madeni frene bağla: zayıf olan serbest kalırsa domuz bile huysuzlanır — ilk temasda dizginle.",
        "Çantada balık var: konuklara sunulmaz — eldekini yaymamak kusuru önler.",
        "Kalçada deri yok, yürüyüş güç: tehlikeyi bilen büyük hataya düşmez.",
        "Çantada balık yok: halkından kopan, ayaklanmayı davet eder.",
        "Kabak yaprağıyla örtülü güzellik: içte tutulan parlaklık gökten düşer gibi kendiliğinden ortaya çıkar.",
        "Boynuzlarıyla karşılaşma: sona gelmiş temas sertleşir — utanç var, kusur yok.",
    ],
    45: [
        "İçtenlik sonuna kadar taşınmazsa topluluk dağılır; bir çağrıyla el birliği döner — gülüşe aldırma, ilerle.",
        "Kendiliğinden çekiliş talihlidir: içtenlik varsa küçük sunu bile kabul görür.",
        "Toplanmak isteyip iç çeken: yol görünmüyorsa küçük utançla ilerle — kusur değildir.",
        "Büyük toplanma: hükümdar adına toplayana kusur yazılmaz.",
        "Toplanmışların başında konum var ama güven eksik: kalıcı doğrulukla pişmanlık silinir.",
        "Ağıt ve gözyaşı: dışarıda kalanın yakınması — kusur değil, uyarıdır.",
    ],
    46: [
        "Güvenle yükseliş: yukarıdakiler kucak açar, büyük talih.",
        "İçtenlik varsa küçük sunu bile yeter: yaz kurbanı sadeliğiyle makbuldür.",
        "Boş şehre girer gibi yükselmek: dirençsiz ilerleyiş — ama boşluğun nedenini sor.",
        "Kral Çi Dağı'nda sunar: yükseliş töreni ehliyle taçlanır, kusur doğmaz.",
        "Adım adım yükseliş: doğrulukta basamakları tek tek çıkmak talihtir.",
        "Karanlıkta yükseliş: durmayan tırmanış ancak aralıksız doğrulukla zarar vermez — yine de tüketir.",
    ],
    47: [
        "Kütüğün altında sıkışan, karanlık vadiye çekilir; üç yıl görünmez — darlıkta çöküş derinleşir.",
        "Şarap ve yemek içinde bile darlık: kızıl kuşaklı gelir — sunu yap, ilerleme; kusur yazılmaz.",
        "Taşa takılıp dikene yaslanan, evine girer karısını bulamaz: yanlış dayanağın sonu yalnızlıktır.",
        "Altın arabayla yavaş gelir: utanç var ama iş sonuna erer.",
        "Burnu ve ayakları kesilmiş, kızıl kuşaklıların elinde darlık: sevinç yavaş gelir — sunu ve adakla bekle.",
        "Sarmaşık içinde, sallanan kayada darlık: 'kımıldarsam pişman olurum' deyip pişmanlığı göze alan, ilerleyince talihi bulur.",
    ],
    48: [
        "Çamurlu kuyudan kimse içmez; eski kuyuya kuş bile gelmez — bakımsız kaynak terk edilir.",
        "Kuyu ağzından balığa ok atılır, testi delik: kaynağı oyuncağa çeviren hiç dolduramaz.",
        "Kuyu temizlenmiş ama içen yok: yüreğimiz sızlar — ehil aranmıyor; kral aydın olsa herkes nimetlenirdi.",
        "Kuyunun içi taşla örülür: bakım süresince veremez ama sonrası kusursuzdur.",
        "Kuyuda berrak, soğuk pınar: kaynağın en saf hali içilmeyi bekler.",
        "Kuyu örtüsüz, herkese açık: tükenmez kaynak içtenlikle sunulursa en yüksek talih budur.",
    ],
})

CIZGILER.update({
    49: [
        "Sarı öküz derisiyle sarılıp sabitlenmek: değişimin ilk saatinde kıpırdamamak gerekir.",
        "Kendi günü gelince değiştir: vakitli devrim ilerleyişe talih, harekete kusursuzluk getirir.",
        "Aceleyle değiştirmek felaket, tehlikeli doğruluk şart: söz üç kez olgunlaşınca güven doğar.",
        "Pişmanlık kaybolur: içtenlikle buyruk değişince halk da inanır — talih.",
        "Büyük insan kaplan gibi değişir: falcıya sormadan bile deseni okunur — dönüşümün çizgileri parlar.",
        "Soylu insan pars gibi değişir, küçük insan yüzünü döner: köklü değişim doruğa varınca ısrar felaket, durmak talihtir.",
    ],
    50: [
        "Kazan ters çevrilir, tortusu dökülür: eski kiri boşaltmak için tersine dönüş bile hizmettir; cariye oğluyla el üstünde tutulur.",
        "Kazan dolu; hasetli ortak yaklaşamaz: nasibi olan doluluk kem gözden korunur — talih.",
        "Kazanın kulpları değişmiş, taşınamaz; sülün yağı yenmez: emek askıda kalır ama yağmur pişmanlığı yıkar, sonu talihtir.",
        "Kazanın ayağı kırılır, prensin aşı dökülür: yetmeyen güce büyük yük — utanç ve felaket.",
        "Kazanın sarı kulpları, altın halkaları: ölçülü kavrayış kalıcı doğrulukla taşır.",
        "Yeşim kulplu kazan: en yüksek talih — arıtılmış sunu her yöne kazanç dağıtır.",
    ],
    51: [
        "Gök gürler, önce korku sonra kahkaha: sarsıntıyla terbiye olan talihi bulur.",
        "Sarsıntı tehlikeyle gelir, hazineler bırakılır, dokuz tepeye çıkılır: kovalamayı bırak — yedi günde geri gelir.",
        "Sarsıntı sersemletir; ama sarsıntının kendisiyle harekete geçen beladan kurtulur.",
        "Sarsıntı çamura saplanır: uyarı hareketsizlikte boğulur.",
        "Sarsıntı üstüne sarsıntı: tehlikede bile ortadaki işini kaybetme — yapılacak iş korkuyu taşır.",
        "Sarsıntı çözülme getirir, bakışlar kayar: kendine değmemiş sarsıntıda hareket kusursuzdur; söylenti evliliğe kadar uzanır.",
    ],
    52: [
        "Ayak parmaklarında durmak: en baştan durmasını bilen kusursuzdur; kalıcı doğruluk kazançlıdır.",
        "Baldırlarda durmak: izlediğini kurtaramaz — kalbi sıkılır.",
        "Belde durmak, omurgayı ayırmak: zorla durdurulan gövde tehlikede boğulur, yürek dumanla dolar.",
        "Gövdede durmak: kendi merkezinde duran kusursuzdur.",
        "Çenede durmak: sözü düzenli olanın pişmanlığı silinir.",
        "Cömertçe durmak: durmanın en olgun hali — talih.",
    ],
    53: [
        "Yaban kazı kıyıya yaklaşır: gencin ilk adımı söz getirir ama kusur doğmaz.",
        "Yaban kazı kayaya varır: yiyip içmek huzurludur — sağlam basamak paylaşmayı getirir, talih.",
        "Yaban kazı kuru düzlüğe sapar: koca gider dönmez, kadın taşır doğurmaz — yerinden kopan adım felakettir; yağmacıya karşı koymak kazançtır.",
        "Yaban kazı ağaca varır, düz dala tutunur: eğreti yerde bile uygun tutamak kusuru önler.",
        "Yaban kazı tepeye varır: üç yıl çocuk olmaz ama sonunda kimse engel kalamaz — talih.",
        "Yaban kazı bulut yoluna varır: tüyleri törene süs olur — tamamlanmış yükselişin talihi budur.",
    ],
    54: [
        "Küçük kız kardeş yardımcı eş olarak gider: topal da yürür — mütevazı konumda ilerleyiş talihlidir.",
        "Tek gözle görmek: kenarda kalmış olanın münzevi doğruluğu yine kazançlıdır.",
        "Bekleyen kız kardeş hizmetçiliğe razı olur: uygunsuz bağa dönmektense bekle.",
        "Vadeyi geçirir: geç evlilik vakitsiz evlilikten iyidir — bekleyişin de mevsimi vardır.",
        "Prenses sade giyinir: gelinin kolları nedimesinden gösterişsizdir; ay dolunaya yakınken talih gelir.",
        "Kadının sepeti boş, adamın koyunu kansız: kabuk kalmış törenin hiçbir yönü kazançlı değildir.",
    ],
    55: [
        "Dengi olan efendiyle buluşmak: on gün birlikte kalmak kusur değildir; ilerleyiş değer görür.",
        "Perde öyle kalın ki öğlen Kepçe görünür: kuşkuyla gidilirse hastalık bulaşır — içtenlik uyandırılırsa talih gelir.",
        "Perde sıklaşır, öğlen küçük yıldız görünür; sağ kol kırılır — ama kusur yazılmaz.",
        "Perdenin içinde öğlen Kepçe'yi görür ama gizli efendisiyle buluşur: karanlıkta denk bulmak talihtir.",
        "Parlak yetenekleri çağırır: kutlama ve övgü gelir — talih.",
        "Evini büyütür, ailesini perdeler; kapısından bakan kimseyi göremez, üç yıl ses çıkmaz — bolluğun zirvesinde yalnızlık felakettir.",
    ],
    56: [
        "Gezgin ufak işlerle oyalanırsa felaketi kendi toplar.",
        "Gezgin hana varır, parasını korur, sadık genç hizmetkâr bulur: yolda ölçülülük güven kazandırır.",
        "Gezgin hanı yakar, hizmetkârını kaybeder: yolda kibir tehlikedir.",
        "Gezgin barınak bulur, baltasını edinir; ama yüreği rahat değildir — eğreti güvenlik huzur vermez.",
        "Sülüne tek okla vurur; ok kaybolur ama sonu övgü ve makamdır: yerinde küçük bedel büyük kabul getirir.",
        "Kuş yuvasını yakar: gezgin önce güler sonra ağlar; sınırda öküzünü kaybeder — yabancı yerde taşkınlık felakettir.",
    ],
    57: [
        "İlerleyip geri çekilen kararsızlık: savaşçı disiplini kararı getirir.",
        "Yatağın altına sinmiş nüfuz: kâhinler ve büyücülerle didik didik aramak talihi getirir, kusur kalmaz.",
        "Tekrarlana tekrarlana sızmak: bezdiren ısrar utançtır.",
        "Pişmanlık kaybolur: avda üç tür av birden — yumuşak nüfuz yerini bulunca verim üçlenir.",
        "Başlangıcı yok ama sonu var: değişimden üç gün önce, üç gün sonra tart — kalıcı doğrulukla talih gelir.",
        "Yatağın altına sinmiş, baltasını da kaybetmiş: nüfuz silikleşip araç da gidince ısrar felakettir.",
    ],
    58: [
        "Uyumlu sevinç: dışa muhtaç olmayan iç neşe talihlidir.",
        "İçten sevinç: doğruluktan gelen neşe pişmanlık bırakmaz.",
        "Gelmesi için çağrılan sevinç: dışarıdan devşirilen neşe felakettir.",
        "Hesaplaşılan sevinç: sınır konursa hastalıklı olan bile sevince döner.",
        "Soyucuya güvenmek tehlikedir: sevinç çağında sızan yabancıya dikkat.",
        "Kendini sevince kaptırıp sürüklenmek: çekilen neşe yönetilmezse yönetir.",
    ],
    59: [
        "Güçlü atla kurtarışa koşmak: dağılmanın ilk anında hızlı destek talihlidir.",
        "Dağılma çağında dayanağına koş: pişmanlık silinir.",
        "Kendini dağıtan pişmanlık duymaz: benlik erirse yakınma da erir.",
        "Hizbini dağıtan en yüksek talihi bulur: dağılıştan tepe yapmak sıradan akla gelmez.",
        "Büyük buyruk ter gibi yayılır: kral kendi merkezinden dağıtırsa kusur olmaz.",
        "Kanı dağıtır, uzağa çıkarır: tehlikeyi kaynağından uzak tutan kusursuzdur.",
    ],
    60: [
        "Kapıdan avluya çıkmamak: vakti değilken eşikte durmak kusursuzdur.",
        "Kapıdan avluya hiç çıkmamak: vakti gelmişken eşikte kalmak felakettir.",
        "Sınır tanımayan sonra ağıt yakar; ama suçu kendindedir — kusur başkasına yazılmaz.",
        "Sınırı huzurla kabullenmek: doğal ölçüye yerleşen başarıya akar.",
        "Tatlı sınır: ölçüyü sevdiren önder talihi bulur, ilerleyişi değer görür.",
        "Acı sınır: dayatılan ölçüde ısrar felakettir; ama pişmanlık sonunda silinir.",
    ],
    61: [
        "İçte hazır olan huzurludur; başka hesap gizlenirse huzur kaçar.",
        "Gölgedeki turna öter, yavrusu karşılık verir: 'kadehim dolu, paylaşalım' — içten ses en uzaktan duyulur.",
        "Düşmanını bulur: kâh davul kâh susuş, kâh gözyaşı kâh şarkı — dışa bağlanan iç dengesini kaybeder.",
        "Ay dolunaya yakın: at eşini bırakıp yukarı koşar — kusur yazılmaz.",
        "İçtenlik bağı: tam güven kusursuz bağlar.",
        "Horoz sesi göğe tırmanır: sesin çıkabileceği yerin ötesine iddia taşımak, ısrarla felakettir.",
    ],
    62: [
        "Uçmaya kalkan kuş yavrusu: küçüğün çağında yükseğe atılmak felakettir.",
        "Atasını geçip ceddiyle buluşamaz, hanımıyla buluşur; hükümdara varamaz, hizmetkârıyla görüşür: ölçülü hedef kusursuzdur.",
        "Aşırı korunmasız geçiş: arkadan vurulabilir — dikkat şart, gevşeklik felakettir.",
        "Kusursuz ama tetikte: buluşmaya git, geçmeye kalkma; kalıcı doğruluk için uyanık kal.",
        "Yoğun bulut, yağmur yok: prens kuytudaki adamı okla alır — küçüklük çağında ehli gizliden bulunur.",
        "Buluşmayı aşıp uçup giden kuş: haddi aşışın adı felakettir — buna 'taşkınlık' denir.",
    ],
    63: [
        "Tekerleğini geri çeker, kuyruğunu ıslatır: tamamlanmışlığın başında yavaşlamak kusursuzdur.",
        "Kadın arabasının perdesini kaybeder: arama — yedi günde kendiliğinden gelir.",
        "Yüce ata Gui ülkesini üç yılda bastırır: tamamlama savaşı uzundur; küçük insana iş verilmez.",
        "En güzel giysinin altında paçavra hazır: tamamlanmış gün boyu tetikte olmak ister.",
        "Komşunun kestiği öküz, öbürünün sade yaz sunusu kadar bereket getirmez: içtenlik gösterişi geçer.",
        "Başı suya batırmak: tamamlanmışın sonunda geri dönüşsüz dalış tehlikedir.",
    ],
    64: [
        "Kuyruğunu ıslatır: geçişin arifesinde ölçüsüz atılmak utançtır.",
        "Tekerleğini geri çeker: doğrulukta bekleyiş talihlidir.",
        "Tamamlanmamışken saldırıya geçmek felakettir; ama büyük nehri geçmenin vakti de yaklaşmıştır.",
        "Doğrulukla sarsıntıyı üç yıl taşır, Gui ülkesi düşer, ödül büyük ülkeden gelir: pişmanlık silinir.",
        "Soylu insanın ışığı içtendir: doğruluk talih getirir, pişmanlık kalmaz.",
        "Güven içinde kadeh kaldırılır: kusur yok — ama baş ıslanırsa güven ölçüyü kaybetmiştir.",
    ],
})

#: Heksagram 1 ve 2'nin "tüm çizgiler" pasajları (yong jiu / yong liu).
TUM_CIZGILER: dict[int, str] = {
    1: ("Bütün çizgiler dokuz: başsız ejderhalar sürüsü görünür — güç "
        "öndersiz ve gösterişsiz akarsa talih gelir."),
    2: ("Bütün çizgiler altı: kalıcı doğrulukta sebat et — teslimiyetin "
        "gücü süreklilikte belli olur."),
}


def main() -> None:
    veri = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    heksagramlar = {h["number"]: h for h in veri["hexagrams"]}

    eksik = [n for n in range(1, 65) if n not in CIZGILER]
    if eksik:
        raise SystemExit(
            f"{len(eksik)} heksagramın TR aktarımı eksik: {eksik[:8]}... — "
            f"YAZILMADI. Kısmi veri sessizce yayınlanamaz (İ1 tamlık kuralı).")
    for n, cizgiler in CIZGILER.items():
        if len(cizgiler) != 6 or not all(c.strip() for c in cizgiler):
            raise SystemExit(f"Heksagram {n}: 6 dolu çizgi gerekli.")

    for n, cizgiler in CIZGILER.items():
        heksagramlar[n]["lines_tr"] = cizgiler
    for n, pasaj in TUM_CIZGILER.items():
        heksagramlar[n]["all_lines_tr"] = pasaj

    DATA_FILE.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"Tamam: 64x6 TR cizgi + 2 'tum cizgiler' -> {DATA_FILE.name}")


if __name__ == "__main__":
    sys.exit(main())
