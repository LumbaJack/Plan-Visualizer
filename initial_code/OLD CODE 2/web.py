import os
import sys
import thread
import matplotlib as mpl
mpl.use('Agg')

from telegrambot import TelegramBot
from interactivebroker import IBHandler

class WebServer(object):
    """ Standard IB wrapper to have a single entry point """
    def __init__(self):
        self.IBH = IBHandler()

    def start_server(self):
        """Start the server."""
        try:
            #Data Mining Thread
            thread.start_new_thread(self.IBH.data_mining_function, ())
        except:
            print "Error trying to start the WebServer"
            sys.exit(1)

    def content_type(self, path):
        """Return a guess at the mime type for this path
            based on the file extension"""
                
        MIME_TABLE = {'.txt': 'text/plain',
                      '.html': 'text/html',
                      '.htm': 'text/html',
                      '.css': 'text/css',
                      '.js': 'application/javascript',
                     }
 
        _, ext = os.path.splitext(path)
                        
        if ext in MIME_TABLE:
            return MIME_TABLE[ext]
        else:
            return "application/octet-stream"

if __name__ == "__main__":
    bot = TelegramBot()
    bot.start()
    webSrv = WebServer()
    webSrv.start_server()
    bot.join()

