from gamedata.models import Player, Game, PlayerGame, ShiftData, TeamGame

#class Shift():
	#def __init__(self, player, start_time, end_time):
		#self.player = player
		#self.start_time = start_time
		#self.end_time = end_time


def load_game_shifts(teamgame):

	shifts_dict = {}
	tg = TeamGame.objects.filter()
	for p in PlayerGame.objects.filter(team=teamgame):
		shifts_dict[p.player.last_name] = ShiftData.objects.filter(
					playergame__player__last_name__iexact = p.player.last_name)

	return shifts_dict

def get_TeamGame(game, team_initials):
	return 
