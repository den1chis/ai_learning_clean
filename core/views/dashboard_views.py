from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from core.models import Module, Lesson, LessonProgress, Recommendation, UserTask
from core.forms import ProfileUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


@login_required
def profile_settings_view(request):
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
def dashboard_view(request):
    modules = list(Module.objects.filter(course_id=1).order_by('order_index'))

    rec = (Recommendation.objects
           .filter(user=request.user, recommendation_type='next_module')
           .order_by('-timestamp')
           .first())

    recommended_module = rec.module if rec else None

    completed_lesson_ids = set(
        LessonProgress.objects
        .filter(user=request.user, completed=True)
        .values_list('lesson_id', flat=True)
    )

    all_lessons = 0
    completed_lessons = 0
    modules_info = []
    unlocked_flag = True

    for m in modules:
        lessons = Lesson.objects.filter(module=m).order_by('order_index')
        lesson_ids = lessons.values_list('id', flat=True)
        total = lessons.count()
        completed = sum(1 for lid in lesson_ids if lid in completed_lesson_ids)

        all_lessons += total
        completed_lessons += completed

        is_recommended = recommended_module and (m.id == recommended_module.id)

        modules_info.append({
            'module': m,
            'unlocked': unlocked_flag or is_recommended,
            'recommended': is_recommended,
            'total_lessons': total,
            'completed_lessons': completed,
            'module_progress': int((completed / total) * 100) if total > 0 else 0
        })

        if completed < total and not is_recommended:
            unlocked_flag = False

    progress_percent = int((completed_lessons / all_lessons) * 100) if all_lessons > 0 else 0

    return render(request, 'core/dashboard.html', {
        'recommended_module': recommended_module,
        'modules_info': modules_info,
        'progress_percent': progress_percent,
        'recent_actions': [],
    })


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