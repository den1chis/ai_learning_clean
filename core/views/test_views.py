import os
import random
import numpy as np
from joblib import load

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.forms import TestForm, QuestionForm
from core.models import (
    Lesson, LessonProgress, Module, Question, UserAnswer,
    Recommendation, UserProgress
)

import requests
from io import BytesIO

def load_from_huggingface(url):
    response = requests.get(url)
    response.raise_for_status()
    return load(BytesIO(response.content))


@login_required
def test_start(request):
    import random
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    qs_ids = []

    for m in modules:
        all_ids = list(Question.objects.filter(module=m).values_list('id', flat=True))
        # случайный выбор 5 уникальных вопросов на модуль
        selected = random.sample(all_ids, min(5, len(all_ids)))
        qs_ids += selected

    request.session['test_qs'] = qs_ids
    request.session['test_ans'] = []
    return redirect('test_question', idx=0)


@login_required
def test_question(request, idx):
    qs_ids = request.session.get('test_qs', [])
    total = len(qs_ids)

    if idx >= total:
        return redirect('test_loading')

    q = get_object_or_404(Question, pk=qs_ids[idx])

    # Считаем прогресс
    current = idx + 1
    progress = round(current / total * 100)

    if request.method == 'POST':
        # 1) Если нажали «Пропустить» — записываем sel=0 (некорректный вариант)
        if 'skip' in request.POST:
            ans = request.session.get('test_ans', [])
            ans.append({'q_id': q.id, 'sel': 0})
            request.session['test_ans'] = ans
            return redirect('test_question', idx=idx+1)

        # 2) Обычная обработка выбора
        form = QuestionForm(q, data=request.POST)
        if form.is_valid():
            sel = int(form.cleaned_data['choice'])
            ans = request.session.get('test_ans', [])
            ans.append({'q_id': q.id, 'sel': sel})
            request.session['test_ans'] = ans
            return redirect('test_question', idx=idx+1)
    else:
        form = QuestionForm(q)

    return render(request, 'core/test_question.html', {
        'form': form,
        'question': q,
        'current': current,
        'total': total,
        'progress': progress,
    })



@login_required
def test_loading(request):
    # просто страница с “загрузкой”
    return render(request, 'core/test_loading.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import Module, Question, UserAnswer, Recommendation, UserProgress, Lesson, LessonProgress
from core.model_service import get_prediction  # ← наша новая обёртка
import numpy as np


@login_required
def test_result(request):
    qs_ids = request.session.pop('test_qs', [])
    answers = request.session.pop('test_ans', [])

    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    total = {}
    correct = {}

    seen_q_ids = set()

    # Сохраняем ответы пользователя
    for a in answers:
        q_id = a['q_id']
        if q_id in seen_q_ids:
            continue
        seen_q_ids.add(q_id)

        q = Question.objects.get(pk=q_id)
        sel = a['sel']
        is_ok = (sel == q.correct_option) if sel in (1, 2, 3, 4) else False
        selected = sel if sel in (1, 2, 3, 4) else None

        UserAnswer.objects.create(
            user=request.user,
            question=q,
            selected_option=selected,
            is_correct=is_ok
        )

        mid = q.module.id
        total[mid] = total.get(mid, 0) + 1
        correct[mid] = correct.get(mid, 0) + (1 if is_ok else 0)

    # Преобразуем данные в признаки для модели
    features = np.array([[ 
        max((correct.get(m.id, 0) / total.get(m.id, 1)) * 100, 20) 
        for m in modules
    ]])

    # Получаем рекомендацию через модель
    try:
        rec_name = get_prediction(features[0])
        rec_module = Module.objects.get(title=rec_name)
    except Exception as e:
        print(f"[ERROR] Ошибка предсказания: {e}")
        rec_module = modules[0] if modules else None

    # Сохраняем рекомендации и прогресс
    if rec_module:
        Recommendation.objects.create(
            user=request.user,
            module=rec_module,
            recommendation_type='next_module',
            confidence_score=0.0
        )

        first_lesson = Lesson.objects.filter(module=rec_module).order_by('order_index').first()
        if first_lesson:
            LessonProgress.objects.get_or_create(user=request.user, lesson=first_lesson)

        UserProgress.objects.update_or_create(
            user=request.user,
            module=rec_module,
            defaults={'completion_percent': 0, 'recommended_difficulty': None}
        )

    # Статистика по модулям
    demo_info = []
    for m in modules:
        cnt = total.get(m.id, 0)
        pct = int((correct.get(m.id, 0) / cnt) * 100) if cnt else 0
        demo_info.append({
            'module': m,
            'count': correct.get(m.id, 0),
            'percent': pct
        })

    return render(request, 'core/test_result.html', {
        'rec_module': rec_module,
        'demo_info': demo_info
    })


@login_required
def test_view(request):
    # 1) по 3 вопроса из каждого модуля
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    questions = []
    for m in modules:
        questions.extend(Question.objects.filter(module=m).order_by('?')[:5])

    # 2) обработка формы
    if request.method == 'POST':
        form = TestForm(questions, data=request.POST)
        if form.is_valid():
            # 3) сохраняем ответы и считаем
            correct = {}
            total = {}
            for q in questions:
                sel = int(form.cleaned_data[f'question_{q.id}'])
                ok = (sel == q.correct_option)
                UserAnswer.objects.create(
                    user=request.user,
                    question=q,
                    selected_option=sel,
                    is_correct=ok
                )
                mid = q.module.id
                total[mid] = total.get(mid, 0) + 1
                correct[mid] = correct.get(mid, 0) + (1 if ok else 0)

            # 4) формируем массив 20–100 для модели
            features = []
            for m in modules:
                frac = correct.get(m.id, 0) / total.get(m.id, 1)
                features.append(frac * 100)
            data = np.array([features])  # shape (1, n_modules)

            # 5) загружаем модель и энкодер
            model_path   = os.path.join(settings.BASE_DIR, 'ai_recommendation_model.pkl')
            encoder_path = os.path.join(settings.BASE_DIR, 'label_encoder.pkl')
            model        = load(model_path)
            encoder      = load(encoder_path)

            # 6) предсказываем имя модуля
            pred_label       = model.predict(data)[0]
            rec_module_name  = encoder.inverse_transform([pred_label])[0]

            # 7) пытаемся найти модуль по title__startswith
            rec_module = Module.objects.filter(
                title__startswith=rec_module_name
            ).order_by('order_index').first()

            # если не нашли — берём модуль с тем же order_index, что и pred_label
            if rec_module is None:
                try:
                    idx = int(pred_label)
                    rec_module = modules[idx]
                except Exception:
                    rec_module = modules[0]

            # 8) сохраняем результат
            Recommendation.objects.create(
                user=request.user,
                module=rec_module,
                recommendation_type='next_module',
                confidence_score=0.0
            )
            UserProgress.objects.update_or_create(
                user=request.user,
                module=rec_module,
                defaults={
                    'completion_percent': 0,
                    'recommended_difficulty': None
                }
            )

            return redirect('dashboard')
    else:
        form = TestForm(questions)

    return render(request, 'core/test.html', {
        'form': form,
        'modules': modules,
    })