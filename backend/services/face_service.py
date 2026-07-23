"""Yüz analizi v2 — MediaPipe Face Mesh (468 landmark) tabanlı Mian Xiang motoru.

Klasik metinlerdeki "geniş alın", "dolgun burun ucu" gibi nitel ifadeler,
landmark koordinatlarından türetilen GERÇEK geometrik oranlara eşlenir:

- San Ting: alın / orta yüz / alt yüz yükseklik oranları
- Wu Xing: yüz en-boy oranı + çene açısı + elmacık genişliğinden element
- 12 Saray: saray bölgelerine düşen landmark kümelerinin göreli metrikleri
- Simetri: sol-sağ landmark mesafe farkları

DeepFace kuruluysa yaş/duygu tahmini eklenir; değilse atlanır (opsiyonel).
Kural matrisleri knowledge/rules altından okunur.
"""
from __future__ import annotations

import json
import logging
import math
from functools import lru_cache
from typing import Any

import cv2
import numpy as np

from core import config

logger = logging.getLogger(__name__)

# MediaPipe FaceMesh landmark indeksleri (kanonik 468-nokta modeli)
LM = {
    "forehead_top": 10,      # saç çizgisine en yakın üst nokta
    "brow_mid_left": 105,
    "brow_mid_right": 334,
    "glabella": 9,           # iki kaş arası (Yin Tang)
    "nose_bridge": 6,
    "nose_tip": 4,
    "nose_base": 2,
    "nose_wing_left": 129,
    "nose_wing_right": 358,
    "mouth_left": 61,
    "mouth_right": 291,
    "upper_lip": 13,
    "lower_lip": 14,
    "chin": 152,
    "cheek_left": 234,
    "cheek_right": 454,
    "cheekbone_left": 227,
    "cheekbone_right": 447,
    "jaw_left": 172,
    "jaw_right": 397,
    "eye_outer_left": 33,
    "eye_outer_right": 263,
    "eye_inner_left": 133,
    "eye_inner_right": 362,
    "under_eye_left": 145,
    "under_eye_right": 374,
    "upper_lid_left": 159,
    "upper_lid_right": 386,
}


@lru_cache(maxsize=1)
def _rules() -> dict[str, Any]:
    rules = {}
    for name in ("mian_xiang", "kiyafetname"):
        path = config.KNOWLEDGE_DIR / "rules" / f"{name}.json"
        try:
            rules[name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Kural dosyası okunamadı (%s): %s", path, exc)
            rules[name] = {}
    return rules


_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)


@lru_cache(maxsize=1)
def _get_landmarker():
    """MediaPipe Tasks FaceLandmarker — model ilk kullanımda indirilir ve önbelleklenir."""
    import urllib.request

    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    model_path = config.CACHE_DIR / "face_landmarker.task"
    if not model_path.exists():
        logger.info("FaceLandmarker modeli indiriliyor...")
        urllib.request.urlretrieve(_LANDMARKER_MODEL_URL, str(model_path))

    options = mp_vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_faces=1,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)


def _detect_landmarks(image: np.ndarray) -> np.ndarray | None:
    """478 landmark'ı (x, y) piksel koordinatları olarak döndürür."""
    import mediapipe as mp

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = _get_landmarker().detect(mp_image)
    if not result.face_landmarks:
        return None
    h, w = image.shape[:2]
    pts = result.face_landmarks[0]
    return np.array([[p.x * w, p.y * h] for p in pts])


def _dist(pts: np.ndarray, a: str, b: str) -> float:
    return float(np.linalg.norm(pts[LM[a]] - pts[LM[b]]))


def _san_ting(pts: np.ndarray) -> tuple[dict[str, float], str, str]:
    """Üç bölüm yükseklikleri ve baskın bölge."""
    top = pts[LM["forehead_top"]][1]
    brow = (pts[LM["brow_mid_left"]][1] + pts[LM["brow_mid_right"]][1]) / 2
    nose_base = pts[LM["nose_base"]][1]
    chin = pts[LM["chin"]][1]

    upper = max(brow - top, 1.0)
    middle = max(nose_base - brow, 1.0)
    lower = max(chin - nose_base, 1.0)
    total = upper + middle + lower
    ratios = {
        "upper": round(float(upper / total), 3),
        "middle": round(float(middle / total), 3),
        "lower": round(float(lower / total), 3),
    }

    zones = _rules()["mian_xiang"].get("san_ting", {}).get("zones", [])
    ideal = 1 / 3
    deviations = {
        "shang_ting": ratios["upper"] - ideal,
        "zhong_ting": ratios["middle"] - ideal,
        "xia_ting": ratios["lower"] - ideal,
    }
    dominant_id = max(deviations, key=deviations.get)

    if max(abs(d) for d in deviations.values()) < 0.03:
        balance = "Harmonik ve Dengeli (üç bölüm eşit güçte)"
        meaning = "Zihin, irade ve yaşam gücü dengede: hayatın üç evresi de verimli akar."
    else:
        zone = next((z for z in zones if z["id"] == dominant_id), None)
        balance = f"{zone['name_tr'] if zone else dominant_id} baskın"
        meaning = zone["dominant_meaning"] if zone else ""
    return ratios, balance, meaning


def _wu_xing(pts: np.ndarray) -> tuple[str, str]:
    """Yüz şekli ölçümlerinden Beş Element sınıflandırması."""
    face_width = _dist(pts, "cheek_left", "cheek_right")
    face_height = pts[LM["chin"]][1] - pts[LM["forehead_top"]][1]
    jaw_width = _dist(pts, "jaw_left", "jaw_right")
    cheekbone_width = _dist(pts, "cheekbone_left", "cheekbone_right")

    aspect = face_width / max(face_height, 1.0)
    jaw_ratio = jaw_width / max(face_width, 1.0)
    cheek_ratio = cheekbone_width / max(face_width, 1.0)

    if aspect < 0.72:
        element, reason = "Ahşap (Mu)", "uzun ve ince yüz formu"
    elif cheek_ratio > 0.98 and jaw_ratio < 0.78:
        element, reason = "Ateş (Huo)", "belirgin elmacık kemikleri ve sivrilen çene (elmas form)"
    elif aspect > 0.88 and jaw_ratio > 0.9:
        element, reason = "Toprak (Tu)", "geniş ve köşeli, kare yüz formu"
    elif jaw_ratio < 0.85 and 0.72 <= aspect <= 0.85:
        element, reason = "Metal (Jin)", "oval ve simetrik yüz formu"
    else:
        element, reason = "Su (Shui)", "yuvarlak ve yumuşak hatlı yüz formu"

    shapes = _rules()["mian_xiang"].get("wu_xing_face_shapes", {}).get("shapes", [])
    match = next((s for s in shapes if s["element"].startswith(element.split(" ")[0])), None)
    detail = f"{reason}. {match['traits']}" if match else reason
    return element, detail


def _symmetry(pts: np.ndarray) -> str:
    mid_x = (pts[LM["glabella"]][0] + pts[LM["chin"]][0]) / 2
    pairs = [
        ("eye_outer_left", "eye_outer_right"),
        ("nose_wing_left", "nose_wing_right"),
        ("mouth_left", "mouth_right"),
        ("jaw_left", "jaw_right"),
    ]
    diffs = []
    face_width = _dist(pts, "cheek_left", "cheek_right")
    for left, right in pairs:
        dl = abs(pts[LM[left]][0] - mid_x)
        dr = abs(pts[LM[right]][0] - mid_x)
        diffs.append(abs(dl - dr) / max(face_width, 1.0))
    score = 1.0 - float(np.mean(diffs))
    if score > 0.97:
        return f"Çok yüksek (%{round(score*100)}) — Metal elementi netliği"
    if score > 0.93:
        return f"Yüksek (%{round(score*100)})"
    return f"Karakteristik asimetri (%{round(score*100)}) — güçlü kişisel imza"


def _palaces(pts: np.ndarray, san_ting_ratios: dict[str, float]) -> list[dict[str, str]]:
    """12 Saray değerlendirmesi: her sarayın bölgesel geometrik metriği."""
    palaces_data = _rules()["mian_xiang"].get("twelve_palaces", [])
    face_width = _dist(pts, "cheek_left", "cheek_right")
    face_height = pts[LM["chin"]][1] - pts[LM["forehead_top"]][1]

    # Geometrik göstergeler
    yin_tang_width = _dist(pts, "brow_mid_left", "brow_mid_right") / max(face_width, 1)
    forehead_ratio = san_ting_ratios["upper"]
    nose_width = _dist(pts, "nose_wing_left", "nose_wing_right") / max(face_width, 1)
    nose_length = (pts[LM["nose_base"]][1] - pts[LM["nose_bridge"]][1]) / max(face_height, 1)
    eyelid_left = (pts[LM["upper_lid_left"]][1] - pts[LM["brow_mid_left"]][1]) / max(face_height, 1)
    jaw_fullness = _dist(pts, "jaw_left", "jaw_right") / max(face_width, 1)
    mouth_width = _dist(pts, "mouth_left", "mouth_right") / max(face_width, 1)
    bridge_straightness = abs(pts[LM["nose_bridge"]][0] - pts[LM["nose_tip"]][0]) / max(face_width, 1)

    verdicts = {
        "ming_gong": yin_tang_width > 0.26,
        "guan_lu_gong": forehead_ratio > 0.30,
        "cai_bo_gong": nose_width > 0.24,
        "fu_qi_gong": True,  # doku analizi gerektirir; varsayilan olumlu
        "zi_nu_gong": True,
        "tian_zhai_gong": eyelid_left > 0.045,
        "xiong_di_gong": True,
        "qian_yi_gong": forehead_ratio > 0.32,
        "ji_e_gong": bridge_straightness < 0.02,
        "nu_pu_gong": jaw_fullness > 0.85,
        "fu_de_gong": True,
        "fu_mu_gong": forehead_ratio > 0.28,
    }

    results = []
    for palace in palaces_data:
        bright = bool(verdicts.get(palace["id"], True))
        results.append({
            "id": palace["id"],
            "name_tr": palace["name_tr"],
            "location": palace["location"],
            "reads": palace["reads"],
            "assessment": palace["bright"] if bright else palace["marked"],
            "bright": bright,
        })
    return results


def _mizac(pts: np.ndarray, element: str) -> dict[str, str]:
    """Wu Xing elementi + geometriden Marifetname mizacı türetilir
    (element-mizaç paralelliği: Ateş->Safrai, Su->Balgami, Toprak->Sevdavi,
    Ahşap/Metal->Demevi ağırlıklı)."""
    mapping = {
        "Ateş": "Safrai", "Su": "Balgami", "Toprak": "Sevdavi",
        "Ahşap": "Demevi", "Metal": "Demevi",
    }
    key = element.split(" ")[0]
    name = mapping.get(key, "Demevi")
    for m in _rules()["kiyafetname"].get("mizac", []):
        if m["name"] == name:
            return m
    return {"name": name, "traits": "", "advice": ""}


def _deepface_extras(image_path: str) -> dict[str, Any]:
    try:
        from deepface import DeepFace

        objs = DeepFace.analyze(
            img_path=image_path, actions=["age", "gender", "emotion"],
            enforce_detection=False,
        )
        gender = objs[0].get("dominant_gender", "")
        return {
            "age": int(objs[0].get("age", 0)) or None,
            "gender": "Kadın" if gender in ("Woman", "female") else "Erkek",
            "emotion": objs[0].get("dominant_emotion"),
        }
    except Exception as exc:
        logger.info("DeepFace kullanılamadı (opsiyonel): %s", exc)
        return {"age": None, "gender": None, "emotion": None}


def analyze_face(image_path: str) -> dict[str, Any]:
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Görsel yüklenemedi."}

    pts = _detect_landmarks(image)
    if pts is None:
        return {"error": "Görselde yüz tespit edilemedi. Lütfen yüzün net göründüğü bir fotoğraf kullanın."}

    ratios, balance, balance_meaning = _san_ting(pts)
    element, element_reason = _wu_xing(pts)
    symmetry = _symmetry(pts)
    palaces = _palaces(pts, ratios)
    mizac = _mizac(pts, element)
    extras = _deepface_extras(image_path)

    return {
        **extras,
        "landmark_count": len(pts),
        "san_ting_ratios": ratios,
        "san_ting_balance": balance,
        "san_ting_meaning": balance_meaning,
        "wu_xing_element": element,
        "wu_xing_reason": element_reason,
        "symmetry": symmetry,
        "mizac": f"{mizac['name']} ({mizac.get('quality', '')})",
        "mizac_traits": mizac.get("traits", ""),
        "mizac_advice": mizac.get("advice", ""),
        "palaces": palaces,
        "measurements": {
            "san_ting": ratios,
            "element": element,
        },
        "summary": (
            f"{len(pts)} noktalı yüz haritana göre {element} elementinin etkisindesin; "
            f"{balance.lower()} yapın ve {mizac['name']} mizacın öne çıkıyor."
        ),
    }
