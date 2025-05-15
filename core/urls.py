from django.urls import path
from core.views import (
    auth_views,
    dashboard_views,
    admin_views,
    test_views,
    lesson_views,
    crud_views,
    ai_recommendation
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 🔹 Общие
    path('', auth_views.home_view, name='home'),

    path('register/', auth_views.register_view, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),

    # 🔹 Дашборд
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('profile/settings/', dashboard_views.profile_settings_view, name='profile_settings'),


    # 🔹 Админка
    path('admin-panel/profile/', admin_views.admin_profile_view, name='admin_profile'),
    path('admin-panel/students/', admin_views.admin_students_view, name='admin_students'),
    path('admin-panel/students/<int:user_id>/', admin_views.admin_student_detail, name='admin_student_detail'),

    # 🔹 Demo тест
    path('demo/test/', ai_recommendation.demo_test, name='demo_test'),
    path('demo/result/', ai_recommendation.demo_result, name='demo_result'),

    # 🔹 Адаптивное тестирование
    path('test/start/', test_views.test_start, name='test_start'),
    path('test/question/<int:idx>/', test_views.test_question, name='test_question'),
    path('test/loading/', test_views.test_loading, name='test_loading'),
    path('test/result/', test_views.test_result, name='test_result'),

    # 🔹 Уроки и модули
    path('module/<int:module_id>/', lesson_views.module_lessons_view, name='module_lessons'),
    path('module/<int:module_id>/lesson/<int:order_index>/', lesson_views.lesson_by_index_view, name='lesson_detail'),

    # 🔹 Курсы
    path('courses/', crud_views.manage_courses, name='manage_courses'),
    path('courses/add/', crud_views.add_course, name='add_course'),
    path('courses/<int:course_id>/edit/', crud_views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', crud_views.delete_course, name='delete_course'),

    # 🔹 Модули
    path('modules/<int:course_id>/', crud_views.manage_modules, name='manage_modules'),
    path('modules/add/', crud_views.add_module, name='add_module'),
    path('modules/<int:module_id>/edit/', crud_views.edit_module, name='edit_module'),
    path('modules/<int:module_id>/delete/', crud_views.delete_module, name='delete_module'),

    # 🔹 Уроки
    path('lessons/<int:module_id>/', crud_views.manage_lessons, name='manage_lessons'),
    path('lessons/add/', crud_views.add_lesson, name='add_lesson'),
    path('lessons/<int:lesson_id>/edit/', crud_views.edit_lesson, name='edit_lesson'),
    path('lessons/<int:lesson_id>/delete/', crud_views.delete_lesson, name='delete_lesson'),

    # 🔹 Тесты
    path('quizzes/<int:lesson_id>/', crud_views.manage_quizzes, name='manage_quizzes'),
    path('quizzes/add/', crud_views.add_quiz, name='add_quiz'),
    path('quizzes/<int:quiz_id>/edit/', crud_views.edit_quiz, name='edit_quiz'),
    path('quizzes/<int:quiz_id>/delete/', crud_views.delete_quiz, name='delete_quiz'),


    # 🔹 Задания
    path('tasks/<int:lesson_id>/', crud_views.manage_tasks, name='manage_tasks'),
    path('tasks/add/', crud_views.add_task, name='add_task'),
    path('tasks/<int:task_id>/edit/', crud_views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/delete/', crud_views.delete_task, name='delete_task'),
]   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
