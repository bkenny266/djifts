# -*- coding: utf-8 -*-
#DATA MANAGER APP - utility.py
#functions used by admin.py for creating data.

import requests
import re
from datetime import datetime, date
import string
import ipdb
from django.db.models import Q


from bs4 import BeautifulSoup
from nameparser import HumanName

from games.models import Game, TeamGame, PlayerGame, ShiftGame, TeamGameEvent, LineGame, LineGameTime, Line
from players.models import Player
from teams.models import Team

from .myfunks import convertToSecs, deleteAfter
from .eventprocessor import EventProcessor


def get_soup(game_num, link_type):
	'''
	returns a beautiful soup object of different types of game data
	link_type is a string to specify data type - 'roster', 'shifts_home', 'shifts_away', or 'play_by_play'
	'''

	#extract season number from game_id and use it for the data source URL
	season_num = game_num / 1000000
	season_string = "20%d20%d" % (season_num, season_num + 1)

	#extract game_string from game_id and use it for the data source URL
	game_string = "%d" % game_num
	game_string = game_string[2:]

	if link_type == 'roster':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/RO' + game_string + '.HTM')

	elif link_type == 'shifts_home':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/TH' + game_string + '.HTM')

	elif link_type == 'shifts_away':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/TV' + game_string + '.HTM')

	elif link_type == 'play_by_play':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/PL' + game_string + '.HTM')
	elif link_type =='front_page':
		r = requests.get('http://www.nhl.com/ice/gamestats.htm?fetchKey=20133ALLSATAll&sort=gameDate&viewName=teamRTSSreports')

	else:
		raise(ValueError("Valid link_type arguments are 'front_page', 'roster', 'play_by_play', 'shifts_home', and 'shifts_away'"))


	soup = BeautifulSoup(r.text)

	if soup.title.text == "404 Not Found":
		raise(ValueError("Data could not be found at this address for game %s in season %s" % (game_string, season_string)))

	return soup


def create_game(game_num, roster_soup):

	#pull team name data from txt - first two instances of class teamHeading
	teams = roster_soup.find_all('td', class_ = "teamHeading")
	away_name = teams[0].text.encode('utf-8')
	home_name = teams[1].text.encode('utf-8')

	#Creates TeamGame objects home, away
	away = TeamGame.objects.create(team = Team.objects.get(name=away_name))
	home = TeamGame.objects.create(team = Team.objects.get(name=home_name))


	game = Game(game_id=game_num, team_home=home, team_away=away, date=import_date(roster_soup))	
	game.save()

	return game



def import_player_data(team, roster_soup):

	#Determines if the team is the home or away team for the game
	if team.is_home():
		homeaway = "home"
		game_id = team.home.all()[0].game_id
	elif team.is_away():
		homeaway = "away"
		game_id = team.away.all()[0].game_id
	else:
		raise(Exception("TeamGame object (%s) has no home or away status") % team)

	##GET ROSTER
	

	#Indicates the list index of "roster" from which to begin iterating
	START_ROSTER = 3

	#Indices of player data within each player's 'roster' tags
	POSITION_INDEX = 3
	NAME_INDEX = 5
	NUMBER_INDEX = 1

	#number is a value to determine which index of the BeautifulSoup object to extract data from
	if homeaway == "home":
		number = 1
	else:
		number = 0

	#Sets 'roster' to a BeautifulSoup object which contains the data for a team's roster
	roster = roster_soup.find_all("td", text="#")[number].parent.parent

	#Iterates over the 'roster', skipping every other item (null tags)
	for i in range(START_ROSTER, len(roster), 2):

		position = roster.contents[i].contents[POSITION_INDEX].text.encode('utf-8')

		name = roster.contents[i].contents[NAME_INDEX].text.encode('utf-8')
		hname = HumanName(name)
		first_name = hname.first
		last_name = hname.last

		number = roster.contents[i].contents[NUMBER_INDEX].text.encode('utf-8')

		#Checks if player exists or if multiple players with this name.  
		#If player does not exist, add to Player database and PlayerGame database.
		#If player exists, add to PlayerGame database.
		try:
			p = Player.objects.get(last_name=last_name, team=team.team, number=number, position=position)
			PlayerGame.objects.create(player=p, team=team)
		except Player.MultipleObjectsReturned:
			#Check if multiple players in the league or if player has been traded
			print "Multiple players returned"
			pass
		except Player.DoesNotExist:
			#Check if new player or data error
			p = Player.objects.create(first_name=first_name, last_name=last_name, position=position, number=number, team=team.team)
			PlayerGame.objects.create(player=p, team=team)
			#print "Added - " + p.first_name + " " + p.last_name + " (" + p.position + ") " + team.team.initials 
	
	
	###GET SHIFTS

	if homeaway == "home":
		shift_soup = get_soup(game_id, 'shifts_home')
	else:
		shift_soup = get_soup(game_id, 'shifts_away')

	#Get list of players from BeautifulSoup object
	players = shift_soup.find_all('td', class_='playerHeading')
	
	for player in players:
		playerName = HumanName(player.text)

		#Strip out player's number from name
		split_string = string.split(playerName.last, " ", 1)
		number = split_string[0]
		playerName.last = split_string[1]
		playerObj = Player.objects.get(last_name=playerName.last, team=team.team, number=number)

		#Create new object for PlayerGame and save to database
		playerGameObj = PlayerGame.objects.get(player=playerObj, team=team)

		#Parse the individual player BeautifulSoup object for shift data
		shift = player.parent.next_sibling.next_sibling.next_sibling.next_sibling
		shift_list = shift.find_all("td")

		#If 6 items in shift_list object, it matches the structure of valid shift data
		while(len(shift_list) == 6):
			period = shift_list[1].text
			if period == "OT":
				period = 4
			else:
				period = int(period)
			timeOn = deleteAfter(shift_list[2].text, '/')
			timeOn = convertToSecs(timeOn, period)
			timeOff = deleteAfter(shift_list[3].text, '/')
			timeOff = convertToSecs(timeOff, period)


			ShiftGame.objects.create(playergame=playerGameObj, start_time=timeOn, end_time=timeOff)

			#Get next shift for this player
			shift = shift.next_sibling.next_sibling
			shift_list = shift.find_all("td")

	#don't need to include goalies in line combinations
	ShiftGame.objects.filter(playergame__player__position='G').delete()


def make_lines(teamgame):

	def is_active_penalty(line):
		for shift in line:
			if not shift.active_penalty:
				return False

		return True

	###############################################


	prev_end = 0
	prev_line = None
	game_end = ShiftGame.objects.filter(playergame__team=teamgame).reverse()[0].end_time
		
	#Loop until end of the game is the lowest time of a line
	while(prev_end < game_end):
		
		exception_case = False
		current_line = ShiftGame.objects.filter(playergame__team=teamgame, start_time__lte=prev_end, end_time__gt=prev_end)

		#if a line comes out with more players than the previous line, some work needs to be done to figure out
		#what time the extra player came on the ice.
		if (prev_line and current_line.count() > prev_line.count()):
			#check if the current group all started at the same time.  no need to proceed if so.
			if not is_new_group(current_line):
				exception_case = True
				#ipdb.set_trace()

				prev_end = compare_groups(prev_line, current_line, prev_end)

				prev_line_set = LineGameTime.objects.filter(
					linegame__teamgame=teamgame, start_time__lte=prev_end, end_time__gt=prev_end)
				
				for prev_line_obj in prev_line_set:
					prev_line_obj.end_time = prev_end
					prev_line_obj.save()

				current_line = ShiftGame.objects.filter(playergame__team=teamgame, start_time__lte=prev_end, end_time__gt=prev_end)
				#ipdb.set_trace()

		lowest_time = get_lowest(current_line)

		if lowest_time == 99999:
			ipdb.set_trace()

		shift_start = prev_end
		shift_end = lowest_time


		if is_active_penalty(current_line):
			import_line(current_line, teamgame, shift_start, shift_end)
		else:
			import_line(current_line, teamgame, shift_start, shift_end, 'F')
			import_line(current_line, teamgame, shift_start, shift_end, 'D')

		#if exception_case:
		#	ipdb.set_trace()

		#get offensive players
		prev_end = lowest_time
		prev_line = current_line

		#ipdb.set_trace()


def import_line(shift_set, teamgame, shift_start, shift_end, line_type='O'):

	try:
		filtered_shift_set = {'D' : shift_set.filter(playergame__player__position='D'),
						'F' : shift_set.filter(Q(playergame__player__position='C') | 
								Q(playergame__player__position='R') | 
								Q(playergame__player__position='L')), 
						'O' : shift_set, 
						'PP' : shift_set
		}[line_type.upper()]
	except KeyError:
		print "Invalid paramater in line_type.  Accepts 'F','D', 'O', 'PP'"

	shift_length = shift_end - shift_start

	linegame_object = teamgame.get_line(filtered_shift_set, line_type)
	#ipdb.set_trace()

	if linegame_object:

		linegame_object.ice_time += shift_length
		linegame_object.num_shifts += 1
		linegame_object.save()


	else:
		#check if this Line exists in database, and if not, create it
		line = Line.objects.filter(team=teamgame.team, line_type=line_type, num_players=len(filtered_shift_set))
		for shiftgame in filtered_shift_set:
			line = line.filter(players=shiftgame.playergame.player)

		if line.count() == 0:
			line = Line(num_players=len(filtered_shift_set), line_type=line_type, team=teamgame.team)
			line.save()
			for shiftgame in filtered_shift_set:
				line.players.add(shiftgame.playergame.player)

		elif line.count() == 1:
			line = line[0]
		else:
			raise(ValueError("More than one database match on Line"))


		linegame_object = LineGame.objects.create(teamgame = teamgame, 
			ice_time = shift_length,
			num_shifts = 1,
			goals = 0,
			hits = 0,
			blocks = 0,
			shots = 0,
			line = line)

		for shiftgame in filtered_shift_set:
			linegame_object.playergames.add(shiftgame.playergame)




	lg = LineGameTime(linegame = linegame_object, start_time=shift_start, end_time=shift_end, ice_time=shift_length)

	if line_type == 'O':
		lg.active_penalty = True
		
	lg.save()



def check_penalty_lines(game):

	TEAMS = [game.team_home, game.team_away]
	#list of lines to add and delete after the processing is complete
	add_list = []
	delete_list = []

	for tindex, team in enumerate(TEAMS):
		lgt_list = LineGameTime.objects.filter(linegame__teamgame=team, active_penalty=True)
		for lgt in lgt_list:
			#get the number of players on the current line and the other team's line that is on the ice when this line arrives
			this_count = lgt.linegame.playergames.count()
			other_lgt = LineGameTime.objects.get(linegame__teamgame=team.get_other_team(), start_time__lte=lgt.start_time, end_time__gt=lgt.start_time)
			other_count = other_lgt.linegame.playergames.count()


			#if the lines both have 5 players, recalculate both as normal lines (F+D), delete original lines
			#can do this immediately so we don't need to rerun process on away team loop iteration
			if this_count == 5 and other_count == 5:
				for thistype in ['F', 'D']:
					add_list.append((lgt.get_shiftgames(thistype), lgt.linegame.teamgame, lgt.start_time, lgt.end_time, thistype))

				delete_list.append(lgt)

			if this_count == 5 and other_count != 5:
				add_list.append((lgt.get_shiftgames(), team, lgt.start_time, lgt.end_time, 'PP'))
				delete_list.append(lgt)
				#ipdb.set_trace()



	#bulk delete from delete_list
	for item in delete_list:
		delete_line_game_time(item)

	#bulk add from add_list
	for item in add_list:
		import_line(*item)


def delete_line_game_time(lgt):
	'''cleanly removes a LineGameTime object from the database'''
	
	lg = lgt.linegame

	if lg.linegametime_set.count() == 1:
		#if this is the only LineGameTime in this set, delete the parent LineGame
		l = lg.line
		if l.linegame.count() == 1:
			l.delete()
		else:
			lg.delete()
	else:
		lg.num_shifts = lg.num_shifts - 1
		lg.ice_time = lg.ice_time - lgt.ice_time
		lgt.delete()


def is_new_group(shifts):
	#iterates through a ShiftGame query, and returns True if all players started shift at the same time
	start_time = shifts.all()[0].start_time
	for player in shifts.all()[1:]:
		if player.start_time != start_time:
			return False
	
	return True

def get_lowest(shifts):
	#iterates through a ShiftGame query, returns the lowest end_time attribute value

	lowest_end = 99999
	for shift in shifts:
		if shift.end_time < lowest_end:
			lowest_end = shift.end_time

	return lowest_end


def compare_groups(prev_line, current_line, exclude_time):
	#compares two ShiftGame queries and returns the start time for
	# the first shift that exists in current_line but not prev_line
	# AND doesn't have a start time of ::exclude_time::
	#Used for detecting special case players that come on the ice 
	# without replacing another player

	q = current_line.exclude(start_time__gte = exclude_time)
	for this_player in prev_line:
		q = q.exclude(playergame=this_player.playergame)

	if q.count() == 0:
		return exclude_time

	return q[0].start_time




def import_events(game, events):
#Pull game event data from an EventProcessor object and add to the database in the Games model.

	def increment_event(teamgame, event):
		#ipdb.set_trace()
		#when querying the line, select the time at event_time-1 to make sure it takes the end of the shift rather than the beginning
		try:
			lgt = LineGameTime.objects.get(linegame__playergames__player__number=event.event_player, linegame__teamgame=teamgame, start_time__lte=event.event_time_in_seconds-1, end_time__gt=event.event_time_in_seconds-1)
		except:
			try:
				lgt = LineGameTime.objects.get(linegame__playergames__player__number=event.event_player, linegame__teamgame=teamgame, start_time__lte=event.event_time_in_seconds, end_time__gt=event.event_time_in_seconds)
			except:
				print "%s %s not found at %s (pd %s) -  %s" % (event.event_team_initials, event.event_player, event.event_time, event.event_period, event.event_type.upper())
				ipdb.set_trace()
				return
		line = lgt.linegame


		#print event.event_type
		#print event.event_time_in_seconds
		if event.event_type == 'SHOT':
			line.shots += 1
		elif event.event_type == 'HIT':
			line.hits += 1
		elif event.event_type == 'BLOCK':
			line.blocks += 1
		elif event.event_type == 'GOAL':
			line.goals += 1
			line.shots += 1
		else:
			raise(ValueError, "Event type not valid")

		player = PlayerGame.objects.get(team=teamgame, player__number=event.event_player)
		line.save()
		TeamGameEvent.objects.create(playergame=player, event_time=event.event_time_in_seconds, event_type=event.event_type, linegame=line)



	#get objects and initials for home and away teams
	home_team_initials = game.team_home.team.initials
	away_team_initials = game.team_away.team.initials

	for event in events.flatten():
		if event.event_team_initials == home_team_initials:
			team = game.team_home
		elif event.event_team_initials == away_team_initials:
			team = game.team_away
		else:
			raise(ValueError("Event team initials (%s) do not match data" % event.event_team_initials))

		increment_event(team, event)


def import_date(soup):
	#Pull a date from the roster file.  ROSTER FILE ONLY

	days = ["^Sunday,", "^Monday,", "^Tuesday,", "^Wednesday,", "^Thursday,", "^Friday,", "^Saturday,"]
	date_text = None

	for day in days:
		search_str = re.compile(day)
		date_soup = soup.find('td', text=search_str)

		if date_soup:
			break


	if not date_soup:
		raise(Exception, "No date found in soup file")

	date_text = date_soup.text
	date_text = date_text[date_text.index(',')+1:].strip()

	temp_date = datetime.strptime(date_text, "%B %d, %Y")
	return date(temp_date.year, temp_date.month, temp_date.day)


def consolidate_penalties(penalty_list):
	consolidated = []
	prev_end_time = -1
	
	for index in range(0, len(penalty_list)):
		start_time = penalty_list[index].event_time_in_seconds
		end_time = penalty_list[index].event_end_time_in_seconds

		if index+1 < len(penalty_list) and start_time > prev_end_time:
			for subindex in range(index+1, len(penalty_list)):
				if penalty_list[subindex].event_time_in_seconds <= end_time:
					if penalty_list[subindex].event_end_time_in_seconds > end_time:
						end_time = penalty_list[subindex].event_end_time_in_seconds
						if subindex+1 == len(penalty_list):
							consolidated.append((start_time, end_time))
				else:
					consolidated.append((start_time, end_time))
					prev_end_time = end_time
					break
		elif index+1 == len(penalty_list):
			consolidated.append((start_time, end_time))
		
	return consolidated


def process_penalties(game, penalty_list):

	penalties = consolidate_penalties(penalty_list)

	TEAMS = [game.team_home, game.team_away]

	for penalty in penalties:
		for team in TEAMS:
			for p in penalty:
				sshifts = ShiftGame.objects.filter(playergame__team=team, start_time__lt=p, end_time__gt=p)
				for shift in sshifts:
					split_shift(shift, p)

			pshifts = ShiftGame.objects.filter(playergame__team=team, start_time__gte=penalty[0], end_time__lte=penalty[1])
			
			for shift in pshifts:
				shift.active_penalty = True
				shift.save()



def split_shift(shift_in, time):
	'''Splits a ::shift:: object into two parts, around an argument ::time::
		After the split is created, the original shift object is deleted.
		Does nothing if ::time:: equals start_time or end_time of the shift.
	'''

	if shift_in.start_time >= time:
		raise ValueError("Shift start time (%d) >= time argument (%d)" % (shift_in.start_time, time))
	if shift_in.end_time <= time:
		raise ValueError("Shift start time (%d) <= time argument (%d)" % (shift_in.end_time, time))

	if not shift_in.id:
		raise ValueError("Shift no longer exists")

	#create shift data before time split
	ShiftGame.objects.create(playergame = shift_in.playergame, start_time = shift_in.start_time, end_time = time)

	#create shift data after time split
	ShiftGame.objects.create(playergame = shift_in.playergame, start_time = time, end_time = shift_in.end_time)

	#delete the original object
	shift_in.delete()

