#!/bin/env python

import numpy as np
import pylab
from scipy.signal import argrelextrema


class Pattern:
    start = "max"
    def pattern(self): pass

    def parse(self, data):
        e=1
        d=""
        for a in data:
            d+="E%s=float('%s')\r" % (e,a)
            e+=1
        return d


class PatternDB:
    def __init__(self):
        self.pattern = []

    def add (self, pattern):
        self.pattern.append(pattern)

    def check(self, data, date):
        dataarr = np.asarray(data)
        extmax = argrelextrema(dataarr, np.greater)
        extmin = argrelextrema(dataarr, np.less)

        newdata = [[],[]]
        retpattern = []
        for i,d in enumerate(data):
            if i in extmax[0] or i in extmin[0]:
                newdata[0].append(date[i])
                newdata[1].append(d)

        for idx, val in enumerate(newdata[0]):
            if idx + 6 > len(newdata[0]):
                break
            itemx = newdata[0][idx: idx+6]
            itemy = newdata[1][idx: idx+6]
            for p in self.pattern:
                try:
                    ret = p.pattern(itemy)
                    if ret:
                        print p.name 
                        print itemx, itemy
                        #pylab.scatter(itemx, itemy)
                        retpattern.append({'name': p.name, "iyd": itemy, \
                                                                "ixd": itemx})
                except:
                    print "error in %s" % p.name

        return retpattern


class HS(Pattern):
    name = "Head-and-shoulders (HS)"

    def pattern(self, data):
        exec(self.parse(data))
        L1=abs( E3-E2 )
        L2=abs( E3-E4 )
        AD=abs( (L1-L2)/2 )
        

        #print D1, D2
      #  return E3 > E1 and E3 > E5 and abs(E1 - (E1+E5)/2) < 1.5/100 * (E1+E5)/2 and abs(E5 - (E1+E5)/2) < 1.5/100 * (E1+E5)/2 and abs(E2 - (E2+E4)/2) < 1.5/100 * (E2+E4)/2 and abs(E4 - (E2+E4)/2) < 1.5/100 * (E2+E4)/2 and E1>E2 and E4<E5
        return E3 > E1 and E3 > E5 and  E1>E2 and E4<E5 and AD <.015 and E6 < E4

class IHS(Pattern):
    start = "min"
    name = "Inverted Head-and-shoulders (IHS)"

    def pattern(self, data):
        exec(self.parse(data))
        L1=abs( E2-E3 )
        L2=abs( E4-E3 )
        AD=abs( (L1-L2)/2 )
        return E3 < E1 and E3 < E5 and  E1<E2 and E4<E5 and E3 < E4 and E6 > E4
        #return E3 < E1 and E3 < E5 and abs(E1 - (E1+E5)/2) < 1.5/100 * (E1+E5)/2 and abs(E5 - (E1+E5)/2) < 1.5/100 * (E1+E5)/2 and abs(E2 - (E2+E4)/2) < 1.5/100 * (E2+E4)/2 and abs(E4 - (E2+E4)/2) < 1.5/100 * (E2+E4)/2


class BTOP(Pattern):
    name = "Broadening tops (BTOP)"

    def pattern(self, data):
        exec(self.parse(data))
        return E1 < E3 and E3 < E5 and E2 > E4

class BBOT(Pattern):
    name = "Broadening bottoms (BBOT)"
    start = "min"

    def pattern(self, data):
        exec(self.parse(data))
        return E1 > E3 and E3 > E5 and E2 < E4

class TTOP(Pattern):
    name = "Triangle tops (TTOP)"

    def pattern(self, data):
        exec(self.parse(data))
        return E1 > E3 and E3 > E5 and E2 < E4

class TBOT(Pattern):
    name = "Triangle bottoms (TBOT)"
    start = "min"

    def pattern(self, data):
        exec(self.parse(data))
        return E1 < E3 and E3 < E5 and E2 > E4

class RTOP(Pattern):
    name = "Rectangle tops (RTOP)"

    def pattern(self, data):
        exec(self.parse(data))
        avgtop = (E1+E3+E5)/3
        avgbop = (E2+E4)/2
        return abs(E1 - avgtop) < 0.75/100 * avgtop and \
               abs(E3 - avgtop) < 0.75/100 * avgtop and \
               abs(E5 - avgtop) < 0.75/100 * avgtop and \
               abs(E2 - avgbop) < 0.75/100 * avgbop and \
               abs(E4 - avgbop) < 0.75/100 * avgbop and \
               min(E1,E3,E5) > max(E2,E4)

class RBOT(Pattern):
    name = "Rectangle bottoms (RBOT)"
    start = "min"

    def pattern(self, data):
        exec(self.parse(data))
        avgtop = (E2+E4)/2
        avgbop = (E1+E3+E5)/3
        return abs(E2 - avgtop) < 0.75/100 * avgtop and \
               abs(E4 - avgtop) < 0.75/100 * avgtop and \
               abs(E1 - avgbop) < 0.75/100 * avgbop and \
               abs(E3 - avgbop) < 0.75/100 * avgbop and \
               abs(E5 - avgbop) < 0.75/100 * avgbop and \
               min(E2,E4) > max(E1,E3,E5)

class DTDB(Pattern):
    name = "Double Top And Double Bottom (DTDB)"

    def pattern(self, data):
        exec(self.parse(data))
        secondtop = max(E)
        secondtopt = t[which.max(E)]
        avg = (E1 + second.top)/2
        return abs(E1         - avg) < 1.5/100 * avg and \
               abs(second.top - avg) < 1.5/100 * avg and \
               second.top.t - t1 > 22
class DBOT(Pattern):
    name = "Double bottoms (DBOT)"
    start = "min"

    def pattern(self, data):
        exec(self.parse(data))
        return abs(E1 -  (E1+min(E))/2) < 1.5/100 * (E1+min(E))/2 and \
               abs(max(E[-1]) - (E1+min(E))/2) < 1.5/100 * (E1+min(E))/2 and \
               t[which.min(E)] - t1 > 22


if __name__ == "__main__":
    patterndb = PatternDB()
    patterndb.add(HS())
    patterndb.add(IHS())
    #patterndb.add(BTOP())
    #patterndb.add(BBOT())
    #patterndb.add(TTOP())
    #patterndb.add(TBOT())
    #patterndb.add(RTOP())
    #patterndb.add(RBOT())
    #patterndb.add(DTDB())
    #patterndb.add(DBOT())
    
    data = [191.78,191.59,191.59,191.41,191.47,191.33,191.25, 191.33,191.48,191.48,191.51,191.43,191.42,191.54, 191.5975,191.555,191.52,191.25,191.15,191.01,191.01, 191.05,190.98,190.97,190.905,190.72,190.79,190.901, 190.91,190.89,190.69,190.79,190.81,190.81,190.74, 190.58,190.49,190.41,190.5099,190.38,190.29,190.1299, 190.13,190.21,190.28,190.16,190.14,190.16,190.21, 190.2408,190.18,190.12,190.25,190.13,190.3,190.495, 190.39,190.515,190.5843,190.4466,190.59,190.51,190.44, 190.41,190.41,190.32,190.23,190.31,190.4336,190.3201, 190.3801,190.2531,190.27,190.22,190.405,190.48,190.48, 190.47,190.275,190.15,190.29,190.15,190.17,190.15, 190.17,190.38,190.311,190.44,190.5762,190.479,190.553, 190.6099,190.49,190.53,190.66,190.69,190.8,190.849, 190.816,190.73,190.6,190.44,190.38,190.38,190.42, 190.33,190.299,190.43,190.249,190.25,190.179,190.21, 190.275,190.23,190.2,190.18,190.08,189.825,189.79, 189.575,189.64,189.6001,189.69,189.72,189.6,189.49, 189.54,189.55,189.55,189.64,189.65,189.5973,189.67, 189.67,189.72,189.63,189.55,189.64,189.5292,189.47, 189.54,189.499,189.59,189.5,189.5499,189.67,189.62, 189.62,189.541,189.55,189.43,189.465,189.385,189.45, 189.45,189.44,189.37,189.23,189.2,189.1999,189.21, 189.18,189.117,189.12,189.09,189.27,189.25,189.19, 189.21,189.18,189.08,189.01,189.05,189.02,189.1,189.18, 189.295,189.28,189.3,189.2499,189.18,189.15,189.1268, 188.995,188.96,188.98,188.99,188.98,188.92,188.98, 189.01,189.04,189.1,189.01,188.95,188.84,188.77, 188.8267,188.81,188.75,188.83,188.7,188.769,188.81, 188.86,188.84,188.67,188.87,188.94,188.7492,188.67, 188.765,188.89,188.7135,188.89,188.94,189.105,189.09, 189.18,189.15,189.175,189.16,189.06,188.995,188.92, 189.01,188.96,188.785,188.8504,188.69,188.75,188.75, 188.73,188.85,188.87,188.715,188.725,188.66,188.61, 188.58,188.655,188.65,188.91,188.93,188.78,188.84, 188.73,188.9,189.03,189.035,189.0301,188.89,189.,189.04, 189.05,188.99,189.005,188.93,188.87,188.78,188.735, 188.815,188.715,188.67,188.495,188.49,188.46,188.54, 188.47,188.43,188.36,188.24,188.35,188.33,188.35, 188.25,188.1,188.1175,188.13,188.335,188.33,188.28, 188.16,188.14,188.02,188.08,187.91,187.9767,187.8979, 187.845,187.92,187.83,187.91,188.02,188.02,188.12, 188.01,188.07,188.17,188.1604,188.31,188.145,188.24, 188.2099,188.17,188.22,188.24,188.4,188.45,188.43, 188.57,188.58,188.56,188.48,188.55,188.71,188.75,188.6, 188.4699,188.51,188.45,188.47,188.43,188.36,188.23, 188.2169,188.14,188.17,188.13,188.03,188.16,188.04, 187.99,188.03,188.1,188.23,188.12,188.05,187.9999, 187.99,187.85,187.78,187.729,187.85,187.81,187.82, 187.85,187.99,188.03,188.05,188.0899,188.14,188.05, 187.91,187.98,187.85,187.95,188.,187.89,187.7999, 187.82,187.95,188.02,188.13,188.14,188.22,188.42, 188.35,188.49,188.28,188.25,188.44,188.52,188.62, 188.45,188.38,188.33,188.5,188.4,188.42,188.5,188.6, 188.54,188.47,188.36,188.42,188.3,188.22,188.06, 188.03]
    
    
    
    
    patterndb.check(data)
    pylab.plot(data)
    #pylab.plot(extmax[0], dataarr[extmax[0]])
    #pylab.plot(extmin[0], dataarr[extmin[0]])
    
    #pylab.scatter([377, 378, 381, 384, 385], [188.5, 188.4, 188.6, 188.36, 188.42])
    
    pylab.show()
    
    #print data[0][77], data[1][77]
