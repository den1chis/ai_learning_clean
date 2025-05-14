from django.contrib import admin
from .models import Question, UserAnswer, Recommendation, UserProgress

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'difficulty', 'question_text')
    list_filter = ('module', 'difficulty')
    search_fields = ('question_text',)

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('user__username',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'recommendation_type', 'confidence_score', 'timestamp')
    list_filter = ('recommendation_type',)

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'completion_percent', 'last_accessed')
    list_filter = ('module',)
