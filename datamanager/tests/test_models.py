import datetime
from django.test import TestCase
from datamanager.models import GameList


class ConvertDateTest(TestCase):
	def test_good_date_conversion(self):
		d = "Mar 13 '14"
		d_converted = GameList.convert_date(d)
		self.assertEqual(d_converted, datetime.date(2014, 3, 13))

	def test_incorrect_format(self):
		d = "Mar 13 14"
		self.assertRaises(ValueError, GameList.convert_date, d)


class ConvertGameId(TestCase):
	def test_good_game_id_conversion(self):
		season = "20122013"
		game_id = "020431"
		self.assertEqual(12020431, GameList.convert_game_id(season, game_id))

	def test_game_id_conversion_season_error_message(self):
		season = "199121444"
		game_id = "020431"
		with self.assertRaises(Exception) as context:
			GameList.convert_game_id(season, game_id)
		self.assertEqual(context.exception.message, 
			"season value is 91 - should be between 12 and 19")

	def test_game_id_conversion_game_id_error_message(self):
		season = "20122013"
		game_id = "139299"
		with self.assertRaises(Exception) as context:
			GameList.convert_game_id(season, game_id)
		self.assertEqual(context.exception.message, 
			"game_id starts with 13 - should start with 02 or 03")


	def test_game_id_conversion_wrong_input_size(self):
		season = "201211111"
		game_id = "02040000"
		with self.assertRaises(Exception) as context:
			GameList.convert_game_id(season, game_id)
		self.assertEqual(context.exception.message, 
			"game_id is length 10 - should be length 8")


'''
class GetLowestTest(TestCase):

	fixtures = ['datamanager_testdb.json']

	def test_get_lowest(self):
		shift_list = ShiftGame.objects.all()[0:24]
		self.assertEqual(get_lowest(shift_list), 49)

class IsNewGroupTest(TestCase):

	fixtures = ['datamanager_testdb.json']

	def setUp(self):
		self.g = Game.objects.get(pk=12020598)

	def test_is_new_group(self):
		shift_list = ShiftGame.objects.filter(playergame__team = self.g.team_home, start_time = 0)
		self.assertEqual(is_new_group(shift_list), True)

	def test_is_NOT_new_group(self):
		shift_list = ShiftGame.objects.filter(playergame__team=self.g.team_home, start_time__lte = 50, end_time__gt=50)
		self.assertEqual(is_new_group(shift_list), False)


class CompareGroupsTest(TestCase):

	fixtures = ['datamanager_testdb2.json']

	def test_ONE_added_player(self):
		shift_list1 = ShiftGame.objects.filter(start_time__lte = 91000, end_time__gt = 91000)
		shift_list2 = ShiftGame.objects.filter(start_time__lte = 91020, end_time__gt = 91020)

		self.assertEqual(compare_groups(shift_list1, shift_list2, 91020), 91015)
		self.assertEqual(shift_list1.count(), 4)
		self.assertEqual(shift_list2.count(), 5)

	def test_TWO_added_players(self):
		shift_list1 = ShiftGame.objects.filter(start_time__lte = 92000, end_time__gt = 92000)
		shift_list2 = ShiftGame.objects.filter(start_time__lte = 92020, end_time__gt = 92020)

		self.assertEqual(compare_groups(shift_list1, shift_list2, 92020), 92013)
		self.assertEqual(shift_list1.count(), 5)
		self.assertEqual(shift_list2.count(), 6)

	def test_EXCLUDE_previous_player(self):
		g = Game.objects.get(pk=12020610)
		shift_list1 = ShiftGame.objects.filter(playergame__team = g.team_home, start_time__lte = 2133, end_time__gt = 2133)
		shift_list2 = ShiftGame.objects.filter(playergame__team = g.team_home, start_time__lte = 2186, end_time__gt = 2186)

		self.assertEqual(compare_groups(shift_list1, shift_list2, 2186), 2174)
'''