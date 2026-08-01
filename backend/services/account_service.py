"""Hesap silme.

Apple 5.1.1(v) ve Google Play, hesap oluşturmaya izin veren her uygulamada
**uygulama içinden** hesap silmeyi zorunlu tutuyor. Tek başına red sebebi.

Silme yalnızca kullanıcının kendi dokümanını kaldırmak değil: veri altı
koleksiyonlara, ikinci bir koleksiyona (kullanıcı adı rezervasyonu), BAŞKA
kullanıcıların dokümanlarına (karşılıklı arkadaşlık kayıtları, gönderdiğim
tepkiler) ve kişiye özel yapay zeka üretimlerine dağılmış durumda. Bunlardan
biri atlanırsa "hesabımı sildim" diyen kullanıcının verisi sistemde kalır.

**Bilinçli istisna: şikayet kayıtları (`reports`).** Bunlar başka kullanıcılar
hakkında güvenlik kayıtlarıdır; silinmeleri kötü niyetli bir kullanıcının
hesabını silerek kanıtı ortadan kaldırmasına izin verirdi. Gizlilik metninde
açıkça yazılıdır.

Sıra önemlidir: önce veriler, en son kimlik. Kimliği önce silseydik ve veri
silme yarıda kalsaydı, kullanıcı geri dönüp tekrar deneyemezdi.
"""
from __future__ import annotations

import logging
from typing import Any

from core import config, firestore as firestore_client

logger = logging.getLogger(__name__)

#: Kullanıcı dokümanının altındaki tüm koleksiyonlar.
_SUB_COLLECTIONS = ("private", "friends", "nudges", "blocked")

#: Tek seferde silinecek doküman sayısı.
_BATCH = 200


class DeletionReport(dict):
    """Neyin silindiğinin sayımı. Log ve testte kanıt olarak kullanılır."""


def _delete_collection(coll_ref, sayac: DeletionReport, ad: str) -> None:
    """Bir koleksiyonu sayfalayarak siler (alt koleksiyonlar dahil değil)."""
    while True:
        belgeler = list(coll_ref.limit(_BATCH).stream())
        if not belgeler:
            return
        for belge in belgeler:
            belge.reference.delete()
        sayac[ad] = sayac.get(ad, 0) + len(belgeler)
        if len(belgeler) < _BATCH:
            return


def _delete_user_subcollections(client, uid: str,
                                sayac: DeletionReport) -> None:
    kullanici = client.collection("users").document(uid)
    for ad in _SUB_COLLECTIONS:
        try:
            _delete_collection(kullanici.collection(ad), sayac, ad)
        except Exception as exc:
            logger.warning("Alt koleksiyon silinemedi (%s/%s): %s", uid, ad, exc)


def _delete_friend_edges(client, uid: str, sayac: DeletionReport) -> None:
    """Arkadaşlık ÇİFT TARAFLI tutuluyor; karşı taraftaki kayıt da silinmeli.

    Silinmezse arkadaşın listesinde artık var olmayan bir kişi görünür ve
    o kişiye ikili okuma denenebilir.
    """
    kullanici = client.collection("users").document(uid)
    try:
        arkadaslar = [b.id for b in kullanici.collection("friends").stream()]
    except Exception as exc:
        logger.warning("Arkadas listesi okunamadi (%s): %s", uid, exc)
        return

    for arkadas_uid in arkadaslar:
        karsi = client.collection("users").document(arkadas_uid)
        try:
            karsi.collection("friends").document(uid).delete()
            sayac["friendEdges"] = sayac.get("friendEdges", 0) + 1
        except Exception as exc:
            logger.warning("Karsi arkadaslik silinemedi (%s): %s",
                           arkadas_uid, exc)

        # Bu kişiye gönderdiğim, henüz okunmamış tepkiler.
        try:
            from google.cloud.firestore_v1.base_query import FieldFilter

            gelen = (karsi.collection("nudges")
                     .where(filter=FieldFilter("fromUid", "==", uid))
                     .stream())
            for belge in gelen:
                belge.reference.delete()
                sayac["sentNudges"] = sayac.get("sentNudges", 0) + 1
        except Exception as exc:
            logger.warning("Gonderilen tepkiler silinemedi (%s): %s",
                           arkadas_uid, exc)


def _delete_username(client, uid: str, profil: dict[str, Any],
                     sayac: DeletionReport) -> None:
    """Kullanıcı adı rezervasyonunu serbest bırakır.

    Bırakılmazsa ad sonsuza kadar tutulu kalır ve başkası alamaz.
    """
    username = (profil or {}).get("username")
    if not username:
        return
    try:
        kayit = client.collection("usernames").document(username).get()
        # Yalnızca gerçekten bu kullanıcıya aitse sil; ad devredilmiş olabilir.
        if kayit.exists and (kayit.to_dict() or {}).get("uid") == uid:
            kayit.reference.delete()
            sayac["username"] = 1
    except Exception as exc:
        logger.warning("Kullanici adi birakilamadi (%s): %s", uid, exc)


def _delete_owned_cache(client, uid: str, sayac: DeletionReport) -> None:
    """Kişiye özel yapay zeka üretimlerini siler.

    Önbellek dokümanının kimliği anahtarın özeti olduğu için kullanıcıya göre
    sorgulanamaz; bu yüzden kişiye özel kayıtlara ``ownerUid`` yazılıyor
    (bkz. core/cache.py). Paylaşımlı kayıtlar (burç yorumu, gökyüzü) sahipsiz
    olduğu için bu sorguya girmez — bir kullanıcının hesabını silmesi herkesin
    yorumunu silmemeli.
    """
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter

        while True:
            belgeler = list(
                client.collection(config.CACHE_COLLECTION)
                .where(filter=FieldFilter("ownerUid", "==", uid))
                .limit(_BATCH).stream())
            if not belgeler:
                return
            for belge in belgeler:
                belge.reference.delete()
            sayac["aiCache"] = sayac.get("aiCache", 0) + len(belgeler)
            if len(belgeler) < _BATCH:
                return
    except Exception as exc:
        logger.warning("Kisiye ozel onbellek silinemedi (%s): %s", uid, exc)


def delete_account(uid: str) -> DeletionReport:
    """Kullanıcının tüm verisini siler ve kimliğini kaldırır.

    Sıra bilinçli: veriler önce, kimlik en son. Kimliği önce silseydik ve veri
    silme yarıda kalsaydı kullanıcı geri dönüp tekrar deneyemezdi — verisi
    sistemde kalır, kendisi de erişemezdi.
    """
    sayac = DeletionReport()
    client = firestore_client.get_client()

    if client is None:
        # Veriyi silemeden kimliği silmek, sahipsiz veri birakmak olur.
        raise RuntimeError("Firestore erisilemiyor; silme yapilmadi.")

    kullanici_ref = client.collection("users").document(uid)
    try:
        profil = (kullanici_ref.get().to_dict() or {})
    except Exception as exc:
        logger.warning("Profil okunamadi (%s): %s", uid, exc)
        profil = {}

    # 1. Başka kullanıcılardaki izler (önce: kendi listem hâlâ duruyorken)
    _delete_friend_edges(client, uid, sayac)

    # 2. Kendi alt koleksiyonlarım (hafıza, abonelik, bildirim kaydı, tepkiler)
    _delete_user_subcollections(client, uid, sayac)

    # 3. Kişiye özel yapay zeka üretimleri
    _delete_owned_cache(client, uid, sayac)

    # 4. Herkese açık kart ve kullanıcı adı
    _delete_username(client, uid, profil, sayac)
    try:
        client.collection("publicProfiles").document(uid).delete()
        sayac["publicProfile"] = 1
    except Exception as exc:
        logger.warning("Herkese acik kart silinemedi (%s): %s", uid, exc)

    # 5. Ana profil (doğum verisi burada)
    try:
        kullanici_ref.delete()
        sayac["user"] = 1
    except Exception as exc:
        logger.error("Kullanici dokumani silinemedi (%s): %s", uid, exc)
        raise

    # 6. Kimlik — en son
    sayac["auth"] = 1 if _delete_auth_user(uid) else 0

    logger.info("Hesap silindi: uid=%s sayim=%s", uid, dict(sayac))
    return sayac


def _delete_auth_user(uid: str) -> bool:
    try:
        from firebase_admin import auth as fb_auth

        fb_auth.delete_user(uid)
        return True
    except Exception as exc:
        # Veri silindi ama kimlik kaldı: kullanıcı tekrar giriş yaparsa boş
        # bir hesapla karşılaşır. Sessizce geçmiyoruz — bu takip edilmeli.
        logger.error("Auth kullanicisi silinemedi (%s): %s", uid, exc)
        return False
