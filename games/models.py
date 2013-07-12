'''
GAMES - models.py
'''

import requests

from django.db import models

from players.models import Player
from teams.models import Team


class TeamGame(models.Model):
#TeamGame is a data representation of each team that players in each game.  
#Every game will have a 'home team' and 'away team', which can be accessed through the 
#corresponding Game's related fields of 'team_home' (home) and 'team_away' (away).

#TeamGame contains functions for retrieving team-specific data from individual 
#games such as roster, shifts, and lines.

	team = models.ForeignKey(Team)
	
	def __unicode__(self):
		return "%s" % (self.team.name)

	def is_home(self):
	#return True if TeamGame object is 'home team'
		if len(self.home.all()):
			return True
		else:
			return False

	def is_away(self):
	#return True if TeamGame object is 'away team'
		if len(self.away.all()):
			return True
		else:
			return False

	def get_game_object(self):
	#returns the Game object that this TeamGame is related to
		if self.is_home():
			return self.home.get()
		elif self.is_away():
			return self.away.get()
		else:
			raise Error("TeamGame object (%s) is not linked to a game.")

	def get_roster(self, pos='a'):
		#returns QuerySet of ALL PLAYERS involed in this TeamGame.  accepts an optional player position argument.
		#default 'a' (all) argument excludes goalie shift data
		if pos == 'a' or pos == 'A':
			return PlayerGame.objects.filter(team = self)
		elif pos == 'd' or pos == 'D':
			return PlayerGame.objects.filter(team = self).filter(
											player__position='D')
		elif pos == 'f' or pos == 'F':
			return PlayerGame.objects.filter(team = self).filter(
											Q(player__position='C') | 
											Q(player__position='R') | 
											Q(player__position='L'))
		elif pos == 'c' or pos == 'C':
			return PlayerGame.objects.filter(team = self).filter(
											player__position='C')
		elif pos == 'r' or pos == 'R':
			return PlayerGame.objects.filter(team = self).filter(
											player__position='R')
		elif pos == 'l' or pos == 'L':
			return PlayerGame.objects.filter(team = self).filter(
											player__position='L')
		elif pos == 'g' or pos == 'G':
			return PlayerGame.objects.filter(team = self).filter(
											player__position='G')
		else:
			raise(ValueError("Valid arguments are 'c', 'd', 'r', 'l', 'f'"))

	def get_shifts(self, pos='a'):
		#returns QuerySet of ALL SHIFTS involed in this TeamGame.  accepts an optional player position argument.
		#'a' (all) argument excludes goalie shift data
		if pos == 'a' or pos == 'A':
			q = ShiftGame.objects.filter(playergame__team = self).exclude(
											playergame__player__position='G')
		elif pos == 'd' or pos == 'D':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											playergame__player__position='D')
		elif pos == 'f' or pos == 'F':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											Q(playergame__player__position='C') | 
											Q(playergame__player__position='R') | 
											Q(playergame__player__position='L'))
		elif pos == 'c' or pos == 'C':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											playergame__player__position='C')
		elif pos == 'r' or pos == 'R':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											playergame__player__position='R')
		elif pos == 'l' or pos == 'L':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											playergame__player__position='L')
		elif pos == 'g' or pos == 'G':
			q = ShiftGame.objects.filter(playergame__team = self).filter(
											playergame__player__position='G')
		else:
			raise(ValueError("Valid arguments are 'c', 'd', 'r', 'l', 'f'"))

		return q.order_by('start_time', 'end_time')

	def get_events(self, event_type='all'):
		#returns query set of all events.  
		#accepts an optional event_type argument 'all', 'goals', 'shots', 'hits', 'blocks'

		event_type = event_type.lower()

		q = TeamGameEvent.objects.filter(playergame__team = self)

		if event_type == 'goals':
			q = q.filter(event_type = "GOAL")
		elif event_type == 'shots':
			q = q.filter(event_type = "SHOT")
		elif event_type == 'hits':
			q = q.filter(event_type = "HIT")
		elif event_type == 'blocks':
			q = q.filter(event_type = "BLOCK")
		elif event_type == 'all':
			pass
		else:
			raise(ValueError("Valid arguments are 'all', 'goals', shots', 'hits', and 'blocks'"))

		return q.order_by('event_time')

	def get_line_by_time(self, time):
		#receives argument of game time (in seconds) and returns the line that was on the ice

		q = TeamGame.objects.filter(linegame__teamgame = self).filter(
										linegame__start_time__lte = time).filter(
										linegame__end_time__gt = time)

		
		#raise an error if more than one time value matches
		if q.len() > 1:
			raise (RuntimeError("Multiple lines on the ice at this time."))
		elif q.len() == 0:
			raise (RuntimeError("There are no lines at this time"))

		#return the first element of the query (ther will only be one)
		return q[0]



class Game(models.Model):
	game_id = models.IntegerField(primary_key = True)

	team_home = models.ForeignKey(TeamGame, related_name='home')
	team_away = models.ForeignKey(TeamGame, related_name='away')

	def __unicode__(self):
		return "%s (%s @ %s)" % (self.game_id, self.team_away.team.initials, self.team_home.team.initials)

	def roster_home(self, pos = 'a'):
		return self.team_home.get_roster(pos)

	def roster_away(self, pos = 'a'):
		return self.team_away.get_roster(pos)

	def shifts_home(self, pos = 'a'):
		return self.team_home.get_shifts(pos)
	
	def shifts_away(self, pos = 'a'):
		return self.team_away.get_shifts(pos)



class PlayerGame(models.Model):
	#also includes teamgame (many to many)
	player = models.ForeignKey(Player)
	team = models.ForeignKey(TeamGame)
		
	def __unicode__(self):
		return "%s - %s" % (self.team.team, self.player)

	def shifts(self):
		return ShiftGame.objects.filter(playergame = self)


class ShiftGame(models.Model):
	playergame = models.ForeignKey(PlayerGame)
	start_time = models.IntegerField()
	end_time = models.IntegerField()

	def __unicode__(self):
		return '(%s, %d, %d)' % (self.playergame.player.last_name, self.start_time, self.end_time)


class LineGame(models.Model):
	playergames = models.ManyToManyField(PlayerGame)
	teamgame = models.ForeignKey(TeamGame)

	start_time = models.IntegerField()
	end_time = models.IntegerField()
	shift_length = models.IntegerField()

	def __unicode__(self):
		if self.playergames.count() > 0:
			playerlist = ''
			for player in self.playergames.all():
				playerlist = playerlist + '%s\n' % player
			return playerlist
		else:
			return unicode("Empty (%d)" % self.pk)


class TeamGameEvent(models.Model):
	playergame = models.ForeignKey(PlayerGame)
	event_time = models.IntegerField()
	event_type = models.CharField(max_length=25)

	def __unicode__(self):
		text = "%s by %s (%d)" % (self.event_type, self.playergame, self.event_time)
		return unicode(text)