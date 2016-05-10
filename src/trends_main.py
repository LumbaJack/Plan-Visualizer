import sys

from threading import Thread
from interactivebroker import IBHandler

class DataMining(object):
    """ Standard IB wrapper to have a single entry point """
    def __init__(self):
        self.IBH = IBHandler()

    def start_mining(self):
        """Start the data mining."""
        try:
            #Data Mining Thread

            t = Thread(target=self.IBH.data_mining_function)
            t.start()
            t.join()
        except Exception, excp:
            print excp
            print "Error trying to start the data mining thread"
            sys.exit(1)

if __name__ == "__main__":
    # start data mining thread
    dataobj = DataMining()
    dataobj.start_mining()