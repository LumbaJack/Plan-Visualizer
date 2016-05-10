#!/bin/env python

import sys
import pylab
import itertools
import numpy as np

from scipy.signal import argrelextrema

class Pattern:
    start = "max"

    def __init__(self):
        self.X1 = 0
        self.Y1 = 0
        self.X2 = 0
        self.Y2 = 0
        self.X3 = 0
        self.Y3 = 0
        self.X4 = 0
        self.Y4 = 0
        self.X5 = 0
        self.Y5 = 0
        self.X6 = 0
        self.Y6 = 0

    def pattern(self): pass

    def parse(self, data, var = "X"):
        e=1
        d=""
        for a in data:
            d+="self.%s%s=float('%s')\r" % (var,e,a)
            e+=1
        return d

    def getSlope(self, x1, y1, x2, y2):
        x2 = (x2 - x1)
        y2 = (y2 - y1)
        m = (1.0 * y2 / x2)
        return m
    
    def getIntercept(self, x1, y1, x2, y2):
        m = self.getSlope(x1, y1, x2, y2)
        b = y2 - (m * x2)
        return b

    def calc_area(self, xA, yA, xB, yB, xC, yC):
        return 0.5 * abs((xA * yB) + (xB * yC) + (xC * yA) - \
                         (xA * yC) - (xC * yB) - (xB * yA))

    def percentage_change(self, old_value, new_value, multiply=True):
        change = new_value - old_value
        try:
            percentage_change = (change / float(old_value))
            if multiply:
                percentage_change = percentage_change * 100
            return percentage_change
        except ZeroDivisionError:
            return None

    def validate_area(self):
        print self.percentage_change(\
                                    self.calc_area(self.X1, self.Y1, self.X2, \
                                                   self.Y2, self.X3, self.Y3), \
                                     self.calc_area(self.X3, self.Y3, self.X4, \
                                                    self.Y4, self.X5, self.Y5))
        
        return True

    def validateDimensions(self, isdown=False):
        slope = self.getSlope(self.X2, self.Y2, self.X4, self.Y4)
 
#         if abs(self.getSlope(0, self.Y2, 2, self.Y4)) > 1:
#             return False, ""
#         if not self.validate_area():
#             return False, ""
 
        yint = self.getIntercept(self.X2, self.Y2, self.X4, self.Y4)
 
        liney3 = abs(self.Y3 - ((slope * self.X3) + yint)) 
        liney1 = abs(self.Y1 - ((slope * self.X1) + yint))
        liney5 = abs(self.Y5 - ((slope * self.X5) + yint))
         
        if isdown:
            firscheck = self.Y5 + (liney5 / 2)
            secondcheck = (slope * self.X6) + yint
        else:
            firscheck = (slope * self.X6) + yint
            secondcheck = self.Y5 - (liney5 / 2)

        if self.Y6:
#         if secondcheck >= self.Y6 >= firscheck:
#             if isdown:
#                 return (liney1 > (liney3 * .20) < liney5), \
#                                                     (self.Y5 - liney3, self.X5)
#             else:
#                 return (liney1 > (liney3 * .20) < liney5), \
#                                                     (self.Y5 + liney3, self.X5)
            if isdown:
                return (firscheck >= self.Y6), (self.Y5 - liney3, self.X5)
            else:
                return (secondcheck <= self.Y6), (self.Y5 + liney3, self.X5)
        else:
            return False, ""

class PatternDB:
    def __init__(self):
        self.pattern = []

    def add (self, pattern):
        self.pattern.append(pattern)

    def check(self, datay, datax):
        retpattern = []
        dataarr = np.asarray(datay)

        for p in self.pattern:
            if p.start == "min":
                extodd  = argrelextrema(dataarr, np.less)
                exteven = argrelextrema(dataarr, np.greater)
            else:
                extodd  = argrelextrema(dataarr, np.greater)
                exteven = argrelextrema(dataarr, np.less)

            itemx = [0] * 6
            itemy = [0] * 6
            for xin in range(0,len(extodd[0])-3):
                cnt = extodd[0][xin:xin + 3]
                if (cnt[2] - cnt[1] - cnt[0]) < 2 or \
                            (p.start == "max" and max(datay[cnt[0]:cnt[2]]) \
                             > datay[cnt[1]]) or (p.start == "min" and \
                                  min(datay[cnt[0]:cnt[2]]) < datay[cnt[1]]):
                    continue
                itemx[0] = datax[cnt[0]]
                itemy[0] = datay[cnt[0]]
                for l1 in range(cnt[0], cnt[1]):
                    if l1 not in exteven[0] or \
                           (p.start == "max" and min(datay[cnt[0]:cnt[1]]) \
                            < datay[l1]) or (p.start == "min" and \
                                         max(datay[cnt[0]:cnt[1]]) > datay[l1]):
                        continue
                    itemx[1:3] = datax[l1], datax[cnt[1]]
                    itemy[1:3] = datay[l1], datay[cnt[1]]
                    for l2 in range(cnt[1], cnt[2]):
                        if l2 not in exteven[0] or \
                            (p.start == "max" and min(datay[cnt[1]:cnt[2]]) \
                             < datay[l2]) or (p.start == "min" and \
                                      max(datay[cnt[1]:cnt[2]]) > datay[l2]):
                            continue
                        itemx[3:6] = datax[l2], datax[cnt[2]], datax[-1]
                        itemy[3:6] = datay[l2], datay[cnt[2]], datay[-1]
                        try:
                            ret, pos = p.pattern(itemx, itemy)
                            if ret:
                                retpattern.append({'name': p.name, \
                                                   "iyd": itemy, \
                                                   "ixd": itemx, \
                                                   "pos": pos})
                        except Exception, excp:
                            sys.stderr.write("ERROR: patterns check failed " \
                                             "with exception %s (name: %s)\n" \
                                             % (excp, p.name))
    
        return retpattern


class HS(Pattern):
    name = "Head-and-shoulders (HS)"

    def pattern(self, datax, datay):
        positions = ""

        exec(self.parse(datax, "X") + self.parse(datay, "Y"))
        L1= abs(self.Y3 - self.Y2)
        L2= abs(self.Y3 - self.Y4)
        AD= abs((L1 - L2) / 2)

        #Filter basic
        ret = self.Y3 > self.Y1 and \
                self.Y3 > self.Y5 and \
                self.Y1 > self.Y2 and \
                self.Y4 < self.Y5 and \
                self.Y2 >= self.Y4 #and \
#                 ((self.X3 - self.X1) * 3) > (self.X6 - self.X3)

        if ret:
            ret, positions = self.validateDimensions()

        return ret, positions

class IHS(Pattern):
    start = "min"
    name = "Inverted Head-and-shoulders (IHS)"

    def pattern(self, datax, datay):
        positions = ""

        exec(self.parse(datax, "X") + self.parse(datay, "Y"))
        L1 = abs(self.Y2 - self.Y3)
        L2 = abs(self.Y4 - self.Y3)
        AD = abs((L1 - L2) / 2)
        
        #Filter basic
        ret = self.Y3 < self.Y1 and \
                self.Y3 < self.Y5 and \
                self.Y1 < self.Y2 and \
                self.Y4 < self.Y5 and \
                self.Y3 < self.Y4 and \
                self.Y2 <= self.Y4 and \
                (self.X5 - self.X1) > (self.X6 - self.X5)

        if ret:
            ret, positions = self.validateDimensions(isdown=True)

        return ret, positions


class BTOP(Pattern):
    name = "Broadening tops (BTOP)"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        return self.Y1 < self.Y3 and self.Y3 < self.Y5 and self.Y2 > self.Y4

class BBOT(Pattern):
    name = "Broadening bottoms (BBOT)"
    start = "min"

    def pattern(self, datax, datay):
        exec(self.parse(datay))
        return self.Y1 > self.Y3 and self.Y3 > self.Y5 and self.Y2 < self.Y4

class TTOP(Pattern):
    name = "Triangle tops (TTOP)"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        return self.Y1 > self.Y3 and self.Y3 > self.Y5 and self.Y2 < self.Y4

class TBOT(Pattern):
    name = "Triangle bottoms (TBOT)"
    start = "min"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        return self.Y1 < self.Y3 and self.Y3 < self.Y5 and self.Y2 > self.Y4

class RTOP(Pattern):
    name = "Rectangle tops (RTOP)"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        avgtop = (self.Y1+self.Y3+self.Y5)/3
        avgbop = (self.Y2+self.Y4)/2
        return abs(self.Y1 - avgtop) < 0.75/100 * avgtop and \
               abs(self.Y3 - avgtop) < 0.75/100 * avgtop and \
               abs(self.Y5 - avgtop) < 0.75/100 * avgtop and \
               abs(self.Y2 - avgbop) < 0.75/100 * avgbop and \
               abs(self.Y4 - avgbop) < 0.75/100 * avgbop and \
               min(self.Y1,self.Y3,self.Y5) > max(self.Y2,self.Y4)

class RBOT(Pattern):
    name = "Rectangle bottoms (RBOT)"
    start = "min"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        avgtop = (self.Y2+self.Y4)/2
        avgbop = (self.Y1+self.Y3+self.Y5)/3
        return abs(self.Y2 - avgtop) < 0.75/100 * avgtop and \
               abs(self.Y4 - avgtop) < 0.75/100 * avgtop and \
               abs(self.Y1 - avgbop) < 0.75/100 * avgbop and \
               abs(self.Y3 - avgbop) < 0.75/100 * avgbop and \
               abs(self.Y5 - avgbop) < 0.75/100 * avgbop and \
               min(self.Y2,self.Y4) > max(self.Y1,self.Y3,self.Y5)

class DTDB(Pattern):
    name = "Double Top And Double Bottom (DTDB)"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        secondtop = max(E)
        secondtopt = t[which.max(E)]
        avg = (self.Y1 + second.top)/2
        return abs(self.Y1         - avg) < 1.5/100 * avg and \
               abs(second.top - avg) < 1.5/100 * avg and \
               second.top.t - t1 > 22
class DBOT(Pattern):
    name = "Double bottoms (DBOT)"
    start = "min"

    def pattern(self, datax, datay):
        exec(self.parse(data))
        return abs(self.Y1 -  (self.Y1+min(E))/2) < 1.5/100 * (self.Y1+min(E))/2 and \
               abs(max(E[-1]) - (self.Y1+min(E))/2) < 1.5/100 * (self.Y1+min(E))/2 and \
               t[which.min(E)] - t1 > 22


if __name__ == "__main__":
#     tester = MathEquations()
#     #x1 = left low / x2 = right low / x3 = top high
#     heigth = tester.validateDimensions(1, 1, 5, 2, 2, 2)
    
    patterndb = PatternDB()
    patterndb.add(HS())
    #patterndb.add(IHS())
    #patterndb.add(BTOP())
    #patterndb.add(BBOT())
    #patterndb.add(TTOP())
    #patterndb.add(TBOT())
    #patterndb.add(RTOP())
    #patterndb.add(RBOT())
    #patterndb.add(DTDB())
    #patterndb.add(DBOT())
    
    data = [191.78,191.59,191.59,191.41,191.47,191.33,191.25, 191.33,191.48,191.48,191.51,191.43,191.42,191.54, 191.5975,191.555,191.52,191.25,191.15,191.01,191.01, 191.05,190.98,190.97,190.905,190.72,190.79,190.901, 190.91,190.89,190.69,190.79,190.81,190.81,190.74, 190.58,190.49,190.41,190.5099,190.38,190.29,190.1299, 190.13,190.21,190.28,190.16,190.14,190.16,190.21, 190.2408,190.18,190.12,190.25,190.13,190.3,190.495, 190.39,190.515,190.5843,190.4466,190.59,190.51,190.44, 190.41,190.41,190.32,190.23,190.31,190.4336,190.3201, 190.3801,190.2531,190.27,190.22,190.405,190.48,190.48, 190.47,190.275,190.15,190.29,190.15,190.17,190.15, 190.17,190.38,190.311,190.44,190.5762,190.479,190.553, 190.6099,190.49,190.53,190.66,190.69,190.8,190.849, 190.816,190.73,190.6,190.44,190.38,190.38,190.42, 190.33,190.299,190.43,190.249,190.25,190.179,190.21, 190.275,190.23,190.2,190.18,190.08,189.825,189.79, 189.575,189.64,189.6001,189.69,189.72,189.6,189.49, 189.54,189.55,189.55,189.64,189.65,189.5973,189.67, 189.67,189.72,189.63,189.55,189.64,189.5292,189.47, 189.54,189.499,189.59,189.5,189.5499,189.67,189.62, 189.62,189.541,189.55,189.43,189.465,189.385,189.45, 189.45,189.44,189.37,189.23,189.2,189.1999,189.21, 189.18,189.117,189.12,189.09,189.27,189.25,189.19, 189.21,189.18,189.08,189.01,189.05,189.02,189.1,189.18, 189.295,189.28,189.3,189.2499,189.18,189.15,189.1268, 188.995,188.96,188.98,188.99,188.98,188.92,188.98, 189.01,189.04,189.1,189.01,188.95,188.84,188.77, 188.8267,188.81,188.75,188.83,188.7,188.769,188.81, 188.86,188.84,188.67,188.87,188.94,188.7492,188.67, 188.765,188.89,188.7135,188.89,188.94,189.105,189.09, 189.18,189.15,189.175,189.16,189.06,188.995,188.92, 189.01,188.96,188.785,188.8504,188.69,188.75,188.75, 188.73,188.85,188.87,188.715,188.725,188.66,188.61, 188.58,188.655,188.65,188.91,188.93,188.78,188.84, 188.73,188.9,189.03,189.035,189.0301,188.89,189.,189.04, 189.05,188.99,189.005,188.93,188.87,188.78,188.735, 188.815,188.715,188.67,188.495,188.49,188.46,188.54, 188.47,188.43,188.36,188.24,188.35,188.33,188.35, 188.25,188.1,188.1175,188.13,188.335,188.33,188.28, 188.16,188.14,188.02,188.08,187.91,187.9767,187.8979, 187.845,187.92,187.83,187.91,188.02,188.02,188.12, 188.01,188.07,188.17,188.1604,188.31,188.145,188.24, 188.2099,188.17,188.22,188.24,188.4,188.45,188.43, 188.57,188.58,188.56,188.48,188.55,188.71,188.75,188.6, 188.4699,188.51,188.45,188.47,188.43,188.36,188.23, 188.2169,188.14,188.17,188.13,188.03,188.16,188.04, 187.99,188.03,188.1,188.23,188.12,188.05,187.9999, 187.99,187.85,187.78,187.729,187.85,187.81,187.82, 187.85,187.99,188.03,188.05,188.0899,188.14,188.05, 187.91,187.98,187.85,187.95,188.,187.89,187.7999, 187.82,187.95,188.02,188.13,188.14,188.22,188.42, 188.35,188.49,188.28,188.25,188.44,188.52,188.62, 188.45,188.38,188.33,188.5,188.4,188.42,188.5,188.6, 188.54,188.47,188.36,188.42,188.3,188.22,188.06, 188.03]
    
    
    
    
    patterndb.check(data, data)
    pylab.plot(data)
    #pylab.plot(extmax[0], dataarr[extmax[0]])
    #pylab.plot(extmin[0], dataarr[extmin[0]])
    
    #pylab.scatter([377, 378, 381, 384, 385], [188.5, 188.4, 188.6, 188.36, 188.42])
    
    pylab.show()
    
    #print data[0][77], data[1][77]
