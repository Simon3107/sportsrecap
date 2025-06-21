from django.urls import path
from . import views
from .views import add_comment, CustomLoginView, CustomLogoutView, register
from core.views import load_filter_options

urlpatterns = [
    path('ajax/load-tournaments/', views.load_tournaments, name='load_tournaments'),
    path('ajax/load-teams/', views.load_teams, name='load_teams'),
    path('', views.home, name='index'),
    path('sports/', views.sport_list, name='sport_list'),
    path('match/<int:id>/', views.match_detail, name='match_detail'),
    path('profile/', views.profile, name='profile'),
    path('sports/<int:id>/matches/', views.sport_matches, name='sport_matches'),
    path('match/<int:match_id>/comment/', add_comment, name='add_comment'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('ajax/load-filter-options/', load_filter_options, name='load_filter_options'),

    # 👇 Neue URL für Favoriten-Funktion:
    path('favorit/<int:team_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favoriten/', views.favorite_matches, name='favorite_matches'),
    path('suche/', views.search, name='search'),
    path('ajax/live-search/', views.ajax_live_search, name='ajax_live_search'),
    path('favoriten/bearbeiten/', views.favorite_team_browser, name='favorite_team_browser'),



]

