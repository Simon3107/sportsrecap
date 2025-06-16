from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Sport(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name}"

class Team(models.Model):
    name = models.CharField(max_length=100)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)

    class Meta:
        unique_together = ('name', 'sport')

    def __str__(self):
        return self.name

class Match(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    score = models.CharField(max_length=20)
    yt_url = models.URLField(blank=True, null=True)
    match_date = models.DateField()
    
    def __str__(self):
        return f"{self.team1} vs {self.team2} | {self.tournament.name} | {self.match_date.strftime('%a, %d.%m.%Y')}"

class Comment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.created_at.strftime('%Y-%m-%d')}"

class FavoriteTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'team')  # verhindert doppelte Favoriten

    def __str__(self):
        return f"{self.user.username} favorisiert {self.team.name}"
