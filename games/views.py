# Create your views here.

from games.models import Game, LineGame

from django.http import HttpResponse
from django.shortcuts import render


def game_view(request, game_id, team):

	game_id = int(game_id)
	game = Game.objects.get(pk=game_id)

	if team == "home":
		teamgame = game.team_home
	if team == "away":
		teamgame = game.team_away

	header = "%s at %s - %s" % (game.team_away, game.team_home, game.date)

	results = teamgame.get_lines()

	return render(request, "game_view.html", {"results" : results, "header" : header})
		

def test_bootstrap(request):

	return render(request, "testbootstrap.html")