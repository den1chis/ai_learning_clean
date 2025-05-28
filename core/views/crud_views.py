from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

from core.forms import (
    CourseForm, ModuleForm, LessonForm,
    TaskForm, LessonQuizForm
)
from core.models import (
    Course, Module, Lesson,
    Task, LessonQuiz
)


def is_admin(user):
    return user.is_authenticated and user.role in ('admin', 'teacher')


# ------- Courses --------

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

login_required
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


# ------- Modules --------

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
        'module': module,  
        'course': module.course
    })
@login_required
@user_passes_test(is_admin)
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.method == 'POST':
        module.delete()
        return redirect('manage_modules', course_id=course.id)

    return render(request, 'core/confirm_delete.html', {'object': module, 'title': 'Удалить модуль'})



# ------- Lessons --------

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


# ------- Quizzes --------

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

