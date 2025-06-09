from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),
    path('sports/', views.sport_list, name='sport_list'),
    path('match/<int:id>/', views.match_detail, name='match_detail'),
    path('profile/', views.profile, name='profile'),
    path('sports/<int:id>/matches/', views.sport_matches, name='sport_matches'),
	
]
