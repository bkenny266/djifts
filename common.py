from string import join
from games.models import *


def time_convert(secIn):
    mins = secIn / 60
    secs = secIn % 60
    if mins < 10:
        mins = "0" + str(mins)
    if secs < 10:
        secs = "0" + str(secs)

    period_mins = mins%20

    return str(period_mins) + ":" + str(secs) + ", period " + str(mins/20+1)

def prev_lines(teamgame, num_lines=5):
    all_lines = LineGameTime.objects.filter(linegame__teamgame=teamgame)
    lines = []

    for x in range(len(all_lines)-5, len(all_lines)):
        lines.append(all_lines[x])

    for line in lines:
        print join((line.__unicode__(),str(line.start_time),str(line.end_time)),"\t")
    return lines


def prev_shifts(teamgame, time, num_shifts=10):
    all_shifts = ShiftGame.objects.filter(playergame__team=teamgame, start_time__lt=time)

    for shift in all_shifts[len(all_shifts)-num_shifts-1:len(all_shifts)-1]:
        print shift

    return all_shifts[len(all_shifts)-num_shifts:len(all_shifts)-1]

def next_shifts(teamgame, time, num_shifts=10):
    all_shifts = ShiftGame.objects.filter(playergame__team=teamgame, start_time__gte=time)

    for shift in all_shifts[0:num_shifts]:
        print shift

    return all_shifts[0:num_shifts]


