# Create your views here.

from games.models import Game, LineGame

from django.http import HttpResponse
from django.shortcuts import render


def test_view(request, game_id, team):

	game_id = int(game_id)
	game = Game.objects.get(pk=game_id)

	if team == "home":
		teamgame = game.team_home
	if team == "away":
		teamgame = game.team_away

	results = teamgame.get_lines()

	return render(request, "game_view.html", {"results" : results})
		