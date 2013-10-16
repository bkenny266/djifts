from django.test import TestCase
import mock

from datamanager.utility import *
from datamanager.eventprocessor import PenaltyEvent

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

class ConsolidatePenaltiesTest(TestCase):

	def setUp(self):
		self.penalty_list = []
		add_list = [(0, 50), (14, 50), (35, 55), (57, 68), (70,100), (90, 110), (110, 120), (122, 130), (130, 150), (155, 160)]


		for item in add_list:
			event = PenaltyEvent("PENL", "TEST", 0, 1, "1:22", 2)
			event.event_time_in_seconds = item[0]
			event.event_end_time_in_seconds = item[1]
			self.penalty_list.append(event)

		self.consolidated = consolidate_penalties(self.penalty_list)

	def test_Is_Consolidation_Working(self):
		self.assertEqual(self.consolidated[0], (0, 55))
		self.assertEqual(self.consolidated[1], (57, 68))
		self.assertEqual(self.consolidated[2], (70, 120))
		self.assertEqual(self.consolidated[3], (122, 150))
		self.assertEqual(self.consolidated[4], (155, 160))

	def test_Consolidation_Array_is_Correct_Length(self):
		self.assertEqual(len(self.consolidated), 5)

class SplitShiftTest(TestCase):

	def setUp(self):
		pg = mock.Mock(spec=PlayerGame)
		pg._state = mock.Mock()
		pg.id = 99999

		self.shift_start = 20
		self.shift_end = 50 
		self.testshift = ShiftGame(playergame = pg, start_time = self.shift_start, end_time = self.shift_end)
		self.testshift.save()

	def test_Split_Working_Correctly_Normal_Case(self):
		self.assertEqual(ShiftGame.objects.filter(start_time__gte=self.shift_start, end_time__lte=self.shift_end).count(), 1)
		split_shift(self.testshift, self.shift_start, self.shift_end)
		self.assertEqual(ShiftGame.objects.filter(start_time__gte=self.shift_start, end_time__lte=self.shift_end).count(), 2)