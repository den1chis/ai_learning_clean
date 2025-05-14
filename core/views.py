import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from joblib import load
from sklearn.exceptions import NotFittedError
import numpy as np
from .forms import CustomUserCreationForm, CustomAuthenticationForm, TestForm, QuestionForm
from .models import Question, Module, UserAnswer, Recommendation, UserProgress, Lesson, LessonProgress, Task, UserTask, LessonQuiz

import os
import numpy as np
from django.shortcuts import render, redirect
from django.conf import settings
from joblib import load

from .forms import DemoTestForm
from .models import Module

from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_profile_view(request):
    return render(request, 'core/admin_profile.html', {
        'admin_user': request.user
    })
from .forms import ProfileUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
@login_required
def profile_settings(request):
    user = request.user
    profile_form = ProfileUpdateForm(instance=user)
    password_form = CustomPasswordChangeForm(user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Профиль обновлён успешно.')
                return redirect('profile_settings')

        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменён.')
                return redirect('profile_settings')

    return render(request, 'core/profile_settings.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })

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

from django.db.models import Avg
from .models import User, UserProgress

@login_required
@user_passes_test(is_admin)
def admin_students_view(request):
    from django.db.models import Avg, Count
    from .models import Lesson, LessonProgress, Module, UserProgress

    students = User.objects.filter(role='student')
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    lessons = list(Lesson.objects.filter(module__in=modules))

    data = []

    for student in students:
        # Прогресс по всем урокам
        completed_lessons = LessonProgress.objects.filter(user=student, completed=True).count()
        total_lessons = len(lessons)
        avg_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

        # Прогресс по каждому модулю
        module_progresses = []
        for module in modules:
            module_lessons = [l for l in lessons if l.module_id == module.id]
            total = len(module_lessons)
            completed = LessonProgress.objects.filter(user=student, lesson__in=module_lessons, completed=True).count()
            percent = int((completed / total) * 100) if total > 0 else 0
            module_progresses.append({
                'module': module,
                'percent': percent
            })

        data.append({
            'student': student,
            'avg_progress': avg_percent,
            'module_progresses': module_progresses,
        })

    return render(request, 'core/admin_students.html', {
        'students': data,
        'modules': modules
    })


from .models import User, UserProgress, LessonProgress, Module, Lesson

@login_required
@user_passes_test(is_admin)
def admin_student_detail(request, user_id):
    student = get_object_or_404(User, id=user_id, role='student')
    modules = Module.objects.filter(course_id=1).order_by('order_index')

    module_info = []
    total_lessons = 0
    total_completed = 0

    for module in modules:
        lessons = Lesson.objects.filter(module=module).order_by('order_index')
        lessons_info = []
        completed = 0

        for lesson in lessons:
            is_done = LessonProgress.objects.filter(user=student, lesson=lesson, completed=True).exists()
            if is_done:
                completed += 1

            # Задания и решения
            tasks = Task.objects.filter(lesson=lesson)
            task_info = []
            for t in tasks:
                ut = UserTask.objects.filter(user=student, task=t).first()
                task_info.append({
                    'task': t,
                    'user_task': ut
                })

            # Мини-тесты
            quizzes = LessonQuiz.objects.filter(lesson=lesson)
            quiz_info = []
            for quiz in quizzes:
                ua = UserAnswer.objects.filter(user=student, question_id=quiz.id).first()
                quiz_info.append({
                    'quiz': quiz,
                    'answer': ua
                })

            lessons_info.append({
                'lesson': lesson,
                'completed': is_done,
                'tasks': task_info,
                'quizzes': quiz_info
            })

        count = lessons.count()
        total_lessons += count
        total_completed += completed
        percent = round((completed / count) * 100) if count > 0 else 0

        module_info.append({
            'module': module,
            'percent': percent,
            'lessons': lessons_info
        })

    avg_progress = round((total_completed / total_lessons) * 100) if total_lessons > 0 else 0

    return render(request, 'core/admin_student_detail.html', {
        'student': student,
        'avg_progress': avg_progress,
        'module_info': module_info
    })
@login_required
@user_passes_test(is_admin)
def demo_result(request):
    data = request.session.get('demo_answers')
    if not data:
        return redirect('demo_test')

    # 1) Модули и demo_info собираем как прежде…
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    demo_info = []
    features = []
    for m in modules:
        cnt = max(0, min(5, data.get(f"mod_{m.id}", 0)))
        pct = int(cnt/5*100)
        demo_info.append({'module': m, 'count': cnt, 'percent': pct})
        features.append(max(pct, 20))

    # 2) Загружаем модель и encoder
    model = load(os.path.join(settings.BASE_DIR, 'ai_recommendation_model.pkl'))
    le    = load(os.path.join(settings.BASE_DIR, 'label_encoder.pkl'))

    # 3) Предсказываем метку и приводим её к названию модуля
    pred_label = model.predict([features])[0]
    pred_name  = le.inverse_transform([pred_label])[0]

    # 4) Выбираем модуль по названию
    rec_module = Module.objects.get(title=pred_name)

    return render(request, 'core/demo_result.html', {
        'demo_info':  demo_info,
        'rec_module': rec_module,
    })# Create your views here.
def home(request):
    return render(request, 'core/home.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Ошибка регистрации. Проверьте введённые данные.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # 🔁 Перенаправление в зависимости от роли
            if user.role == 'admin':
                return redirect('admin_profile')
            return redirect('dashboard')  # студент и другие
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('home')
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Module, Lesson, LessonProgress, Recommendation

@login_required
def dashboard_view(request):
    # 1) Загружаем модули
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))

    # 2) Последняя рекомендация
    rec = (Recommendation.objects
           .filter(user=request.user, recommendation_type='next_module')
           .order_by('-timestamp')
           .first())

    recommended_module = rec.module if rec else None

    # 3) Получаем завершённые уроки
    completed_lesson_ids = set(
        LessonProgress.objects
        .filter(user=request.user, completed=True)
        .values_list('lesson_id', flat=True)
    )

    # 4) Вычисляем прогресс
    all_lessons = 0
    completed_lessons = 0
    modules_info = []

    unlocked_flag = True  # первый модуль всегда открыт

    for i, m in enumerate(modules):
        lessons = Lesson.objects.filter(module=m).order_by('order_index')
        lesson_ids = lessons.values_list('id', flat=True)
        total = lessons.count()
        completed = sum(1 for lid in lesson_ids if lid in completed_lesson_ids)

        all_lessons += total
        completed_lessons += completed

        modules_info.append({
            'module': m,
            'unlocked': unlocked_flag,
            'recommended': recommended_module and (m.id == recommended_module.id),
            'total_lessons': total,
            'completed_lessons': completed,
            'module_progress': int((completed / total) * 100) if total > 0 else 0
        })

        # 🔒 Если текущий не завершён — все последующие блокируем
        if completed < total:
            unlocked_flag = False

    progress_percent = int((completed_lessons / all_lessons) * 100) if all_lessons > 0 else 0
    recent_actions = []  # можно реализовать позже

    return render(request, 'core/dashboard.html', {
        'recommended_module': recommended_module,
        'modules_info': modules_info,
        'progress_percent': progress_percent,
        'recent_actions': recent_actions,
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

import os
import numpy as np
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from joblib import load

from .models import Module, Question, UserAnswer, Recommendation, UserProgress
@login_required
def test_result(request):
    from joblib import load
    import os
    import numpy as np
    from .models import Module, Question, UserAnswer, Recommendation, UserProgress

    qs_ids = request.session.pop('test_qs', [])
    answers = request.session.pop('test_ans', [])

    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))
    total = {}
    correct = {}

    seen_q_ids = set()

    for a in answers:
        q_id = a['q_id']
        if q_id in seen_q_ids:
            continue  # ⛔ пропускаем дублирующий вопрос
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

    features = np.array([[ 
        max((correct.get(m.id, 0) / total.get(m.id, 1)) * 100, 20) 
        for m in modules
    ]])

    model_path = os.path.join(settings.BASE_DIR, 'ai_recommendation_model.pkl')
    encoder_path = os.path.join(settings.BASE_DIR, 'label_encoder.pkl')
    model = load(model_path)
    encoder = load(encoder_path)

    try:
        pred_label = model.predict(features)[0]
        rec_name = encoder.inverse_transform([pred_label])[0]
        rec_module = Module.objects.get(title=rec_name)
    except:
        rec_module = modules[0]

    Recommendation.objects.create(
        user=request.user,
        module=rec_module,
        recommendation_type='next_module',
        confidence_score=0.0
    )
    UserProgress.objects.update_or_create(
        user=request.user,
        module=rec_module,
        defaults={'completion_percent': 0, 'recommended_difficulty': None}
    )

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




from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Module, Lesson, LessonProgress

@login_required
def module_lessons_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    lessons = list(Lesson.objects.filter(module=module).order_by('order_index'))

    # Прогресс по урокам
    progress_qs = LessonProgress.objects.filter(user=request.user, lesson__in=lessons)
    progress_map = {lp.lesson_id: lp.completed for lp in progress_qs}

    lessons_info = []
    unlocked_flag = True
    current_lesson_id = None

    for lesson in lessons:
        completed = progress_map.get(lesson.id, False)

        # текущий первый незавершённый
        if not completed and current_lesson_id is None:
            current_lesson_id = lesson.id

        lessons_info.append({
            'lesson': lesson,
            'completed': completed,
            'unlocked': unlocked_flag
        })

        # если урок не завершён, последующие — заблокированы
        if not completed:
            unlocked_flag = False

        # Прогресс текущего модуля
    total_lessons = len(lessons)
    completed_lessons = sum(1 for l in lessons if progress_map.get(l.id))
    module_progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0


    return render(request, 'core/module_lessons.html', {
        'module': module,
        'lessons_info': lessons_info,
        'module_progress': module_progress,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
    })



import subprocess


from django.http import JsonResponse

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.models import Lesson, Task, UserTask, LessonQuiz, LessonProgress, Module




def check_user_code(request, tasks, user_tasks_dict):
    import tempfile
    import subprocess
    import os

    task_id = int(request.POST.get("task_id", 0))
    code = request.POST.get("code", "")
    task = next((t for t in tasks if t.id == task_id), None)

    if not task:
        return {"output": "Задание не найдено.", "is_correct": False, "task_id": task_id}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = stdout if stdout else stderr
        hint = ""

        if "NameError" in stderr and "is not defined" in stderr:
            if "pront" in stderr:
                hint = "💡 Возможно, вы имели в виду <code>print</code>, а не <code>pront</code>?"
            else:
                hint = "💡 Проверьте правильность написания имён переменных и функций."
        elif "SyntaxError" in stderr:
            hint = "💡 Проверьте синтаксис: возможно, не хватает двоеточия, кавычек или скобок."
        elif "IndentationError" in stderr:
            hint = "💡 Проверьте отступы: Python чувствителен к пробелам в начале строк."
        elif "TypeError" in stderr:
            hint = "💡 Возможно, вы используете операцию не для того типа данных."

        # объединяем вывод
        if hint:
            output += "\n\n=== ПОДСКАЗКА ===\n" + hint


        is_correct = stdout == (task.expected_output or "").strip()

    except subprocess.TimeoutExpired:
        output = "⏱ Превышено время выполнения"
        is_correct = False
    except Exception as e:
        output = f"Ошибка: {str(e)}"
        is_correct = False
    finally:
        os.remove(temp_path)

    # Обновление/создание результата
    user_task = user_tasks_dict.get(task_id)
    if user_task:
        user_task.code = code
        user_task.output = output
        user_task.is_correct = is_correct
        user_task.save()
    else:
        user_task = UserTask.objects.create(
            user=request.user,
            task=task,
            code=code,
            output=output,
            is_correct=is_correct,
            attempts = 1
        )
        user_tasks_dict[task_id] = user_task

    return {
        "output": output,
        "is_correct": is_correct,
        "task_id": task_id,
    }

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Lesson, Task, UserTask, LessonProgress, LessonQuiz

import subprocess
import tempfile

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Lesson, Task, UserTask, LessonProgress, LessonQuiz, Module

import subprocess
import tempfile
import os


@login_required
def lesson_by_index_view(request, module_id, order_index):
    lesson = get_object_or_404(Lesson, module_id=module_id, order_index=order_index)
    module = lesson.module
    tasks = Task.objects.filter(lesson=lesson)
    quizzes = LessonQuiz.objects.filter(lesson=lesson)
    user_tasks = {ut.task_id: ut for ut in UserTask.objects.filter(user=request.user, task__in=tasks)}
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    # Определяем следующий урок и модуль
    next_lesson = Lesson.objects.filter(module=module, order_index__gt=lesson.order_index).order_by('order_index').first()
    is_last_lesson = not next_lesson
    next_module = None
    first_lesson_next_module = None

    if is_last_lesson:
        next_module = Module.objects.filter(order_index__gt=module.order_index).order_by('order_index').first()
        if next_module:
            first_lesson_next_module = Lesson.objects.filter(module=next_module).order_by('order_index').first()

    # ✅ AJAX: завершение урока или запуск кода
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if 'complete_lesson' in request.POST:
            all_tasks_correct = all(
                user_tasks.get(task.id) and user_tasks[task.id].is_correct
                for task in tasks
            )
            correct_quiz_count = 0
            for quiz in quizzes:
                answer = request.POST.get(f'q{quiz.id}')
                if answer and int(answer) == quiz.correct_option:
                    correct_quiz_count += 1
            test_passed = (correct_quiz_count == len(quizzes)) if quizzes else True

            if all_tasks_correct and test_passed:
                progress.completed = True
                progress.save()

                if next_lesson:
                    LessonProgress.objects.get_or_create(user=request.user, lesson=next_lesson)
                elif first_lesson_next_module:
                    LessonProgress.objects.get_or_create(user=request.user, lesson=first_lesson_next_module)

                return JsonResponse({"success": True})
            return JsonResponse({"success": False})

        # ✅ запуск кода
        task_id = request.POST.get("task_id")
        code = request.POST.get("code")
        task_level = request.POST.get("task_level", "default")
        output = ""
        is_correct = False
        hint = ""

        try:
            task = Task.objects.get(id=task_id)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w', encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name

            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            output = stdout if stdout else stderr

            # Подсказки по типовым ошибкам
            if "NameError" in stderr and "is not defined" in stderr:
                if "pront" in stderr:
                    hint = "💡 Возможно, вы имели в виду <code>print</code>, а не <code>pront</code>?"
                else:
                    hint = "💡 Проверьте правильность написания имён переменных и функций."
            elif "SyntaxError" in stderr:
                hint = "💡 Проверьте синтаксис: возможно, не хватает кавычек, скобок или двоеточия."
            elif "IndentationError" in stderr:
                hint = "💡 Проверьте отступы: Python чувствителен к пробелам в начале строк."
            elif "TypeError" in stderr:
                hint = "💡 Возможно, вы используете операцию для неподходящего типа данных."

            # Ожидаемый вывод по уровню
            if task_level == "easy":
                expected = (task.expected_output_easy or "").strip()
            elif task_level == "hard":
                expected = (task.expected_output_hard or "").strip()
            else:
                expected = (task.expected_output or "").strip()

            is_correct = stdout == expected

            user_task, created = UserTask.objects.get_or_create(user=request.user, task=task)
            user_task.code = code
            user_task.output = output
            user_task.is_correct = is_correct
            if created:
                user_task.attempts = 1  # первая попытка
            else:
                user_task.attempts += 1  # последующие
            user_task.save()
        except Exception as e:
            output = f"Ошибка: {str(e)}"
            is_correct = False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return JsonResponse({
            "output": output,
            "is_correct": is_correct,
            "hint": hint
        })

    # POST без AJAX (резервное завершение)
    if request.method == 'POST' and 'complete_lesson' in request.POST:
        return redirect('lesson_detail', module_id=module.id, order_index=order_index)

    # Дополнительные данные
    expected_easy = {t.id: t.expected_output_easy for t in tasks}
    expected_hard = {t.id: t.expected_output_hard for t in tasks}
    task_easy_map = {t.id: t.description_easy for t in tasks}
    task_hard_map = {t.id: t.description_hard for t in tasks}

    all_modules = Module.objects.prefetch_related('lesson_set').order_by('order_index')
    all_lesson_progress = LessonProgress.objects.filter(user=request.user)
    lesson_progress_map = {lp.lesson_id: lp for lp in all_lesson_progress}

    return render(request, 'core/lesson_detail.html', {
        'lesson': lesson,
        'module': module,
        'tasks': tasks,
        'quizzes': quizzes,
        'user_tasks': user_tasks,
        'progress': progress,
        'next_lesson': next_lesson,
        'is_last_lesson': is_last_lesson,
        'next_module': next_module,
        'first_lesson_next_module': first_lesson_next_module,
        'all_modules': all_modules,
        'lesson_progress': lesson_progress_map,
        'current_lesson_id': lesson.id,
        'lesson_easy': lesson.content_html_easy,
        'lesson_hard': lesson.content_html_hard,
        'expected_easy': expected_easy,
        'expected_hard': expected_hard,
        'task_easy_map': task_easy_map,
        'task_hard_map': task_hard_map,
    })




from .models import Course, Lesson, Task
from .forms import CourseForm, ModuleForm, LessonForm, TaskForm, LessonQuizForm
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role in ('admin', 'teacher')

@login_required
@user_passes_test(is_admin)
def manage_courses(request):
    courses = Course.objects.all()
    return render(request, 'core/manage_courses.html', {'courses': courses})

@login_required
@user_passes_test(is_admin)
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            return redirect('manage_courses')
    else:
        form = CourseForm()
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Добавить курс'})

@login_required
@user_passes_test(is_admin)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('manage_courses')
    else:
        form = CourseForm(instance=course)

    return render(request, 'core/course_form.html', {
        'form': form,
        'title': 'Редактировать курс',
        'course': course  # ← добавлено
    })


@login_required
@user_passes_test(is_admin)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('manage_courses')
    return render(request, 'core/confirm_delete.html', {'object': course, 'title': 'Удалить курс'})


@login_required
@user_passes_test(is_admin)
def manage_modules(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course).order_by('order_index')
    return render(request, 'core/manage_modules.html', {'course': course, 'modules': modules})


@login_required
@user_passes_test(is_admin)
def add_module(request):
    course_id = request.GET.get('course')
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            return redirect('manage_modules', course_id=course.id)
    else:
        form = ModuleForm()

    return render(request, 'core/module_form.html', {'form': form, 'title': 'Добавить модуль', 'course': course})

@login_required
@user_passes_test(is_admin)
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect('manage_modules', course_id=module.course.id)
    else:
        form = ModuleForm(instance=module)

    return render(request, 'core/module_form.html', {
        'form': form,
        'title': 'Редактировать модуль',
        'module': module  # ← это важно
    })


@login_required
@user_passes_test(is_admin)
def manage_tasks(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    tasks = Task.objects.filter(lesson=lesson)
    return render(request, 'core/manage_tasks.html', {'lesson': lesson, 'tasks': tasks})


@login_required
@user_passes_test(is_admin)
def add_task(request):
    lesson_id = request.GET.get('lesson')
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.lesson = lesson
            task.module = lesson.module  # важно: заполняем связанный module
            task.save()
            return redirect('manage_tasks', lesson_id=lesson.id)
    else:
        form = TaskForm()

    return render(request, 'core/task_form.html', {
        'form': form,
        'lesson': lesson,
        'title': 'Добавить задание'
    })


@login_required
@user_passes_test(is_admin)
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    lesson = task.lesson

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('manage_tasks', lesson_id=lesson.id)
    else:
        form = TaskForm(instance=task)

    return render(request, 'core/task_form.html', {'form': form, 'lesson': lesson, 'title': 'Редактировать задание'})


@login_required
@user_passes_test(is_admin)
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    lesson = task.lesson

    if request.method == 'POST':
        task.delete()
        return redirect('manage_tasks', lesson_id=lesson.id)

    return render(request, 'core/confirm_delete.html', {'object': task, 'title': 'Удалить задание'})


@login_required
@user_passes_test(is_admin)
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.method == 'POST':
        module.delete()
        return redirect('manage_modules', course_id=course.id)

    return render(request, 'core/confirm_delete.html', {'object': module, 'title': 'Удалить модуль'})


@login_required
@user_passes_test(is_admin)
def manage_lessons(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    lessons = Lesson.objects.filter(module=module).order_by('order_index')
    return render(request, 'core/manage_lessons.html', {'module': module, 'lessons': lessons})


@login_required
@user_passes_test(is_admin)
def add_lesson(request):
    module_id = request.GET.get('module')
    module = get_object_or_404(Module, id=module_id)

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            return redirect('manage_lessons', module_id=module.id)
    else:
        form = LessonForm()

    return render(request, 'core/lesson_form.html', {'form': form, 'title': 'Добавить урок', 'module': module})


@login_required
@user_passes_test(is_admin)
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    module = lesson.module
    tasks = Task.objects.filter(lesson=lesson)
    quizzes = LessonQuiz.objects.filter(lesson=lesson)

    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('manage_lessons', module_id=module.id)
    else:
        form = LessonForm(instance=lesson)

    return render(request, 'core/lesson_form.html', {
        'form': form,
        'title': 'Редактировать урок',
        'module': module,
        'lesson': lesson,
        'tasks': tasks,
        'quizzes': quizzes,
    })


@login_required
@user_passes_test(is_admin)
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    module = lesson.module

    if request.method == 'POST':
        lesson.delete()
        return redirect('manage_lessons', module_id=module.id)

    return render(request, 'core/confirm_delete.html', {'object': lesson, 'title': 'Удалить урок'})


@login_required
@user_passes_test(is_admin)
def manage_quizzes(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quizzes = LessonQuiz.objects.filter(lesson=lesson)
    return render(request, 'core/manage_quizzes.html', {'lesson': lesson, 'quizzes': quizzes})


@login_required
@user_passes_test(is_admin)
def add_quiz(request):
    lesson_id = request.GET.get('lesson')
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST':
        form = LessonQuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            return redirect('manage_quizzes', lesson_id=lesson.id)
    else:
        form = LessonQuizForm()

    return render(request, 'core/quiz_form.html', {'form': form, 'lesson': lesson, 'title': 'Добавить вопрос'})


@login_required
@user_passes_test(is_admin)
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(LessonQuiz, id=quiz_id)
    lesson = quiz.lesson

    if request.method == 'POST':
        form = LessonQuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            return redirect('manage_quizzes', lesson_id=lesson.id)
    else:
        form = LessonQuizForm(instance=quiz)

    return render(request, 'core/quiz_form.html', {'form': form, 'lesson': lesson, 'title': 'Редактировать вопрос'})


@login_required
@user_passes_test(is_admin)
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(LessonQuiz, id=quiz_id)
    lesson = quiz.lesson

    if request.method == 'POST':
        quiz.delete()
        return redirect('manage_quizzes', lesson_id=lesson.id)

    return render(request, 'core/confirm_delete.html', {'object': quiz, 'title': 'Удалить вопрос'})


