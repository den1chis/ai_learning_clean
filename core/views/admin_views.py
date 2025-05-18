from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test

from core.models import User, Module, Lesson, LessonProgress, Task, UserTask, LessonQuiz, UserAnswer


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'



@login_required
@user_passes_test(is_admin)
def admin_profile_view(request):
    return render(request, 'core/admin_profile.html', {
        'admin_user': request.user
    })


@login_required
@user_passes_test(is_admin)
def admin_students_view(request):
    from django.db.models import Avg, Count
    from core.models import Lesson, LessonProgress, Module, UserProgress

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
