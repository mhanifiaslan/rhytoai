"""Token cüzdanı — abonelik hakkı + satın alınan paketler.

## Neden var

Abonelik tek başına "sınırsız sohbet" vaat ediyordu ve sohbet, kullanıcı
başına önbelleksiz LLM çağrısı olan TEK uçtur: öngörülemeyen yoğun kullanım
maliyeti doğrusal büyütür. Model değişti — abonelik aylık bir token hakkı
verir, dilenirse üstüne paket alınır:

* ``allowance`` — abonelikle gelen aylık hak. Dönem bitince YENİLENİR,
  DEVREDİLMEZ (kullanıcı kararı).
* ``purchased`` — satın alınan paket bakiyesi. Aya DEVREDER, hiç yanmaz.

Harcama sırası önce ``allowance`` sonra ``purchased``: yanacak olan önce
harcanır, kullanıcının parayla aldığı bakiye korunur.

## Neden transaction

Mevcut ``consume_quota`` get-then-set çalışır ve bu bilinçli bir
yumuşaklıktır (günlük 5 sohbet hakkında yarış penceresi kimseyi
ilgilendirmez). Cüzdan İSE para: iki eşzamanlı istek aynı bakiyeyi iki kez
harcayabilir ya da webhook yeniden denemesi aynı paketi iki kez
yükleyebilir. Harcama ve kredi Firestore transaction'ı içinde; kredi ayrıca
RevenueCat olay kimliğiyle deftere yazılıp idempotent kılınır.

## Sıfır bakiyede ne olur

402 döner — mevcut paywall borusunun aynısı — ama yanına
``X-Paywall-Reason: tokens`` başlığı eklenir. ``detail`` alanı istemcide
kullanıcıya gösterilen düz metindir (friendlyError sözleşmesi), ayrım oraya
gömülemez; istemci başlığa bakıp paywall yerine token mağazasını açar.

## Kademeli açılış

``RYTHO_TOKENS_ENFORCE=0`` iken harcama hesaplanır ve loglanır ama asla
reddedilmez. Eski mobil sürümler yayılana kadar üretim bu kipte çalışır;
bayrak açıldığında istemciler mağaza ekranını zaten biliyor olur.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
from typing import Any, Callable

from fastapi import HTTPException

from core import firestore as firestore_client
# `entitlements` MODÜL olarak: `from ... import is_subscriber` ile kopyalanan
# ad, testlerin (ve olası çalışma zamanı yamalarının) `entitlements.X`
# üzerine yaptığı monkeypatch'i GÖRMEZ — bu dosyada bir kez yaşandı.
from core import entitlements
from core.entitlements import PAYWALL_STATUS
from core.i18n import DEFAULT as DEFAULT_LANG
from core.messages import text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ürün gerçeği — SUNUCUDA tutulur, istemciye güvenilmez
# ---------------------------------------------------------------------------

#: Özellik başına token bedeli. Fiyatlandırma LLM maliyetiyle hizalı:
#: sohbet tek kısa çağrı (1), derin raporlar uzun üretim (5). Önbellekten
#: servis edilen tekrar okumalar HİÇ düşmez (bkz. report_service).
TOKEN_COSTS: dict[str, int] = {
    "chat": 1,
    "iching": 2,
    "dyad": 3,
    "natal": 5,
    "bazi": 5,
    "synastry": 5,
    "face": 5,
    # Doğum Heksagramı (İ5): natal ile aynı sınıf — kişiye özel, 30 gün
    # önbellekli kalıcı üretim.
    "birth_hexagram": 5,
}

#: Abonelikle gelen aylık hak. En kötü durum maliyeti sınırlar: 300 token
#: tamamı sohbete gitse ~$0,45 LLM gideri — abonelik bedelinin küçük kesri.
MONTHLY_TOKEN_ALLOWANCE = 300

#: RevenueCat consumable ürün kimliği -> token adedi. Webhook yalnızca bu
#: listedeki ürünleri paket sayar; liste dışı ürün kimliği abonelik borusuna
#: gider. İstemciden gelen hiçbir sayıya güvenilmez.
TOKEN_PACKS: dict[str, int] = {
    "rytho_tokens_small": 100,
    "rytho_tokens_medium": 300,
    "rytho_tokens_large": 1000,
}

#: Kuru çalışma bayrağı. 0 iken harcama loglanır ama reddedilmez.
TOKENS_ENFORCE: bool = os.getenv("RYTHO_TOKENS_ENFORCE", "0") == "1"


def _wallet_ref(uid: str):
    client = firestore_client.get_client()
    if client is None:
        return None
    return (client.collection("users").document(uid)
            .collection("private").document("wallet"))


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _ts(value: Any) -> float:
    """Firestore zaman damgasını karşılaştırılabilir sayıya indirger."""
    try:
        return value.timestamp()
    except AttributeError:
        return 0.0


# ---------------------------------------------------------------------------
# Okuma
# ---------------------------------------------------------------------------

def get_wallet(uid: str) -> dict[str, Any]:
    """Cüzdanın istemciye gösterilecek hâli; tembel sıfırlama YANSITILIR
    ama yazılmaz (yazma yalnızca harcama/kredi anında, transaction içinde).
    """
    ref = _wallet_ref(uid)
    data: dict[str, Any] = {}
    if ref is not None:
        try:
            snapshot = ref.get()
            data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        except Exception as exc:
            logger.warning("Cüzdan okunamadı (%s): %s", uid, exc)

    allowance = int(data.get("allowance", 0))
    marker = data.get("allowanceExpiresAt")

    sub = entitlements.get_subscription(uid)
    sub_expires = sub.get("expiresAt")
    if sub.get("active") and _ts(sub_expires) > _ts(marker):
        # Yeni dönem başlamış, webhook resetini kaçırmışız: görünümde tam
        # hakkı göster. Kalıcı yazım ilk harcamada yapılır.
        allowance = MONTHLY_TOKEN_ALLOWANCE
        marker = sub_expires

    return {
        "allowance": allowance if sub.get("active") else 0,
        "purchased": int(data.get("purchased", 0)),
        "monthly_allowance": MONTHLY_TOKEN_ALLOWANCE,
        "allowance_resets_at": marker,
        "costs": dict(TOKEN_COSTS),
    }


# ---------------------------------------------------------------------------
# Harcama
# ---------------------------------------------------------------------------

def _spend_txn(transaction, ref, uid: str, cost: int) -> bool:
    """Transaction gövdesi: oku, gerekirse dönemi tazele, düş, yaz."""
    snapshot = ref.get(transaction=transaction)
    data = (snapshot.to_dict() or {}) if snapshot.exists else {}

    allowance = int(data.get("allowance", 0))
    marker = data.get("allowanceExpiresAt")

    # Tembel dönem tazeleme: webhook RENEWAL'i kaçırdıysa bile kullanıcı
    # yeni dönemde hakkını alır. `get_subscription` transaction dışı bir
    # okuma ama tek yönlü: yalnızca İLERİ tarihli döneme tazeler, aynı
    # dönemde ikinci kez tetiklenemez (işaret eşitlenince koşul düşer).
    sub = entitlements.get_subscription(uid)
    if sub.get("active"):
        if _ts(sub.get("expiresAt")) > _ts(marker):
            allowance = MONTHLY_TOKEN_ALLOWANCE
            marker = sub.get("expiresAt")
    else:
        # Abonelik yoksa dönem de yok: sönmüş dönemden kalan hak HARCANAMAZ.
        # Yalnızca satın alınmış bakiye geçerlidir; o zaten devrediyor.
        allowance = 0

    purchased = int(data.get("purchased", 0))
    if allowance + purchased < cost:
        return False

    # Önce yanacak olan: dönem sonunda sıfırlanan allowance.
    dusen = min(allowance, cost)
    allowance -= dusen
    purchased -= cost - dusen

    transaction.set(ref, {
        "allowance": allowance,
        "allowanceExpiresAt": marker,
        "purchased": purchased,
        "updatedAt": _now(),
    })
    return True


def spend(uid: str, feature: str, *, lang: str = DEFAULT_LANG) -> None:
    """Özelliğin bedelini düşer; bakiye yetmezse 402 (tokens) fırlatır.

    Firestore erişilemezse İSTEK DÜŞÜRÜLMEZ (fail-open) — mevcut kota
    katmanının duruşuyla tutarlı: altyapı sorunu kullanıcının suçu değil.
    """
    cost = TOKEN_COSTS.get(feature)
    if not cost:
        return

    ref = _wallet_ref(uid)
    if ref is None:
        logger.warning("Cüzdan yok (Firestore kapalı); %s bedava geçti.", feature)
        return

    try:
        from google.cloud import firestore as gcf

        client = firestore_client.get_client()
        transaction = client.transaction()

        @gcf.transactional
        def _run(txn):
            return _spend_txn(txn, ref, uid, cost)

        yeterli = _run(transaction)
    except Exception as exc:
        logger.warning("Token düşümü yapılamadı (%s/%s): %s", uid, feature, exc)
        return

    if yeterli:
        return

    if not TOKENS_ENFORCE:
        # Kuru çalışma: reddedilecek isteği logla ama geçir. Bayrak
        # açılmadan önce üretimdeki gerçek etkiyi buradan ölçeriz.
        logger.info("TOKENS kuru-çalışma: %s/%s reddedilecekti.", uid, feature)
        return

    raise HTTPException(
        status_code=PAYWALL_STATUS,
        detail=text("tokens.empty", lang),
        headers={"X-Paywall-Reason": "tokens"},
    )


def refund_spend(uid: str, feature: str) -> None:
    """LLM üretemediyse bedeli iade eder — kullanıcı almadığı şeye ödemez.

    İade ``purchased``'a yazılır: hangi kovadan düştüğünü geri izlemek
    transaction dışında güvenilmez ve kullanıcı LEHİNE yanılmak doğrudur
    (purchased devrettiği için iade asla yanmaz).
    """
    cost = TOKEN_COSTS.get(feature)
    if not cost:
        return
    ref = _wallet_ref(uid)
    if ref is None:
        return
    try:
        from google.cloud import firestore as gcf
        ref.set({"purchased": gcf.Increment(cost), "updatedAt": _now()},
                merge=True)
    except Exception as exc:
        logger.warning("Token iadesi yapılamadı (%s/%s): %s", uid, feature, exc)


def spender(uid: str, feature: str, *, lang: str = DEFAULT_LANG) -> Callable[[], None]:
    """`_cached_generate`'e verilecek harcama geri çağrısı üretir."""
    def _spend() -> None:
        spend(uid, feature, lang=lang)
    return _spend


# ---------------------------------------------------------------------------
# Ücretsiz katman + cüzdan birleşik kapısı (sohbet / iching)
# ---------------------------------------------------------------------------

def charge_metered(user, feature: str, free_limit: int,
                   *, lang: str = DEFAULT_LANG) -> bool:
    """Günlük ücretsiz hak + cüzdanı tek kapıda birleştirir (ÖNBELLEKSİZ
    uçlar için — sohbet). Dönen değer: cüzdandan token düştü mü (iade
    kararı için; ücretsiz kotadan geçen istekte iade edilecek şey yok).

    Sıra: abone cüzdanından harcar (aylık hak bunun için var); ücretsiz
    kullanıcı önce günlük hakkını yer, bitince satın alınmış paketi varsa
    ondan harcar (paket almak için abonelik ŞART DEĞİL — bilinçli karar),
    o da yoksa mevcut kota metniyle 402.
    """
    from core.entitlements import consume_quota  # döngüsel import kırıcı

    if entitlements.is_subscriber(user.uid):
        spend(user.uid, feature, lang=lang)
        return True

    if consume_quota(user.uid, feature, free_limit):
        return False

    # Günlük hak bitti; paket bakiyesi kurtarabilir.
    wallet_state = get_wallet(user.uid)
    if wallet_state.get("purchased", 0) >= TOKEN_COSTS.get(feature, 0):
        spend(user.uid, feature, lang=lang)
        return True

    raise HTTPException(
        status_code=PAYWALL_STATUS,
        detail=text(f"quota.{feature}", lang, fallback="quota.default",
                    limit=free_limit),
    )


def metered_callbacks(user, feature: str, free_limit: int,
                      *, lang: str = DEFAULT_LANG,
                      ) -> tuple[Callable[[], None] | None,
                                 Callable[[], None] | None]:
    """ÖNBELLEKLİ ölçülü uçlar (iching) için harcama geri çağrıları.

    `charge_metered`'dan farkı: burada hiçbir şey HEMEN harcanmaz — dönen
    ``spend`` geri çağrısı `_cached_generate` içinde yalnızca önbellek
    kaçırıldığında çalışır. Peşin harcasaydık abone, saatlik önbellekteki
    aynı çekilişe ikinci bakışında da ödeme yapardı.

    Ücretsiz günlük hak İSE peşin düşer (bugünkü davranış): "günde 1 çekiliş"
    ritüel sınırıdır, üretim maliyeti sınırı değil.
    """
    from core.entitlements import consume_quota  # döngüsel import kırıcı

    def _spend() -> None:
        spend(user.uid, feature, lang=lang)

    def _refund() -> None:
        refund_spend(user.uid, feature)

    if entitlements.is_subscriber(user.uid):
        return _spend, _refund

    if consume_quota(user.uid, feature, free_limit):
        return None, None

    wallet_state = get_wallet(user.uid)
    if wallet_state.get("purchased", 0) >= TOKEN_COSTS.get(feature, 0):
        return _spend, _refund

    raise HTTPException(
        status_code=PAYWALL_STATUS,
        detail=text(f"quota.{feature}", lang, fallback="quota.default",
                    limit=free_limit),
    )


# ---------------------------------------------------------------------------
# Kredi — RevenueCat webhook'undan
# ---------------------------------------------------------------------------

def credit_pack(uid: str, product_id: str, event_id: str) -> bool:
    """Paket satın alımını cüzdana yükler. Olay kimliğiyle idempotent:
    webhook yeniden denemesi aynı paketi İKİ KEZ yükleyemez.
    """
    amount = TOKEN_PACKS.get(product_id)
    if not amount:
        return False
    ref = _wallet_ref(uid)
    if ref is None:
        # Yükleme kaybolmasın: hata fırlat ki webhook 500 görüp yeniden
        # denesin. Harcamadaki fail-open BURADA YANLIŞ olurdu — orada
        # kaybedilen tek istek, burada kullanıcının parası.
        raise RuntimeError("Firestore erisilemiyor; kredi ertelendi.")

    ledger_ref = ref.collection("ledger").document(str(event_id))

    from google.cloud import firestore as gcf

    client = firestore_client.get_client()
    transaction = client.transaction()

    @gcf.transactional
    def _run(txn) -> bool:
        if ledger_ref.get(transaction=txn).exists:
            return False  # zaten işlendi
        snapshot = ref.get(transaction=txn)
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        txn.set(ref, {**data,
                      "purchased": int(data.get("purchased", 0)) + amount,
                      "updatedAt": _now()})
        txn.set(ledger_ref, {"type": "credit", "productId": product_id,
                             "amount": amount, "at": _now()})
        return True

    islendi = _run(transaction)
    if islendi:
        logger.info("Token paketi yüklendi: uid=%s ürün=%s +%d", uid, product_id, amount)
    else:
        logger.info("Token kredisi zaten işlenmiş (idempotent): %s", event_id)
    return True


def credit_promo(uid: str, code: str, amount: int) -> bool:
    """Ortak kodu bonusunu cüzdana yükler (W7) — credit_pack'in varyantı.

    Defter kimliği ``promo-{KOD}``: aynı kullanıcı aynı kodu iki kez
    yükleyemez (uid başına idempotent; kod zaten attribution'la tek sefer
    ama savunma iki katmanlı). ``False`` = zaten işlenmişti.
    """
    if amount <= 0:
        return False
    ref = _wallet_ref(uid)
    if ref is None:
        raise RuntimeError("Firestore erisilemiyor; promo ertelendi.")

    ledger_ref = ref.collection("ledger").document(f"promo-{code}")

    from google.cloud import firestore as gcf

    client = firestore_client.get_client()
    transaction = client.transaction()

    @gcf.transactional
    def _run(txn) -> bool:
        if ledger_ref.get(transaction=txn).exists:
            return False
        snapshot = ref.get(transaction=txn)
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        txn.set(ref, {**data,
                      "purchased": int(data.get("purchased", 0)) + amount,
                      "updatedAt": _now()})
        txn.set(ledger_ref, {"type": "promo", "code": code,
                             "amount": amount, "at": _now()})
        return True

    islendi = _run(transaction)
    logger.info("Promo %s: uid=%s kod=%s +%d",
                "yüklendi" if islendi else "zaten işlenmiş", uid, code, amount)
    return islendi


def debit_refund(uid: str, product_id: str, event_id: str) -> bool:
    """Paket iadesini bakiyeden düşer (0'da kelepçe), defterle idempotent."""
    amount = TOKEN_PACKS.get(product_id)
    if not amount:
        return False
    ref = _wallet_ref(uid)
    if ref is None:
        raise RuntimeError("Firestore erisilemiyor; iade ertelendi.")

    ledger_ref = ref.collection("ledger").document(f"refund-{event_id}")

    from google.cloud import firestore as gcf

    client = firestore_client.get_client()
    transaction = client.transaction()

    @gcf.transactional
    def _run(txn) -> None:
        if ledger_ref.get(transaction=txn).exists:
            return
        snapshot = ref.get(transaction=txn)
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        # Kelepçe: kullanıcı bakiyeyi harcadıysa eksiye düşürmeyiz; mağaza
        # iade kararını verdi, biz borç defteri tutmayız.
        yeni = max(int(data.get("purchased", 0)) - amount, 0)
        txn.set(ref, {**data, "purchased": yeni, "updatedAt": _now()})
        txn.set(ledger_ref, {"type": "refund", "productId": product_id,
                             "amount": amount, "at": _now()})

    _run(transaction)
    logger.info("Token paketi iadesi işlendi: uid=%s ürün=%s", uid, product_id)
    return True


def reset_allowance(uid: str, expires_at: dt.datetime | None) -> None:
    """Yeni abonelik dönemi: aylık hakkı tazeler (webhook birincil yol,
    ``spend`` içindeki tembel tazeleme yedek).

    İşaret karşılaştırması idempotent kılar: aynı dönemin tekrarlanan
    webhook'u hakkı İKİ KEZ vermez.
    """
    if expires_at is None:
        return
    ref = _wallet_ref(uid)
    if ref is None:
        return
    try:
        snapshot = ref.get()
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}
        if _ts(expires_at) <= _ts(data.get("allowanceExpiresAt")):
            return
        ref.set({**data,
                 "allowance": MONTHLY_TOKEN_ALLOWANCE,
                 "allowanceExpiresAt": expires_at,
                 "updatedAt": _now()})
        logger.info("Aylık token hakkı tazelendi: uid=%s", uid)
    except Exception as exc:
        logger.warning("Hak tazelenemedi (%s): %s", uid, exc)


#: Devirde taşınan alanlar. Tüm dokümanı körlemesine kopyalamak yasak:
#: kaynakta cüzdan dışı bir şey varsa (bozuk yazım, ileride eklenen alan)
#: hedefte ne olduğu belirsiz bir doküman doğar.
_WALLET_FIELDS = ("allowance", "allowanceExpiresAt", "purchased")


def transfer_wallet(client, sources: list[str], targets: list[str]) -> None:
    """TRANSFER olayında cüzdanı da taşır — satın alınmış bakiye kullanıcının
    parasıdır, kimlik değişiminde kaybolamaz.

    Yalnızca [_WALLET_FIELDS] taşınır ve kaynakta bu alanlardan hiçbiri
    yoksa hedefe HİÇ yazılmaz: cüzdanı olmayan bir kimlikten devir, hedefin
    mevcut cüzdanını sıfırlamamalı.
    """
    def _ref(uid: str):
        return (client.collection("users").document(uid)
                .collection("private").document("wallet"))

    kayit: dict[str, Any] | None = None
    for kaynak in sources:
        try:
            snapshot = _ref(kaynak).get()
            if snapshot.exists and kayit is None:
                ham = snapshot.to_dict() or {}
                alanlar = {k: ham[k] for k in _WALLET_FIELDS if k in ham}
                kayit = alanlar or None
            _ref(kaynak).set({"allowance": 0, "purchased": 0,
                              "updatedAt": _now()}, merge=True)
        except Exception as exc:
            logger.warning("Cüzdan devri (kaynak %s) hatası: %s", kaynak, exc)

    if not kayit:
        return
    for hedef in targets:
        try:
            _ref(hedef).set({**kayit, "updatedAt": _now()}, merge=True)
        except Exception as exc:
            logger.warning("Cüzdan devri (hedef %s) hatası: %s", hedef, exc)
