#!/usr/bin/python
import sys
import pusherclient
import time
import json
import matplotlib as mpl
from patternsdb import *
mpl.use('Agg')
from telegrambot import TelegramBot, SimpleTelegramBot

class Pusher:
    def __init__(self):
        self.pusher = pusherclient.Pusher('')
        self.pusher.connection.bind('pusher:connection_established', self.connect_handler)
        self.pusher.connect()
        self.patterndb = PatternDB()
        self.patterndb.add(HS())
        self.patterndb.add(IHS())
        self.itemy = []
        self.itemx = []
        self.telecobj = SimpleTelegramBot(token = "", dbname = "btc_telegram.db")

    def callback(self, data):
        d = json.loads(data)
        self.itemy.append(d["price"])
        self.itemx.append(d["id"])
        if len(self.itemx) > 60:
            self.itemx.pop(1)
            self.itemy.pop(1)

        if len(self.itemx)> 6:
            ret = self.patterndb.check(self.itemy, self.itemx)
            if ret:
                print ret
                self.telecobj.sendmsg(text = "New pattern found in BTC ")

    def connect_handler(self, data):
        channel = self.pusher.subscribe('live_trades')
        channel.bind('trade', self.callback)


if __name__ == "__main__":
    #Message bot handler
    bot = TelegramBot(token = "", dbname = "btc_telegram.db")
    bot.start()

    # Add a logging handler so we can see the raw communication data
    import logging
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    root.addHandler(ch)

    pu = Pusher()

    try:
        while True:
            time.sleep(1)
    except:
        pass
    bot.stop()
