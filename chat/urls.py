from django.urls import path
from . import views

urlpatterns = [
    path('', views.conversations_list, name='chat_list'),
    path('thread/<int:pk>/', views.thread_view, name='chat_thread'),
    path('bot/', views.openai_chat, name='chat_bot'),
]
