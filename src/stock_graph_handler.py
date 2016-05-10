import os
import sys
import time
import json
import pytz
import pylab
import calendar
import datetime
import traceback
import matplotlib
 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

from datetime import date
from time import strftime, localtime
from matplotlib.finance import candlestick

matplotlib.rcParams.update({'font.size': 9})
 
class StockGraphFunctions():
    def __init__(self):
        self.MA_NOTIFICATION = False
        self.MEAN_NOTIFICATION = False
        self.TREND_NOTIFICATION = False
        self.SECTIME = calendar.timegm(time.gmtime()) * 1000
 
    def rsiFunc(self, closep, n=14):
        try:
            deltas = np.diff(closep)
            seed = deltas[:n+1]
            up = seed[seed>=0].sum()/n
            down = -seed[seed<0].sum()/n
     
            if not down == 0:
                rs = up/down
            else:
                rs = 0
     
            rsi = np.zeros_like(closep)
            rsi[:n] = 100. - 100./(1.+rs)
          
            for i in range(n, len(closep)):
                delta = deltas[i-1] # cause the diff is 1 shorter
          
                if delta>0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta
          
                up = (up*(n-1) + upval)/n
                down = (down*(n-1) + downval)/n
          
                if not down == 0:
                    rs = up/down
                else:
                    rs = 0
                rsi[i] = 100. - 100./(1.+rs)
        except Exception, excp:
            sys.stderr.write("ERROR: rsiFunc failed with exception %s\n" % excp)
            rsi = np.zeros_like(closep)
      
        return rsi
 
    def TR(self, date, close, high, low, yestclose):
        x = high - low
        y = abs(high - yestclose)
        z = abs(low - yestclose)
         
        if y <= x >= z:
            TR = x
        elif x <= y >= z:
            TR = y
        elif x <= z >= y:
            TR = z
 
        return date, TR
 
    def DM(self, date , high, low, close, yestopen, yesthigh, \
                                                            yestlow, yestclose):
        moveUp = high - yesthigh
        moveDown = yestlow - low
         
        if 0 < moveUp > moveDown:
            PDM = moveUp
        else:
            PDM = 0
 
        if 0 < moveDown > moveUp:
            NDM = moveDown
        else:
            NDM = 0
         
        return date, PDM, NDM
 
    def calcDIs(self, date, closep, highp, lowp, openp):
        x = 1
        TRDates = []
        TrueRanges = []
        PosDMs = []
        NegDMs = []
         
        while x < len(date):
            TRDate, TrueRange = self.TR(date[x], closep[x], highp[x], lowp[x], \
                                                                    closep[x-1])
            TRDates.append(TRDate)
            TrueRanges.append(TrueRange)
 
            _, PosDM, NegDM = self.DM(date[x], highp[x], lowp[x], closep[x], \
                              openp[x-1], highp[x-1], lowp[x-1], closep[x-1])
 
            PosDMs.append(PosDM)
            NegDMs.append(NegDM)
             
            x += 1
         
        expPosDM = self.ExpMovingAverage(PosDMs, 14)
        expNegDM = self.ExpMovingAverage(NegDMs, 14)
        ATR = self.ExpMovingAverage(TrueRanges, 14)
         
        xx = 0
        PDIs = []
        NDIs = []
         
        while xx < len(ATR):
            if not ATR[xx] == 0:
                PDI = 100 * (expPosDM[xx] / ATR[xx])
            else:
                PDI = 0
 
            PDIs.append(PDI)
             
            if not ATR[xx] == 0:
                NDI = 100 * (expNegDM[xx] / ATR[xx])
            else:
                NDI = 0
 
            NDIs.append(NDI)
             
            xx += 1
         
        return PDIs, NDIs
 
    def ADX(self, date, closep, highp, lowp, openp, ax2=None, SP=None, \
                                                                    plt=None):
        PositiveDI, NegativeDI = self.calcDIs(date, closep, highp, lowp, openp)
        
        yy = 0
        DXs = []
         
        while yy < len(date[1:]):
            if not (PositiveDI[yy] + NegativeDI[yy]) == 0:
                DX = 100 * ((abs(PositiveDI[yy] - NegativeDI[yy]) / \
                                            (PositiveDI[yy] + NegativeDI[yy])))
            else:
                DX = 0
             
            DXs.append(DX)
            yy += 1
         
        try:
            ADX = self.ExpMovingAverage(DXs, 14)
        except Exception, excp:
            sys.stderr.write("ERROR: ADX (EMA) failed with exception %s\n" % \
                                                                        excp)
            ADX = []
 
        plotDate = date[1:] 
         
        if ax2:
            ax2.plot(plotDate[-SP:], ADX[-SP:], 'w')
            ax2.plot(plotDate[-SP:], PositiveDI[-SP:], 'g')
            ax2.plot(plotDate[-SP:], NegativeDI[-SP:], 'r')
            plt.ylabel('ADX(14)', color='w')
        else:
            return plotDate, ADX, PositiveDI, NegativeDI
 
    def movingaverage(self, values, window):
        weigths = np.repeat(1.0, window)/window
        smas = np.convolve(values, weigths, 'valid')
        return smas # as a numpy array
      
    def ExpMovingAverage(self, values, window):
        weights = np.exp(np.linspace(-1., 0., window))
        weights /= weights.sum()
        a =  np.convolve(values, weights, mode='full')[:len(values)]
        a[:window] = a[window]
        return a
 
    def check_for_ma_alerts(self, date, ma1, ma2, ma3, plotEnt, symbol, \
                                                                    dataset):
        idx = np.argwhere(np.isclose(ma1, ma2, atol=.1)).reshape(-1)
        idx2 = np.argwhere(np.isclose(ma1, ma3, atol=.1)).reshape(-1)
        idx3 = np.argwhere(np.isclose(ma2, ma3, atol=.1)).reshape(-1)
        
        idx = np.concatenate((idx, idx2))
        idx = np.concatenate((idx, idx3))

        plotEnt.plot(date[idx], ma1[idx], 'bo', markersize=7)
         
        if (self.check_for_notification_alert(date[idx[-1:]])):
            self.MA_NOTIFICATION = True
            datafile = os.path.join("live_trading_captures", symbol, \
                                datetime.datetime.now().strftime('%Y-%m-%d'), \
                                                        dataset, "movingavg")
            if not os.path.isdir(datafile):
                os.makedirs(datafile)

            filehand = open(os.path.join(datafile, \
                                            str(self.SECTIME) + ".json"), 'w')
            data = {}
            data[str(date[idx[-1:]][0])] = str(entry1[idx[-1:]][0])
            json_data = json.dumps(data)

            filehand.write(json_data)
            filehand.close()
        
            plotEnt.annotate('MA Marker',(date[idx[-1:]], ma1[idx[-1:]]),
                    xytext=(0.8, 0.9), textcoords='axes fraction',
                    arrowprops=dict(facecolor='blue', shrink=0.05),
                    fontsize=14, color = 'b',
                    horizontalalignment='right', verticalalignment='bottom')
 
    def computeMACD(self, x, slow=26, fast=12):
        """
        compute the MACD (Moving Average Convergence/Divergence) using
        a fast and slow exponential moving avg return value is emaslow,
        emafast, macd which are len(x) arrays
        """
        emaslow = self.ExpMovingAverage(x, slow)
        emafast = self.ExpMovingAverage(x, fast)
        return emaslow, emafast, emafast - emaslow
  
    def segtrends(self, data, dates, plotEnt=None, SP=None, segments=2, \
                                                    symbol=None, dataset=None):
        """
        Turn minitrends to iterative process more easily adaptable to
        implementation in simple trading systems; allows backtesting functionality.
      
        :param x: One-dimensional data set
        :param window: How long the trendlines should be. If window < 1, then it
                       will be taken as a percentage of the size of the data
        """
        templist = list()
        trendslist = list()
        entries = np.array(data)
      
        # Implement trendlines
        segments = int(segments)
        maxima = np.ones(segments)
        minima = np.ones(segments)
        segsize = int(len(entries)/segments)
        for i in range(1, segments+1):
            ind2 = i*segsize
            ind1 = ind2 - segsize
            maxima[i-1] = max(entries[ind1:ind2])
            minima[i-1] = min(entries[ind1:ind2])
      
        # Find the indexes of these maxima in the data
        x_maxima = np.ones(segments)
        x_minima = np.ones(segments)
        for i in range(0, segments):
            x_maxima[i] = np.where(entries == maxima[i])[0][0]
            x_minima[i] = np.where(entries == minima[i])[0][0]
      
        for i in range(0, segments-1):
            if not (maxima[i+1] - maxima[i]) == 0:
                maxslope = (maxima[i+1] - maxima[i]) / (x_maxima[i+1] - \
                                                                    x_maxima[i])
            else:
                maxslope = 0
 
            a_max = maxima[i] - (maxslope * x_maxima[i])
            b_max = maxima[i] + (maxslope * (len(entries) - x_maxima[i]))
            maxline = np.linspace(a_max, b_max, len(entries))
      
            if not (x_minima[i+1] - x_minima[i]) == 0:
                minslope = (minima[i+1] - minima[i]) / (x_minima[i+1] - \
                                                                    x_minima[i])
            else:
                minslope = 0
 
            a_min = minima[i] - (minslope * x_minima[i])
            b_min = minima[i] + (minslope * (len(entries) - x_minima[i]))
            minline = np.linspace(a_min, b_min, len(entries))
      
            if plotEnt:
                plotEnt.plot(dates[-SP:], maxline[-SP:], 'b', \
                                            label="Resistance", linewidth=1.5)
                self.check_for_trend_alerts(dates[-SP:], maxline[-SP:], \
                                        data[-SP:], plotEnt, symbol, dataset)
      
                plotEnt.plot(dates[-SP:], minline[-SP:], 'r', label="Support", \
                                                                linewidth=1.5)
                self.check_for_trend_alerts(dates[-SP:], minline[-SP:], \
                                        data[-SP:], plotEnt, symbol, dataset)
            else:
                for date, maxval in zip(dates, maxline):
                    maxlist = [date, maxval]
                    templist = templist + [maxlist]
                trendslist.append(templist)
                 
                templist = list()
                for date, minval in zip(dates, minline):
                    maxlist = [date, minval]
                    templist = templist + [maxlist]
                trendslist.append(templist)
 
        if not plotEnt:
            return trendslist
 
    def check_for_trend_alerts(self, date, entry1, entry2, plotEnt, symbol, \
                                                                    dataset):
        idx = np.argwhere(np.isclose(entry1, entry2, atol=.1)).reshape(-1)
        plotEnt.plot(date[idx], entry1[idx], 'w^', markersize=7)
         
        if (self.check_for_notification_alert(date[idx[-1:]])):
            self.TREND_NOTIFICATION = True
            datafile = os.path.join("live_trading_captures", symbol, \
                                datetime.datetime.now().strftime('%Y-%m-%d'), \
                                                            dataset, "trend")
            if not os.path.isdir(datafile):
                os.makedirs(datafile)

            filehand = open(os.path.join(datafile, \
                                            str(self.SECTIME) + ".json"), 'w')
            data = {}
            data[str(date[idx[-1:]][0])] = str(entry1[idx[-1:]][0])
            json_data = json.dumps(data)

            filehand.write(json_data)
            filehand.close()

            plotEnt.annotate('Trend Marker',(date[idx[-1:]],entry1[idx[-1:]]),
                    xytext=(0.7, 0.8), textcoords='axes fraction',
                    arrowprops=dict(facecolor='white', shrink=0.05),
                    fontsize=14, color = 'w',
                    horizontalalignment='right', verticalalignment='bottom')
 
    def mean_population(self, data, dates, plotEnt, SP):       
        A = np.array([dates, np.ones(len(dates))])
  
        # linearly generated sequence
        w = np.linalg.lstsq(A.T, data)[0] # obtaining the parameters
          
        # plotting the line
        line = w[0] * dates + w[1] # regression line
  
        plotEnt.plot(dates[-SP:], line[-SP:], 'w', ls='--', \
                                        label="Regression Line", linewidth=2.0)
#         self.check_for_mean_alerts(dates[-SP:], line[-SP:], data[-SP:], plotEnt)
 
    def check_for_mean_alerts(self, date, entry1, entry2, plotEnt, symbol, \
                                                                    dataset):
        idx = np.argwhere(np.isclose(entry1, entry2, atol=.1)).reshape(-1)
        plotEnt.plot(date[idx], entry1[idx], 'ro', markersize=7)
 
        if (self.check_for_notification_alert(date[idx[-1:]])):
            self.MEAN_NOTIFICATION = True
            datafile = os.path.join("live_trading_captures", symbol, \
                                datetime.datetime.now().strftime('%Y-%m-%d'), \
                                                            dataset, "mean")
            if not os.path.isdir(datafile):
                os.makedirs(datafile)

            filehand = open(os.path.join(datafile, \
                                            str(self.SECTIME) + ".json"), 'w')
            data = {}
            data[str(date[idx[-1:]][0])] = str(entry1[idx[-1:]][0])
            json_data = json.dumps(data)

            filehand.write(json_data)
            filehand.close()
            plotEnt.annotate('Mean Marker',(date[idx[-1:]],entry1[idx[-1:]]),
                    xytext=(0.75, 0.85), textcoords='axes fraction',
                    arrowprops=dict(facecolor='red', shrink=0.05),
                    fontsize=14, color = 'r',
                    horizontalalignment='right', verticalalignment='bottom')
 
    def check_for_notification_alert(self, date):
        if date:
            x = ({0:mdates.num2date(date)}[0][0]).replace(tzinfo=pytz.UTC)      
            timesince = datetime.datetime.now().replace(tzinfo=pytz.UTC) - x
            minutessince = int(timesince.total_seconds() / 60)

            if minutessince in [4, 3, 2, 1, 0]:
                return True
 
        return False
 
    def get_data_response(self, interval, symbol):
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

    def graphData(self, interval, symbol, fullset):
        ''' Use this to dynamically pull a stock '''
        (MA1, MA2, MA3) = (10, 20, 40)
        stockFile = list()

        initInput = self.get_data_response(interval, symbol)
        
        if not initInput and len(initInput) < 100:
            return None

        if fullset:
            subdir = "fullset"
            datainput = initInput[0]
            volumeinput = initInput[1]
        else:
            subdir = "subset"
            datainput = initInput[0][-100:]
            volumeinput = initInput[1][-100:]

        for data, volume in zip(datainput, volumeinput):
            dataStr = '%s, %s, %s, %s, %s, %s' % \
                        (strftime("%Y-%m-%d %H:%M:%S", \
                                  localtime(int(str(data[0]))/1000)), data[1], \
                                  data[2], data[3], data[4], str(volume[1]))
 
            stockFile = stockFile + [dataStr]
 
        try:
            convertStr = '%Y-%m-%d %H:%M:%S'
            date, openp, highp, lowp, closep, volume = \
                            np.loadtxt(stockFile, delimiter=',', unpack=True, \
                           converters={0:mdates.strpdate2num(convertStr)})
 
            x = 0
            y = len(date)
            newAr = []
 
            while x < y:
                appendLine = date[x], openp[x], closep[x], highp[x], lowp[x], \
                                                                    volume[x]
                newAr.append(appendLine)
                x+=1

                 
            Av1 = self.movingaverage(closep, MA1)
            Av2 = self.movingaverage(closep, MA2)  
            Av3 = self.movingaverage(closep, MA3)        
     
            SP = len(date[MA3-1:])
                 
            fig = plt.figure(facecolor='#07000d')
            ax1 = plt.subplot2grid((6,4), (1,0), rowspan=4, colspan=4, \
                                                            axisbg='#07000d')

            canWidth = 0.0005
            candlestick(ax1, newAr[-SP:], width=canWidth, colorup='#53c156', \
                                                            colordown='#ff1717')
     
            Label1 = str(MA1)+' SMA'
            Label2 = str(MA2)+' SMA'
            Label3 = str(MA3)+' SMA'
      
            if len(date[-SP:]) == len(Av1[-SP:]):
                ax1.plot(date[-SP:],Av1[-SP:],'c',label=Label1, linewidth=1.5)
   
            if len(date[-SP:]) == len(Av2[-SP:]):
                ax1.plot(date[-SP:],Av2[-SP:],'y',label=Label2, linewidth=1.5)
            
            if len(date[-SP:]) == len(Av3[-SP:]):
                ax1.plot(date[-SP:],Av3[-SP:],'y',label=Label3, linewidth=1.5)

#             if len(date[-SP:]) == len(Av1[-SP:]) and \
#                                         len(date[-SP:]) == len(Av2[-SP:]) and \
#                                         len(date[-SP:]) == len(Av3[-SP:]):
#                 self.check_for_ma_alerts(date[-SP:], Av1[-SP:], Av2[-SP:], \
#                                                                 Av3[-SP:], ax1)

            self.segtrends(closep[-SP:], date[-SP:], ax1, SP, segments=2, \
                                                symbol=symbol, dataset=subdir)
            self.mean_population(closep[-SP:], date[-SP:], ax1, SP)
              
            ax1.grid(True, color='w')
            ax1.xaxis.set_major_locator(mticker.MaxNLocator(20))
            ax1.xaxis.set_major_formatter(mdates.\
                                                DateFormatter('%m-%d %H:%M:%S'))
            ax1.yaxis.label.set_color("w")
            ax1.spines['bottom'].set_color("#5998ff")
            ax1.spines['top'].set_color("#5998ff")
            ax1.spines['left'].set_color("#5998ff")
            ax1.spines['right'].set_color("#5998ff")
            ax1.tick_params(axis='y', colors='w')
            plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(\
                                                              prune='upper'))
            ax1.yaxis.set_major_formatter(matplotlib.ticker.\
                                                    FormatStrFormatter("%.1f"))
            ax1.tick_params(axis='x', colors='w')
            plt.ylabel('Stock price and Volume')
      
            maLeg = plt.legend(loc=9, ncol=2, prop={'size':7},
                                                fancybox=True, borderaxespad=0.)
            maLeg.get_frame().set_alpha(0.4)
            textEd = pylab.gca().get_legend().get_texts()
            pylab.setp(textEd[0:5], color = 'w')
              
            ax0 = plt.subplot2grid((6,4), (0,0), sharex=ax1, rowspan=1, \
                                                    colspan=4, axisbg='#07000d')
  
            rsi = self.rsiFunc(closep)
            rsiCol = '#c1f9f7'
            posCol = '#386d13'
            negCol = '#8f2020'
              
            ax0.plot(date[-SP:], rsi[-SP:], rsiCol, linewidth=1.5)
            ax0.axhline(70, color=negCol)
            ax0.axhline(30, color=posCol)
  
            ax0.fill_between(date[-SP:], rsi[-SP:], 70, where=(rsi[-SP:]>=70), \
                                facecolor=negCol, edgecolor=negCol, alpha=0.5)
            ax0.fill_between(date[-SP:], rsi[-SP:], 30, where=(rsi[-SP:]<=30), \
                                facecolor=posCol, edgecolor=posCol, alpha=0.5)
  
            ax0.set_yticks([30,70])
            ax0.yaxis.label.set_color("w")
            ax0.spines['bottom'].set_color("#5998ff")
            ax0.spines['top'].set_color("#5998ff")
            ax0.spines['left'].set_color("#5998ff")
            ax0.spines['right'].set_color("#5998ff")
            ax0.tick_params(axis='y', colors='w')
            ax0.tick_params(axis='x', colors='w')
            plt.ylabel('RSI')

            volumeMin = 0
            ax1v = ax1.twinx()
            ax1v.fill_between(date[-SP:],volumeMin, volume[-SP:], \
                                                facecolor='#00ffe8', alpha=.4)
            ax1v.axes.yaxis.set_ticklabels([])
            ax1v.grid(False)

            ###Edit this to 3, so it's a bit larger
            ax1v.set_ylim(0, 3*volume.max())

            ax1v.spines['bottom'].set_color("#5998ff")
            ax1v.spines['top'].set_color("#5998ff")
            ax1v.spines['left'].set_color("#5998ff")
            ax1v.spines['right'].set_color("#5998ff")
            ax1v.tick_params(axis='x', colors='w')
            ax1v.tick_params(axis='y', colors='w')
            ax2 = plt.subplot2grid((6,4), (5,0), sharex=ax1, rowspan=1, \
                                                    colspan=4, axisbg='#07000d')

            fillcolor = '#00ffe8'
            nema = 9
            _, _, macd = self.computeMACD(closep)
            ema9 = self.ExpMovingAverage(macd, nema)
          
            ax2.plot(date[-SP:], macd[-SP:], color='#4ee6fd', lw=2)
            ax2.plot(date[-SP:], ema9[-SP:], color='#e1edf9', lw=1)
            ax2.fill_between(date[-SP:], macd[-SP:]-ema9[-SP:], 0, alpha=0.5, \
                                    facecolor=fillcolor, edgecolor=fillcolor)
    
            self.ADX(date, closep, highp, lowp, openp, ax2, SP, plt)
      
            plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(\
                                                              prune='upper'))
            ax2.spines['bottom'].set_color("#5998ff")
            ax2.spines['top'].set_color("#5998ff")
            ax2.spines['left'].set_color("#5998ff")
            ax2.spines['right'].set_color("#5998ff")
            ax2.tick_params(axis='x', colors='w')
            ax2.tick_params(axis='y', colors='w')
            plt.ylabel('MACD', color='w')
            ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, \
                                                                prune='upper'))
            for label in ax2.xaxis.get_ticklabels():
                label.set_rotation(45)
      
            plt.setp(ax0.get_xticklabels(), visible=False)
            plt.setp(ax1.get_xticklabels(), visible=False)
      
            plt.subplots_adjust(left=.09, bottom=.14, right=.94, top=.95, \
                                                        wspace=.20, hspace=0)
             
            if self.MA_NOTIFICATION or self.MEAN_NOTIFICATION or \
                                                        self.TREND_NOTIFICATION:
                mydir = os.path.join(os.getcwd(), 'live_trading_captures', \
                                             symbol, datetime.datetime.now().\
                                             strftime('%Y-%m-%d'), subdir)
                if not os.path.isdir(mydir):
                    os.makedirs(mydir)
                
                fig.savefig(os.path.join(mydir, str(self.SECTIME) + ".png"), \
                                                facecolor=fig.get_facecolor())
                plt.close(fig)
            
                return os.path.join(mydir, str(self.SECTIME) + ".png")
            else:
                return None   
        except Exception, excp:
            traceback.print_exc(file=sys.stdout)
            sys.stderr.write('ERROR: main loop %s\n' % excp)

