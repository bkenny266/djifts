import re
from datetime import date

def convert_month(month_str):
	if month_str == "Jan":
		return 1
	elif month_str == "Feb":
		return 2
	elif month_str == "Mar":
		return 3
	elif month_str == "Apr":
		return 4
	elif month_str == "May":
		return 5
	elif month_str == "Jun":
		return 6
	elif month_str == "Jul":
		return 7
	elif month_str == "Aug":
		return 8
	elif month_str == "Sep":
		return 9
	elif month_str == "Oct":
		return 10
	elif month_str == "Nov":
		return 11
	elif month_str == "Dec":
		return 12


def process_date(date_str):

	date_parts = re.split('\W+', date_str)

	month = convert_month(date_parts[0])
	day = int(date_parts[1])
	year = int(date_parts[2]) + 2000

	return date(year, month, day)

