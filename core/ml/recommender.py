import numpy as np
import os
from joblib import load

from django.conf import settings
from core.models import Module

MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml', 'ai_recommendation_model.pkl')
ENCODER_PATH = os.path.join(settings.BASE_DIR, 'ml', 'label_encoder.pkl')


def recommend_module(features: list):
    """
    Возвращает объект Module, рекомендованный моделью на основе features (список процентов по модулям)
    """
    model = load(MODEL_PATH)
    encoder = load(ENCODER_PATH)

    features_np = np.array([features])
    label = model.predict(features_np)[0]
    module_name = encoder.inverse_transform([label])[0]

    return Module.objects.get(title=module_name)
