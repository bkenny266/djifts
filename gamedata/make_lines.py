from gamedata.models import Game, ShiftData

#shift_list is a two-dimensional array - first dimension is the index of
#each list, the second dimension is the values within each list
shift_list = []

def process_list(shift_item, list_index):
	#Function to make sure shift end_time values are in order
	#If something is out of order, will pull it into a separate list
	#Each list will be in the correct order of end_time values

	try:
		#checks if the last item in list_index is equal to or greater than 
		#the value of shift_item.
		#if not, recursively call this function and check again on the next level's list
		if shift_item.end_time >= shift_list[list_index][-1].end_time:
			shift_list[list_index].append(shift_item)

		else:
			process_list(shift_item, list_index+1)

	except IndexError:
		#if an index error occurs, list does not exist at list_index
		#creates a new list and appends the value to it
		shift_list.append([shift_item])


line_list = []



def make_lines():

	def check_list(list_index, shift_index):
		#determines how to handle the list data for each shift
		#recursive function, runs on itself to advance the list


		list_end = False

		#if shift index is the last in the list
		if shift_index >= len(shift_list[list_index]) - 1:
			list_end = True

		#if shift index was previously marked as the last of a list
		if shift_index == -1:
			#mark as end of list, point to end of list
			list_end = True
			shift_index = len(shift_list[list_index]) - 1

		#initializes return value to current value
		return_index = shift_index

		#set a variable to current list object
		current = shift_list[list_index][shift_index]

		#no further actions if current item has not yet been reached
		if current.start_time > prev_end:
			pass

		#if current item is no longer relevant, move ahead in list and re-check
		#note: advances return index
		elif current.end_time <= prev_end:
			if not list_end:
				return_index = check_list(list_index, shift_index + 1)

		#if current item is part of the active shift, add to list and check the next item
		#note: does not advance the return index
		elif current.start_time <= prev_end and prev_end < current.end_time:
			current_line.append(current)

			if not list_end:
				check_list(list_index, shift_index + 1)

		#set index to a special value if list is at the end
		if list_end:
			return_index = -1

		return return_index
	###############################################


	#set index start position to zero for each list
	shift_index = []
	
	for x in range(0, len(shift_list)):
		shift_index.append(0)

	prev_end = 0
		
	#Loop until end of the game is the lowest time from a line
	while(prev_end < 3600):
		current_line = []

		#runs checks on each list in the shift_array
		#each iteration of the loop returns the list index of where to begin next time
		for current_list_index in range(0, len(shift_list)):
			shift_index[current_list_index] = check_list(current_list_index, shift_index[current_list_index])
			
		#get the lowest end_time and use it to calculate the next shift
		prev_end = get_lowest(current_line)
		line_list.append(current_line)


def get_lowest(line):

	lowest_end = 99999
	for shift in line:
		if shift.end_time < lowest_end:
			lowest_end = shift.end_time

	return lowest_end


