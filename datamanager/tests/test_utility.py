from django.test import TestCase
from datamanager.utility import *

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