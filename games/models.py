# -*- coding: utf-8 -*-
'''
GAMES - models.py
'''

import json
from django.db import models

from players.models import Player
from teams.models import Team


class TeamGame(models.Model):
#TeamGame is a data representation of each team that plays in each game.  
#Every game will have a 'home team' and 'away team', which can be accessed through the 
#corresponding Game's related fields of 'team_home' (home) and 'team_away' (away).

#TeamGame contains functions for retrieving team-specific data from individual 
#games such as roster, shifts, and lines.

	team = models.ForeignKey(Team)
	#homeaway = lambda x: return u"home" if t.is_home() else return u"away"


	def __unicode__(self):
		return u"%s" % (self.team.name)

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

	def get_json(self):
		'''
		returns json representation of TeamGame object'''
		data = []
		for lg in self.linegame_set.all():
			data.append(lg.get_json())

		return data


	def get_game_object(self):
	#returns the Game object that this TeamGame is related to
		if self.is_home():
			return self.home.get()
		elif self.is_away():
			return self.away.get()
		else:
			raise Error("TeamGame object (%s) is not linked to a game.")

	def get_other_team(self):
		'''returns the TeamGame object of the other team from this game'''
		if self.is_home():
			return self.home.get().team_away
		if self.is_away():
			return self.away.get().team_home


	def get_lines_json(self, event, position):
		'''
		returns a json object of this TeamGame's line data'''

		lgset = self.get_lines()


	def get_roster(self, pos='A'):
		#returns QuerySet of ALL PLAYERS involed in this TeamGame.  accepts an optional player position argument.
		#default 'a' (all) argument excludes goalie shift data

		q = self.playergame_set.all()

		try:
			return {'A' : q,
					'D' : q.filter(player__position='D'),
					'F' : q.filter(models.Q(player__position='C')| 
								   models.Q(player__position='R')| 
								   models.Q(player__position='L')),
					'C' : q.filter(player__position='C'),
					'R' : q.filter(player__position='R'),
					'L' : q.filter(player__position='L'),
					'G' : q.filter(player__position='G')
					}[pos.upper()]
		except KeyError:
			print "Valid arguments are 'c', 'd', 'r', 'l', 'f', 'g'"

	def get_shifts(self, pos='a'):
		#returns QuerySet of ALL SHIFTS involed in this TeamGame.  accepts an optional player position argument.
		#'a' (all) argument excludes goalie shift data

		q = ShiftGame.objects.filter(playergame__team = self)

		try:
			return {'A' : q.exclude(playergame__player__position='G'),
					'D' : q.filter(playergame__player__position='D'),
					'F' : q.filter(models.Q(playergame__player__position='C') | 
									models.Q(playergame__player__position='R') | 
									models.Q(playergame__player__position='L')),
					'C' : q.filter(playergame__player__position='C'),
					'R' : q.filter(playergame__player__position='R'),
					'L' : q.filter(playergame__player__position='L')
					}[pos.upper()].order_by('start_time', 'end_time')
		except KeyError:
			print "Valid arguments are 'c', 'd', 'r', 'l', 'f'"

	def get_events(self, event_type='all'):
		#returns query set of all events.  
		#accepts an optional event_type argument 'all', 'goals', 'shots', 'hits', 'blocks'

		event_type = event_type.lower()

		q = TeamGameEvent.objects.filter(playergame__team = self)

		try:
			return {'goals' : q.filter(event_type = "GOAL"),
					'shots' : q.filter(event_type = "SHOT"),
					'hits' : q.filter(event_type = "HIT"),
					'blocks' : q.filter(event_type = "BLOCK"),
					'all' : q }[event_type.lower()].order_by('event_time')

		except KeyError:
			print "Valid arguments are 'all', 'goals', shots', 'hits', and 'blocks'"

	def get_line(self, shiftlist, line_type):
		#receives a list of ShiftGames, returns the line object they play on
		
		#quietly fail if no items in the list
		
		num_players = shiftlist.count()

		if num_players == 0:
			return None
		
		q = LineGame.objects.filter(playergames = shiftlist[0].playergame)

		for shift_index in range(1, num_players):
			q = q.filter(playergames = shiftlist[shift_index].playergame)

		q = q.filter(line__num_players = shiftlist.count())

		q = q.filter(line__line_type=line_type)

		if q.count() == 0:
			return None
		
		return q[0]

	def get_lines(self, event_type='all'):
	#returns a queryset of lines for this game
	#event_type accepts 'all', 'goals', 'hits', 'shots', 'blocks' as values

		goals = 0
		shots = 0
		hits = 0
		blocks = 0

		if (event_type == 'all'):
			sort_type = '-ice_time'
		elif (event_type == 'goals'):
			goals = 1
			sort_type = '-goals'
		elif (event_type == 'shots'):
			shots = 1
			sort_type = '-shots'
		elif (event_type == 'hits'):
			hits = 1
			sort_type = '-hits'
		elif (event_type == 'blocks'):
			blocks = 1
			sort_type = '-blocks'
		elif (event_type == 'shifts'):
			sort_type = '-num_shifts'
		else:
			raise(AttributeError("Valid event_type attributes are 'all', 'goals', 'shots', 'hits', 'blocks', 'shifts'"))

		return self.linegame_set.filter(goals__gte=goals, shots__gte=shots, hits__gte=hits, blocks__gte=blocks).order_by(sort_type, '-ice_time')

	def line_at_time(self, time, position="A"):

		q = LineGameTime.objects.filter(linegame__teamgame=self, start_time__lte=time, end_time__gt=time)

		if position != 'A':
			q.filter(linegame__line__line_type=position)

		return q


class Game(models.Model):
#Game model represents each game played.
#team_home and team_away are used to access
#the TeamGame model and drill deeper into the game data

	#game_id is the primary key and based on the game number from NHL website.  
	#see datamanager.admin comments for info on how this value is assigned
	game_id = models.IntegerField(primary_key = True)
	date = models.DateField()

	team_home = models.ForeignKey(TeamGame, related_name='home')
	team_away = models.ForeignKey(TeamGame, related_name='away')

	class Meta:
	 	ordering = ['date']

	def __unicode__(self):
		return u"%s (%s @ %s)" % (self.game_id, self.team_away.team.initials, self.team_home.team.initials)

	def get_json(self):
		teams = [self.team_home, self.team_away]
		game_dict = {}
		for team in teams:
			team_line_data = team.get_json()
			if team.is_home():
				status = "home_team"
			else:
				status = "away_team"
			game_dict[status] = team_line_data
		
		game_dict['date'] = self.get_date_str()
		game_dict['id'] = self.game_id

		return json.dumps(game_dict)

	def get_date_str(self):
		return self.date.strftime('%m/%d/%Y')

	def roster_home(self, pos = 'a'):
		return self.team_home.get_roster(pos)

	def roster_away(self, pos = 'a'):
		return self.team_away.get_roster(pos)

	def shifts_home(self, pos = 'a'):
		return self.team_home.get_shifts(pos)
	
	def shifts_away(self, pos = 'a'):
		return self.team_away.get_shifts(pos)



class PlayerGame(models.Model):
#Scoring data for each player that participates in the corresponding TeamGame/Game.  
#Future implementation tracks goals, shots, hits, blocks, and the number of GameLines 
#they play on.
	player = models.ForeignKey(Player)
	team = models.ForeignKey(TeamGame)

	class Meta:
		ordering = ['team', 'player__last_name']
		
	def __unicode__(self):
		return u"%s - %s" % (self.team.team, self.player)


class ShiftGame(models.Model):
#Shift time data for each PlayerGame
	playergame = models.ForeignKey(PlayerGame)
	active_penalty = models.BooleanField(default=False)
	start_time = models.IntegerField()
	end_time = models.IntegerField()

	class Meta:
		ordering = ['playergame__team', 'end_time']

	def __unicode__(self):
		return u'(%s, %d, %d)' % (self.playergame.player.last_name, self.start_time, self.end_time)

class Line(models.Model):
	players = models.ManyToManyField(Player)
	num_players = models.IntegerField()
	line_type = models.CharField(max_length=2)
	team = models.ForeignKey(Team)

	def __unicode__(self):
		playerlist = ''
		x = 0
		for player in self.players.all():
			playerlist = playerlist + '%s - ' % player.last_name
			x += 1
			
		playerlist = playerlist + self.line_type
		return playerlist

class LineGame(models.Model):
#Line data for each TeamGame

	line = models.ForeignKey(Line, related_name='linegame')
	playergames = models.ManyToManyField(PlayerGame)
	teamgame = models.ForeignKey(TeamGame)

	num_shifts = models.IntegerField()
	ice_time = models.IntegerField()
	ice_time_str = models.CharField(max_length=6, blank=True)
	goals = models.IntegerField()
	shots = models.IntegerField()
	blocks = models.IntegerField()
	hits = models.IntegerField()


	def __unicode__(self):
		count = self.playergames.count()
		if count > 0:
			x = 0
			playerlist = ''
			for player in self.playergames.all():
				playerlist = playerlist + '%s' % player.player.last_name
				if x < count-1:
					playerlist = playerlist + "-"
				x += 1
			#pulled statlist at least temporarily
			#statslist = "{0:4d} {1:4d} {2:4d} {3:4d} {4:6d} {5:6d} {6:3s}".format(self.goals, self.shots, self.hits, self.blocks, self.ice_time, self.num_shifts, self.line.line_type)
			return "{0}".format(playerlist)
		else:
			return unicode("Empty (%d)" % self.pk)
	
	def get_json(self):
		'''
		dumps json LineGame representation'''
		return json.dumps({'pk': self.pk, 'players': self.__unicode__(), 
			"type" : self.line.line_type, "num_shifts" : self.num_shifts, "ice_time_num": self.ice_time, 
			"ice_time_str": self.ice_time_str, "goals": self.goals,
			"shots": self.shots, "blocks": self.blocks, "hits": self.hits})
		


	def set_ice_time_str(self):
		'''
		Converts object's integer of seconds into a 
		MM:SS string and saves it in data'''
		sec_in = self.ice_time
		mins = sec_in / 60
		secs = sec_in % 60
		if mins < 10:
			mins = "0" + str(mins)
		if secs < 10:
			secs = "0" + str(secs)
		self.ice_time_str = str(mins) + ":" + str(secs)
		self.save()

class LineGameTime(models.Model):
#Shift instances for LineGame objects

	linegame = models.ForeignKey(LineGame, blank=True)
	start_time = models.IntegerField()
	end_time = models.IntegerField()
	ice_time = models.IntegerField()
	active_penalty = models.BooleanField(default=False)

	def __unicode__(self):
		return unicode("%s - %d - %d" % (self.linegame, self.start_time, self.end_time))

	def get_shiftgames(self, type_override="N"):
		'''queries the database to return the shift games for this LineGameTime
			Can override the line type with ::type_override:: argument'''

		if type_override=="N":
			line_type = self.linegame.line.line_type
		else:
			line_type = type_override

		return {'O' : ShiftGame.objects.filter(playergame__team=self.linegame.teamgame, start_time__lte=self.start_time, end_time__gt=self.start_time),
			'F' : ShiftGame.objects.filter(playergame__team=self.linegame.teamgame, start_time__lte=self.start_time, end_time__gt=self.start_time).filter(models.Q(playergame__player__position='C')| 
								   models.Q(playergame__player__position='R')| 
								   models.Q(playergame__player__position='L')),
			'D' : ShiftGame.objects.filter(playergame__team=self.linegame.teamgame, start_time__lte=self.start_time, end_time__gt=self.start_time, playergame__player__position='D')
			}[line_type]


class TeamGameEvent(models.Model):
#Statistical events from a TeamGame that are pulled from the game's Play-by-Play data
#Includes all game data from goals, shots, hits, blocks.

	linegame = models.ForeignKey(LineGame)
	playergame = models.ForeignKey(PlayerGame)
	event_time = models.IntegerField()
	event_type = models.CharField(max_length=25)

	def __unicode__(self):
		text = "%s by %s (%d)" % (self.event_type, self.playergame, self.event_time)
		return unicode(text)

def print_lines(q):
	#prints all lines from a LineGame queryset
	#attribute q = a LineGame queryset

	print "{0:<50s} {1:>4s} {2:>4s} {3:>4s} {4:>4s} {5:>6s} {6:>6s}".format("LINE", "G", "S", "H", "B", "TIME", "SHIFTS")
	for line in q:
		print line


def write_to(json):
	f = open('testjson.json', 'w')
	f.write(json)
	f.close()
