#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np
import datetime
from dateutil import parser
import time

debug = 1
logfile = '/home/curt/bin/adsense.txt'

# google accumulates days relative to the pacific time zone, so define your
# offset here. (i.e. central time zone = 2 * (1/24)

tzoffset = 0 * (1.0 / 24.0)     # sure seems like reporting is in local tz
#tzoffset = 2 * (1.0 / 24.0)

# month zero has zero days. :-)
MDAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]

# return the day of the week from the date_index
def day_of_week(date_index):
    year = int(date_index[0:4])
    mon = int(date_index[4:6])
    day = int(date_index[6:8])
    dow = datetime.date(year, mon, day).weekday()
    return dow
    
# return a simple date index
def date_index(unix_sec=None):
    if not unix_sec:
        result = time.localtime()
    else:
        result = time.localtime(unix_sec)
    return "%04d%02d%02d" % (result.tm_year, result.tm_mon, result.tm_mday)

def gen_func( coeffs, min, max, steps ):
    if abs(max-min) < 0.0001:
        max = min + 0.1
    xvals = []
    yvals = []
    step = (max - min) / steps
    func = np.poly1d(coeffs)
    for x in np.arange(min, max+step, step):
        y = func(x)
        xvals.append(x)
        yvals.append(y)
    return xvals, yvals

today_dow = day_of_week(date_index())
print("Today's day of week:", today_dow)

print("Reading log file:", logfile)
f = open(logfile, 'r')
# pass one: daily totals
first_day = None
day_totals = {}
for line in f:
    (index_today, index_yesterday, dayperc, today, yesterday,
       last7, thismo, last28) = line.split(',')
    if not first_day:
        first_day = index_today
    day_totals[index_yesterday] = float(yesterday)
    #print( day_of_week(index_today) )

firstday_str = first_day[:4] + "-" + first_day[4:6] + "-" + first_day[6:8]
start_day = parser.parse(firstday_str)
    
# pass two: progress
data = []
averages = {}
f.seek(0)
for line in f:
    (index_today, index_yesterday, dayperc, today, yesterday,
       last7, thismo, last28) = line.rstrip().split(',')
    #line = "%s,%s,%.4f,%s,%s,%s,%s,%s" \
    #    % (index_today, index_yesterday, float(dayperc)-tzoffset, today, yesterday,
    #       last7, thismo, last28)
    #print(line.rstrip())
    if index_today in day_totals:
        if day_totals[index_today] > 0:
            if day_of_week(index_today) == today_dow:
                amt_perc = float(today) / day_totals[index_today]
                data.append( [float(dayperc), amt_perc] )
    today_str = index_today[:4] + "-" + index_today[4:6] + "-" + index_today[6:8]
    today_day = parser.parse(today_str)
    diff = (today_day - start_day).days
    averages[diff] = [ diff, float(last7)/7, float(last28)/28 ]
    
f.close()
if debug >= 2:
    print(day_totals)
    print(data)

# complete end points
data.insert(0, [0,0])
data.append([1+tzoffset,1])

if False:
    # encourage the plot to go through [0,0] and [1,1]
    weights = np.ones(len(data))
    weights[0] = len(data)
    weights[-1] = len(data)
else:
    # weight more recent data more
    weights = np.ones(len(data))
    for i in range(len(data)):
        weights[i] = i
    weights[0] = len(data)*len(data)
    weights[-1] = len(data)*len(data)

# fit and plot the progress data
data = np.array(data)
fit, res, _, _, _ = np.polyfit( data[:,0], data[:,1], 4, w=weights, full=True )
xvals, yvals = gen_func(fit, 0.0, 1.0, 100)
plt.figure()
plt.title("Progress")
plt.xlabel("Percent of Day")
plt.ylabel("Percent of Revenue")
plt.plot(data[:,0], data[:,1],'b.',label='Raw data')
plt.plot(xvals, yvals,'r',label='Fit')

# plot the rolling averages (convert dict to array)
avg = []
for key in sorted(averages):
    avg.append(averages[key])
avg = np.array(avg)
plt.figure()
plt.title("Rolling Averages")
plt.xlabel("Days")
plt.ylabel("Daily Revenue")
plt.grid('on')
plt.plot(avg[:,0], avg[:,1], label="7 Day")
plt.plot(avg[:,0], avg[:,2], label="28 Day")
plt.legend()
plt.show()

result = time.localtime()

print("Enter revenue:")
today = float(input("  Today so far: "))
yesterday = float(input("  Yesterday: "))
last7 = float(input("  Last 7 days: "))
thismo = float(input("  This month: "))
last28 = float(input("  Last 28 days: "))

print("Today's date index:", date_index())
print("Yesterday's date index:", date_index(time.time() - 86400))

dayperc = (result.tm_hour + (result.tm_min / 60)) / 24.0 - tzoffset
if dayperc < 0.0:
    dayperc = 0.0
dayest = today / dayperc

# append data to log file
print("Saving raw data..")
f = open(logfile, 'a')
line = "%s,%s,%.4f,%.2f,%.2f,%.2f,%.2f,%.2f" \
    % (date_index(), date_index(time.time() - 86400), dayperc, today, yesterday,
       last7, thismo, last28)
f.write(line + "\n")
f.close()

monthperc = (result.tm_mday - 1 + dayperc) / MDAYS[result.tm_mon]

ave7 = last7 / 7.0
ave28 = last28 / 28.0
avemo = thismo / (result.tm_mday -1 + dayperc)
print("  average 7 =", ave7, "28 =", ave28, "mo =", avemo)

aveday = (2 * ave7 + 4 * avemo + 8 * ave28) / 14
print("  weighted average day =", aveday)

func = np.poly1d(fit)

fit_perc = func(dayperc)
print('fit perc:', fit_perc)
fit_est = today / fit_perc

if debug >= 2:
    print("  month = ", result.tm_mon, ", days this month = ", MDAYS[result.tm_mon])

remmon = 1.0 - monthperc
monthest = thismo + remmon * aveday * MDAYS[result.tm_mon]

if debug >= 1:
      print("  day %% = %.4f" % dayperc)
      print( "  month %% = %.4f" % monthperc)
#print("Today's total (est by time) = $%.2f" % dayest)
print("Today's total (est by fit) = $%.2f" % fit_est)
print("This month's total (est) = $%.2f" % monthest)
google_sluff_factor = 0.89
print("Estimated google revenue = $%.0f" % (int((monthest*google_sluff_factor)/10)*10))


