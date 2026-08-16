import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel

from core import device, entitlements
from core.auth import AuthUser, get_current_user
from core.entitlements import FREE_CHAT_PER_DAY
from core.wallet import charge_metered, refund_spend
from core.i18n import get_language
from core.messages import text
from services import (
    chart_context,
    chat_history,
    chart_query,
    gemini_service,
    memory_extractor,
    memory_service,
    notification_service,
    profile_service,
    prompts,
    sky_service,
)
from services.prompt_composer import compose_chat_message, should_use_rag
from services.rag_service import retrieve_passages
from services.safety_rules import forbidden_topic
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageItem(BaseModel):
    sender: str  # USER | AI
    text: str


class ChatRequest(BaseModel):
    history: List[ChatMessageItem] = []
    message: str
    #: Sürdürülen konunun kimliği; boşsa yeni konu açılır ve yanıtta döner.
    conversation_id: str | None = None
    #: R4-2: soru bir ARKADAŞ bağlamındaysa arkadaşın kimliği. Sunucu
    #: arkadaşlığı doğrular ve ölçülen ilişki eksenlerini fısıltı olarak
    #: prompt'a ekler — istemciye ham doğum verisi HİÇ dönmez.
    friend_uid: str | None = None


def _sky_summary(lang: str, profile: dict | None = None) -> str:
    """Bugünün gökyüzünün kompakt özeti; hata durumunda boş döner.

    Gökyüzü sohbetin çalışması için zorunlu değil — alınamazsa sohbet
    haritasız/gökyüzsüz ama çalışır durumda devam eder.

    Etiketler dile bağlı: bu blok prompt'a giriyor ve İngilizce bir prompt'un
    içinde Türkçe etiketler modelin dili karıştırmasına yol açıyordu.

    ``profile`` yalnızca **saat dilimi** için kullanılır: günün yöneticisi
    kullanıcının yerel tarihine bağlıdır ve gökyüzü yükü UTC'de hesaplanıp
    tüm kullanıcılarla paylaşıldığı için oraya gömülemez.
    """
    try:
        sky = prompts.localize_sky(lang, get_sky_now())
    except Exception as exc:
        logger.warning("Gökyüzü alınamadı: %s", exc)
        return ""

    p = prompts.get(lang)
    moon = sky.get("moon_phase") or {}
    retros = ", ".join(sky.get("retrogrades", [])) or p.NONE_LABEL
    aspects = "; ".join(
        f"{a['p1']}-{a['p2']} {a['aspect']}" for a in (sky.get("aspects") or [])[:3]
    )

    satirlar = [
        p.SKY_MOON.format(name=moon.get("name"),
                          illumination=moon.get("illumination")),
        p.SKY_RETROS.format(retros=retros),
    ]
    if aspects:
        satirlar.append(p.SKY_ASPECTS.format(aspects=aspects))

    # Marifetname katmanı: korpusa girdiği hâlde motorda karşılığı olmayan
    # iki bilgi buradan geliyor. Karşılığı olmasaydı model bunlar hakkında
    # dayanaksız konuşurdu.
    yerel_gun = notification_service.local_now(profile or {}).date()
    satirlar.append(p.SKY_DAY_RULER.format(
        planet=prompts.planet_name(lang, sky_service.day_ruler(yerel_gun))))
    menzil = sky.get("moon_mansion") or {}
    if menzil:
        satirlar.append(p.SKY_MOON_MANSION.format(
            number=menzil.get("number"), name=menzil.get("name")))

    return "\n".join(satirlar)


@router.post("")
@router.post("/")
def chat(request: ChatRequest, background: BackgroundTasks,
         user: AuthUser = Depends(get_current_user),
         lang: str = Depends(get_language),
         x_device_id: str | None = Header(default=None)):
    """Sohbet: ucretsiz katmanda gunde [FREE_CHAT_PER_DAY] mesaj; abonede
    aylik token hakkindan, hak bitince satin alinan paketten harcanir.

    Bedel LLM cagrisindan ONCE dusulur; aksi halde hata donen istekler de
    kullaniciya bedava mesaj kazandirirdi. LLM yanit uretemezse iade edilir.
    """
    # Yasak alan kapısı kotadan ÖNCE: reddedilen bir soru kullanıcının günlük
    # hakkını yemez.
    blocked = forbidden_topic(request.message, lang=lang)
    if blocked is not None:
        kategori, reply = blocked
        logger.info("Yasak alan reddedildi: %s", kategori)
        return {"status": "success", "reply": reply, "blocked": kategori}

    # Tek cihaz kilidi (yalnızca abonede etkili) HARCAMADAN önce: 409 alan
    # istek token da yakmamalı.
    device.enforce_single_device(user.uid, x_device_id, lang=lang)

    # Ücretsiz günlük hak + token cüzdanı tek kapıda (Revize R1). Abone
    # cüzdanından harcar; ücretsiz kullanıcı önce günlük hakkını yer, sonra
    # varsa satın alınmış paketten. Sohbet ÖNBELLEKSİZ tek uç olduğu için
    # harcama peşin; LLM yanıt veremezse aşağıda iade edilir.
    token_harcandi = charge_metered(user, "chat", FREE_CHAT_PER_DAY, lang=lang)

    # Konu hedefi SENKRON çözülür (yanıt kimliği döndürmek zorunda), mesaj
    # yazımı arka planda (kullanıcı Firestore'u beklemez). Kırpma 422 yerine:
    # uzun yazan kullanıcının mesajını reddetmek yerine kısaltıyoruz.
    mesaj_metni = chat_history.clip_message(request.message)
    hazir_konu = chat_history.prepare(user.uid, request.conversation_id)

    try:
        # Prompt geçmişi tavanlı (K4): son 12 mesaj × 1.200 karakter —
        # arşiv kırpması değil, yalnız LLM'e giden girdinin maliyet sınırı.
        history = [
            {"sender": m.sender,
             "text": chat_history.clip_for_prompt(m.text)}
            for m in request.history[-chat_history.PROMPT_HISTORY_MESSAGES:]
        ]

        # Profil bir kez okunur, iki yerde kullanılır: haritayı prompt'a
        # iliştirmek ve bilgi tabanı sorgusunu kurmak.
        profile = profile_service.get_profile(user.uid)
        facts = chart_context.chart_facts(user.uid, profile) if profile else None

        # Seçici RAG: selamlaşma/duygu/kısa onay turlarında korpus araması
        # (ve embedding çağrısı) atlanır; kadim bilgi soran mesajlarda en
        # fazla 2 kırpılmış pasaj "arka plan fısıltısı" olarak eklenir.
        #
        # Arama artık kullanıcının CÜMLESİYLE değil, cümlenin konusu +
        # haritanın o konuyla ilgili faktörleriyle yapılıyor. "İşimle ilgili
        # ne yapmalıyım?" diye aramak kadim metinde hiçbir şeye denk gelmez;
        # "meslek, statü + Satürn 10. evde + Güneş Kare Mars" gelir.
        passages = []
        if should_use_rag(request.message, lang):
            sorgu = chart_query.build_query(request.message, facts, lang=lang)
            passages = retrieve_passages(sorgu, top_k=2, lang=lang)

        # Kullanıcı hafızası: "seni tanıyor" hissinin kaynağı burası. Okuma
        # ucuz (tek Firestore dokümanı) ve RAG'den bağımsız olarak her turda
        # yapılır — kullanıcı hakkında bilinenler her mesajda geçerlidir.
        memory = memory_service.memory_context(user.uid)

        # Kullanıcının haritası. Uzun süre yalnızca Güneş/Ay/Yükselen
        # geçiyordu; artık ev yerleşimleri, element dengesi, doğum açıları ve
        # bugün haritaya dokunan transitler de geliyor — cevabın "herkese
        # uyan" olmaktan çıkması bu ayrıntılara bağlı. Efemeris hesabı
        # önbellekli, LLM maliyeti yok.
        # BaZi fısıltısı yalnızca Rytho+ sohbetinde (Revize B8): BaZi
        # ücretli üründür; abone olmayanın prompt'una girmez — dürüst
        # kapı. Abonede "Day Master'ım ne?" deterministik veriyle yanıtlanır.
        chart = chart_context.chart_whisper(
            user.uid, profile, lang=lang, facts=facts,
            include_bazi=entitlements.is_subscriber(user.uid))

        # Bugünün gökyüzü paylaşımlı önbellekten gelir (kullanıcı başına
        # maliyeti yok) ve sohbetin "şu an" ile bağını kurar.
        sky = _sky_summary(lang, profile)

        # İlişki fısıltısı (R4-2): istemci arkadaş bağlamı gönderdiyse ve
        # arkadaşlık ÇİFT TARAFLI doğruysa ölçülen eksenler prompt'a girer.
        # Doğrulanamazsa bağlam SESSİZCE atlanır ve loglanır — sohbet
        # düşmez, model yalnız kullanıcının kendi haritasıyla cevaplar.
        relationship = ""
        if request.friend_uid and request.friend_uid != user.uid:
            if profile_service.are_friends(user.uid, request.friend_uid):
                try:
                    from services import synastry_service
                    relationship = synastry_service.relationship_whisper(
                        user.uid, request.friend_uid, lang)
                except Exception as exc:
                    logger.warning("İlişki fısıltısı üretilemedi (%s→%s): %s",
                                   user.uid, request.friend_uid, exc)
            else:
                logger.info("Sohbet ilişki bağlamı reddedildi: arkadaş "
                            "değil (%s→%s)", user.uid, request.friend_uid)

        message = compose_chat_message(mesaj_metni, passages,
                                       memory=memory, chart=chart, sky=sky,
                                       relationship=relationship, lang=lang)

        reply = gemini_service.chat(history, message, lang=lang)
        if reply is None:
            # Kullanıcı almadığı yanıta ödemez.
            if token_harcandi:
                refund_spend(user.uid, "chat")
            reply = text("llm_unavailable", lang)
        # Olgu çıkarımı yanıttan SONRA, arka planda: kullanıcı ikinci bir LLM
        # çağrısını beklemez. Kendi içinde kotalı ve hataya dayanıklı.
        background.add_task(
            memory_extractor.extract_and_store, user.uid, history, request.message
        )

        # Arşiv yazımı da arka planda (Revize R4). Hafıza çıkarıcı AYNEN
        # duruyor: damıtılmış olgular ile ham arşiv farklı işler görüyor —
        # biri "seni tanıyorum", öteki "kaldığın yerden devam".
        if hazir_konu is not None:
            background.add_task(
                chat_history.write_turn, user.uid, hazir_konu,
                mesaj_metni, reply, lang,
            )

        return {"status": "success", "reply": reply,
                "conversation_id": (hazir_konu.conversation_id
                                    if hazir_konu else None)}
    except Exception as e:
        logger.exception("Sohbet ucunda hata", exc_info=e)
        raise HTTPException(status_code=500, detail=text("internal", lang))


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str,
                        user: AuthUser = Depends(get_current_user),
                        lang: str = Depends(get_language)):
    """Konuyu mesajlarıyla siler.

    Uçtan, çünkü istemci `conversations` altına YAZAMAZ (rules) — silme de
    bir yazımdır. Yalnızca kendi konuları: yol kimliği değil, doğrulanmış
    oturum kimliği kullanılır.
    """
    try:
        silinen = chat_history.delete_conversation(user.uid, conversation_id)
    except Exception as exc:
        logger.exception("Konu silinemedi (%s)", user.uid, exc_info=exc)
        raise HTTPException(status_code=500, detail=text("internal", lang))
    return {"status": "success", "deleted_messages": silinen}


# `/moderate` ucu KALDIRILDI (Revize R0).
#
# Docstring'i "istemci çağırır" diyordu ama hiçbir istemci çağırmıyordu:
# sosyal katman serbest metin içermiyor (hazır tepkiler), moderasyona konu
# içerik yok. Buna karşılık uç kotasız ve `require_plus`'sız bir LLM
# çağrısıydı — kimliği doğrulanmış herhangi bir istemci 60 istek/dk hızında
# bütçe yakabilirdi. Ölü VE masraflı kodun kotalanmış hâli değil, yokluğu
# doğrudur. Sosyal serbest metin bir gün gelirse denetim, çağıranın kendi
# ucunda kota arkasında kurulmalı.
