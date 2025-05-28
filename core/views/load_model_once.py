import os
import threading
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

MODEL_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/ai_recommendation_model.pkl"
ENCODER_URL = "https://huggingface.co/den1chik/ai-model/resolve/main/label_encoder.pkl"

MODEL_PATH = "/app/models/ai_recommendation_model.pkl"
ENCODER_PATH = "/app/models/label_encoder.pkl"

def download_file(url, path):
    if not os.path.exists(path):
        print(f"[LOAD] ⬇ Скачиваем {url}")
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"[LOAD] ✅ Сохранено: {path}")
    else:
        print(f"[LOAD] 🟢 Уже есть: {path}")

def download_in_background():
    try:
        download_file(MODEL_URL, MODEL_PATH)
        download_file(ENCODER_URL, ENCODER_PATH)
        print("[LOAD] ✅ Загрузка завершена.")
    except Exception as e:
        print(f"[LOAD ERROR] ❌ {e}")

@csrf_exempt
def load_model_once(request):
    threading.Thread(target=download_in_background).start()
    return JsonResponse({"status": "started", "message": "Загрузка модели началась в фоновом режиме."})
