import os
import numpy as np
from joblib import load

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test

from core.forms import DemoTestForm
from core.models import Module, Recommendation


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def demo_test(request):
    if request.method == 'POST':
        form = DemoTestForm(request.POST)
        if form.is_valid():
            request.session['demo_answers'] = form.cleaned_data
            return redirect('demo_result')
    else:
        form = DemoTestForm()
    return render(request, 'core/demo_test.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def demo_result(request):
    data = request.session.get('demo_answers')
    if not data:
        return redirect('demo_test')

    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    demo_info = []
    features = []

    for m in modules:
        cnt = max(0, min(5, data.get(f"mod_{m.id}", 0)))
        pct = int(cnt / 5 * 100)
        demo_info.append({'module': m, 'count': cnt, 'percent': pct})
        features.append(max(pct, 20))

    model_path = os.path.join(settings.BASE_DIR, 'ai_recommendation_model.pkl')
    encoder_path = os.path.join(settings.BASE_DIR, 'label_encoder.pkl')
    model = load(model_path)
    encoder = load(encoder_path)

    pred_label = model.predict([features])[0]
    pred_name = encoder.inverse_transform([pred_label])[0]
    rec_module = Module.objects.get(title=pred_name)

    return render(request, 'core/demo_result.html', {
        'demo_info': demo_info,
        'rec_module': rec_module,
    })
