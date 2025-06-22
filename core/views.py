from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from collections import defaultdict
from itertools import chain
from django.template.loader import render_to_string


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

@login_required
def profile(request):
    user = request.user

    # Kommentare des Benutzers
    comments = Comment.objects.filter(user=user).order_by('-created_at')

    # Favorisierte Teams
    favorite_teams = FavoriteTeam.objects.filter(user=user).select_related('team')

    # Letzte Spiele je Team (z. B. 5)
    team_matches = {}
    for fav in favorite_teams:
        team = fav.team
        matches = Match.objects.filter(
            Q(team1=team) | Q(team2=team)
        ).order_by('-match_date')[:5]
        team_matches[team] = matches

    return render(request, 'profile.html', {
        'comments': comments,
        'favorite_teams': favorite_teams,
        'team_matches': team_matches,
    })

def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    
    # Basis-QuerySet
    matches = Match.objects.filter(sport=sport)
    
    # Filterparameter aus GET-Request
    tournament_id = request.GET.get('tournament')
    team_id = request.GET.get('team')
    
    # Filter anwenden
    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if team_id:
        matches = matches.filter(Q(team1_id=team_id) | Q(team2_id=team_id))
    
    # Daten für Filter-Dropdowns sammeln
    tournaments = Tournament.objects.filter(sport=sport)
    teams = Team.objects.filter(sport=sport)
    
    return render(request, 'sport_matches.html', {
        'sport': sport,
        'matches': matches.order_by('-match_date'),
        'tournaments': tournaments,
        'teams': teams,
        'selected_tournament': int(tournament_id) if tournament_id else None,
        'selected_team': int(team_id) if team_id else None,
    })

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


def load_filter_options(request):
    sport_id = request.GET.get('sport_id')
    option_type = request.GET.get('type')  # 'teams' oder 'tournaments'
    
    if not sport_id or option_type not in ['teams', 'tournaments']:
        return HttpResponse('')
    
    if option_type == 'teams':
        queryset = Team.objects.filter(sport_id=sport_id)
    else:
        queryset = Tournament.objects.filter(sport_id=sport_id)
    
    return render(request, 'core/includes/filter_options.html', {
        'items': queryset,
        'item_type': option_type
    })
    
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
    # Favorisierte Teams + IDs
    favorite_teams = FavoriteTeam.objects.filter(user=request.user).select_related('team__sport')
    favorite_ids = set(favorite_teams.values_list('team_id', flat=True))

    # Filterparameter
    sport_id = request.GET.get('sport')
    tournament_id = request.GET.get('tournament')
    team_id = request.GET.get('team')

    # Spiele mit favorisierten Teams
    matches = Match.objects.filter(
        Q(team1__in=favorite_ids) | Q(team2__in=favorite_ids)
    )

    if sport_id:
        matches = matches.filter(sport_id=sport_id)
    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if team_id:
        matches = matches.filter(Q(team1_id=team_id) | Q(team2_id=team_id))

    # Sportarten, Teams und Turniere richtig filtern
    all_sports = Sport.objects.all().order_by('name')
    all_teams = Team.objects.select_related('sport').all()
    all_tournaments = Tournament.objects.filter(
        id__in=matches.values_list('tournament', flat=True).distinct()
    )

    # Favoritenlisten korrekt nach Sport gruppieren
    sports_with_teams = []
    for sport in all_sports:
        teams_in_sport = all_teams.filter(sport=sport)
        sports_with_teams.append({
            'sport': sport,
            'teams': teams_in_sport
        })

    # Gruppiere Matches nach Sport und Turnier
    sports_data = []
    for sport in all_sports:
        sport_matches = matches.filter(sport=sport)
        tournaments_data = defaultdict(list)
        for match in sport_matches:
            tournaments_data[match.tournament].append(match)
        if sport_matches.exists():
            sports_data.append({
                'sport': sport,
                'tournaments': dict(tournaments_data)
            })

    return render(request, 'favorite_matches.html', {
        'sports_data': sports_data,
        'all_sports': all_sports,
        'all_tournaments': all_tournaments,
        'all_teams': all_teams,
        'sports_with_teams': sports_with_teams,
        'favorite_ids': favorite_ids,
        'selected_sport': int(sport_id) if sport_id else None,
        'selected_tournament': int(tournament_id) if tournament_id else None,
        'selected_team': int(team_id) if team_id else None,
    })



    # Filter anwenden
    if sport_id:
        matches = matches.filter(sport_id=sport_id)
    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if team_id:
        matches = matches.filter(Q(team1_id=team_id) | Q(team2_id=team_id))

    # Daten für Filter-Dropdowns sammeln
    sports = Sport.objects.filter(
        id__in=set(ft.team.sport.id for ft in favorite_teams)
    )
    tournaments = Tournament.objects.filter(
        id__in=matches.values_list('tournament', flat=True).distinct()
    )
    teams = Team.objects.filter(
        id__in=set([ft.team.id for ft in favorite_teams])
    )

    # Gruppierung für die Anzeige
    sports_data = []
    for sport in sports:
        sport_matches = matches.filter(sport=sport)
        if not sport_matches.exists():
            continue
            
        tournaments_data = defaultdict(list)
        for match in sport_matches:
            tournaments_data[match.tournament].append(match)
        
        sports_data.append({
            'sport': sport,
            'tournaments': dict(tournaments_data)
        })

    return render(request, 'favorite_matches.html', {
        'sports_data': sports_data,
        'all_sports': sports,
        'all_tournaments': tournaments,
        'all_teams': teams,
        'selected_sport': int(sport_id) if sport_id else None,
        'selected_tournament': int(tournament_id) if tournament_id else None,
        'selected_team': int(team_id) if team_id else None,
    })
@login_required
def search(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return redirect('index')

    matching_tournaments = Tournament.objects.filter(name__icontains=query)
    matching_teams = Team.objects.filter(name__icontains=query)

    matches = Match.objects.filter(
        Q(team1__name__icontains=query) |
        Q(team2__name__icontains=query) |
        Q(tournament__name__icontains=query)
    ).distinct()

    if matches.count() == 1 and not matching_tournaments.exists() and not matching_teams.exists():
        return redirect('match_detail', id=matches.first().id)

    # NEU: teams_with_matches vorbereiten
    teams_with_matches = []
    for team in matching_teams:
        team_matches = Match.objects.filter(
            Q(team1=team) | Q(team2=team)
        ).order_by('-match_date')
        teams_with_matches.append((team, team_matches))

    return render(request, 'search_results.html', {
        'query': query,
        'teams_with_matches': teams_with_matches,  # <- NEU
        'tournaments': matching_tournaments,
        'matches': matches,
    })

@login_required
def ajax_live_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({'html': ''})

    matches = Match.objects.filter(
        Q(team1__name__icontains=query) |
        Q(team2__name__icontains=query) |
        Q(tournament__name__icontains=query)
    ).order_by('-match_date')[:5]

    teams = Team.objects.filter(name__icontains=query)[:5]
    tournaments = Tournament.objects.filter(name__icontains=query)[:5]

    html = render_to_string("includes/search_suggestions.html", {
        "matches": matches,
        "teams": teams,
        "tournaments": tournaments
    })

    return JsonResponse({"html": html})


@login_required
def favorite_team_browser(request):
    sports = Sport.objects.all()
    favorite_ids = set(FavoriteTeam.objects.filter(user=request.user).values_list('team_id', flat=True))

    sports_with_teams = []
    for sport in sports:
        teams = Team.objects.filter(sport=sport)
        sports_with_teams.append({
            'name': sport.name,
            'teams': teams,
            'id': sport.id,
        })

    return render(request, 'core/favorite_team_browser.html', {
        'sports': sports_with_teams,
        'favorite_ids': favorite_ids,
    })


