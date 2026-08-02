r"""Acilis maliyeti — soguk baslatma koruma testleri.

Cloud Run konteyneri bosta kalinca sifira iniyor. Kullanicinin "bekliyor
bekliyor bekliyor, sonra mesajlar geliyor" diye bildirdigi sey buydu: uretim
loglarinda ilk istek **14,65 saniye**, hemen sonraki 0,0036 saniye surdu.

Iki onlem alindi:

1. `min-instances=1` — ilk instance hep ayakta (altyapi tarafi).
2. Agir kutuphaneler modul duzeyinden cikarildi. `maxScale=3` oldugu icin yuk
   2. ve 3. instance'i actirdiginda onlar hala soguk basliyor; yani bu ikinci
   onlem min-instances'in alternatifi degil, tamamlayicisi.

Olculen: `import main` 1611 ms -> 433 ms.

Bu dosya ikinci onlemi koruyor. Biri `services/gemini_service.py` ya da
`services/astro_service.py` basina `import` geri koyarsa kusur SESSIZ olur —
hicbir sey bozulmaz, sadece her soguk baslatma yeniden yavaslar.

Calistirma:  .venv\Scripts\python.exe -m pytest tests/test_cold_start.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import PurePath

BACKEND = PurePath(__file__).parent.parent

#: Acilista ice aktarilMAMASI gereken pahali moduller ve olculen bedelleri.
AGIR_MODULLER = {
    "google.genai": 624,
    "kerykeion": 212,
}


def _acilista_yuklenenler() -> set[str]:
    """`import main` sonrasi `sys.modules` icerigi — AYRI bir surecte.

    Ayri surec sart: test kosucusu bu modulleri baska testler icin coktan
    yuklemis oluyor ve ayni surecte bakmak her zaman "yuklu" der.
    """
    kod = "import main, sys; print('\\n'.join(sys.modules))"
    sonuc = subprocess.run(
        [sys.executable, "-c", kod],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=180,
    )
    assert sonuc.returncode == 0, f"import main dustu:\n{sonuc.stderr}"
    return set(sonuc.stdout.split())


def test_agir_kutuphaneler_acilista_yuklenmiyor():
    yuklu = _acilista_yuklenenler()
    suclular = [m for m in AGIR_MODULLER if m in yuklu]
    assert not suclular, (
        "Bu moduller acilista ice aktariliyor ve her soguk baslatmaya "
        f"maliyet biniyor: {suclular}. Modul duzeyindeki `import` satirini "
        "kaldirip ilk kullanim anina erteleyin "
        "(bkz. gemini_service._get_client / astro_service._kerykeion)."
    )


def test_uygulama_yine_de_kurulabiliyor():
    """Tembellestirme uygulamayi bozmamali — uclar yerinde durmali."""
    kod = (
        "import main;"
        "yollar = set(main.app.openapi()['paths']);"
        "assert '/api/v1/chat' in yollar, sorted(yollar);"
        "assert '/api/v1/astrology/natal-chart' in yollar, sorted(yollar);"
        "assert '/api/v1/face/reading' in yollar, sorted(yollar);"
        "assert '/healthz' in yollar, sorted(yollar);"
        "print('ok')"
    )
    sonuc = subprocess.run(
        [sys.executable, "-c", kod],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=180,
    )
    assert sonuc.returncode == 0, sonuc.stderr
    assert "ok" in sonuc.stdout


def test_tembel_erisimciler_calisiyor():
    """Ice aktarma ertelendi ama ERISIM calismali; yoksa sessizce bozulur."""
    from services import astro_service

    ker = astro_service._kerykeion()
    assert hasattr(ker, "AstrologicalSubjectFactory")
    # Ikinci cagri onbellekten donmeli.
    assert astro_service._kerykeion() is ker
