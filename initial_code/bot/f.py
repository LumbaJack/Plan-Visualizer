import argparse
import thread
import io
import os
import time
import logging
import threading


from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class Memory(LoggingMixIn, Operations):

    def getattr(self, path, fh=None):
        if os.path.basename(args.src) in path:
            st = os.lstat(args.src)
        else:
            st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_gid',
            'st_mode', 'st_mtime', 'st_size', 'st_uid'))

    def read(self, path, size, offset, fh):
        if goffset < offset + size and not fileopn.closed:
            lock.acquire()
            try:
                fileopn.seek(offset)
                buf = fileopn.read(size)
                fileopn.seek(goffset)
            finally:
                lock.release()
        else:
            filemem.seek(offset)
            buf = filemem.read(size)
        return buf


    def readdir(self, path, fh):
        return ['.', '..', os.path.basename(args.src)]


def copybg():
    global filemem, goffset 
    blksize =  os.stat(args.src).st_blksize
    while True:
        lock.acquire()
        try:
            data = fileopn.read(blksize)
            if not data:
                break
            filemem.seek(0,2)
            filemem.write(data)
            goffset = fileopn.tell()
        finally:
            lock.release()
    fileopn.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Program to copy with cache')
    parser.add_argument('src', nargs=1, help='Source file')
    parser.add_argument('dst', nargs=1, help='Destination virtual file')
    parser.add_argument('-d', nargs='*', help='Debug info')
    args = parser.parse_args()

    args.src = os.path.abspath(args.src[0])
    args.dst = os.path.abspath(args.dst[0])

    if not os.path.isfile(args.src):
        print "File does not exist"
        sys.exit(-1)

    if not os.path.isdir(args.dst) and os.listdir(args.dst) != []:
        print "Mount directory does not exist or is not empty"
        sys.exit(-2)

    filemem = io.BytesIO()
    fileopn = open(args.src, "rb")
    goffset = 0
    thread.start_new_thread(copybg, ())
    lock = threading.Lock()


    if args.d:
        logger = logging.getLogger('fuse.log-mixin')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add the handlers to the logger
        logger.addHandler(ch)


    fuse = FUSE(Memory(), args.dst, foreground=True, nothreads=True)


