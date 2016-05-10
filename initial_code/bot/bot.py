import telegram
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import logging
import time 
from google import *
from pattersdb import *

CHATIDS = []
def sendmsg(msg):
    global LAST_UPDATE_ID
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
   
    for chatid in CHATIDS:
        bot.sendMessage(chat_id=chatid, text=msg)
        bot.sendPhoto(chat_id=chatid, photo=open('temp.png','rb'))

def checkmsgs():
    global LAST_UPDATE_ID
    for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
        text = update.message.text.encode('utf-8')
        chat_id = update.message.chat.id
        if text == "/start":
            CHATIDS.append(chat_id)
            bot.sendMessage(chat_id=chat_id, text="Welcome")
        if text == "/stop" and chat_id in CHATIDS:
            CHATIDS.remove(chat_id)
            bot.sendMessage(chat_id=chat_id, text="Bye")
        if text == "/w":
            text = "Users:\n"
            text += '\n'.join(str(e) for e in CHATIDS)
            bot.sendMessage(chat_id=chat_id, text=text)

          
        LAST_UPDATE_ID = update.update_id + 1


def main():
    global LAST_UPDATE_ID, bot

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

    try:
        LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
    except IndexError:
        LAST_UPDATE_ID = None

    while True:
	data =None
        print "This prints once a minute."
        try:
	    spy =get_google_data("SPY",60,1)
	    #spy = spy[-30:]
	    datay = np.array(spy.c.values).flatten()[-120:]
	    datax = np.array(spy.ts.values).flatten()[-120:]
	    data = patterndb.check(datay, datax)
        except:
            print "Error getting data minute."
            pass

        checkmsgs()

        if data:
            for s in data:
                print s["name"]
                plt.plot(datax, datay)
                plt.plot(s["ixd"],s["iyd"])
                plt.savefig('temp.png')
                sendmsg("New pattern found %s" % (s["name"]))

        time.sleep(60)


if __name__ == '__main__':
    bot = telegram.Bot(token='')
    main()
