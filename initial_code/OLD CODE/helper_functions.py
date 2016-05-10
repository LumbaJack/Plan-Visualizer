""" Helper Functions """
import os
import sys
import math
import datetime
import itertools
import threading

from Queue import Queue
from yahoo_finance import Share
from datetime import date, timedelta

class HlpFuncs(object):
    """ Helper Functions for CSV files """
    def __init__(self):
        self.queue = Queue()
        self.num_fetch_threads = 10

    def count_workdays(self, expdate):
        """ Function to count to work days left to expiration """
        now = datetime.datetime.now()
        fromdate = date(now.year, now.month, now.day)

        todate = date(int(str(expdate)[0:4]), \
                                                int(str(expdate)[4:6]), \
                                                int(str(expdate)[6:8]))

        daygenerator = (fromdate + timedelta(x + 1) \
                                    for x in xrange((todate - fromdate).days))
        timeframe = sum(1 for day in daygenerator if day.weekday() < 5)

        if datetime.datetime.now().hour < 15 and \
                                            datetime.datetime.now().minute < 30:
            timeframe += 1

        return timeframe

    def calculate_expected_value(self, optionsdf, key):
        """ Function to calculate expected value """
        width = abs(optionsdf.loc[str(key)]["short_strike"] - \
                                optionsdf.loc[str(key)]["long_strike"])

        prem_gain = optionsdf.loc[str(key)]["max_gain"]
        probability_decimal = \
                    optionsdf.loc[str(key)]["probabilityofprofit"] / 100

        gain_probability = probability_decimal
        gain_return = probability_decimal * prem_gain

        loss_probability = 1 - gain_probability
        loss_return = loss_probability * (prem_gain - (width * 100))

        return (gain_return + loss_return) * 100000000000000

    def combinations(self, tval, optionkeys, entries_so_far, combos):
        """ Function find all permutation of the provided list """
        if (tval * .9) <= sum([pair[1] for pair in entries_so_far]) < tval:
            combos.append(entries_so_far)

        if sum([pair[1] for pair in entries_so_far]) == tval:
            combos.append(entries_so_far)
        elif sum([pair[1] for pair in entries_so_far]) > tval:
            pass
        elif optionkeys == []:
            pass
        else:
            self.queue.put(((tval, optionkeys[:], \
                        entries_so_far+[(str(optionkeys[0]['short_strike']) + \
                         "/" + str(optionkeys[0]['long_strike']), \
                         optionkeys[0]['max_loss'], \
                         optionkeys[0]['max_gain'], \
                         optionkeys[0]['expectedvalue'], \
                         optionkeys[0]['probabilityofprofit'])], combos, self)))
            self.queue.put((tval, optionkeys[1:], entries_so_far, combos, self))

    def calc_inv_amount_comb(self, optionslist, inv_amount):
        """ Function to calculate the total combinations for the inv. amnt. """
        combos = []

        optionslist.sort(['max_loss'], ascending=[True], inplace=True)
        optionkeys = optionslist.T.to_dict().values()
        optionkeys = sorted(optionkeys, key=lambda k: k['max_loss'])

        for _ in range(1):
            workhand = SuperDuperWorker(self.queue)
            workhand.setDaemon(True)
            workhand.start()

        self.combinations(inv_amount, optionkeys, [], combos)
        self.queue.join()

        combos.sort()
        combos = list(combos for combos, _ in itertools.groupby(combos))

        return combos

    def standard_deviation(self, csvdata):
        """ Function to calculate the standard deviation """
        currentprice = csvdata['last_undPrice'].real[0]

        yahoo = Share('^VIX')
        vixcurrent = yahoo.get_price()

        timeframe = self.count_workdays(expdate=csvdata['m_expiry'].real[0])
        standev = (float(currentprice) * (float(vixcurrent)/100) * \
                                math.sqrt(float(timeframe))) / math.sqrt(252)

        return standev

    def find_latest_csv(self):
        """ Function to find the latest spx file created """
        if not os.path.isdir(os.path.join('.', 'spx_files')):
            sys.stderr.write("ERROR: please verify that the directory " \
                            "%s exist.\n\n" % os.path.join('.', 'spx_files'))
            raise OSError

        all_subdirs = self.all_subdirs_of(os.path.join('.', 'spx_files'))
        latest_subdir = max(all_subdirs, key=os.path.getmtime)
        return os.path.join(latest_subdir, 'Options.csv')

    def all_subdirs_of(self, spxloc):
        """ Helper function for finding directories """
        result = []
        for item in os.listdir(spxloc):
            pathloc = os.path.join(spxloc, item)

            if os.path.isdir(pathloc):
                result.append(pathloc)

        return result

class SuperDuperWorker(threading.Thread):
    """ Recursive worker implementation """
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        """ Thread creator """
        while True:
            (tval, optionkeys, entries_so_far, combos, thobj) = self.queue.get()
            thobj.combinations(tval, optionkeys, entries_so_far, combos)
            self.queue.task_done()

