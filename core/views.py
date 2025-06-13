from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from collections import defaultdict

from .models import (
    Sport,
    Match,
    Comment,
    Tournament,
    Team,
    FavoriteTeam,
)
from .forms import CommentForm

# ---------- Registrierung ----------
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# ---------- Startseite ----------
def home(request):
    sports = Sport.objects.all()
    data = []

    for sport in sports:
        matches = Match.objects.filter(sport=sport).order_by('-match_date')

        tournaments_all = defaultdict(list)
        tournaments_latest = {}

        for match in matches:
            tournament = match.tournament

            # Alle Matches für Favoriten-Seite
            tournaments_all[tournament].append(match)

            # Nur das neueste Match pro Turnier (für Startseite)
            if tournament not in tournaments_latest:
                tournaments_latest[tournament] = match

        data.append({
            'sport': sport,
            'tournaments_all': dict(tournaments_all),
            'tournaments_latest': tournaments_latest
        })

    return render(request, 'index.html', {'data': data})

# ---------- Sport- und Match-Ansichten ----------
def sport_list(request):
    return render(request, 'sport_list.html')

def match_detail(request, id):
    match = get_object_or_404(Match, pk=id)
    comments = Comment.objects.filter(match=match).order_by('-created_at')
    
    # Check if teams are favorited by the user
    is_team1_favorite = False
    is_team2_favorite = False
    
    if request.user.is_authenticated:
        is_team1_favorite = FavoriteTeam.objects.filter(
            user=request.user, 
            team=match.team1
        ).exists()
        is_team2_favorite = FavoriteTeam.objects.filter(
            user=request.user, 
            team=match.team2
        ).exists()
    
    return render(request, 'match_detail.html', {
        'match': match,
        'comments': comments,
        'comment_form': CommentForm(),
        'is_team1_favorite': is_team1_favorite,
        'is_team2_favorite': is_team2_favorite,
    })

@login_required
def add_comment(request, match_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.match = get_object_or_404(Match, pk=match_id)
            comment.save()
            return JsonResponse({
                'success': True,
                'comment': comment.text,
                'user': comment.user.username,
                'date': comment.created_at.strftime("%d.%m.%Y %H:%M"),
            })
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def profile(request):
    return render(request, 'profile.html')

def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    matches = Match.objects.filter(sport=sport)
    return render(request, 'sport_matches.html', {'sport': sport, 'matches': matches})

# ---------- Auth Views ----------
class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Erfolgreich eingeloggt!")
        return response

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Erfolgreich ausgeloggt!")
        return super().dispatch(request, *args, **kwargs)

def load_teams(request):
    sport_id = request.GET.get('sport_id')
    teams = Team.objects.filter(sport_id=sport_id)
    return render(request, 'admin/core/match/team_options.html', {'teams': teams})

# ---------- Ajax für Turnierauswahl ----------
def load_tournaments(request):
    sport_id = request.GET.get('sport_id')
    tournaments = Tournament.objects.filter(sport_id=sport_id)
    return render(request, 'admin/core/match/tournament_options.html', {'tournaments': tournaments})

# ---------- Favoriten-Toggle ----------
@login_required
def toggle_favorite(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    favorite, created = FavoriteTeam.objects.get_or_create(user=request.user, team=team)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed', 'team_id': team_id})
        return JsonResponse({'status': 'added', 'team_id': team_id})
    
    if not created:
        favorite.delete()
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# ---------- Favoriten-Seite ----------
@login_required
def favorite_matches(request):
    # Hole alle Favoriten inkl. Sportart des Teams
    favorite_teams = FavoriteTeam.objects.filter(
        user=request.user
    ).select_related('team__sport')

    # IDs der favorisierten Teams
    favorite_team_ids = [ft.team.id for ft in favorite_teams]
    
    # Filtere nur Matches mit den favorisierten Teams
    matches = Match.objects.filter(
        Q(team1__in=favorite_team_ids) | Q(team2__in=favorite_team_ids)
    ).order_by('-match_date')

    # Gruppierung nach Sportarten und Turnieren
    sports_data = []
    favorite_sports = Sport.objects.filter(
        id__in=set(ft.team.sport.id for ft in favorite_teams)
    )

    for sport in favorite_sports:
        sport_matches = matches.filter(sport=sport)
        
        tournaments = defaultdict(list)
        for match in sport_matches:
            tournaments[match.tournament].append(match)
        
        sports_data.append({
            'sport': sport,
            'tournaments': dict(tournaments)
        })

    return render(request, 'favorite_matches.html', {'sports_data': sports_data})
