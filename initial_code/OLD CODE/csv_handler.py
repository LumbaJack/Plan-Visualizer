""" CSV HANDLER """
import os
import sys
import itertools
import pandas as pd
import helper_functions

from random import randint
from collections import Counter

class StrategyFuntions(object):
    """ Main class for stock option strategies """
    def __init__(self):
        self.hlpr = helper_functions.HlpFuncs()
        self.csvdata = pd.DataFrame().from_csv(self.hlpr.find_latest_csv())
        self.stdeviation = self.hlpr.standard_deviation(self.csvdata)
        self.putoptions = pd.DataFrame(columns=['short_strike', 'long_strike', \
                            'delta', 'max_loss', 'max_gain', 'percent_gain', \
                            'probabilityofprofit', 'expectedvalue'])
        self.calloptions = pd.DataFrame(columns=['short_strike', 'long_strike',\
                            'delta', 'max_loss', 'max_gain', 'percent_gain', \
                            'probabilityofprofit', 'expectedvalue'])

    def generate_put_options(self, poperc, min_percent_gain, results=False):
        """ Main function to generate single put options """
        put_chain = self.csvdata[self.csvdata['m_right'] == "P"].fillna(0).\
                                            sort(['m_strike'], ascending=[True])

        currentprice = next(obj for obj in put_chain['last_undPrice'].real \
                                                            if not obj == 0.0)

        if currentprice == 0.0:
            sys.stdout.write("ERROR: Your input file doesn't contain a valid" \
                                                            " current price")
            return

        lowerboundsd = currentprice - (self.stdeviation * 2)

        sys.stdout.write("Starting put spread individual calculations...")
        for shortstrike, longstrike in itertools.product(\
                             put_chain['m_strike'], put_chain['m_strike']):
            if (lowerboundsd < longstrike < shortstrike < currentprice) \
                                    and ((shortstrike - longstrike) <= 10):
                longputprem = put_chain[put_chain['m_strike'] == \
                                            longstrike].last_optPrice.item()

                if longputprem == 0:
                    continue
                else:
                    shortputprem = put_chain[put_chain['m_strike'] == \
                                         shortstrike].last_optPrice.item()

                conid = ''.join(["%s" % randint(0, 9) for _ in \
                                                            range(0, 12)])

                bullpsv = shortputprem - longputprem

                self.putoptions.loc[str(conid), 'short_strike'] = \
                                                                shortstrike
                self.putoptions.loc[str(conid), 'long_strike'] = longstrike
                self.putoptions.loc[str(conid), 'delta'] = \
                                    (put_chain[put_chain['m_strike'] == \
                                    longstrike].last_delta.item()) - \
                                    (put_chain[put_chain['m_strike'] == \
                                    shortstrike].last_delta.item())
                self.putoptions.loc[str(conid), 'max_loss'] = \
                                    ((shortstrike - longstrike) - bullpsv) * 100
                self.putoptions.loc[str(conid), 'max_gain'] = bullpsv * 100
                self.putoptions.loc[str(conid), 'percent_gain'] = bullpsv / \
                                        ((shortstrike - longstrike) - bullpsv)
                self.putoptions.loc[str(conid), 'probabilityofprofit'] = 100 - \
                                    (bullpsv / (shortstrike - longstrike)) * 100
                self.putoptions.loc[str(conid), 'expectedvalue'] = \
                                        self.hlpr.calculate_expected_value(\
                                                   self.putoptions, conid)

        self.putoptions = self.putoptions[self.putoptions\
                                      ['probabilityofprofit'] >= float(poperc)]
        self.putoptions = self.putoptions[self.putoptions\
                                  ['percent_gain'] >= float(min_percent_gain)]
        self.putoptions = self.putoptions.sort(['expectedvalue'], \
                                                            ascending=[True])

        sys.stdout.write("Done\n")

        if not results:
            sys.stdout.write("Writing files...")
            if not os.path.isdir(os.path.join('.', 'results')):
                os.makedirs('results')

            self.putoptions.to_csv(os.path.join('.', 'results', \
                                                    'put_spread_results.csv'))
            sys.stdout.write("Done\n\n")

    def generate_combo_put_options(self, poperc, min_percent_gain, \
                                                                inv_amount=1000):
        """ Main function to generate combo put options """
        self.generate_put_options(poperc, min_percent_gain, results=True)

        sys.stdout.write("Starting put spread combinations calculations...")
        finalcombolist = [["Options", "totalloss", "totalgain", \
                                "percentgain", "totalev", "probability"]]

        for item in self.hlpr.calc_inv_amount_comb(self.putoptions, \
                                                            int(inv_amount)):
            totalev = sum([pair[3] for pair in item])

            if totalev <= 0:
                continue

            totalloss = sum([pair[1] for pair in item])
            totalgain = sum([pair[2] for pair in item])

            freqs = Counter([data[0] for data in item])
            probability = min([pair[4] for pair in item])

            finalcombolist.append([freqs, totalloss, totalgain, \
                                (totalgain/totalloss), totalev, probability])
        sys.stdout.write("Done\n")

        sys.stdout.write("Writing files...")
        if not os.path.isdir(os.path.join('.', 'results')):
            os.makedirs('results')

        thefile = open(os.path.join('.', 'results', \
                                        'put_spread_combo_results.txt'), "w")
        for item in finalcombolist:
            for entry in item:
                thefile.write("%s\t" % entry)
            thefile.write("\n")
        sys.stdout.write("Done\n\n")

    def generate_call_options(self, poperc, min_percent_gain, results=False):
        """ Main function to generate single call options """
        call_chain = self.csvdata[self.csvdata['m_right'] == "C"].fillna(0).\
                                            sort(['m_strike'], ascending=[True])

        currentprice = next(obj for obj in call_chain['last_undPrice'].real \
                                                            if not obj == 0.0)

        if currentprice == 0.0:
            sys.stdout.write("ERROR: Your input file doesn't contain a valid" \
                                                            " current price")
            return

        upperboundsd = currentprice + (self.stdeviation * 2)

        sys.stdout.write("Starting call spread individual calculations...")
        for shortstrike, longstrike in itertools.product(\
                             call_chain['m_strike'], call_chain['m_strike']):
            if (upperboundsd > longstrike > shortstrike > currentprice) \
                                    and ((longstrike - shortstrike) <= 10):
                longputprem = call_chain[call_chain['m_strike'] == \
                                            longstrike].last_optPrice.item()

                if longputprem == 0:
                    continue
                else:
                    shortputprem = call_chain[call_chain['m_strike'] == \
                                         shortstrike].last_optPrice.item()

                conid = ''.join(["%s" % randint(0, 9) for _ in \
                                                            range(0, 12)])

                bearpsv = shortputprem - longputprem

                self.calloptions.loc[str(conid), 'short_strike'] = \
                                                                shortstrike
                self.calloptions.loc[str(conid), 'long_strike'] = longstrike
                self.calloptions.loc[str(conid), 'delta'] = \
                                    (call_chain[call_chain['m_strike'] == \
                                    longstrike].last_delta.item()) - \
                                    (call_chain[call_chain['m_strike'] == \
                                    shortstrike].last_delta.item())
                self.calloptions.loc[str(conid), 'max_loss'] = \
                                            ((longstrike - shortstrike) - \
                                             bearpsv) * 100
                self.calloptions.loc[str(conid), 'max_gain'] = \
                                                        bearpsv * 100
                self.calloptions.loc[str(conid), 'percent_gain'] = \
                                        bearpsv / ((longstrike - \
                                           shortstrike) - bearpsv)
                self.calloptions.loc[str(conid), 'probabilityofprofit'] = \
                                        100 - (bearpsv / \
                                       (longstrike - shortstrike)) * 100
                self.calloptions.loc[str(conid), 'expectedvalue'] = \
                                        self.hlpr.calculate_expected_value(\
                                                   self.calloptions, conid)

        self.calloptions = self.calloptions[self.calloptions\
                                  ['probabilityofprofit'] >= float(poperc)]
        self.calloptions = self.calloptions[self.calloptions\
                              ['percent_gain'] >= float(min_percent_gain)]
        self.calloptions = self.calloptions.sort(['probabilityofprofit', \
                        'max_gain', 'delta'], ascending=[True, True, False])

        sys.stdout.write("Done\n")

        if not results:
            sys.stdout.write("Writing files...")
            if not os.path.isdir(os.path.join('.', 'results')):
                os.makedirs('results')

            self.calloptions.to_csv(os.path.join('.', 'results', \
                                                    'call_spread_results.csv'))
            sys.stdout.write("Done\n\n")

    def generate_combo_call_options(self, poperc, min_percent_gain, \
                                                            inv_amount=1000):
        """ Main function to generate combo call options """
        self.generate_call_options(poperc, min_percent_gain, results=True)

        sys.stdout.write("Starting put spread combinations calculations...")
        finalcombolist = [["Options", "totalloss", "totalgain", \
                                "percentgain", "totalev", "probability"]]

        for item in self.hlpr.calc_inv_amount_comb(self.calloptions, \
                                                            int(inv_amount)):
            totalev = sum([pair[3] for pair in item])

            if totalev <= 0:
                continue

            totalloss = sum([pair[1] for pair in item])
            totalgain = sum([pair[2] for pair in item])

            freqs = Counter([data[0] for data in item])
            probability = min([pair[4] for pair in item])

            finalcombolist.append([freqs, totalloss, totalgain, \
                                (totalgain/totalloss), totalev, probability])
        sys.stdout.write("Done\n")

        sys.stdout.write("Writing files...")
        if not os.path.isdir(os.path.join('.', 'results')):
            os.makedirs('results')

        thefile = open(os.path.join('.', 'results', \
                                        'call_spread_combo_results.txt'), "w")
        for item in finalcombolist:
            for entry in item:
                thefile.write("%s\t" % entry)
            thefile.write("\n")
        sys.stdout.write("Done\n\n")

