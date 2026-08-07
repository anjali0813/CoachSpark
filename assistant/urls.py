"""
urls.py - Coach Spark app routes

If your project's main urls.py doesn't already include this app,
add: path('', include('assistant.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat_api, name='chat_api'),
    path('quiz/start/', views.quiz_start, name='quiz_start'),
    path('quiz/answer/', views.quiz_answer, name='quiz_answer'),
]