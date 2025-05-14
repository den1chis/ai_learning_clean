import os
import subprocess
import tempfile

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.models import (
    Module, Lesson, Task, UserTask,
    LessonProgress, LessonQuiz
)


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