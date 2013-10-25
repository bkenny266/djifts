from django.db import models
import games


# Create your models here.

class Team(models.Model):
	name = models.CharField(max_length = 100)
	initials = models.CharField(max_length = 3)

	def __unicode__(self):
		return self.name

	def get_last_games(self, num_games):
	#get aggregate statistics of lines from the last ::num_games:: games
	#returns a queryset of lines with stat counts aggregated over ::num_games:: games

		games_played = games.models.TeamGame.objects.filter(team__initials=self.initials).count()

		if num_games > games_played:
			num_games = games_played

		games_q = games.models.TeamGame.objects.filter(team__initials=self.initials).reverse()[:num_games]

		game_set = []

		for game in games_q:
			game_set.append(game.pk)

		return game_set


	def combine_game_lines(self, num_games):
	#combines the line data from the last ::num_games:: into a single queryset

		game_set = self.get_last_games(num_games)

		total_line_set = games.models.LineGame.objects.none()

		for game in game_set:
			line_set = game.linegame_set.all()
			total_line_set = total_line_set | line_set

		
		return total_line_set

	def match_lines(self, line, num_games):
	#takes a queryset of a LineGame object called ::line::, and finds all instances
	#of this line combination over the last ::num_games::

		line_query = self.combine_game_lines(num_games)

		for player in line.playergames.all():
			line_query = line_query.filter(playergames = player)

		return line_query



		