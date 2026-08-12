"""İstemci açılış yapılandırması — kimliksiz, hafif.

Tek tüketicisi mobil uygulamanın açılış kapısı: giriş ekranından ÖNCE
çağrıldığı için kimlik istemez ve istemci ağ hatasında FAIL-OPEN davranır
(bkz. apps/mobile/lib/core/app_config.dart). Bu uçtan asla kullanıcıya
özgü veri dönülmez.
"""
from fastapi import APIRouter

from core import config

router = APIRouter()


@router.get("/app")
def app_config():
    """Zorunlu güncelleme eşiği.

    `min_build`: Android versionCode (pubspec `+N`). İstemcinin build'i
    bundan küçükse ForceUpdateScreen'e kilitlenir. 0 = kapı kapalı.
    """
    return {"status": "success", "data": {
        "min_build": config.MIN_APP_BUILD,
    }}
