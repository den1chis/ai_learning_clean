from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Question, Module, Course, Lesson, Task, LessonQuiz

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Электронная почта'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user



class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'


class TestForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions
        for q in questions:
            choices = [
                (1, q.option_1),
                (2, q.option_2),
                (3, q.option_3),
                (4, q.option_4),
            ]
            self.fields[f'question_{q.id}'] = forms.ChoiceField(
                label=q.question_text,
                choices=choices,
                widget=forms.RadioSelect,
                required=True,
            )

class QuestionForm(forms.Form):
    choice = forms.ChoiceField(
        widget=forms.RadioSelect,
        label='',
        error_messages={'required': 'Пожалуйста, выберите вариант ответа'}  # <-- ваш текст
    )

    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choice'].label = question.question_text
        self.fields['choice'].choices = [
            (1, question.option_1),
            (2, question.option_2),
            (3, question.option_3),
            (4, question.option_4),
        ]


class DemoTestForm(forms.Form):
    """
    Поля mod_<id> для каждого модуля: целое 0–5.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        modules = Module.objects.filter(course_id=1).order_by('order_index')
        for m in modules:
            self.fields[f"mod_{m.id}"] = forms.IntegerField(
                label=m.title,
                min_value=0, max_value=5,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'w-20 px-2 py-1 bg-[#0f172a] border border-gray-700 text-white rounded'
                })
            )

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'level', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-32'
            }),
            'level': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-indigo-600'
            }),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order_index', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-24'}),
            'order_index': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox text-indigo-600'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_html', 'content_html_easy', 'content_html_hard', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'content_html': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-32'}),
            'content_html_easy': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-32'}),
            'content_html_hard': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-32'}),
            'order_index': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
        }



class TaskForm(forms.ModelForm):
    TASK_TYPE_CHOICES = [
        ('code', 'Код'),
        ('quiz', 'Тест'),
        ('text', 'Текст'),
    ]

    task_type = forms.ChoiceField(
        choices=TASK_TYPE_CHOICES,
        initial='code',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'
        })
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'description_easy',
            'description_hard',
            'task_type',
            'input_data',
            'expected_output',
            'expected_output_easy',
            'expected_output_hard',
            'is_ai_adaptive',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded h-24'}),
            'description_easy': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-blue-300 border border-gray-600 rounded h-24'}),
            'description_hard': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-purple-300 border border-gray-600 rounded h-24'}),
            'input_data': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-gray-300 border border-gray-600 rounded h-20'}),
            'expected_output': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-green-300 border border-gray-600 rounded h-20'}),
            'expected_output_easy': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-blue-300 border border-gray-600 rounded h-20'}),
            'expected_output_hard': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-purple-300 border border-gray-600 rounded h-20'}),
            'is_ai_adaptive': forms.CheckboxInput(attrs={'class': 'form-checkbox text-indigo-600'}),
        }


class LessonQuizForm(forms.ModelForm):
    class Meta:
        model = LessonQuiz
        fields = ['question_text', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'option_1': forms.TextInput(attrs={'class': 'form-input'}),
            'option_2': forms.TextInput(attrs={'class': 'form-input'}),
            'option_3': forms.TextInput(attrs={'class': 'form-input'}),
            'option_4': forms.TextInput(attrs={'class': 'form-input'}),
            'correct_option': forms.Select(attrs={'class': 'form-select bg-[#1e293b] text-white'}),
        }


class LessonQuizForm(forms.ModelForm):
    class Meta:
        model = LessonQuiz
        fields = ['question_text', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'option_1': forms.TextInput(attrs={'class': 'form-input w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'option_2': forms.TextInput(attrs={'class': 'form-input w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'option_3': forms.TextInput(attrs={'class': 'form-input w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'option_4': forms.TextInput(attrs={'class': 'form-input w-full px-4 py-2 bg-[#1e293b] text-white border border-gray-600 rounded'}),
            'correct_option': forms.Select(attrs={'class': 'form-select bg-[#1e293b] text-white border border-gray-600 rounded'}),
        }


from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from core.models import User

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'w-full p-3 rounded border border-white bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Введите новый email'
        })
        self.fields['avatar'].widget.attrs.update({
            'class': 'w-full p-2 rounded border border-white text-white bg-transparent'
        })


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full p-3 rounded border border-white bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-red-500'
            })
