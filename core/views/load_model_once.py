import os
import requests
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

def load_model_once(request):
    model_url = "https://huggingface.co/den1chik/ai-model/resolve/main/ai_recommendation_model.pkl"
    encoder_url = "https://huggingface.co/den1chik/ai-model/resolve/main/label_encoder.pkl"

    save_dir = "/app/models"
    os.makedirs(save_dir, exist_ok=True)

    def download(url, filename):
        path = os.path.join(save_dir, filename)
        if not os.path.exists(path):
            r = requests.get(url, stream=True, timeout=(20, 300))
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        return path

    try:
        model_path = download(model_url, "ai_recommendation_model.pkl")
        encoder_path = download(encoder_url, "label_encoder.pkl")
        return HttpResponse(f"✅ Модель загружена: {model_path}<br>✅ Энкодер: {encoder_path}")
    except Exception as e:
        return HttpResponse(f"❌ Ошибка: {str(e)}", status=500)
