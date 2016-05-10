""" Interactive Broker Handler """
import os
import sys
import json
import time
import sqlite3
import datetime
import pandas as pd
from patternsdb import *

import numpy as np
import matplotlib.dates as mdates
from time import sleep, strftime, localtime
from stock_graph_handler import StockGraphFunctions
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from ib.ext.TickType import TickType as tt
from telegrambot import SimpleTelegramBot

OPTIONS = pd.DataFrame(columns=["ask", "ask_delta", "ask_gamma", \
              "ask_impliedVol", "ask_optPrice", "ask_pvDividend", "ask_theta", \
              "ask_undPrice", "ask_vega", "bid", "bid_delta", "bid_gamma", \
              "bid_impliedVol", "bid_optPrice", "bid_pvDividend", "bid_theta", \
              "bid_undPrice", "bid_vega", "close", "last_delta", "last_delta", \
              "last_gamma", "last_impliedVol", "last_optPrice", \
              "last_pvDividend", "last_theta", "last_undPrice", "m_conId", \
              "m_currency", "m_exchange", "m_expiry", "m_localSymbol", \
              "m_multiplier", "m_right", "m_secType", "m_strike", "m_symbol"])

SCHEDULELIMIT = [("1 d", "1 min"), \
                 ("1 w", "3 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "5 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "10 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "3 mins"), \
                 ("1 d", "1 min"), \
                 ("2 w", "15 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "3 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "5 mins"), \
                 ("1 d", "1 min"), \
                 ("2 w", "20 mins"), \
                 ("1 d", "1 min"), \
                 ("1 w", "3 mins"), \
                 ("1 d", "1 min"), \
                 ("1 m", "30 mins")]

# SCHEDULELIMIT = [("1 w", "5 mins")]


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

    def get_contract_details(self, connection, reqid, contract_values):
        """ IB function to retrieve contract details """
        sys.stdout.write("Calling Contract Details\n")

        # Contract creation
        contract = Contract()
        contract.m_symbol = contract_values.m_symbol
        contract.m_exchange = contract_values.m_exchange
        contract.m_secType = contract_values.m_secType

        # If expiry is empty it will download all available expiries
        if contract_values.m_expiry <> "":
            contract.m_expiry = contract_values.m_expiry

        connection.reqContractDetails(reqid, contract)
        sleep(20)

    def get_market_data(self, connection):
        """ IB function to retrieve market data per contract """
        sys.stdout.write("Calling Market Data\n")

        # Loop through all options contracts
        for _, option in OPTIONS.iterrows():
            contract_values = Contract()
            contract_values.m_symbol = option['m_symbol']
            contract_values.m_localSymbol = option['m_localSymbol']
            contract_values.m_exchange = "SMART"
            contract_values.m_currency = "USD"
            contract_values.m_secType = "OPT"
            contract_values.m_multiplier = option['m_expiry']
            contract_values.m_expiry = option['m_expiry']
            contract_values.m_strike = option['m_strike']
            contract_values.m_right = option['m_right']
            contract_values.m_conId = option['m_conId']

            connection.reqMktData(str(option['m_conId']), \
                                                    contract_values, "", True)
            sleep(1)

        sleep(30)

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
        self.telecobj = SimpleTelegramBot()
        self.MSGDB = []

    def generate_spx(self, symbol="SPX", exchange="SMART", currency="USD", \
                                            secType="OPT", expiry="20151023",
                                            strikep=None):
        """ Function to resemble a main function """
        # Establish a connection
        sys.stdout.write("\nCalling connection\n")
        connection = ibConnection()
        connection.registerAll(self.ibhndl.my_callback_handler)
        connection.connect()

        # Get contract details
        contract_values = Contract()
        contract_values.m_symbol = symbol
        contract_values.m_exchange = exchange
        contract_values.m_currency = currency
        contract_values.m_secType = secType
        contract_values.m_expiry = expiry
        
        if strikep:
            contract_values.m_strike = strikep

        self.ibhndl.get_contract_details(connection, 1, contract_values)

        # Get Market values
        self.ibhndl.get_market_data(connection)

        if not os.path.isdir(os.path.join('.', 'spx_files')):
            os.makedirs('spx_files')

        mydir = os.path.join(os.getcwd(), 'spx_files', \
                         datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(mydir)

        OPTIONS.to_csv(os.path.join(mydir, 'Options.csv'))
        sys.stdout.write("\n\n")

    def request_market_data(self, timeframe, interval, symbol, sectype, \
                                        exchange, currency=None, expiry=None, \
                                        primexch=None, latestdate=None, \
                                        enhanced=None, bot=False):
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
            if not bot:
                return rtnData
            else:
                return rtnData, ""

        if enhanced:
            dateList = list()
            stockFile = list()
            for data, volume in zip(rtnData[0], rtnData[1]):
                dateList = dateList + [data[0]]
                dataStr = '%s, %s, %s, %s, %s, %s' % \
                            (strftime("%Y-%m-%d %H:%M:%S", \
                                  localtime(int(str(data[0]))/1000)), data[1], \
                                  data[2], data[3], data[4], str(volume[1]))

                stockFile = stockFile + [dataStr]

            convertStr = '%Y-%m-%d %H:%M:%S'
            date, openp, highp, lowp, closep, volume = \
                            np.loadtxt(stockFile, delimiter=',', unpack=True, \
                           converters={0:mdates.strpdate2num(convertStr)})

            #RIS function
            SGFOBJ = StockGraphFunctions()
            RSIGRAPH = SGFOBJ.rsiFunc(closep)

            x = 0
            RSILIST = []

            try:
                while x < len(RSIGRAPH):
                    entry = [dateList[x], RSIGRAPH[x]]
                    RSILIST = RSILIST + [entry]
                    x += 1
            except Exception, excp:
                sys.stderr.write("ERROR: RSILIST failed with exception %s\n" % \
                                                                        excp)

            rtnData.append(RSILIST)

            #ADX function
            x = 0
            ADXREAL = []
            ADXPOS = []
            ADXNEG = []

            try:
                adxdate, adxreal, adxposi, adxnegi = \
                                SGFOBJ.ADX(dateList, closep, highp, lowp, openp)

                while x < len(adxdate):
                    entry = [adxdate[x], adxreal[x]]
                    ADXREAL = ADXREAL + [entry]

                    entry = [adxdate[x], adxposi[x]]
                    ADXPOS = ADXPOS + [entry]

                    entry = [adxdate[x], adxnegi[x]]
                    ADXNEG = ADXNEG + [entry]
                    x += 1
            except Exception, excp:
                sys.stderr.write("ERROR: rsiFunc failed with exception %s\n" % \
                                                                        excp)

            rtnData.append(ADXREAL)
            rtnData.append(ADXPOS)
            rtnData.append(ADXNEG)

            try:
                #TRENDLINES functions
                TRENDLINES = SGFOBJ.segtrends(closep, dateList, segments=2)
                for item in TRENDLINES:
                    rtnData.append(item)
            except Exception, excp:
                sys.stderr.write("ERROR: TRENDLINES failed with exception " \
                                                                "%s\n" % excp)

            #PATTERNS
            retpat = []
            try:
                patterndb = PatternDB()
                patterndb.add(HS())
                patterndb.add(IHS())

                #if len(closep) >= 60:
                    #retpat = patterndb.check(closep[-60:], date[-60:])
                #else:
                retpat = patterndb.check(closep, date)
    
                if retpat:
                    rtnData.append({"Patterns": retpat})
            except Exception, excp:
                sys.stderr.write("ERROR: PATTERNS failed with exception " \
                                                                "%s\n" % excp)

        if not bot:
            return rtnData
        else:
            return rtnData, retpat

    def data_mining_function(self):
        #Check to see if historical directory exists
        mainDirectory = "historical_data"
        if not os.path.exists(mainDirectory):
            os.makedirs(mainDirectory)

        with open('stocks.txt') as data_file:
            stocks = json.load(data_file)

        while 1:
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

                    dataentry, retpat = self.request_market_data(slimit[0], \
                             slimit[1], str(stock["symbol"]), \
                             str(stock["sectype"]), str(stock["exchange"]), \
                             str(stock["currency"]), expiry, primaryexch, \
                             enhanced=True, bot=True)

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
                        elif retpat:
                            #Create picture
                            SGFOBJ = StockGraphFunctions()
                            imageloc = SGFOBJ.graphData(15, 40, \
                                                interval=slimit[1], \
                                                symbol=str(stock["symbol"]), \
                                                bot=True, botData=retpat)
            
                            msgid = retpat[0]["ixd"]
                            if not msgid in self.MSGDB:
                                #Send picture
                                self.telecobj.sendmsg(text = "New pattern " \
                                            "found %s for stock/interval: " \
                                            "%s:%s" % (retpat[0]["name"], \
                                               str(stock["symbol"]), \
                                               slimit[1]), filename=imageloc)
                                self.MSGDB.append(msgid[:5])
                            else:
                                sys.stdout.write("\n******* Chart Pattern " \
                                                    "already sent *******\n")
#                 time.sleep(60)

    def get_http_response(self, interval, symbol):
        response = ""
        datafile = os.path.join("historical_data", symbol, \
                              datetime.datetime.now().strftime('%Y-%m-%d'), \
                              interval + ".json")

        if os.path.exists(datafile):
            with open(datafile) as data_file:
                response = json.load(data_file)

            if not len(response[0]):
                sys.stderr.write("ERROR: no data found in file %s.\n" % \
                                                                    datafile)
                response = ""
        else:
            sys.stderr.write("ERROR: file %s was not found.\n" % datafile)

        return response

    def get_http_update_response(self, interval, symbol, timeframe):
        response = ""
        datafile = os.path.join("historical_data", symbol, \
                              datetime.datetime.now().strftime('%Y-%m-%d'), \
                              interval + ".json")

        if os.path.exists(datafile):
            with open(datafile) as data_file:
                response = json.load(data_file)

            if not len(response[0]):
                sys.stderr.write("ERROR: no data found in file %s.\n" % \
                                                                    datafile)
                response = ""
        else:
            sys.stderr.write("ERROR: file %s was not found.\n" % datafile)

        #ADD UPDATE CODE HERE

        return response


