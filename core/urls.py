from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.home,             name='home'),
    path('concepts/',               views.concepts_list,    name='concepts_list'),
    path('concepts/<slug:slug>/',   views.concept_detail,   name='concept_detail'),
    path('ask/',                    views.ask,              name='ask'),
    path('recent/',                 views.recent_questions, name='recent_questions'),
    path('clear-history/',          views.clear_history,    name='clear_history'),
]