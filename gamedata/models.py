from django.db import models
from django.db.models import Q
from bs4 import BeautifulSoup
from nameparser import HumanName
import requests
import re
from bisect import bisect_left
import gamedata.myfunks


# Create your models here.
class Team(models.Model):
	name = models.CharField(max_length = 100)
	initials = models.CharField(max_length = 3)

	def __unicode__(self):
		return self.name


class TeamGame(models.Model):
	team = models.ForeignKey(Team)
	
	def __unicode__(self):
		return "%s" % (self.team.name)


class Player(models.Model):
	first_name = models.CharField(max_length = 255)
	last_name = models.CharField(max_length = 255)
	number = models.IntegerField()
	position = models.CharField(max_length = 2)

	def __unicode__(self):
		return self.last_name + ", " + self.first_name


class Game(models.Model):
	game_id = models.IntegerField(primary_key = True)

	away_team = models.ForeignKey(TeamGame, related_name='away')
	home_team = models.ForeignKey(TeamGame, related_name='home')

	def __unicode__(self):
		return "%s (%s @ %s)" % (self.game_id, self.away_team.team.initials, self.home_team.team.initials)

	def roster_home(self, pos = 'a'):
		return self.__roster__(self.home_team, pos)

	def roster_away(self, pos = 'a'):
		return self.__roster__(self.away_team, pos)

	def shifts_home(self, pos = 'a'):
		return self.__shifts__(self.home_team, pos)
	
	def shifts_away(self, pos = 'a'):
		return self.__shifts__(self.away_team, pos)		





	def __roster__(self, team, pos):
		if pos == 'a' or pos == 'A':
			return PlayerGame.objects.filter(team = team)
		elif pos == 'd' or pos == 'D':
			return PlayerGame.objects.filter(team = team).filter(
											player__position='D')
		elif pos == 'f' or pos == 'F':
			return PlayerGame.objects.filter(team = team).filter(
											Q(player__position='C') | 
											Q(player__position='R') | 
											Q(player__position='L'))
		elif pos == 'c' or pos == 'C':
			return PlayerGame.objects.filter(team = team).filter(
											player__position='C')
		elif pos == 'r' or pos == 'R':
			return PlayerGame.objects.filter(team = team).filter(
											player__position='R')
		elif pos == 'l' or pos == 'L':
			return PlayerGame.objects.filter(team = team).filter(
											player__position='L')
		elif pos == 'g' or pos == 'G':
			return PlayerGame.objects.filter(team = team).filter(
											player__position='G')
		else:
			raise(ValueError("Valid arguments are 'c', 'd', 'rw', 'lw', 'f'"))

	def __shifts__(self, team, pos):
		if pos == 'a' or pos == 'A':
			q = ShiftData.objects.filter(playergame__team = team)
		elif pos == 'd' or pos == 'D':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											playergame__player__position='D')
		elif pos == 'f' or pos == 'F':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											Q(playergame__player__position='C') | 
											Q(playergame__player__position='R') | 
											Q(playergame__player__position='L'))
		elif pos == 'c' or pos == 'C':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											playergame__player__position='C')
		elif pos == 'r' or pos == 'R':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											playergame__player__position='R')
		elif pos == 'l' or pos == 'L':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											playergame__player__position='L')
		elif pos == 'g' or pos == 'G':
			q = ShiftData.objects.filter(playergame__team = team).filter(
											playergame__player__position='G')
		else:
			raise(ValueError("Valid arguments are 'c', 'd', 'rw', 'lw', 'f'"))

		return q.order_by('start_time', 'end_time')




class PlayerGame(models.Model):
	#also includes teamgame
	player = models.ForeignKey(Player)
	team = models.ForeignKey(TeamGame)
		
	def __unicode__(self):
		return "%s - %s" % (self.team.team, self.player)

	def shifts(self):
		return ShiftData.objects.filter(playergame = self)

	
class ShiftData(models.Model):
	playergame = models.ForeignKey(PlayerGame)
	start_time = models.IntegerField()
	end_time = models.IntegerField()

	def __unicode__(self):
		return '(%s, %d, %d)' % (self.playergame.player.last_name, self.start_time, self.end_time)



###---Functions for models


def add_game(gameNum):
	try: 
		Game.objects.get(game_id=gameNum)
		print "Game %s already exists in database." % gameNum
		return False
	
	except Game.DoesNotExist:

		r = requests.get('http://www.nhl.com/scores/htmlreports/20122013/RO' + gameNum + '.HTM')

		roster_soup = BeautifulSoup(r.text)

		if roster_soup.title.text == "404 Not Found":
			print "Error - no game match at this URL"
			return False

		
		#pull team name data from txt - first two instances of class teamHeading
		teams = roster_soup.find_all('td', class_ = "teamHeading")
		away_name = teams[0].text.encode('ASCII')
		home_name = teams[1].text.encode('ASCII')

		#Creates TeamGame objects home, away
		away = TeamGame.objects.create(team = Team.objects.get(name=away_name))
		home = TeamGame.objects.create(team = Team.objects.get(name=home_name))

		game = Game(game_id=gameNum, home_team=home, away_team=away)
		game.save()

		import_player_data(away, roster_soup)
		import_player_data(home, roster_soup)

		return True



def import_player_data(team, roster_soup):

	#Determines if the team is the home or away team for the game
	if len(team.home.all()):
		homeaway = "home"
		game_id = team.home.all()[0].game_id
	elif len(team.away.all()):
		homeaway = "away"
		game_id = team.away.all()[0].game_id
	else:
		print "Error - no away or home status for Team"
		return False

	#Turn game_id into a string for future reference
	game_id_str = "0" + str(game_id)

	##GET ROSTER

	#Indicates the list index of "roster" from which to begin iterating
	START_ROSTER = 3

	#Indices of player data within each player's 'roster' tags
	POSITION_INDEX = 3
	NAME_INDEX = 5
	NUMBER_INDEX = 1

	if homeaway == "home":
		number = 1
	else:
		number = 0

	#Sets 'roster' to a BeautifulSoup object which contains the data for a team's roster
	roster = roster_soup.find_all("td", text="#")[number].parent.parent

	#Iterates over the 'roster', skipping every other item (null tags)
	for i in range(START_ROSTER, len(roster), 2):

		position = roster.contents[i].contents[POSITION_INDEX].text.encode('ASCII')

		name = roster.contents[i].contents[NAME_INDEX].text.encode('ASCII')
		hname = HumanName(name)
		first_name = hname.first
		last_name = hname.last

		number = roster.contents[i].contents[NUMBER_INDEX].text.encode('ASCII')

		#Checks if player exists or if multiple players with this name.  
		#If player does not exist, add to Player database and PlayerGame database.
		#If player exists, add to PlayerGame database.
		try:
			p = Player.objects.get(first_name=first_name, last_name=last_name)
			PlayerGame.objects.create(player=p, team=team)
			#print "Added %s %s to GameData" % (p.first_name, p.last_name)
		except Player.MultipleObjectsReturned:
			#Check if multiple players in the league or if player has been traded
			print "Multiple players with this name"
			pass
		except Player.DoesNotExist:
			#Check if new player or data error
			p = Player.objects.create(first_name=first_name, last_name=last_name, position=position, number=number)
			PlayerGame.objects.create(player=p, team=team)
			print "Added - " + p.first_name + " " + p.last_name + " (" + p.position + ") " + team.team.initials 
			#print "and to GameData"
	
	###GET SHIFTS

	if homeaway == "home":
		r = requests.get('http://www.nhl.com/scores/htmlreports/20122013/TH' + game_id_str + '.HTM')
	else:
		r = requests.get('http://www.nhl.com/scores/htmlreports/20122013/TV' + game_id_str + '.HTM')

	shift_soup = BeautifulSoup(r.text)

	if shift_soup.title.text == "404 Not Found":
		print "Error - no game match at this URL"
		return False

	#Get list of players from BeautifulSoup object
	players = shift_soup.find_all('td', class_='playerHeading')
	
	for player in players:
		playerName = HumanName(player.text)

		#Strip out player's number from name
		playerName.last = re.sub("\d+", "", playerName.last).strip()
		playerObj = Player.objects.get(first_name=playerName.first, last_name=playerName.last)

		#Create new object for PlayerGame and save to database
		playerGameObj = PlayerGame.objects.get(player=playerObj, team=team)
		#playerGameObj.save()
	
		#print playerGameObj.player
		#print playerGameObj.game

		#Parse the individual player BeautifulSoup object for shift data
		shift = player.parent.next_sibling.next_sibling.next_sibling.next_sibling
		shift_list = shift.find_all("td")

		#If 6 items in shift_list object, it matches the structure of valid shift data
		while(len(shift_list) == 6):
			period = int(shift_list[1].text)
			timeOn = gamedata.myfunks.deleteAfter(shift_list[2].text, '/')
			timeOn = gamedata.myfunks.convertToSecs(timeOn, period)
			timeOff = gamedata.myfunks.deleteAfter(shift_list[3].text, '/')
			timeOff = gamedata.myfunks.convertToSecs(timeOff, period)


			ShiftData.objects.create(playergame=playerGameObj, start_time=timeOn, end_time=timeOff)
			#print playerGameObj.player.last_name
			#print playerGameObj.game.game_id
			#print timeOn

			#Get next shift for this player
			shift = shift.next_sibling.next_sibling
			shift_list = shift.find_all("td")
				
