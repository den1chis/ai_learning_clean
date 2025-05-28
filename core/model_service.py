import os
import requests
from joblib import load
from django.conf import settings

MODEL_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/ai_recommendation_model.pkl"
ENCODER_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/label_encoder.pkl"

MODEL_PATH = os.path.join(settings.BASE_DIR, "ai_recommendation_model.pkl")
ENCODER_PATH = os.path.join(settings.BASE_DIR, "label_encoder.pkl")

_model = None
_encoder = None


def _download_if_missing(url: str, path: str):
    if not os.path.exists(path):
        print(f"[MODEL] Загружаем {url} → {path}")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[MODEL] ✅ Загружено: {path}")


def load_model():
    global _model, _encoder
    if _model is None or _encoder is None:
        _download_if_missing(MODEL_URL, MODEL_PATH)
        _download_if_missing(ENCODER_URL, ENCODER_PATH)
        _model = load(MODEL_PATH)
        _encoder = load(ENCODER_PATH)
        print("[MODEL] Модель и энкодер успешно загружены.")
    return _model, _encoder


def get_prediction(features: list[float]) -> str:
    print(f"[PREDICT] Получены признаки: {features}")
    model, encoder = load_model()
    pred = model.predict([features])[0]
    label = encoder.inverse_transform([pred])[0]
    print(f"[PREDICT] Предсказано: {label}")
    return label
