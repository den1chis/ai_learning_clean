import os
import gdown

def load_model_from_drive(file_id: str, local_path: str):
    """
    Скачивает файл модели из Google Drive по ID, если он отсутствует локально.
    """
    if not file_id:
        print("⚠ Переменная MODEL_FILE_ID не задана")
        return

    if not os.path.exists(local_path):
        print(f"⬇ Загружаем модель из Google Drive → {local_path}")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, local_path, quiet=False)
    else:
        print(f"✅ Модель уже существует по пути: {local_path}")
