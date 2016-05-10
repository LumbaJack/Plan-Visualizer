""" Telegram classr Handler """
import sys
import time
import Queue
import sqlite3
import telegram
import threading


class TelegramBot(threading.Thread):
    def __init__(self, token="file", dbname = "telegramdb.db"):
        self.q = Queue.Queue()
        if token == "file":
            data = open ("token.txt", "r").read().rstrip()
        else:
            data = token
        self.bot = telegram.Bot(token=data)
        self.LAST_UPDATE_ID = 0
        self.dbname  = dbname
        self.checktable()
        self.signal = True
        threading.Thread.__init__ (self)

    def checktable(self):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'create table if not exists chats (idchat integer PRIMARY KEY ON CONFLICT REPLACE)'
        c.execute(sql)

    def sendmsg(self, chatid = "all", text = "", filename = None):
        if chatid == "all":
            for row in self._lstchat():
                chatid = row[0]
                self.q.put((chatid, text, filename))
        else:
            self.q.put((chatid, text, filename))

    def run(self):
        try:
            while self.signal:
                self._checkmsgs()
                if not self.q.empty():
                    data = self.q.get()
                    self._sendmsg(data[0], data[1], data[2])
                else:
                    time.sleep(5)
        except:
            raise
        

    def _addchat(self, chatid):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'insert or replace into chats (idchat) values (?)'
        c.execute(sql, (chatid,))
        conn.commit()

    def _deletechat(self, chatid):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'delete from chats where idchat = ?'
        c.execute(sql, (chatid,))
        conn.commit()

    def _lstchat(self):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'select idchat from chats'
        c.execute(sql)
        data = c.fetchall()
        return data


    def _sendmsg(self, chatid, msg, filename = None):
        try:
            self.bot.sendMessage(chat_id=chatid, text=msg)
            if filename:
                self.bot.sendPhoto(chat_id=chatid, photo=open(filename,'rb'))
        except:
            self._deletechat(chatid)
    
    def _checkmsgs(self):
        try:
            for update in self.bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=10):
                text = update.message.text.encode('utf-8')
                chat_id = update.message.chat.id
                if text == "/start":
                    self._addchat(chat_id)
                    self.sendmsg(chat_id, "Welcome")
                if text == "/stop":
                    self._deletechat(chat_id)
                    self.sendmsg(chat_id, "Bye")
                if text == "/w":
                    text = "Users:\n"
                    text += '\n'.join(str(e[0]) for e in self._lstchat())
                    self.sendmsg(chat_id, text)
                self.LAST_UPDATE_ID = update.update_id + 1
        except Exception, excp:
            sys.stderr.write("ERROR: checkmsg failed with exception %s\n" \
                                                                        % excp)
            pass


class SimpleTelegramBot():
    def __init__(self, token = "file", dbname = "telegramdb.db"):
        if token == "file":
            data = open ("token.txt", "r").read().rstrip()
        else:
            data = token
        self.bot = telegram.Bot(token=data)
        self.dbname  = dbname

    def sendmsg(self, chatid = "all", text = "", filename = None):
        if chatid == "all":
            for row in self._lstchat():
                chatid = row[0]
                self._sendmsg(chatid, text, filename)
        else:
            self._sendmsg(chatid, text, filename)

    def _deletechat(self, chatid):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'delete from chats where idchat = ?'
        c.execute(sql, (chatid,))
        conn.commit()

    def _lstchat(self):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        sql = 'select idchat from chats'
        c.execute(sql)
        data = c.fetchall()
        return data

    def _sendmsg(self, chatid, msg, filename = None):
        try:
            self.bot.sendMessage(chat_id=chatid, text=msg)
            if filename:
                self.bot.sendPhoto(chat_id=chatid, photo=open(filename,'rb'))
        except:
            self._deletechat(chatid)
