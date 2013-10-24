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

	results_all = teamgame.get_lines().exclude(line_type="O")
	results_f = results_all.filter(line_type="F")
	results_d = results_all.filter(line_type="D")
	results_pp = results_all.filter(line_type="PP")

	return render(request, "game_view.html", {"results_all" : results_all, "results_f" : results_f, "results_d" : results_d, "results_pp" : results_pp, "header" : header})
		

def test_bootstrap(request):

	return render(request, "testbootstrap.html")