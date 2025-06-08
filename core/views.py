from django.shortcuts import render, get_object_or_404
from .models import Sport, Match
from collections import defaultdict

# Create your views here.
from django.shortcuts import render

def home(request):
    sports = Sport.objects.all()
    data = []

    for sport in sports:
        matches = Match.objects.filter(sport=sport).order_by('-match_date')
        tournaments = defaultdict(list)
        for match in matches:
            tournaments[match.tournament].append(match)
        data.append({
            'sport': sport,
            'tournaments': dict(tournaments)
        })

    return render(request, 'index.html', {'data': data})

def sport_list(request):
    return render(request, 'sport_list.html')

def match_detail(request, id):
    match = get_object_or_404(Match, pk=id)
    return render(request, 'match_detail.html', {'match': match})

def profile(request):
    return render(request, 'profile.html')


def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    matches = Match.objects.filter(sport=sport)
    return render(request, 'sport_matches.html', {
        'sport': sport,
        'matches': matches
    })
