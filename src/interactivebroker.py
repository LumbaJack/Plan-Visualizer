""" Interactive Broker Handler """
import os
import sys
import json
import time
import datetime
import pandas as pd
import requests

from time import sleep
from slacker import Slacker
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from ib.ext.TickType import TickType as tt
from stock_graph_handler import StockGraphFunctions
 
OPTIONS = pd.DataFrame(columns=["ask", "ask_delta", "ask_gamma", \
              "ask_impliedVol", "ask_optPrice", "ask_pvDividend", "ask_theta", \
              "ask_undPrice", "ask_vega", "bid", "bid_delta", "bid_gamma", \
              "bid_impliedVol", "bid_optPrice", "bid_pvDividend", "bid_theta", \
              "bid_undPrice", "bid_vega", "close", "last_delta", "last_delta", \
              "last_gamma", "last_impliedVol", "last_optPrice", \
              "last_pvDividend", "last_theta", "last_undPrice", "m_conId", \
              "m_currency", "m_exchange", "m_expiry", "m_localSymbol", \
              "m_multiplier", "m_right", "m_secType", "m_strike", "m_symbol"])
 
SCHEDULELIMIT = [("1 d", "1 min")]

class ReferenceApp(object):
    """ Wrapper class for communications with IB """
    def __init__(self):
        self.NEWDATALIST = []
        self.NEWVOLUMELIST = []

    def error_handler(self, msg):
        """ Basic error handler """
        print msg
 
    def my_callback_handler(self, msg):
        """ Simple call back handler """
        if msg.typeName == "contractDetails":
            opt_contract = msg.values()[1]
 
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                    'm_conId'] = opt_contract.m_summary.m_conId
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                'm_symbol'] = opt_contract.m_summary.m_symbol
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                'm_secType'] = opt_contract.m_summary.m_secType
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                'm_expiry'] = opt_contract.m_summary.m_expiry
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                'm_strike'] = opt_contract.m_summary.m_strike
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                                    'm_right'] = opt_contract.m_summary.m_right
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                        'm_multiplier'] = opt_contract.m_summary.m_multiplier
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                            'm_exchange'] = opt_contract.m_summary.m_exchange
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                            'm_currency'] = opt_contract.m_summary.m_currency
            OPTIONS.loc[str(opt_contract.m_summary.m_conId).replace(" ", ""),\
                        'm_localSymbol'] = opt_contract.m_summary.m_localSymbol
        elif msg.typeName == "tickOptionComputation":
            sys.stdout.write('=> option computation update for tickerId %s\n' \
                                                                % msg.tickerId)
 
            if tt.getField(msg.field) == "askOptComp" or \
                                    tt.getField(msg.field) == "bidOptComp" or \
                                    tt.getField(msg.field) == "modelOptComp":
                field = "bid" if tt.getField(msg.field) == "bidOptComp" else \
                    "ask" if tt.getField(msg.field) == "askOptComp" else "last"
 
                OPTIONS.loc[str(msg.tickerId), '%s_impliedVol' % field] = \
                                                                msg.impliedVol
                OPTIONS.loc[str(msg.tickerId), '%s_delta' % field] = msg.delta
                OPTIONS.loc[str(msg.tickerId), '%s_gamma' % field] = msg.gamma
                OPTIONS.loc[str(msg.tickerId), '%s_theta' % field] = msg.theta
                OPTIONS.loc[str(msg.tickerId), '%s_vega' % field] = msg.vega
                OPTIONS.loc[str(msg.tickerId), '%s_optPrice' % field] = \
                                                                    msg.optPrice
                OPTIONS.loc[str(msg.tickerId), '%s_undPrice' % field] = \
                                                                    msg.undPrice
        elif msg.typeName == "historicalData":
            if ('finished' in str(msg.date)) == False:
                addentry = True
                entrydate = int(msg.date) * 1000
 
                if self.latestdate and entrydate < self.latestdate:
                    addentry = False
 
                if addentry:
                    dataStr = [entrydate, msg.open, msg.high, msg.low, \
                                                                    msg.close]
                    self.NEWDATALIST = self.NEWDATALIST + [dataStr]
 
                    volStr = [entrydate, msg.volume]
                    self.NEWVOLUMELIST = self.NEWVOLUMELIST + [volStr]
 
    def reqHistoricalData(self, contract, interval, connection, timeframe, \
                                                            latestdate=None):
        self.NEWDATALIST = []
        self.NEWVOLUMELIST = []
        self.latestdate = latestdate
 
        connection.reqHistoricalData(0, contract, '', timeframe, interval, \
                                                                'TRADES', 0, 2)
        sleep(3)
 
        return [self.NEWDATALIST, self.NEWVOLUMELIST]
 
class IBHandler(object):
    """ Standard IB wrapper to have a single entry point """
    def __init__(self):
        self.ibhndl = ReferenceApp()
        self.slack = Slacker('')

    def request_market_data(self, timeframe, interval, symbol, sectype, \
                                        exchange, currency=None, expiry=None, \
                                        primexch=None, latestdate=None):
        # Establish a connection
        sys.stdout.write("\nCalling connection\n")
        connection = ibConnection()
        connection.register(self.ibhndl.my_callback_handler, \
                                                        message.historicalData)
        connection.connect()
 
        #Contract
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sectype
        contract.m_exchange = exchange
        contract.m_currency = currency
 
        if primexch:
            contract.m_primaryExch = primexch
 
        if expiry:
            contract.m_expiry = expiry
 
        # Get historical data
        rtnData = self.ibhndl.reqHistoricalData(contract, interval, connection,\
                                                        timeframe, latestdate)
        connection.disconnect()
 
        if not rtnData[0]:
            sys.stderr.write("ERROR: No data return for %s : %s\n" % (symbol,\
                                                                    interval)) 

        return rtnData
 
    def data_mining_function(self):
        #Check to see if historical directory exists
        mainDirectory = "historical_data"
        if not os.path.exists(mainDirectory):
            os.makedirs(mainDirectory)
 
        with open('stocks.txt') as data_file:
            stocks = json.load(data_file)
 
        while True:           
            for slimit in SCHEDULELIMIT:
                for stock in stocks:
                    sys.stdout.write("\n******* Retrieving %s: %s *******\n" % \
                                                (str(stock["symbol"]), slimit))
 
                    entrystockname = os.path.join(mainDirectory, \
                                                        str(stock["symbol"]))
                    if not os.path.exists(entrystockname):
                        os.makedirs(entrystockname)
 
                    if "primaryexch" in stock:
                        primaryexch = str(stock["primaryexch"])
                    else:
                        primaryexch = None
 
                    if "expiry" in stock:
                        expiry = str(stock["expiry"])
                    else:
                        expiry = None
 
                    dataentry = self.request_market_data(slimit[0], \
                             slimit[1], str(stock["symbol"]), \
                             str(stock["sectype"]), str(stock["exchange"]), \
                             str(stock["currency"]), expiry, primaryexch)
 
                    if dataentry and dataentry[0]:
                        datafolder = os.path.join(entrystockname, \
                                  datetime.datetime.now().strftime('%Y-%m-%d'))
                        if not os.path.exists(datafolder):
                            os.makedirs(datafolder)
 
                        saveloc = os.path.join(datafolder, slimit[1] + ".json")
                        with open(saveloc, 'w') as outfile:
                            json.dump(dataentry, outfile)
 
                        if not os.path.isfile(saveloc):
                            sys.stderr.write("ERROR: File %s wasn't created\n."\
                                                                    % saveloc)
                            sys.exit(0)

                        # check if time is within stock hours
                        if not self.checkcurrenttime():
                            sys.stdout.write("\nOutside of stock working " \
                                                                    "hours.\n")
                        else:
                            # create picture from stock data
                            for xint in range(0, 2):
                                SGFOBJ = StockGraphFunctions()
                                imageloc = SGFOBJ.graphData(slimit[1], \
                                            str(stock["symbol"]), xint in [1])
         
                                if imageloc:
                                    # send picture
                                    if not xint in [1]:
                                        self.slack.chat.post_message('#trends',\
                                            'New stock trend found! Current ' \
                                            'price ' + str(dataentry[0][-1]\
                                                            [4]), as_user=True)
                                        self.slack.chat.post_message('#trends',\
                                                'Subset of last 60~ minutes', \
                                                                as_user=True)
                                    else:
                                        self.slack.chat.post_message('#trends',\
                                            'Full day of data', as_user=True)
        
                                    url = 'https://slack.com/api/files.upload'
                                    files = {'file': open(imageloc, 'rb')}
                                    values = {'channels': '#trends',
                                          'token': ''}
                                    requests.post(url, files=files, data=values)

                    sys.stdout.write("Sleeping for 60 seconds...\n")
                    time.sleep(60)

    def checkcurrenttime(self):
        now = datetime.datetime.now()
        now_time = now.time()

        if datetime.time(8,30) <= now.time() <= datetime.time(15,00):        
            return True

        return False

