# Create your views here.
from games.models import Game
from datamanager.models import GameProcessor

from django.http import HttpResponse


def game_request(request, game_id):

	game = Game.objects.get(pk=game_id)
	
	return HttpResponse(game.get_json(), content_type="application/json")


def game_list_request(request, *arg):
	if arg:
		json = GameProcessor.get_json(team_initials=arg[0],)
	else:
		json = GameProcessor.get_json()

	return HttpResponse(json, content_type="application/json")