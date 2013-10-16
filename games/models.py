'''
GAMES - models.py
'''

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

	def get_line(self, shiftlist):
		#receives a list of ShiftGames, returns the line object they play on
		
		#quietly fail if no items in the list
		
		num_players = shiftlist.count()

		if num_players == 0:
			return None
		
		q = LineGame.objects.filter(playergames = shiftlist[0].playergame)

		for shift_index in range(1, num_players):
			q = q.filter(playergames = shiftlist[shift_index].playergame)

		q = q.filter(num_players = shiftlist.count())


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
#Scoring data for each player that participates in the corresponding TeamGame/Game.  
#Future implementation tracks goals, shots, hits, blocks, and the number of GameLines 
#they play on.
	player = models.ForeignKey(Player)
	team = models.ForeignKey(TeamGame)

	class Meta:
		ordering = ['team', 'player__last_name']
		
	def __unicode__(self):
		return "%s - %s" % (self.team.team, self.player)


class ShiftGame(models.Model):
#Shift time data for each PlayerGame
	playergame = models.ForeignKey(PlayerGame)
	active_penalty = models.BooleanField(default=False)
	start_time = models.IntegerField()
	end_time = models.IntegerField()

	class Meta:
		ordering = ['playergame__team', 'end_time']

	def __unicode__(self):
		return '(%s, %d, %d)' % (self.playergame.player.last_name, self.start_time, self.end_time)


class LineGame(models.Model):
#Line data for each TeamGame

	playergames = models.ManyToManyField(PlayerGame)
	teamgame = models.ForeignKey(TeamGame)
	linetype = models.CharField(max_length=2)

	num_shifts = models.IntegerField()
	num_players = models.IntegerField()
	ice_time = models.IntegerField()
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
			statslist = "{0:4d} {1:4d} {2:4d} {3:4d} {4:6d} {5:6d}".format(self.goals, self.shots, self.hits, self.blocks, self.ice_time, self.num_shifts)
			return "{0:50s} {1}".format(playerlist, statslist)
		else:
			return unicode("Empty (%d)" % self.pk)

class LineGameTime(models.Model):
#Shift instances for LineGame objects

	linegame = models.ForeignKey(LineGame)
	start_time = models.IntegerField()
	end_time = models.IntegerField()
	ice_time = models.IntegerField()
	active_penalty = models.BooleanField(default=False)

	def __unicode__(self):
		return unicode("%s - %d - %d" % (self.linegame, self.start_time, self.end_time))


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