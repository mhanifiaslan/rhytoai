"""Firebase ID token doğrulama.

Üretimde (RYTHO_DEV_MODE=0) her istek `Authorization: Bearer <idToken>` başlığı
taşımak zorundadır. Lokal geliştirmede token yoksa anonim kullanıcı kabul edilir.

**Bu modül her isteğin önünde durur.** Burada saniyeler süren bir işlem
uygulamanın tamamını yavaşlatır — kullanıcı bunu "sohbet geç geliyor",
"ekran açılmıyor" diye görür, kimlik doğrulama diye değil. Cihaz testinde tam
olarak bu oldu: kimlik bilgisi çözülemediği hâlde her istek ~12 saniye deneyip
vazgeçiyordu. O yüzden buradaki iki değişmez korunmalı:

1. **Kimlik bilgisi bir kez yoklanır** (bkz. `core.gcp_credentials`), istek
   başına değil.
2. **Olay döngüsü bloklanmaz**; doğrulama iş parçacığı havuzunda koşar.
"""
import logging

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from core import config, gcp_credentials
from core.i18n import get_language
from core.messages import text

logger = logging.getLogger(__name__)

_firebase_ready = False
_warned = False


def _init_firebase() -> bool:
    global _firebase_ready, _warned
    if _firebase_ready:
        return True

    # `firebase_admin.initialize_app()` kimlik bilgisi olmadan da BAŞARIYLA
    # döner; tembel çalışır. Eksiklik ancak ilk `verify_id_token` çağrısında,
    # uzun bir beklemenin ardından ortaya çıkardı. O yüzden önce yokluyoruz.
    #
    # `available()` beklemez ve emin olmadığında ERİŞİLEBİLİR der; yani buraya
    # düşmek için yoklamanın KESİN olumsuz sonuçlanmış olması gerekiyor.
    # Bu ayrım bir kez atlandı ve üretimde tüm istekler 401 döndü.
    if not gcp_credentials.available():
        if not _warned:
            _warned = True
            if config.DEV_MODE:
                # Geliştirme ortamı: beklenen durum, bir kez söylenir.
                logger.warning(
                    "Kimlik bilgisi yok; token doğrulama atlanıyor (DEV_MODE). "
                    "Bu bir kapı gevşetmesi değil — DEV_MODE zaten tokensiz "
                    "isteği kabul ediyor."
                )
            else:
                # Üretim: bu bir dağıtım hatası. Sessiz kalırsa her istek 401
                # döner ve sebebi loglarda görünmez.
                logger.error(
                    "Application Default Credentials çözülemedi. Token "
                    "doğrulanamayacak ve tüm istekler 401 dönecek."
                )
        return False

    try:
        import firebase_admin

        if not firebase_admin._apps:
            # Cloud Run'da Application Default Credentials kullanılır.
            firebase_admin.initialize_app(
                options={"projectId": config.GOOGLE_CLOUD_PROJECT}
            )
        _firebase_ready = True
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("Firebase Admin başlatılamadı: %s", exc)
        return False


def reset_firebase_state() -> None:
    """Yoklama önbelleğini sıfırlar — yalnızca testler için."""
    global _firebase_ready, _warned
    _firebase_ready = False
    _warned = False
    gcp_credentials.reset()


_bearer = HTTPBearer(auto_error=False)


class AuthUser:
    def __init__(self, uid: str, email: str | None = None,
                 anonymous: bool = False, phone: str | None = None,
                 admin: bool = False):
        self.uid = uid
        self.email = email
        self.anonymous = anonymous
        #: Firebase'in DOĞRULADIĞI telefon numarası (E.164), token'dan gelir.
        #: İstemcinin beyanı değil — SMS doğrulaması Firebase'de bitmiş
        #: numara. Rehber eşleşmesinin güven zinciri buradan başlıyor.
        self.phone = phone
        #: Firebase custom claim `admin: true` (W4). Yalnızca
        #: tools/set_admin.py ile basılır; istemci kendi token'ına claim
        #: yazamaz. Yönetim uçlarının tek kapısı [require_admin].
        self.admin = admin


def _verify(token: str) -> dict:
    from firebase_admin import auth as fb_auth

    return fb_auth.verify_id_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    lang: str = Depends(get_language),
) -> AuthUser:
    """Oturum doğrulama.

    Dil bağımlılığı yalnızca hata metni için: 401 yanıtının `detail` alanı
    istemcide doğrudan kullanıcıya gösteriliyor, o yüzden kullanıcının dilinde
    olmak zorunda.
    """
    if credentials is not None and _init_firebase():
        try:
            # `verify_id_token` bloklayan bir çağrı: imza anahtarları süresi
            # dolduğunda (~6 saatte bir) Google'dan yeniden çekiliyor. `async`
            # bir işlevin içinde doğrudan çağrılırsa o ağ turu boyunca olay
            # döngüsü durur ve TÜM istekler bekler.
            decoded = await run_in_threadpool(_verify, credentials.credentials)
            return AuthUser(uid=decoded["uid"], email=decoded.get("email"),
                            phone=decoded.get("phone_number"),
                            admin=decoded.get("admin") is True)
        except Exception as exc:
            logger.info("Token doğrulanamadı: %s", exc)
            if not config.DEV_MODE:
                raise HTTPException(status_code=401,
                                    detail=text("auth_invalid", lang))

    if config.DEV_MODE:
        # DEV_MODE'un anonim kullanıcısı admin DEĞİLDİR (bir numaralı
        # değişmez): geliştirme kolaylığı yönetim yetkisine dönüşemez.
        # Yerelde admin uçlarını denemek isteyen, ayrı ve AÇIK bir bayrak
        # kaldırır (RYTHO_DEV_ADMIN=1).
        return AuthUser(uid="dev-user", anonymous=True,
                        admin=config.DEV_ADMIN)

    raise HTTPException(status_code=401, detail=text("auth_required", lang))


def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Yönetim uçlarının kapısı (W4): custom claim `admin: true` şart.

    403 döner, 401 değil — kimlik geçerli ama yetki yok. Yanıt jenerik
    tutulur; ucun varlığı hakkında ipucu vermez.
    """
    if not user.admin:
        raise HTTPException(status_code=403, detail="Yetkisiz.")
    return user
