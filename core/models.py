from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
        ('ai', 'ИИ'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        db_table = 'core_user'
    def __str__(self):
        return self.username


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='created_by',
        on_delete=models.CASCADE
    )
    level = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        managed = False

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(
        Course,
        db_column='course_id',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'modules'
        managed = False
        ordering = ['order_index']

    def __str__(self):
        return f'{self.course} — {self.title}'


class Question(models.Model):
    module = models.ForeignKey(
        Module,
        db_column='module_id',
        on_delete=models.CASCADE
    )
    difficulty = models.IntegerField()
    question_text = models.TextField()
    option_1 = models.TextField()
    option_2 = models.TextField()
    option_3 = models.TextField()
    option_4 = models.TextField()
    correct_option = models.IntegerField()
    is_generated_by_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        managed = False
        ordering = ['module_id', 'id']

    def __str__(self):
        return f'Q{self.id} ({self.module.title}): {self.question_text[:50]}…'


class UserAnswer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_option = models.IntegerField(null=True)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_answers'
        managed = False
        ordering = ['-answered_at']

    def __str__(self):
        status = '✔' if self.is_correct else '✘'
        return f'{self.user.username} – Q{self.question_id}: {status}'


class Recommendation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    module = models.ForeignKey(
        Module,
        db_column='module_id',
        on_delete=models.CASCADE
    )
    recommendation_type = models.CharField(max_length=20)
    confidence_score = models.FloatField()
    generated_by = models.CharField(max_length=20, default='ai')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendations'
        managed = False
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.username} → {self.module.title} ({self.recommendation_type})'


class UserProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    module = models.ForeignKey(
        Module,
        db_column='module_id',
        on_delete=models.CASCADE
    )
    completion_percent = models.IntegerField()
    last_accessed = models.DateTimeField(auto_now=True)
    recommended_difficulty = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'user_progress'
        managed = True
        unique_together = ('user', 'module')
        ordering = ['user_id', 'module_id']

    def __str__(self):
        return f'{self.user.username} – {self.module.title}: {self.completion_percent}%'


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        db_column='module_id',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20)  # например: 'article', 'video', 'file'
    content_link = models.TextField(blank=True, null=True)
    content_html = models.TextField(blank=True, null=True)
    content_html_easy = models.TextField(blank=True, null=True)
    content_html_hard = models.TextField(blank=True, null=True)

    order_index = models.IntegerField(default=0)
    template_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'lessons'
        managed = False  # так как таблица уже есть
        ordering = ['order_index']

    def __str__(self):
        return f'{self.module.title} — {self.title}'
    

class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lesson_progress'
        managed = True  # ты создаёшь эту модель — Django её будет управлять
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title}: {"✔" if self.completed else "✘"}'
    


class Task(models.Model):
    id = models.AutoField(primary_key=True)
    module = models.ForeignKey('Module', db_column='module_id', on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', db_column='lesson_id', on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    description_easy = models.TextField(blank=True, null=True)
    description_hard = models.TextField(blank=True, null=True)
    task_type = models.CharField(max_length=20)  # например: 'code', 'quiz'
    input_data = models.TextField(blank=True, null=True)
    expected_output = models.TextField(blank=True, null=True)
    expected_output_easy = models.TextField(blank=True, null=True)
    expected_output_hard = models.TextField(blank=True, null=True)

    is_ai_adaptive = models.BooleanField(default=False)

    class Meta:
        db_table = 'tasks'
        managed = False
        ordering = ['id']

    def __str__(self):
        return self.title



class UserTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    code = models.TextField()
    output = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField()
    checked_at = models.DateTimeField(auto_now=True)
    attempts = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'user_tasks'
        unique_together = ('user', 'task')
        managed = False


class LessonQuiz(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    question_text = models.TextField()
    option_1 = models.TextField()
    option_2 = models.TextField()
    option_3 = models.TextField()
    option_4 = models.TextField()
    correct_option = models.IntegerField(choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lesson_quizzes'  # это важно!
        managed = False  # таблица уже есть, Django её не создаёт и не мигрирует

    def __str__(self):
        return f"Вопрос к уроку {self.lesson_id}: {self.question_text[:40]}"
