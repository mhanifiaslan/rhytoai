"""İstemci açılış yapılandırması — kimliksiz, hafif.

Tek tüketicisi mobil uygulamanın açılış kapısı: giriş ekranından ÖNCE
çağrıldığı için kimlik istemez. Bu uçtan asla kullanıcıya özgü veri
dönülmez.

Sözleşme (PBZ): eşik `core.app_gate.current_min_build()`'den gelir
(env tabanı + `config/app.minBuild`, 60 s memo) ve uç FAIL-OPEN kalır —
okuma fırlatırsa 0 döner, kimse bu uç yüzünden kilitlenmez. Asıl zorlama
artık sunucuda (`AppGateMiddleware`, 426); istemci bu değeri son bilinen
eşik olarak saklar ve çevrimdışıyken de kilitler
(bkz. apps/mobile/lib/core/app_config.dart).
"""
from fastapi import APIRouter, Response

from core import app_gate

router = APIRouter()


@router.get("/app")
def app_config(response: Response):
    """Zorunlu güncelleme eşiği.

    `min_build`: Android versionCode (pubspec `+N`). İstemcinin build'i
    bundan küçükse ForceUpdateScreen'e kilitlenir. 0 = kapı kapalı.

    `Cache-Control: no-store`: panelden çekilen eşik ara önbelleklerde
    (Cloud Run ön yüzü, cihaz HTTP önbelleği) bayat kalmasın.
    """
    try:
        min_build = app_gate.current_min_build()
    except Exception:
        # app_gate zaten fırlatmaz; bu kemer yine de durur — uç fail-open
        # SÖZLEŞMESİ veriyor, iç modülün davranışına güvenmiyor.
        min_build = 0
    response.headers["Cache-Control"] = "no-store"
    return {"status": "success", "data": {
        "min_build": min_build,
    }}
