import os
import sys
import json
import time
import thread
import matplotlib as mpl
mpl.use('Agg')
from telegrambot import TelegramBot
from interactivebroker import IBHandler
from cgi import parse_qs, escape
from wsgiref.simple_server import make_server



class WebServer(object):
    """ Standard IB wrapper to have a single entry point """
    def __init__(self):
        self.IBH = IBHandler()

    def start_server(self):
        """Start the server."""
        try:
            httpd = make_server("0.0.0.0", 80, self.application)
            print "Serving HTTP on port ", 80
            thread.start_new_thread(httpd.serve_forever, ())

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
                                                    
    
    def application(self, environ, start_response):
        """The Web handler."""
        headers = [
            ('Server', 'Phyton'),
            ('Access-Control-Allow-Origin', '*'),
            ('Content-type', 'application/json'),
        ]
        path = environ["PATH_INFO"]
        if path == "/":
            path = "/index.htm"

        response = ""
        response_code = "200 OK"
     
        if environ["REQUEST_METHOD"] == "OPTIONS":
            start_response(response_code, headers)
            return [""]
 
        if path == "/get_hist":
            inargs = parse_qs(environ['QUERY_STRING'])
            
            INTERVAL = inargs.get(["inter"][0])[0]
            INTERVAL = INTERVAL.replace("&", "&amp;")
            INTERVAL = escape(INTERVAL)

            SYMBOL = inargs.get(["sym"][0])[0]
            SYMBOL = escape(SYMBOL)

            response =  json.dumps(self.IBH.get_http_response(INTERVAL, SYMBOL))
        elif path == "/get_update":
            inargs = parse_qs(environ['QUERY_STRING'])
            
            INTERVAL = inargs.get(["inter"][0])[0]
            INTERVAL = INTERVAL.replace("&", "&amp;")
            INTERVAL = escape(INTERVAL)

            SYMBOL = inargs.get(["sym"][0])[0]
            SYMBOL = escape(SYMBOL)         
            
            LATESTDATE = inargs.get(["last"][0])[0]
            LATESTDATE = escape(LATESTDATE)

            response =  json.dumps(self.IBH.get_http_update_response(INTERVAL, \
                                                            SYMBOL, LATESTDATE))
        else:
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)), \
                                    "www", os.path.normpath(path)[1:])
            if os.path.exists(path):
                h = open(path, 'rb')
                response = h.read()
                h.close()
                response_code = "200 OK"
                headers = [('content-type', self.content_type(path))]
            else:
                response_code = "404 OK"
                headers = [('content-type', "text/plain")]
 
        start_response(response_code, headers)
        return [response]

if __name__ == "__main__":
    #Message bot handler
    bot = TelegramBot()
    bot.start()
    webSrv = WebServer()
    webSrv.start_server()
    bot.join()
