"""Bildirim uçları: zamanlayıcı tetikli toplu gönderim + olay tetikli tekil.

İki farklı güven modeli var ve bilinçli olarak ayrılmıştır:

- ``POST /run`` yalnızca **Cloud Scheduler** tarafından çağrılır ve paylaşılan
  gizli anahtarla korunur. Bu uç tüm kullanıcılara bildirim gönderebilir;
  kullanıcı oturumuyla erişilebilir olsaydı herkes herkese bildirim
  attırabilirdi.
- ``POST /reaction`` normal kullanıcı oturumuyla çağrılır ama **yalnızca
  karşılıklı arkadaşa** ve **kapalı tepki kümesinden** gönderim yapar; ikisi
  de sunucuda doğrulanır (istemcinin söylediğine güvenilmez).

Zamanlayıcı SAATTE BİR çalışır; hangi kullanıcının sırası geldiğine
notification_service karar verir (yerel saat + sessiz saat + tekrar koruması).
"""
from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from core import config, i18n
from core import firestore as firestore_client
from core.auth import AuthUser, get_current_user
from core.i18n import get_language
from core.messages import text
from services import (
    chat_history,
    notification_service,
    profile_service,
    prompts,
    push_service,
)
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter()

#: Kullanıcı taramasında tek seferde okunacak doküman sayısı. Tüm koleksiyonu
#: belleğe almak, kullanıcı sayısı büyüdüğünde instance'ı düşürürdü.
PAGE_SIZE = 500

#: Arkadaş tepkisi bildiriminde gösterilebilecek tepkiler. Firestore kuralıyla
#: (infra/firestore.rules, nudges) AYNI küme olmak zorunda.
REACTION_EMOJIS = {
    "streak": "🔥",
    "thinking_of_you": "💭",
    "shine": "✨",
    "keep_going": "💪",
    "congrats": "🎉",
    # OB5 onarımı: burası 🌊 idi, mobil picker 🛰️ gösteriyor — kullanıcının
    # BASTIĞI emoji kanonik olandır; alıcı farklı bir emoji görmemeli.
    "same_frequency": "🛰️",
    "good_night": "🌙",
    "check_today": "👀",
    # R3-4 genişlemesi — mobil kReactions + firestore.rules ile aynı küme.
    "hug": "🤗",
    "luck": "🍀",
    "coffee": "☕",
    "miss": "🫶",
}

#: Tepki anahtarı -> dile göre etiket. İstemcideki reactionLabel ile aynı
#: metinler; bildirim sunucuda üretildiği için burada da gerekli.
REACTION_LABELS = {
    "tr": {
        "streak": "Seriyi sürdür",
        "thinking_of_you": "Seni düşündüm",
        "shine": "Parlıyorsun",
        "keep_going": "Devam et",
        "congrats": "Tebrikler",
        "same_frequency": "Aynı frekans",
        "good_night": "İyi geceler",
        "check_today": "Bugüne bak",
        "hug": "Sarıldım",
        "luck": "Bol şans",
        "coffee": "Kahve içelim",
        "miss": "Özledim",
    },
    "en": {
        "streak": "Keep the streak",
        "thinking_of_you": "Thinking of you",
        "shine": "You're shining",
        "keep_going": "Keep going",
        "congrats": "Congrats",
        "same_frequency": "Same frequency",
        "good_night": "Good night",
        "check_today": "Check today",
        "hug": "A hug",
        "luck": "Good luck",
        "coffee": "Coffee soon?",
        "miss": "Miss you",
    },
}


def _verify_scheduler(authorization: str | None) -> None:
    if not config.NOTIFY_SCHEDULER_SECRET:
        logger.error("NOTIFY_SCHEDULER_SECRET tanimsiz; uc reddedildi.")
        raise HTTPException(status_code=503,
                            detail="Bildirim zamanlayicisi yapilandirilmamis.")
    if not authorization or not secrets.compare_digest(
        authorization, config.NOTIFY_SCHEDULER_SECRET
    ):
        raise HTTPException(status_code=401, detail="Gecersiz zamanlayici anahtari.")


def _iter_profiles():
    """Kullanıcı profillerini sayfalayarak dolaşır."""
    client = firestore_client.get_client()
    if client is None:
        return

    from google.cloud.firestore_v1.base_query import FieldFilter

    son = None
    while True:
        sorgu = (client.collection("users")
                 .where(filter=FieldFilter("onboardingCompleted", "==", True))
                 .order_by("__name__")
                 .limit(PAGE_SIZE))
        if son is not None:
            sorgu = sorgu.start_after({"__name__": son})

        sayfa = list(sorgu.stream())
        if not sayfa:
            return
        for anlik in sayfa:
            veri = anlik.to_dict() or {}
            veri["uid"] = anlik.id
            yield veri
        son = sayfa[-1].id
        if len(sayfa) < PAGE_SIZE:
            return


class RunResult(BaseModel):
    status: str
    type: str
    scanned: int
    queued: int
    sent: int
    failed: int
    pruned: int
    #: Neden gönderilmediğinin dökümü — sessiz düşen bildirimler görünür olmalı.
    skipped: dict[str, int]
    #: Kuyruğa giren mesajların dil dökümü (DM-turu): "hem İngilizce hem
    #: Türkçe" bulgusundan sonra hangi dilde kaç push gittiği görünür olmalı.
    languages: dict[str, int] = Field(default_factory=dict)


def _kosu_kaydet(type_: str, gun: str, sonuc: RunResult,
                 now_utc: dt.datetime) -> None:
    """Koşu sonucunu kalıcılaştırır (AP-turu) — panel "bildirim sağlığı".

    Eskiden RunResult yalnız HTTP yanıtı olarak Cloud Scheduler'a dönüp
    kayboluyordu. Doküman kimliği deterministik ``{gün}-{tür}``; zamanlayıcı
    SAATTE BİR koştuğu için sayılar Increment ile BİRİKİR (set ezseydi gün
    toplamı son saatin sayısına inerdi). Best-effort: yazım düşerse koşu
    düşmez. dry_run buraya hiç uğramaz (prova iz bırakmaz).
    """
    try:
        client = firestore_client.get_client()
        if client is None:
            return
        from google.cloud import firestore as gcf
        client.collection("notifyRuns").document(f"{gun}-{type_}").set({
            "date": gun,
            "type": type_,
            "runs": gcf.Increment(1),
            "scanned": gcf.Increment(sonuc.scanned),
            "queued": gcf.Increment(sonuc.queued),
            "sent": gcf.Increment(sonuc.sent),
            "failed": gcf.Increment(sonuc.failed),
            "pruned": gcf.Increment(sonuc.pruned),
            "skipped": {k: gcf.Increment(v) for k, v in sonuc.skipped.items()},
            "lastStatus": sonuc.status,
            "lastRunAt": now_utc,
        }, merge=True)
    except Exception as exc:
        logger.warning("Bildirim koşusu kaydedilemedi (%s/%s): %s",
                       gun, type_, exc)


@router.post("/run", response_model=RunResult)
def run(type: Literal["daily", "midday", "checkin", "streak"] = "daily",
        dry_run: bool = False,
        force: bool = False,
        ignore_dedupe: bool = False,
        authorization: str | None = Header(default=None)) -> RunResult:
    """Cloud Scheduler tetikli toplu gönderim.

    Saatte bir çağrılır. Her kullanıcı için yerel saat hesaplanır ve yalnızca
    hedef saate denk gelenlere gönderilir; böylece tek bir zamanlayıcı işi tüm
    saat dilimlerini karşılar.

    İki operasyon bayrağı (ikisi de zamanlayıcı anahtarının arkasında):

    - ``dry_run``: her şey hesaplanır ama **hiçbir bildirim gönderilmez** ve
      gönderim kaydı yazılmaz. Deploy sonrası "kime gidecekti" sorusunu
      cevaplar; sıfır riskli.
    - ``force``: yalnızca **hedef saat** kontrolünü atlar.
    - ``ignore_dedupe``: yalnızca **tekrar koruması** kontrolünü atlar; tek
      başına anlamsız olduğu için ``force`` ile birlikte kullanılmalıdır.
      Aynı gün ikinci bir duman testi yapabilmek için var.

    **Sessiz saat ve kullanıcı tercihi hiçbir bayrakla atlanmaz.**
    """
    _verify_scheduler(authorization)

    if ignore_dedupe and not force:
        raise HTTPException(
            status_code=400,
            detail="ignore_dedupe yalnizca force ile birlikte kullanilir.")

    now_utc = dt.datetime.now(dt.timezone.utc)
    # Gökyüzü bir kez okunur ve tüm kullanıcılar için paylaşılır.
    try:
        ham_sky = get_sky_now()
    except Exception as exc:
        logger.warning("Bildirim icin gokyuzu alinamadi: %s", exc)
        ham_sky = {}

    mesajlar: list[push_service.Message] = []
    isaretlenecek: list[tuple[str, str]] = []  # (uid, yerel gün)
    # OT1.1: daily gönderiminin hafıza alanları (gövde + odak sinyal) —
    # başarılı gönderimden sonra mark_sent'e `extra` olarak geçer.
    ekstralar: dict[str, dict[str, Any]] = {}
    taranan = 0
    atlanan: dict[str, int] = {}
    # DM-turu: kuyruğa giren mesajların dil sayımı (özet loga ve yanıta).
    diller: dict[str, int] = {}
    # Dil başına yerelleştirilmiş gökyüzü; her kullanıcı için yeniden
    # hesaplamaya gerek yok.
    sky_by_lang: dict[str, dict[str, Any]] = {}

    for profil in _iter_profiles():
        taranan += 1
        gonder, gerekce = notification_service.should_send(
            profil, type, now_utc, ignore_target_hour=force,
            ignore_dedupe=ignore_dedupe)
        if not gonder:
            atlanan[gerekce] = atlanan.get(gerekce, 0) + 1
            continue

        lang = notification_service.profile_language(profil)
        yerel = notification_service.local_now(profil, now_utc)
        gun = yerel.date().isoformat()
        # SS-turu: gövde SORU biçimliyse üretici bunu beyan eder; sohbet
        # tohumu dil kapısından SONRA atılır (aşağıda).
        soru = False

        if type == "daily":
            sign = profile_service.sun_sign_key(profil)
            if sign is None:
                atlanan["burc-bilinmiyor"] = atlanan.get("burc-bilinmiyor", 0) + 1
                continue
            if lang not in sky_by_lang:
                sky_by_lang[lang] = prompts.localize_sky(lang, ham_sky)
            # R2-S4 → KA-turu: sabah bildirimi kullanıcının 1 numaralı
            # sinyalinin O GÜNE ÖZGÜ AI cümlesi (uç ile paylaşılan
            # paket — günde toplam bir üretim). Üretilemezse paylaşımlı
            # burç satırına geri düşülür; bildirim asla atlanmaz.
            # `route`/`fp`/`idx`/`d`: dokununca ilgili sinyal kartının
            # dayanak sayfası açılsın diye (KA5) — eski istemci bu
            # alanları yok sayar, davranışı değişmez.
            # OT1.3: dünkü gönderimin hafızası tema çarkını döndürür ve
            # "dünle aynı metin" korumasını besler; gönderilen gövde
            # `ekstra` ile geri yazılır (öğle kopya koruması ona bakar).
            onceki = notification_service.last_daily_sent(profil["uid"])
            sinyal_push = notification_service.signal_push(
                profil, lang, today=yerel.date(), onceki=onceki)
            if sinyal_push is not None:
                baslik, govde, iz, idx, ekstra = sinyal_push
                veri = {"type": "daily", "sign": sign, "route": "signal",
                        "fp": iz, "idx": str(idx), "d": gun}
                ekstralar[profil["uid"]] = ekstra
            else:
                baslik = prompts.get(lang).PUSH_DAILY_TITLE
                govde = notification_service.daily_push_body(
                    sign, sky_by_lang[lang], lang, gun)
                # BY-turu: yedek yol da hedefli — dokununca günlük okuma
                # (hikâye) açılır; eskiden yalnız sekme atanıyordu.
                veri = {"type": "daily", "sign": sign,
                        "route": "story", "d": gun}
        elif type == "midday":
            # OB3 → OT1.2: öğle ölçülü slotu — yalnız BUGÜN gerçekten
            # olay varsa gider ve SABAH GÖVDESİNİN KOPYASI ASLA gitmez
            # ("sabahla-ayni" gerekçesiyle görünür atlanır). LLM yakmaz.
            ogle, gerekce = notification_service.midday_push(
                profil, lang, today=yerel.date())
            if ogle is None:
                atlanan[gerekce] = atlanan.get(gerekce, 0) + 1
                continue
            baslik, govde, veri = ogle
        elif type == "checkin":
            # KA4: günün önemli sinyaline bağlı kişisel soru — yalnız
            # sabah paketinde soru YAZILMIŞSA gider; LLM çağrılmaz.
            # Soru FCM yükünde taşınır: içeriği yalnız transit
            # satırlarından üretildiği için kişisel veri sızdırmaz.
            checkin = notification_service.checkin_push(
                profil, lang, today=yerel.date())
            if checkin is None:
                atlanan["soru-yok"] = atlanan.get("soru-yok", 0) + 1
                continue
            baslik, govde = checkin.baslik, checkin.govde
            veri = {"type": "checkin", "route": "chat",
                    "q": govde, "q_date": gun}
            soru = checkin.soru
        else:
            baslik, govde = notification_service.streak_push(profil, lang)
            # BY-turu: "okumanı açmadın" dokununca okumayı AÇAR (hikâye) —
            # yalnız {type} taşıyan eski yükün hedefi yoktu.
            veri = {"type": "streak", "route": "story", "d": gun}

        # DM-turu son emniyet ağı: hangi dalda üretilmiş olursa olsun,
        # başlık ya da gövde profil dilinin DIŞINDA görünüyorsa push
        # GİTMEZ ve görünür atlanır. Üreticiler kendi muhafızını taşır
        # (`_bundle_body`, `checkin_push`); burası kaçağı yakalayan ağ.
        # Sohbet tohumu bu kapıdan SONRA: yanlış dilde soru sohbete girmez.
        if (i18n.language_conflicts(govde, lang)
                or i18n.language_conflicts(baslik, lang)):
            logger.warning(
                "Bildirim dil uyuşmazlığı, gönderilmedi: uid=%s tur=%s "
                "lang=%s baslik=%r govde=%r",
                profil["uid"], type, lang, baslik, govde)
            atlanan["dil-uyusmaz"] = atlanan.get("dil-uyusmaz", 0) + 1
            continue

        # SS-turu: gövde bir SORUysa Rytho sohbette ÖNCE yazar. Karar tür
        # adından değil üreticinin beyanından (`soru`) geliyor. `dry_run`
        # tohumlamaz: prova iz bırakmaz. `cid` yüke `push_service.send`'den
        # ÖNCE girmek zorunda, bu yüzden tohum döngünün içinde kalıyor.
        if soru and not dry_run:
            cid = chat_history.seed_assistant_message(
                profil["uid"], govde, lang, gun)
            if cid:
                veri["route"] = "chat_answer"
                veri["cid"] = cid

        diller[lang] = diller.get(lang, 0) + 1
        mesajlar.append(push_service.Message(
            uid=profil["uid"], token=profil["fcmToken"],
            title=baslik, body=govde, data=veri,
        ))
        isaretlenecek.append((profil["uid"], gun))

    if dry_run:
        logger.info("Bildirim PROVA turu=%s taranan=%d kuyruk=%d diller=%s "
                    "atlanan=%s",
                    type, taranan, len(mesajlar), diller, atlanan)
        return RunResult(
            status="dry-run", type=type, scanned=taranan,
            queued=len(mesajlar), sent=0, failed=0, pruned=0, skipped=atlanan,
            languages=diller,
        )

    sonuc = push_service.send(mesajlar)

    # Gönderim kaydı SONRA yazılır: önce yazsaydık ve gönderim düşseydi,
    # kullanıcı o gün bildirimi hiç almazdı. OT1.5: GEÇİCİ hatalar da
    # işaretlenmez (eskiden yalnız ölü token'lar atlanıyordu ve FCM'in
    # anlık hatası kullanıcının o gününü sessizce yakıyordu) — zamanlayıcı
    # aynı hedef saat penceresi içinde yeniden dener. Süreç gönderim ile
    # işaretleme arasında ölürse dar bir çift-gönderim penceresi kalır;
    # kabul edilmiş sınır (işlemsel FCM+Firestore yok).
    basarisiz_uidler = set(sonuc.failed_uids)
    for uid, gun in isaretlenecek:
        if uid not in basarisiz_uidler:
            notification_service.mark_sent(uid, type, gun,
                                           extra=ekstralar.get(uid))

    logger.info("Bildirim turu=%s taranan=%d kuyruk=%d gonderilen=%d "
                "basarisiz=%d temizlenen=%d diller=%s atlanan=%s",
                type, taranan, len(mesajlar), sonuc.sent, sonuc.failed,
                len(sonuc.pruned), diller, atlanan)

    yanit = RunResult(
        status="ok", type=type, scanned=taranan, queued=len(mesajlar),
        sent=sonuc.sent, failed=sonuc.failed, pruned=len(sonuc.pruned),
        skipped=atlanan, languages=diller,
    )
    _kosu_kaydet(type, now_utc.date().isoformat(), yanit, now_utc)
    return yanit


class ReactionPush(BaseModel):
    friend_uid: str = Field(min_length=1, max_length=128)
    reaction: str = Field(min_length=1, max_length=32)


@router.post("/reaction")
def reaction(req: ReactionPush,
             user: AuthUser = Depends(get_current_user),
             lang: str = Depends(get_language)):
    """Arkadaşa gönderilen hazır tepkinin bildirimi.

    İstemci tepkiyi Firestore'a yazdıktan sonra burayı çağırır. Sunucu
    istemciye güvenmez: arkadaşlık karşılıklı mı, tepki kapalı kümede mi,
    alıcı bu bildirimi istiyor mu — hepsi burada doğrulanır.

    Bildirim gönderilemese bile 200 döner: tepki zaten Firestore'a yazıldı ve
    uygulama içindeki kutuda görünüyor. Push, üstüne eklenen bir şey.
    """
    if req.reaction not in REACTION_EMOJIS:
        raise HTTPException(status_code=400, detail=text("reaction.unknown", lang))

    if req.friend_uid == user.uid:
        raise HTTPException(status_code=400, detail=text("dyad.self", lang))

    if not profile_service.are_friends(user.uid, req.friend_uid):
        raise HTTPException(status_code=403,
                            detail=text("dyad.not_friends", lang))

    alici = profile_service.get_profile(req.friend_uid) or {}
    alici["uid"] = req.friend_uid
    gonder, gerekce = notification_service.can_send_event(alici, "friend")
    if not gonder:
        logger.info("Tepki bildirimi atlandi (%s): %s", req.friend_uid, gerekce)
        return {"status": "skipped", "reason": gerekce}

    gonderen = profile_service.get_profile(user.uid) or {}
    alici_dili = notification_service.profile_language(alici)
    etiket = REACTION_LABELS.get(alici_dili, REACTION_LABELS["tr"])[req.reaction]

    baslik, govde = notification_service.friend_push(
        name=gonderen.get("displayName") or gonderen.get("username") or "…",
        emoji=REACTION_EMOJIS[req.reaction],
        label=etiket,
        lang=alici_dili,
    )

    sonuc = push_service.send([push_service.Message(
        uid=req.friend_uid, token=alici["fcmToken"],
        title=baslik, body=govde,
        # `src` (BY-turu): istemci tepkiyi davetten/kabulden ayırt edip
        # doğru hedefe yönlendirir (src: midday konvansiyonu).
        data={"type": "friend", "fromUid": user.uid, "src": "reaction"},
    )])
    return {"status": "ok", "sent": sonuc.sent}


class InvitePush(BaseModel):
    friend_uid: str = Field(min_length=1, max_length=128)


def _event_push(alici_uid: str, gonderen_uid: str, tur: str,
                baslik_sablonu: str, govde_sablonu: str,
                src: str) -> dict[str, Any]:
    """Davet/kabul push'unun ortak kuyruğu (OB2).

    Doğrulama ÇAĞIRANDA biter; buradan sonrası asla raise etmez — davet
    Firestore'a zaten yazıldı, push üstüne eklenen bir şeydir (tepki
    ucuyla aynı sözleşme). Tekrar koruması alıcının dokümanında
    ``{tur}LastSent`` günüyle: aynı çift aynı gün en fazla bir push
    (davet geri çek-tekrar gönder spam'ine karşı ikinci hat; birinci
    hat çağırandaki gerçek-kenar doğrulaması).
    """
    alici = profile_service.get_profile(alici_uid) or {}
    alici["uid"] = alici_uid

    gonder, gerekce = notification_service.can_send_event(alici, "friend")
    if not gonder:
        logger.info("Davet bildirimi atlandi (%s/%s): %s",
                    tur, alici_uid, gerekce)
        return {"status": "skipped", "reason": gerekce}

    gun = notification_service.local_now(alici).date().isoformat()
    if notification_service.already_sent(alici_uid, tur, gun):
        logger.info("Davet bildirimi atlandi (%s/%s): zaten-gonderildi",
                    tur, alici_uid)
        return {"status": "skipped", "reason": "zaten-gonderildi"}

    gonderen = profile_service.get_profile(gonderen_uid) or {}
    ad = gonderen.get("displayName") or gonderen.get("username") or "…"
    alici_dili = notification_service.profile_language(alici)
    p = prompts.get(alici_dili)

    sonuc = push_service.send([push_service.Message(
        uid=alici_uid, token=alici["fcmToken"],
        title=getattr(p, baslik_sablonu).format(name=ad),
        body=getattr(p, govde_sablonu),
        # `type=friend` + `src` (BY-turu): davet Çevrem sekmesine (istek
        # en üstte), kabul ise doğrudan o arkadaşın ilişki ekranına
        # yönlenir — istemci kararı `src` ile verir.
        data={"type": "friend", "fromUid": gonderen_uid, "src": src},
    )])
    if sonuc.sent:
        notification_service.mark_sent(alici_uid, tur, gun)
    return {"status": "ok", "sent": sonuc.sent}


@router.post("/invite")
def invite(req: InvitePush,
           user: AuthUser = Depends(get_current_user),
           lang: str = Depends(get_language)):
    """Arkadaş daveti gönderilince karşı tarafa push (OB2).

    Davet akışı bugüne dek tamamen sessizdi: istemci Firestore'a kenarları
    yazar, karşı taraf ancak uygulamayı açınca görürdü. Bu uç istemciden
    sonra çağrılır ve istemciye güvenmez: alıcının ağacında GERÇEK bir
    ``incoming`` kenarı olmalı — firestore.rules o kenarı yalnız gerçek
    davet akışının kurmasına izin verdiği için "davet etmeden push atma"
    vektörü kaynağında kapalı.
    """
    if req.friend_uid == user.uid:
        raise HTTPException(status_code=400, detail=text("dyad.self", lang))

    if not profile_service.has_pending_invite(user.uid, req.friend_uid):
        raise HTTPException(status_code=403, detail=text("invite.none", lang))

    return _event_push(req.friend_uid, user.uid, f"invite-{user.uid}",
                       "PUSH_INVITE_TITLE", "PUSH_INVITE_BODY",
                       src="invite")


@router.post("/invite-accepted")
def invite_accepted(req: InvitePush,
                    user: AuthUser = Depends(get_current_user),
                    lang: str = Depends(get_language)):
    """Davet kabul edilince daveti GÖNDERENE push (OB2).

    Kabulden sonra iki kenar da ``accepted`` olduğu için yönün kim davet
    etti tarafı ispatlanamaz (bilinen sınır); ``are_friends`` çift taraflı
    doğrulaması + çift-başına-günlük tekrar koruması bunu zararsız kılar.
    """
    if req.friend_uid == user.uid:
        raise HTTPException(status_code=400, detail=text("dyad.self", lang))

    if not profile_service.are_friends(user.uid, req.friend_uid):
        raise HTTPException(status_code=403,
                            detail=text("dyad.not_friends", lang))

    return _event_push(req.friend_uid, user.uid, f"accept-{user.uid}",
                       "PUSH_INVITE_ACCEPTED_TITLE",
                       "PUSH_INVITE_ACCEPTED_BODY",
                       src="invite_accepted")
