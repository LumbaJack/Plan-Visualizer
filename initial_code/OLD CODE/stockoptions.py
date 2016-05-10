""" Stock Options """
import os
import sys
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from pushbullet import Pushbullet
from interactivebroker import IBHandler
from csv_handler import StrategyFuntions
from stock_graph_handler import StockGraphFunctions
  
TIMEFRAME = None
INSTRUMENT = None
LIVEFIGURE = None
  
def animate(i):
    SGFOBJ = StockGraphFunctions()
    sendNoti = SGFOBJ.graphData(10, 50, timeframe=TIMEFRAME, live=True)

    mydir = os.path.join(os.getcwd(), 'live_trading_captures', \
             datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(mydir)
     
    outputpath = os.path.join(mydir, 'example.png')
    LIVEFIGURE.savefig(outputpath, facecolor=LIVEFIGURE.get_facecolor())
     
#     if sendNoti:
#         pb = Pushbullet('')
#         with open(outputpath, "rb") as pic:
#             file_data = pb.upload_file(pic, "alert.jpg")
#            
#         pb.push_file(**file_data)

if __name__ == '__main__':
    while True:
        OPTION = raw_input(\
                           "---------- GRAPHING TOOLS ----------\n\n" \
                           "1: Generate SPX Options file\n" \
                           "2: Live graph the current stock\n\n" \
                           "---------- STRATEGY GENERATOR TOOLS ----------\n\n" \
                           "3: Generate PUT spread individual options\n" \
                           "4: Generate CALL spread individual options\n" \
                           "5: Generate PUT spread combination options\n" \
                           "6: Generate CALL spread combination options\n\n" \
                           "---------- PROGRAM TOOLS ----------\n\n" \
                           "0: Exit the program\n" \
                           "\nEnter one of the options: ")

        if OPTION == "1":            
            sys.stdout.write("\nPress enter to use the default values.\n")
            symbol = raw_input("Enter the symbol to look up (default: SPX):") \
                                                                        or "SPX"
            exchange = raw_input("Enter the exchange to use (default: " \
                                                        "SMART):") or "SMART"
            currency = raw_input("Enter the currency to look up (default: " \
                                                            "USD):") or "USD"
            secType = raw_input("Enter the section type to look up (default: " \
                                                            "OPT):") or "OPT"
            expiry = raw_input("Enter the expiration to look up (NO DEFAULT," \
                                                        " format: 20150925): ")
            
            if not expiry:
                sys.stderr.write("An expiration date must be entered.\n\n")
            else:
                IBH = IBHandler()
                IBH.generate_spx(symbol, exchange, currency, secType, expiry)
        elif OPTION  == "2":
            sys.stdout.write("\nPress enter to use the default values.\n")

            TIMEFRAME = raw_input('Time frame to plot in days/months ' \
                                    '(default=1 D, example=12 M:): ') or "1 D"

            LIVEFIGURE = plt.figure(facecolor='#07000d')
            while True:
                LIVEFIGURE.clear()
                ani = animation.FuncAnimation(LIVEFIGURE, animate, \
                                                                interval=60000)
                plt.show()
 
            sys.stdout.write("\n")
        elif OPTION in ["3", "4", "5", "6"]:
            try:
                SOBJ = StrategyFuntions()
            except Exception, excp:
                continue
 
            sys.stdout.write("\nPress enter to use the default values.\n")
            POPERC = raw_input("Enter minimum probability of profit " \
                                            "(default value 70 = 70%):") or "70"
            MPGAIN = raw_input("Enter minimum profit in percentage " \
                                        "(default value:0.05 = 5%):") or "0.05"
            if OPTION in ["5", "6"]:
                INV_AMNT = raw_input("Enter your investment amount (" \
                                       "default value:2000 = $2000):") or "2000"
 
            if OPTION == "3":
                SOBJ.generate_put_options(POPERC, MPGAIN)
            elif OPTION == "4":
                SOBJ.generate_call_options(POPERC, MPGAIN)
            elif OPTION == "5":
                SOBJ.generate_combo_put_options(POPERC, MPGAIN, INV_AMNT)
            elif OPTION == "6":
                SOBJ.generate_combo_call_options(POPERC, MPGAIN, INV_AMNT)
        else:
            sys.stdout.write("Exiting program...")
            break

