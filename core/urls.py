from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),

    path('admin-panel/', views.admin_profile_view, name='admin_profile'),
    path('admin-panel/students/', views.admin_students_view, name='admin_students'),
    path('admin-panel/students/<int:user_id>/', views.admin_student_detail, name='admin_student_detail'),




    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('test/', views.test_view, name='test'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),


    path('test/start/',     views.test_start,     name='test_start'),
    path('test/question/<int:idx>/', views.test_question, name='test_question'),
    path('test/loading/',   views.test_loading,   name='test_loading'),
    path('test/result/',    views.test_result,    name='test_result'),



    path('demo-test/', views.demo_test,   name='demo_test'),
    path('demo-result/', views.demo_result, name='demo_result'),



    path('module/<int:module_id>/lessons/', views.module_lessons_view, name='module_lessons'),

    path('module/<int:module_id>/lesson/<int:order_index>/', views.lesson_by_index_view, name='lesson_detail'),



    path('manage/', views.manage_courses, name='manage_courses'),
    path('manage/course/add/', views.add_course, name='add_course'),
    path('manage/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('manage/course/<int:course_id>/delete/', views.delete_course, name='delete_course'),

    path('manage/course/<int:course_id>/modules/', views.manage_modules, name='manage_modules'),
    path('manage/module/add/', views.add_module, name='add_module'),
    path('manage/module/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('manage/module/<int:module_id>/delete/', views.delete_module, name='delete_module'),

    path('manage/module/<int:module_id>/lessons/', views.manage_lessons, name='manage_lessons'),
    path('manage/lesson/add/', views.add_lesson, name='add_lesson'),
    path('manage/lesson/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('manage/lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),


    # управление заданием
    path('manage/lesson/<int:lesson_id>/tasks/', views.manage_tasks, name='manage_tasks'),
    path('manage/task/add/', views.add_task, name='add_task'),
    path('manage/task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('manage/task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    #управление мини-тестами
    path('manage/lesson/<int:lesson_id>/quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('manage/quiz/add/', views.add_quiz, name='add_quiz'),
    path('manage/quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('manage/quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),

    

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)