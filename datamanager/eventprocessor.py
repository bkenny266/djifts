'''
DATAMANAGER - eventprocessor.py
'''

import re

class EventProcessor(object):

	event_types = ['GOAL', 'SHOT', 'HIT', 'BLOCK', 'PENL']
	teams = []


	def __init__(self, soup):

		#Need to load both team names first, so blocked shots can be correctly assigned
		self.teams = []
		
		self.goals = []
		self.shots = []
		self.blocks = []
		self.hits = []
		self.penalties = []

		self.__load_team_names__(soup)

		for event in self.event_types:
			type_objects = soup.find_all('td', text=event)
			
			for current_object in type_objects:
				#period is 6 siblings back
				period = current_object.previous_sibling.previous_sibling.previous_sibling.previous_sibling.previous_sibling.previous_sibling.text
				time = current_object.previous_sibling.previous_sibling.next_element
				data_block = current_object.next_sibling.next_sibling.text

				#format for shot blocks is different (blocking player appears second 
				#and also team referes to the team that was BLOCKED, so need to swap that)
				if event == 'BLOCK':
					parsed = re.match(r'^[ ]*([A-Z.]+)[^#]+#[^#]+#(\d{1,2})', data_block)
					team_initials = self.__get_other_team__(parsed.group(1))
				elif event == 'PENL':
					parsed = re.match(r'^[ ]*([A-Z.]+)[^#]+#(\d{1,2})[^\d{1,2}]+(\d{1,2})[ ]*min', data_block)
					team_initials = parsed.group(1)
					penalty_length = parsed.group(3)
				else:
					parsed = re.match(r'^[ ]*([A-Z.]+)[^#]+#(\d{1,2})', data_block)
					team_initials = parsed.group(1)
				player_number = parsed.group(2)

				if event == 'PENL':
					e = PenaltyEvent(event, team_initials, player_number, period, time, penalty_length)
				else:
					e = Event(event, team_initials, player_number, period, time)

				if event == 'GOAL':
					self.goals.append(e)
				elif event == 'SHOT':
					self.shots.append(e)
				elif event == 'HIT':
					self.hits.append(e)
				elif event == 'BLOCK':
					self.blocks.append(e)
				elif event == 'PENL':
					self.penalties.append(e)
				else:
					raise(ValueError, "Invalid event - %s" % event)

	def flatten(self):
		'''returns a flat list of NON-PENALTY events, sorted by time'''
		flat_list = []

		for goal in self.goals:
			flat_list.append(goal)

		for shot in self.shots:
			flat_list.append(shot)

		for block in self.blocks:
			flat_list.append(block)

		for hit in self.hits:
			flat_list.append(hit)

		return sorted(flat_list, key = lambda x: x.event_time_in_seconds)



	def __load_team_names__(self, soup):
		#loads team names into the EventProcessor object to use later
		for event in self.event_types:
			event_objects = soup.find_all('td', text=event)
			for item in event_objects:
				if len(self.teams) >= 2:
					return

				data_block = item.next_sibling.next_sibling.text
				parsed = re.match(r'^[ ]*([A-Z.]+)', data_block)
				team_initials = parsed.group(0)

				if len(self.teams) == 0 or self.teams[0] != team_initials:
					self.teams.append(team_initials)

	def __get_other_team__(self, team_initials):
		#takes argument of one team and returns the initials of the other team
		if len(self.teams) != 2:
			raise(ValueError("There are more or less than two team names loaded"))

		if team_initials == self.teams[0]:
			return self.teams[1]
		elif team_initials == self.teams[1]:
			return self.teams[0]
		else:
			raise(ValueError("Team %s does not exist" % team_initials))





class Event(object):
	event_team_initials = ''
	event_type = ''
	event_player_number = ''
	event_period = ''
	event_time = ''
	event_time_in_seconds = ''

	def __init__(self, event_type, event_team_initials, event_player, event_period, event_time):
		self.event_type = event_type
		self.event_player = int(event_player)
		self.event_period = int(event_period)
		self.event_time = event_time

		if event_team_initials == "L.A":
			self.event_team_initials = "LAK"
		
		elif event_team_initials == "S.J":
			self.event_team_initials = "SJS"

		elif event_team_initials == "T.B":
			self.event_team_initials ="TBL"

		elif event_team_initials == "N.J":
			self.event_team_initials = "NJD"

		else:
			self.event_team_initials = event_team_initials

		self.__convert_to_seconds__()

	def __convert_to_seconds__(self):
		parsed = re.match('^(\d{1,2}):(\d{2})$', self.event_time)
		timeMins = int(parsed.group(1))
		timeSecs = int(parsed.group(2))
		self.event_time_in_seconds = timeMins * 60 + timeSecs + ((self.event_period * 20 - 20) * 60)


class PenaltyEvent(Event):
	'''special Event subclass - includes additional penalty length and end_time attributes'''

	def __init__(self, event_type, event_team_initials, event_player, event_period, event_time, event_length):

		super(PenaltyEvent, self).__init__(event_type, event_team_initials, event_player, event_period, event_time)

		self.event_length = int(event_length)
		self.event_end_time_in_seconds = (self.event_length * 60) + self.event_time_in_seconds
