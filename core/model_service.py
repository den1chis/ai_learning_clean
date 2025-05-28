import os
import requests
from joblib import load

# Путь к volume — смонтирован как /app/models/
MODEL_PATH = "/app/models/ai_recommendation_model.pkl"
ENCODER_PATH = "/app/models/label_encoder.pkl"

# Hugging Face ссылки
MODEL_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/ai_recommendation_model.pkl"
ENCODER_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/label_encoder.pkl"

_model = None
_encoder = None

def _download_if_missing(url: str, path: str):
    if not os.path.exists(path):
        print(f"[MODEL] ⏳ Загружаем: {url} → {path}")
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()

                total = int(r.headers.get('content-length', 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                print(f"[MODEL] ✅ Загружено: {path} ({round(downloaded / 1024 / 1024, 2)} MB)")
        except Exception as e:
            print(f"[MODEL ERROR] ❌ Ошибка загрузки: {e}")
            raise RuntimeError("Не удалось загрузить модель")

def load_model():
    global _model, _encoder
    if _model is None or _encoder is None:
        _download_if_missing(MODEL_URL, MODEL_PATH)
        _download_if_missing(ENCODER_URL, ENCODER_PATH)
        _model = load(MODEL_PATH)
        _encoder = load(ENCODER_PATH)
        print("[MODEL] ✅ Модель и энкодер успешно загружены в память.")
    return _model, _encoder

def get_prediction(features: list[float]) -> str:
    print(f"[PREDICT] 📥 Входные признаки: {features}")
    try:
        model, encoder = load_model()
        pred = model.predict([features])[0]
        label = encoder.inverse_transform([pred])[0]
        print(f"[PREDICT] 🎯 Предсказано: {label}")
        return label
    except Exception as e:
        print(f"[PREDICT ERROR] ❌ Ошибка предсказания: {e}")
        raise RuntimeError("Предсказание не удалось")
