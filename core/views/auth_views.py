from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages

from core.forms import CustomUserCreationForm, CustomAuthenticationForm

def home_view(request):
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
