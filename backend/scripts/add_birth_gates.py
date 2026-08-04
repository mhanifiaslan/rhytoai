"""64 kapının doğum-karakteri pasajları — Rytho aktarımı (Revize İ8).

Doğum Heksagramı modülü (İ5) kapıyı hesaplar; bu dosya her kapıya
"karakter anahtarı" pasajını verir: heksagramın teması bir ÇEKİM kehaneti
olarak değil, doğuştan taşınan bir doku olarak yazılır (gölgesiyle
birlikte — pohpohlama yok).

TELİF: Gene Keys ve Human Design literatüründen tek cümle YOKTUR;
pasajlar heksagramın kendi doktrininden (İ1 yao verisi + İ7 doktrin
zemini) Rytho Türkçesi/İngilizcesiyle yazıldı. Künye SOURCES.md'de.

Çıktı: backend/data/birth_gates.json — hexagrams.json'a GÖMÜLMEZ (farklı
yaşam döngüsü, farklı künye; her çekimde ısınan _load şişmesin).

Kullanım: backend dizininden
    .venv/Scripts/python.exe scripts/add_birth_gates.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

OUT_FILE = (Path(__file__).resolve().parent.parent
            / "data" / "birth_gates.json")

#: kapı no -> (gate_tr, gate_en)
GATES: dict[int, tuple[str, str]] = {
    1: ("Yaratıcı gök kapısı: başlatmak senin dokunda var — fikri ilk sen "
        "görür, ilk sen söylersin. Gölgesi sabırsızlıktır: tohumu her gün "
        "söküp kök kontrol etmek. Olgun hâli, gücünü vakitli ve öndersiz "
        "gösterebilmektir.",
        "The gate of creative heaven: initiating is in your weave — you see "
        "the idea first and say it first. Its shadow is impatience: pulling "
        "the seed up daily to inspect the roots. Its ripeness is strength "
        "shown at the right hour, without parading."),
    2: ("Alıcı yer kapısı: taşımak, beslemek ve yön vermeden yönlendirmek "
        "senin işin. Gölgesi kendi sesini erteleyip herkesin zemini olmaktır. "
        "Olgun hâli, teslimiyeti edilgenlik sanmadan doğrultuyu sessizce "
        "tutmaktır.",
        "The gate of the receptive earth: carrying, nourishing and steering "
        "without commanding is your work. Its shadow is postponing your own "
        "voice to be everyone's ground. Its ripeness holds direction quietly, "
        "never mistaking devotion for passivity."),
    3: ("Başlangıç sancısı kapısı: düzeni kaostan ilk sen ayıklarsın. "
        "Gölgesi her işi zor doğum sanıp dramına bağlanmaktır. Olgun hâli, "
        "karışıklığa öncü atamayı ve yardım istemesini bilmektir.",
        "The gate of birth-pangs: you are the one who sorts order out of "
        "chaos first. Its shadow is treating every task as a hard labour and "
        "bonding with the drama. Its ripeness knows how to appoint helpers "
        "and to ask for aid."),
    4: ("Toy pınar kapısı: sorularla büyürsün; cevabı formüle çevirmek sana "
        "iyi gelir. Gölgesi yarım cevabı kesin ilan etmektir. Olgun hâli, "
        "'henüz bilmiyorum'u da bir cevap sayan zihin disiplinidir.",
        "The gate of the young spring: you grow by questions and love "
        "turning answers into formulas. Its shadow declares a half-answer "
        "final. Its ripeness is the discipline that counts 'I don't know "
        "yet' as an answer too."),
    5: ("Bekleyiş kapısı: doğru ânı sezmek doğuştan gelir; ritim senin "
        "gücündür. Gölgesi bekleyişi kaçırılmış hayat sanıp paniklemektir. "
        "Olgun hâli, beslenerek beklemek — nehir kıyısında güçlenen "
        "sabırdır.",
        "The gate of waiting: sensing the right moment is inborn; rhythm is "
        "your power. Its shadow panics, mistaking the wait for a missed "
        "life. Its ripeness waits while feeding itself — patience that "
        "strengthens by the riverbank."),
    6: ("Sürtünme kapısı: nerede uyuşmazlık varsa orada uzlaşının yolunu "
        "görürsün. Gölgesi her farkı dava etmektir. Olgun hâli, çatışmayı "
        "duygunun değil zeminin sorunu olarak çözmektir.",
        "The gate of friction: wherever there is discord you can see the "
        "road to settlement. Its shadow litigates every difference. Its "
        "ripeness resolves conflict as a matter of ground, not of feeling."),
    7: ("Ordu kapısı: insanları bir amaç etrafında dizmek sana doğal gelir. "
        "Gölgesi hizmet etmek yerine kumanda koltuğuna âşık olmaktır. Olgun "
        "hâli, öne çıkmadan yön veren kurmay aklıdır.",
        "The gate of the army: arraying people around a purpose comes "
        "naturally to you. Its shadow falls in love with the command chair "
        "instead of the service. Its ripeness is the staff-officer mind that "
        "directs without stepping forward."),
    8: ("Birlik kapısı: bağ kurmak ve tutmak senin mayandır; insanlar "
        "çevrende toplanır. Gölgesi herkese katılıp kendine katılmamaktır. "
        "Olgun hâli, katkısını kendi adıyla ortaya koyan gönüllü bağdır.",
        "The gate of union: forming and keeping bonds is your leaven; people "
        "gather around you. Its shadow joins everyone and never itself. Its "
        "ripeness contributes in its own name, a bond freely given."),
    9: ("Küçük birikim kapısı: ayrıntının gücünü bilirsin; küçük düzenli "
        "adım senin yolun. Gölgesi kırıntıya boğulup büyüğü görmemektir. "
        "Olgun hâli, damlayı bilinçle biriktirip vakti gelince barajı "
        "açmaktır.",
        "The gate of small accumulation: you know the power of detail; the "
        "small steady step is your road. Its shadow drowns in crumbs and "
        "misses the large. Its ripeness gathers the drops deliberately and "
        "opens the dam on time."),
    10: ("Yürüyüş kapısı: duruş ve tavır senin imzandır — kaplanın yanında "
         "bile adabını korursun. Gölgesi biçimi öze yeğlemektir. Olgun "
         "hâli, zarafeti korkusuzlukla birleştiren kendine saygıdır.",
         "The gate of treading: bearing and conduct are your signature — "
         "even beside the tiger you keep your manner. Its shadow prefers "
         "form to substance. Its ripeness joins grace with fearlessness: "
         "self-respect."),
    11: ("Barış kapısı: uyumun mimarı doğdun; gök ile yerin alışverişini "
         "kurarsın. Gölgesi iyi havayı sonsuz sanıp nöbeti bırakmaktır. "
         "Olgun hâli, barışı her gün yeniden ören uyanık dinginliktir.",
         "The gate of peace: you were born an architect of accord, setting "
         "heaven and earth trading. Its shadow assumes fair weather is "
         "forever and quits the watch. Its ripeness re-weaves peace daily — "
         "alert calm."),
    12: ("Duraklama kapısı: geri çekilmenin hikmetini bilirsin; her kapıyı "
         "zorlamazsın. Gölgesi küskün inzivadır. Olgun hâli, tıkalı çağda "
         "içini büyütüp vakitli geri dönmektir.",
         "The gate of standstill: you know the wisdom of withdrawal and do "
         "not force every door. Its shadow is sulking seclusion. Its "
         "ripeness grows inward through the blocked season and returns on "
         "time."),
    13: ("Yoldaşlık kapısı: yabancıyı sofraya oturtmak senin hünerin; "
         "topluluk sende genişler. Gölgesi klik kurup kapıyı daraltmaktır. "
         "Olgun hâli, açık kırda kurulan seçici olmayan dostluktur.",
         "The gate of fellowship: seating the stranger at the table is your "
         "craft; community widens around you. Its shadow builds cliques and "
         "narrows the door. Its ripeness is friendship pitched in the open "
         "field."),
    14: ("Büyük varlık kapısı: değeri toplamak ve taşımak sana verilmiş; "
         "bolluk elinde çirkinleşmez. Gölgesi sahipliği kimlik yapmaktır. "
         "Olgun hâli, arabasını herkes için yük taşıyan zenginliktir.",
         "The gate of great holding: gathering and carrying value is given "
         "to you; abundance does not turn ugly in your hands. Its shadow "
         "makes ownership an identity. Its ripeness is wealth whose cart "
         "carries for everyone."),
    15: ("Alçakgönüllülük kapısı: dengeyi aşırılıkları törpüleyerek "
         "kurarsın; büyüklüğün sade hâli sende. Gölgesi kendini silmeyi "
         "erdem sanmaktır. Olgun hâli, dağ gibi durup ova gibi görünen "
         "ağırlıktır.",
         "The gate of modesty: you level the extremes to make balance; "
         "greatness wears plain clothes on you. Its shadow mistakes "
         "self-erasure for virtue. Its ripeness stands like a mountain and "
         "reads like a plain."),
    16: ("Coşku kapısı: heves uyandırmak, davulu vaktinde vurmak senin "
         "işin. Gölgesi gazı gerçeğin önüne koymaktır. Olgun hâli, şevki "
         "hazırlıkla eşleyen ilham verici öncülüktür.",
         "The gate of enthusiasm: kindling zeal and striking the drum on "
         "time is your work. Its shadow puts hype before fact. Its ripeness "
         "pairs fervour with preparation — inspiring leadership."),
}


GATES.update({
    17: ("İzleme kapısı: doğru olana uymayı ve doğru zamanda takip "
         "değiştirmeyi bilirsin; görüş üretmek sana kolay gelir. Gölgesi "
         "fikri kimlik yapıp savunma savaşına girmektir. Olgun hâli, "
         "görüşünü kanıtla güncelleyebilen esnek omurgadır.",
         "The gate of following: you know how to align with what is right "
         "and to change allegiance at the right time; opinions come easily "
         "to you. Its shadow turns opinion into identity and fights siege "
         "wars for it. Its ripeness is a flexible spine that updates its "
         "view on evidence."),
    18: ("Onarım kapısı: bozulmuşu görmek ve elden geçirmek doğuştan "
         "işin — miras kusurları sende şifa bulur. Gölgesi kusur avcılığına "
         "dönüşmektir. Olgun hâli, eleştiriyi tamir planına çeviren usta "
         "elidir.",
         "The gate of repair: seeing what has spoiled and working it over "
         "is your inborn task — inherited flaws heal in your hands. Its "
         "shadow decays into fault-hunting. Its ripeness is the craftsman's "
         "hand that turns critique into a repair plan."),
    19: ("Yaklaşım kapısı: ihtiyacı önceden sezer, insanlara doğru "
         "eğilirsin. Gölgesi onay için yaklaşmak — sınır eriyene kadar. "
         "Olgun hâli, temas kurup kendi zeminini de koruyan sıcaklıktır.",
         "The gate of approach: you sense need before it speaks and lean "
         "toward people. Its shadow approaches for approval until the "
         "boundary melts. Its ripeness is warmth that makes contact and "
         "keeps its own ground."),
    20: ("Temaşa kapısı: görmek ve göstermek senin gücün; ânın fotoğrafını "
         "çekersin. Gölgesi seyirci kalıp hayata değmemektir. Olgun hâli, "
         "gözlemden vakitli söze geçen berrak tanıklıktır.",
         "The gate of contemplation: seeing and showing is your power; you "
         "photograph the moment. Its shadow stays a spectator and never "
         "touches life. Its ripeness is clear witness that turns to timely "
         "speech."),
    21: ("Kararlı ısırış kapısı: engeli adlandırıp kesmeyi bilirsin; "
         "adalet duygun keskin. Gölgesi sertliği ilk araç yapmaktır. Olgun "
         "hâli, gücü ölçülü kullanan dürüst infazdır — önce uyarı, sonra "
         "kesme.",
         "The gate of biting through: naming the obstacle and cutting it is "
         "in you; your sense of justice is sharp. Its shadow makes severity "
         "the first tool. Its ripeness is honest enforcement in measure — "
         "warning first, cutting after."),
    22: ("Süs kapısı: biçim duygusu doğuştan — neyin nasıl görüneceğini "
         "bilirsin. Gölgesi cilayı içerik sanmaktır. Olgun hâli, özü "
         "taşıyan zarafet; beyaz süsün sadeliğidir.",
         "The gate of adornment: the sense of form is inborn — you know how "
         "things should appear. Its shadow mistakes polish for content. Its "
         "ripeness is grace that carries substance: the plainness of white "
         "ornament."),
    23: ("Soyulma kapısı: fazlalığı dökmeyi, yapıyı iskelete indirmeyi "
         "bilirsin. Gölgesi yıkımı çözüm sanmaktır. Olgun hâli, çürüğü "
         "ayıklarken sağlam meyveyi tohum diye saklamaktır.",
         "The gate of stripping: shedding excess and reducing structure to "
         "its skeleton is your knowledge. Its shadow mistakes demolition "
         "for solution. Its ripeness culls the rot and keeps the sound "
         "fruit as seed."),
    24: ("Dönüş kapısı: yoldan sapsan da dönüş yolunu kaybetmezsin; "
         "yenilenme sende döngüseldir. Gölgesi aynı kapıya tekrar tekrar "
         "dönmektir. Olgun hâli, hatadan erken dönen ve dönüşü büyüme "
         "yapan ritimdir.",
         "The gate of return: however far you stray, you never lose the way "
         "back; renewal cycles in you. Its shadow returns to the same door "
         "again and again. Its ripeness turns back early and makes every "
         "return a growth."),
    25: ("Saf içtenlik kapısı: hesapsızlık senin gücün; beklentisiz iş "
         "sende bereketlenir. Gölgesi saflığı bahane edip sorumluluğu "
         "bırakmaktır. Olgun hâli, beklenmedik belada bile bozulmayan "
         "temiz niyettir.",
         "The gate of innocence: guilelessness is your strength; work "
         "without expectation prospers in you. Its shadow uses purity as an "
         "excuse to drop responsibility. Its ripeness is clean intent that "
         "does not sour even in undeserved trouble."),
    26: ("Büyük ehlileştirme kapısı: gücü biriktirip zapt etmeyi "
         "bilirsin; hafıza ve öğreti sende depolanır. Gölgesi birikimi "
         "gösterişe dökmektir. Olgun hâli, boynuza tahtayı erken vuran "
         "öngörülü terbiyedir.",
         "The gate of great taming: storing power and holding it in check "
         "is your knowledge; memory and teaching bank in you. Its shadow "
         "spills the hoard into display. Its ripeness fixes the board to "
         "the horn early — foresighted discipline."),
    27: ("Beslenme kapısı: neyin beslediğini ayırt edersin — sofra, söz ve "
         "zihin gıdası senin alanın. Gölgesi başkasının lokmasına imrenip "
         "kendi kaynağını unutmaktır. Olgun hâli, önce kendi kuyusunu "
         "temiz tutan besleyiciliktir.",
         "The gate of nourishment: you tell what feeds from what fills — "
         "table, word and food of the mind are your field. Its shadow "
         "envies another's morsel and forgets its own source. Its ripeness "
         "keeps its own well clean first, then feeds."),
    28: ("Büyük aşım kapısı: taşıyamayacak görünen yükü omuzlamak sende "
         "cesarettir; olağanüstü zamanların insanısın. Gölgesi kirişi "
         "çatlatana kadar yüklenmektir. Olgun hâli, hangi yükün ölüme "
         "değer olduğunu seçebilmektir.",
         "The gate of great exceeding: shouldering the load that looks "
         "unbearable is your courage; you belong to extraordinary hours. "
         "Its shadow loads until the beam cracks. Its ripeness can choose "
         "which burden is worth the crossing."),
    29: ("Uçurum kapısı: tehlikeye alışkın değil, tehlikeyle çalışan "
         "birisin; derin su senin okulun. Gölgesi riski bağımlılık "
         "yapmaktır. Olgun hâli, akan su gibi: doldurmadan geçmez, "
         "biçim değiştirir ama özünü kaybetmez.",
         "The gate of the abyss: you are not numbed to danger, you work "
         "with it; deep water is your school. Its shadow makes risk an "
         "addiction. Its ripeness is flowing water: it does not pass "
         "before filling, changes shape and keeps its nature."),
    30: ("Tutunan ateş kapısı: parlamak için bir şeye bağlanman gerek — "
         "dava, insan, iş; bağlandığında aydınlatırsın. Gölgesi neye "
         "tutunduğunu seçmemektir. Olgun hâli, yakıtını bilerek seçen "
         "sürekli ışıktır.",
         "The gate of clinging fire: to shine you must attach — a cause, a "
         "person, a work; attached, you illuminate. Its shadow does not "
         "choose what it clings to. Its ripeness is steady light that "
         "selects its fuel knowingly."),
    31: ("Etkileşim kapısı: çekim alanın doğuştan — insanlar sana doğru "
         "eğilir. Gölgesi etkiyi onaya çevirme açlığıdır. Olgun hâli, "
         "boş dağ gölü gibi: alçakta durduğu için dolduran cazibedir.",
         "The gate of influence: your field of attraction is inborn — "
         "people lean your way. Its shadow hungers to convert influence "
         "into approval. Its ripeness is the mountain lake: it fills "
         "because it lies low."),
    32: ("Süreklilik kapısı: kalıcı olanı kurmak senin işin; sen "
         "bırakmazsın. Gölgesi değişmesi gerekeni de sürdürmektir. Olgun "
         "hâli, özü sabit yöntemi esnek tutan dayanıklılıktır.",
         "The gate of duration: building what lasts is your work; you do "
         "not quit. Its shadow also perpetuates what should change. Its "
         "ripeness keeps the core fixed and the method supple — "
         "endurance."),
})


GATES.update({
    33: ("Geri çekiliş kapısı: vazgeçmeyi strateji yapabilen az kişiden "
         "birisin; mesafe senin gücün. Gölgesi her zorlukta kaybolmaktır. "
         "Olgun hâli, ferah bir çekiliş — kaçış değil, alan kazanmaktır.",
         "The gate of retreat: you are one of the few who can make "
         "withdrawal a strategy; distance is your power. Its shadow "
         "vanishes at every difficulty. Its ripeness is the ample retreat "
         "— not flight but gaining room."),
    34: ("Büyük kuvvet kapısı: gücün erken gelir ve bol gelir. Gölgesi "
         "çite toslayan koçtur: gücü gösterme ihtiyacı. Olgun hâli, "
         "kullanmadığı kuvvetle tanınan olgun kudrettir.",
         "The gate of great power: your strength arrives early and in "
         "plenty. Its shadow is the ram butting the fence — the need to "
         "display force. Its ripeness is mature might, known by the "
         "strength it does not use."),
    35: ("İlerleyiş kapısı: gün ışığında yükselmek — görünür ilerleme "
         "senin iklimin. Gölgesi ilerlemeyi tek ölçü yapmaktır. Olgun "
         "hâli, kayıp-kazanç hesabını bırakan aydınlık yürüyüştür.",
         "The gate of progress: rising in daylight — visible advance is "
         "your climate. Its shadow makes progress the only measure. Its "
         "ripeness walks in brightness and drops the ledger of loss and "
         "gain."),
    36: ("Kararan ışık kapısı: karanlık çağda aklını koruyabilenlerdensin; "
         "zor yerde görürsün. Gölgesi sürekli kuşatma modunda yaşamaktır. "
         "Olgun hâli, ışığını gizleyip söndürmeyen sabırlı bilgeliktir.",
         "The gate of darkened light: you are of those who keep their mind "
         "in a dark age; you see in hard places. Its shadow lives in "
         "permanent siege mode. Its ripeness veils its light without "
         "quenching it — patient wisdom."),
    37: ("Ocak kapısı: aile ve yakın halka senin tapınağın; içeriyi "
         "düzenlersin. Gölgesi sevgiyi kurala boğmaktır. Olgun hâli, "
         "sıcaklıkla sınırı birlikte tutan ev ustalığıdır.",
         "The gate of the hearth: family and the near circle are your "
         "temple; you order the inside. Its shadow drowns love in rules. "
         "Its ripeness holds warmth and boundary together — mastery of "
         "the household."),
    38: ("Karşıtlık kapısı: aykırı durmak senin doğan — farkı herkesten "
         "önce görürsün. Gölgesi muhalefeti kimlik yapmaktır. Olgun hâli, "
         "ayrılıkta bile köprü gözeten verimli inatçılıktır.",
         "The gate of opposition: standing contrary is your nature — you "
         "see the difference before anyone. Its shadow makes dissent an "
         "identity. Its ripeness is fertile stubbornness that keeps a "
         "bridge even in divergence."),
    39: ("Engel kapısı: tıkanıklık seni durdurmaz, düşündürür; engelde "
         "büyüyenlerdensin. Gölgesi her duvara alnını dayamaktır. Olgun "
         "hâli, engeli dolaşan ve dostlarını çağıran akıllı duraksamadır.",
         "The gate of obstruction: blockage does not stop you, it makes "
         "you think; you grow at obstacles. Its shadow leans its forehead "
         "on every wall. Its ripeness pauses wisely, walks around, and "
         "calls its friends."),
    40: ("Kurtuluş kapısı: düğümü çözmek ve yükü indirmek senin ânın; "
         "fırtına sonrası ferahlığı sen getirirsin. Gölgesi affı erteleyip "
         "hesap tutmaktır. Olgun hâli, çözülme gününde sözü kısa kesen "
         "temiz eldir.",
         "The gate of deliverance: untying the knot and setting down the "
         "load is your moment; you bring the ease after the storm. Its "
         "shadow keeps accounts and postpones pardon. Its ripeness speaks "
         "briefly on the day of release — a clean hand."),
    41: ("Azalış kapısı: eksiltmek senin sanatın — sadeleşen her şey sende "
         "güçlenir. Gölgesi kıtlık korkusuyla cimrileşmektir. Olgun hâli, "
         "aşağıdan verip yukarıyı büyüten bilinçli feragattir.",
         "The gate of decrease: paring down is your art — whatever "
         "simplifies grows stronger in you. Its shadow turns miserly with "
         "scarcity fear. Its ripeness gives from below to grow what is "
         "above — deliberate renunciation."),
    42: ("Artış kapısı: büyütmek ve çoğaltmak sana verilmiş; rüzgâr ve "
         "gök gürültüsü birlikte çalışır sende. Gölgesi artışı yalnız "
         "kendine akıtmaktır. Olgun hâli, kâr gününde herkesi ortak eden "
         "cömert hamledir.",
         "The gate of increase: enlarging and multiplying is given to you; "
         "wind and thunder work together in you. Its shadow channels the "
         "increase only to itself. Its ripeness makes everyone a partner "
         "on the day of gain — the generous move."),
    43: ("Kararlı atılım kapısı: son sözü söylemek ve bendi yarmak senin "
         "ânın. Gölgesi ilan etmeden infaz etmektir. Olgun hâli, kararını "
         "meydanda açıkça bildirip öyle yürüyen dürüst kararlılıktır.",
         "The gate of resolute breakthrough: saying the last word and "
         "breaching the dam is your moment. Its shadow executes without "
         "declaring. Its ripeness announces its resolve in the open square "
         "and then walks — honest determination."),
    44: ("Karşılaşma kapısı: tesadüf sende randevudur — doğru insan ve "
         "doğru fikirle karşılaşmayı bilirsin. Gölgesi her geleni içeri "
         "almaktır. Olgun hâli, ilk temasta ölçüp bağlayan seçici "
         "misafirperverliktir.",
         "The gate of coming to meet: coincidence is appointment in you — "
         "you know how to meet the right person and the right idea. Its "
         "shadow lets everything in. Its ripeness measures at first touch "
         "and binds — selective hospitality."),
    45: ("Toplanma kapısı: insanları bir araya getirmek ve merkez olmak "
         "senin işin. Gölgesi kalabalığı onay deposu yapmaktır. Olgun "
         "hâli, toplananı amaçla hizalayan içten önderliktir.",
         "The gate of gathering: bringing people together and being the "
         "centre is your work. Its shadow uses the crowd as a store of "
         "approval. Its ripeness aligns the gathered with a purpose — "
         "sincere leadership."),
    46: ("Yükseliş kapısı: adım adım, kökten yukarı büyürsün — ağaç gibi. "
         "Gölgesi basamak atlamaya kalkmaktır. Olgun hâli, her katta "
         "kökleşerek çıkan sabırlı tırmanıştır.",
         "The gate of pushing upward: you grow step by step, from the root "
         "up — like a tree. Its shadow tries to skip stairs. Its ripeness "
         "roots at every storey while climbing — patient ascent."),
    47: ("Darlık kapısı: kısıtlanmışlıkta bile söz üretebilenlerdensin; "
         "sıkışma sende derinleşmedir. Gölgesi darlığı kadere çevirmektir. "
         "Olgun hâli, kuyunun dibinde bile duruşunu koruyan sessiz "
         "metanettir.",
         "The gate of confinement: even constrained you can still make "
         "meaning; being pressed deepens you. Its shadow turns hardship "
         "into fate. Its ripeness keeps its bearing at the bottom of the "
         "well — quiet fortitude."),
    48: ("Kuyu kapısı: kaynak insanısın — bilgin ve şefkatin herkese açık "
         "bir kuyudur. Gölgesi kuyuyu kazıp suyu sunmamaktır. Olgun hâli, "
         "düzenli bakılan, örtüsüz bırakılan tükenmez kaynaktır.",
         "The gate of the well: you are a source — your knowledge and care "
         "a well open to all. Its shadow digs the well and never serves "
         "the water. Its ripeness is the inexhaustible spring, kept clean "
         "and left uncovered."),
})


GATES.update({
    49: ("Devrim kapısı: eskimişi görmek ve değiştirmek senin refleksin; "
         "dönüşümün öncüsüsün. Gölgesi devrim için devrim yapmaktır. "
         "Olgun hâli, kendi gününü bekleyen ve önce güveni kuran vakitli "
         "değişimdir.",
         "The gate of revolution: seeing the outworn and changing it is "
         "your reflex; you lead transformation. Its shadow makes "
         "revolution for its own sake. Its ripeness waits for its own day "
         "and builds trust first — timely change."),
    50: ("Kazan kapısı: dönüştürüp sunmak — ham olanı pişirip topluluğa "
         "vermek senin görevin. Gölgesi kazanı kendine kaynatmaktır. "
         "Olgun hâli, sunağın kabı gibi: taşıdığıyla değerlenen "
         "hizmettir.",
         "The gate of the cauldron: transforming and serving — cooking "
         "the raw and giving it to the community is your office. Its "
         "shadow boils the cauldron for itself. Its ripeness is the "
         "vessel of the altar, valued by what it carries."),
    51: ("Sarsıntı kapısı: şok seni uyandırır, yıkmaz; gök gürültüsü "
         "senin öğretmenin. Gölgesi sarsıntıyı yayıp paniği çoğaltmaktır. "
         "Olgun hâli, korkuyla gülmeyi aynı anda bilen, kadehi dökmeyen "
         "eldir.",
         "The gate of shock: the jolt wakes you, it does not wreck you; "
         "thunder is your teacher. Its shadow spreads the tremor and "
         "multiplies panic. Its ripeness knows fear and laughter at once "
         "and does not spill the cup."),
    52: ("Dağ kapısı: durmak senin süper gücün — zihin sende susmayı "
         "bilir. Gölgesi donup kalmaktır. Olgun hâli, hareketin tam "
         "ortasında bile erişilebilen iç sükûnettir.",
         "The gate of the mountain: stopping is your superpower — in you "
         "the mind knows how to fall silent. Its shadow freezes. Its "
         "ripeness is inner stillness reachable even in the middle of "
         "motion."),
    53: ("Tedricî ilerleme kapısı: yavaş ve geri dönüşsüz büyüme senin "
         "yolun — yaban kazının göçü gibi. Gölgesi yavaşlığı bahaneye "
         "çevirmektir. Olgun hâli, her konağı sindirerek yükselen emin "
         "akıştır.",
         "The gate of gradual advance: slow, irreversible growth is your "
         "road — the wild goose's migration. Its shadow turns slowness "
         "into an excuse. Its ripeness rises by digesting every station — "
         "assured flow."),
    54: ("Gelin kapısı: verili koşullarda yer edinmeyi bilirsin; ideal "
         "olmayan başlangıçtan yol çıkarırsın. Gölgesi kendini hep ikinci "
         "koltuğa yazmaktır. Olgun hâli, konumu değil katkıyı büyüten "
         "gerçekçi sadakattir.",
         "The gate of the marrying maiden: you know how to take root in "
         "given conditions and make a road from an unideal start. Its "
         "shadow always books itself the second seat. Its ripeness grows "
         "the contribution, not the rank — realistic devotion."),
    55: ("Bolluk kapısı: doruk anları senin iklimin — parlaklığı "
         "yönetmeyi öğrenmek için doğdun. Gölgesi öğlen vakti perde "
         "çekmektir: bolluk içinde karanlık. Olgun hâli, zirvenin "
         "geçiciliğini bilen tok parlayıştır.",
         "The gate of abundance: peak moments are your climate — you were "
         "born to learn the government of brilliance. Its shadow draws "
         "the curtain at noon: darkness inside plenty. Its ripeness "
         "shines full, knowing the summit passes."),
    56: ("Gezgin kapısı: hiçbir yere tam yerleşmemek senin doğan; her "
         "yerde öğrenir, her yerden geçersin. Gölgesi köksüzlüğü kimlik "
         "yapmaktır. Olgun hâli, hafif yük ve ölçülü tavırla her kapıdan "
         "onurla geçen yolculuktur.",
         "The gate of the wanderer: never fully settling is your nature; "
         "you learn everywhere and pass through everywhere. Its shadow "
         "makes rootlessness an identity. Its ripeness travels light and "
         "measured, passing every door with honour."),
    57: ("Nüfuz kapısı: rüzgâr gibi — görünmeden, tekrarla işlersin; "
         "etkin sızarak kurulur. Gölgesi kararsız eğilip bükülmektir. "
         "Olgun hâli, yönü belli esintinin taş oyması gibi sabırlı "
         "etkidir.",
         "The gate of penetration: like wind you work unseen, by "
         "repetition; your influence seeps in. Its shadow bends without "
         "resolve. Its ripeness is the patient effect of a steady breeze "
         "carving stone."),
    58: ("Sevinç kapısı: neşe sende kaynak — insanlar yanında hafifler; "
         "söz ve paylaşım senin alanın. Gölgesi neşeyi dışarıdan satın "
         "almaktır. Olgun hâli, dostlarla bilenerek derinleşen içten "
         "sevinçtir.",
         "The gate of joy: gladness springs in you — people lighten at "
         "your side; word and exchange are your field. Its shadow buys "
         "joy from outside. Its ripeness deepens by whetting with friends "
         "— joy from within."),
    59: ("Dağıtma kapısı: katıyı eritmek, hizbi çözmek senin işin; "
         "ayrılığın buzunu sen kırarsın. Gölgesi kendi sınırını da "
         "eritmektir. Olgun hâli, ter gibi yayılan buyruk — merkezden "
         "dağılan birleştirici akıştır.",
         "The gate of dispersion: melting the rigid and dissolving the "
         "clique is your work; you break the ice of separation. Its "
         "shadow melts its own boundary too. Its ripeness spreads like "
         "sweat from the centre — a uniting flow."),
    60: ("Sınırlama kapısı: ölçü koymak sende sanattır — kanal olmadan "
         "su bataklık olur, bilirsin. Gölgesi acı sınırlar dayatmaktır. "
         "Olgun hâli, tatlı sınır: ölçüyü sevdirerek koyan düzendir.",
         "The gate of limitation: setting measure is an art in you — "
         "without banks, water is a swamp, and you know it. Its shadow "
         "imposes bitter limits. Its ripeness is the sweet limit: order "
         "that makes measure loved."),
    61: ("İç hakikat kapısı: görünmeyeni duyarsın — gölgedeki turnanın "
         "sesine karşılık verensin. Gölgesi inancı kanıt yerine "
         "koymaktır. Olgun hâli, domuzu ve balığı bile ikna eden sessiz "
         "içtenliktir.",
         "The gate of inner truth: you hear the unseen — you are the one "
         "who answers the crane calling in the shade. Its shadow puts "
         "belief in the place of proof. Its ripeness is quiet sincerity "
         "that persuades even pigs and fishes."),
    62: ("Küçüğün üstünlüğü kapısı: ayrıntıda kusursuzluk — küçük işi "
         "büyük özenle yapmak senin imzan. Gölgesi yükseğe erken uçan "
         "kuş olmaktır. Olgun hâli, alçak uçuşun bereketini bilen "
         "titizliktir.",
         "The gate of the small exceeding: perfection in detail — doing "
         "the small task with great care is your signature. Its shadow is "
         "the fledgling flying high too soon. Its ripeness knows the "
         "blessing of flying low — exactness."),
    63: ("Tamamlanma kapısı: bitirmek senin hünerin — düzeni son "
         "vidasına kadar kurarsın. Gölgesi bitmişin başında nöbeti "
         "bırakmaktır. Olgun hâli, tamamlanmış günün akşamında bile "
         "tetikte duran koruyuculuktur.",
         "The gate of completion: finishing is your craft — you set the "
         "order down to the last screw. Its shadow quits the watch once "
         "the work is done. Its ripeness stays alert even on the evening "
         "of the finished day."),
    64: ("Tamamlanmamış kapısı: eşiğin insanısın — her şey neredeyse "
         "hazır ânında en iyi hâlindesin. Gölgesi son adımı hep ertelemek "
         "ya da erken atlamaktır. Olgun hâli, kuyruğunu ıslatmadan geçen "
         "genç tilkinin dikkatidir.",
         "The gate of the not-yet-complete: you are a person of the "
         "threshold — at your best when everything is almost ready. Its "
         "shadow forever defers the last step or leaps too soon. Its "
         "ripeness is the young fox crossing without wetting its tail."),
})


def main() -> None:
    eksik = [n for n in range(1, 65) if n not in GATES]
    if eksik:
        raise SystemExit(
            f"{len(eksik)} kapının pasajı eksik: {eksik[:8]}... — YAZILMADI "
            f"(İ8 tamlık kuralı: kısmi veri yayınlanamaz).")
    for n, (tr, en) in GATES.items():
        if len(tr) < 80 or len(en) < 80:
            raise SystemExit(f"Kapı {n}: pasaj çok kısa.")

    veri = {"wheel_version": "1",
            "gates": {str(n): {"gate_tr": tr, "gate_en": en}
                      for n, (tr, en) in sorted(GATES.items())}}
    OUT_FILE.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"Tamam: 64 kapi pasaji (TR+EN) -> {OUT_FILE.name}")


if __name__ == "__main__":
    sys.exit(main())
