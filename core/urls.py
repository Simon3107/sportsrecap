from django.urls import path
from . import views
from .views import add_comment, CustomLoginView, CustomLogoutView, register

urlpatterns = [
    path('ajax/load-tournaments/', views.load_tournaments, name='load_tournaments'),
    path('', views.home, name='index'),
    path('sports/', views.sport_list, name='sport_list'),
    path('match/<int:id>/', views.match_detail, name='match_detail'),
    path('profile/', views.profile, name='profile'),
    path('sports/<int:id>/matches/', views.sport_matches, name='sport_matches'),
    path('match/<int:match_id>/comment/', add_comment, name='add_comment'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),

    # 👇 Neue URL für Favoriten-Funktion:
    path('favorit/<int:team_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favoriten/', views.favorite_matches, name='favorite_matches'),
]

