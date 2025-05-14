#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.ml.loader import load_model_from_drive

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    # Загрузка модели
    file_id = os.environ.get("MODEL_FILE_ID")
    model_path = os.path.join(BASE_DIR, 'core', 'ml', 'ai_recommendation_model.pkl')
    load_model_from_drive(file_id, model_path)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
