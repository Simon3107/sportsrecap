from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.template.loader import render_to_string
from collections import defaultdict

from .models import Sport, Match, Comment, Tournament, Team, FavoriteTeam
from .forms import CommentForm

# ----------------------------------------
# Auth & Registrierung
# ----------------------------------------

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Erfolgreich eingeloggt!")
        return response


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Erfolgreich ausgeloggt!")
        return super().dispatch(request, *args, **kwargs)

# ----------------------------------------
# Startseite / Übersicht
# ----------------------------------------

def home(request):
    sports = Sport.objects.all()
    data = []

    for sport in sports:
        matches = Match.objects.filter(sport=sport).order_by('-match_date')
        tournaments_all = defaultdict(list)
        tournaments_latest = {}

        for match in matches:
            tournaments_all[match.tournament].append(match)
            if match.tournament not in tournaments_latest:
                tournaments_latest[match.tournament] = match

        data.append({
            'sport': sport,
            'tournaments_all': dict(tournaments_all),
            'tournaments_latest': tournaments_latest
        })

    return render(request, 'index.html', {'data': data})

# ----------------------------------------
# Einzelmatch, Kommentare
# ----------------------------------------

def match_detail(request, id):
    match = get_object_or_404(Match, pk=id)
    comments = Comment.objects.filter(match=match).order_by('-created_at')
    is_team1_favorite = is_team2_favorite = False

    if request.user.is_authenticated:
        is_team1_favorite = FavoriteTeam.objects.filter(user=request.user, team=match.team1).exists()
        is_team2_favorite = FavoriteTeam.objects.filter(user=request.user, team=match.team2).exists()

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

# ----------------------------------------
# Sport-/Turnieransicht & Filter
# ----------------------------------------

def sport_list(request):
    return render(request, 'sport_list.html')


def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    matches = Match.objects.filter(sport=sport)

    tournament_id = request.GET.get('tournament')
    team_id = request.GET.get('team')

    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if team_id:
        matches = matches.filter(Q(team1_id=team_id) | Q(team2_id=team_id))

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

# ----------------------------------------
# Profilansicht
# ----------------------------------------

@login_required
def profile(request):
    user = request.user
    comments = Comment.objects.filter(user=user).order_by('-created_at')
    favorite_teams = FavoriteTeam.objects.filter(user=user).select_related('team', 'team__sport').order_by('team__sport__name')

    team_matches = {}
    for fav in favorite_teams:
        team = fav.team
        team_matches[team] = Match.objects.filter(Q(team1=team) | Q(team2=team)).order_by('-match_date')[:5]

    return render(request, 'profile.html', {
        'comments': comments,
        'favorite_teams': favorite_teams,
        'team_matches': team_matches,
    })

# ----------------------------------------
# Favoriten-Handling
# ----------------------------------------

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


@login_required
def favorite_matches(request):
    return _render_favorite_matches(request, 'favorite_matches.html')


@login_required
def favorite_matches_snippet(request):
    html = _render_favorite_matches(request, 'favorite_matches_snippet.html', as_html=True)
    return JsonResponse({'html': html})


def _render_favorite_matches(request, template_name, as_html=False):
    favorite_teams = FavoriteTeam.objects.filter(user=request.user).select_related('team__sport')
    favorite_ids = set(favorite_teams.values_list('team_id', flat=True))

    sport_id = request.GET.get('sport')
    tournament_id = request.GET.get('tournament')
    team_id = request.GET.get('team')

    matches = Match.objects.filter(Q(team1__in=favorite_ids) | Q(team2__in=favorite_ids))

    if sport_id:
        matches = matches.filter(sport_id=sport_id)
    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if team_id:
        matches = matches.filter(Q(team1_id=team_id) | Q(team2_id=team_id))

    all_sports = Sport.objects.all().order_by('name')
    all_teams = Team.objects.select_related('sport').all()
    all_tournaments = Tournament.objects.filter(id__in=matches.values_list('tournament', flat=True).distinct())

    sports_with_teams = [{
        'sport': sport,
        'teams': all_teams.filter(sport=sport)
    } for sport in all_sports]

    sports_data = []
    for sport in all_sports:
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

    context = {
        'sports_data': sports_data,
        'all_sports': all_sports,
        'all_tournaments': all_tournaments,
        'all_teams': all_teams,
        'sports_with_teams': sports_with_teams,
        'favorite_ids': favorite_ids,
        'selected_sport': int(sport_id) if sport_id else None,
        'selected_tournament': int(tournament_id) if tournament_id else None,
        'selected_team': int(team_id) if team_id else None,
    }

    if as_html:
        return render_to_string(template_name, context, request=request)
    return render(request, template_name, context)

# ----------------------------------------
# Suchfunktion
# ----------------------------------------

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

    teams_with_matches = []
    for team in matching_teams:
        team_matches = Match.objects.filter(Q(team1=team) | Q(team2=team)).order_by('-match_date')
        teams_with_matches.append((team, team_matches))

    return render(request, 'search_results.html', {
        'query': query,
        'teams_with_matches': teams_with_matches,
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

# ----------------------------------------
# Dynamische Dropdowns (Admin/Filter)
# ----------------------------------------

def load_teams(request):
    sport_id = request.GET.get('sport_id')
    teams = Team.objects.filter(sport_id=sport_id)
    return render(request, 'admin/core/match/team_options.html', {'teams': teams})


def load_tournaments(request):
    sport_id = request.GET.get('sport_id')
    tournaments = Tournament.objects.filter(sport_id=sport_id)
    return render(request, 'admin/core/match/tournament_options.html', {'tournaments': tournaments})


def load_filter_options(request):
    sport_id = request.GET.get('sport_id')
    option_type = request.GET.get('type')
    if not sport_id or option_type not in ['teams', 'tournaments']:
        return HttpResponse('')
    queryset = Team.objects.filter(sport_id=sport_id) if option_type == 'teams' else Tournament.objects.filter(sport_id=sport_id)
    return render(request, 'core/includes/filter_options.html', {'items': queryset, 'item_type': option_type})


# ----------------------------------------
# Team-Browser zur Favoritenverwaltung
# ----------------------------------------

@login_required
def favorite_team_browser(request):
    sports = Sport.objects.all()
    favorite_ids = set(FavoriteTeam.objects.filter(user=request.user).values_list('team_id', flat=True))

    sports_with_teams = [{
        'name': sport.name,
        'teams': Team.objects.filter(sport=sport),
        'id': sport.id,
    } for sport in sports]

    return render(request, 'core/favorite_team_browser.html', {
        'sports': sports_with_teams,
        'favorite_ids': favorite_ids,
    })
