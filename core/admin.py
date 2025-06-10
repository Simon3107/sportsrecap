from django.contrib import admin
# Register your models here.
from .models import Sport, Match, Comment, Team, Tournament

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport')
    list_filter = ('sport',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'tournament', 'match_date')
    list_filter = ('sport', 'tournament')

admin.site.register(Sport)
admin.site.register(Comment)
admin.site.register(Team)
