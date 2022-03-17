import hashlib
import lzma
import argparse
import urllib.request
from os import makedirs
from multiprocessing import Pool, cpu_count
from itertools import starmap
from pathlib import Path
import json
def download_file_multi(path,hash):
    filename = Path(path)
    req = url + str(PurePosixPath(filename))
    path = prefix / filename
    print(req)
    try:
        r = urllib.request.Request(req, headers={'User-Agent': 'IntsMagicToaster/4.2.0'})
        u = urllib.request.urlopen(r)
    except ConnectionResetError:
        print("Timed out! you're going to have to redownload...")
        return 1
    if str(filename.parents[0]) != '.':
        spath = path.parents[0]
        makedirs(spath, exist_ok=True)
    memfile = u.read()
    u.close()
    if memfile:
        new_hash = hashlib.sha512(memfile).hexdigest()
        memfile = lzma.decompress(memfile)
        if new_hash != hash:
            raise ArithmeticError("HASH INVALID for file {}".format(filename))
    f = open(path, 'wb')
    print(path)
    f.write(memfile)
    f.close()
    print("File download complete!")

def download_db(path):
    req = url + "oftoast.json"
    r = urllib.request.Request(req, headers={'User-Agent': 'IntsMagicToaster/4.2.0'})
    print("downloading db...")
    memfile = urllib.request.urlopen(r).read()
    if (path/"oftoast.json").exists():
        f = open(path / "oftoast.json", 'r')
        old = f.read()
        f.close()
        return [memfile,old]
    else:
        makedirs(path, exist_ok=True)
        return [memfile,None]

def argvparse():
    global prefix
    global url
    global nproc
    uhelp = """\1
Usage: oftoast -p . [-k (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing]
An installer for Open Fortress - now extra crispy!
  -p: the prefix to place them. Default is CWD.
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  -h: Displays this help message."""

    #
    parser = argparse.ArgumentParser(description=uhelp)
    parser.add_argument("-p",
                        dest="path",
                        action="store",
                        type=str,
                        help="Choose desired path for installation. Default is CWD.")
    parser.add_argument("-n",
                        dest="threads",
                        action="store",
                        type=int,
                        help="Amount of threads to be used - choose 1 to disable multithreading. "
                             "Default is the number of threads in the system.")
    parser.add_argument("-u",
                        dest="url",
                        action="store",
                        type=str,
                        help="Specifies URL to download from. "
                             "Specify the protocol (https:// or http://) as well. "
                             "Default is the OF repository.")

    args = parser.parse_args()
    prefix = Path(args.path)
    if args.threads:
        nproc = args.threads
    else:
        nproc = 12
    if args.url is not None:
        url = args.url
        if url[-1:] != '/':
            url += '/'
def main():
    global prefix
    global hashing
    global url
    global nproc
    argvparse()
    todl = []
    dbs = download_db_local(prefix,1)
    newdb = json.loads(dbs[0])
    if dbs[1]:
         oldb = json.loads(dbs[1])
         for x in oldb:
            if oldb[x] != newdb[x]:
                todl.append([x,newdb[x][0]])
    else:
        todl = [[x,newdb[x][0]] for x in newdb]
    print(todl)
    if nproc > 1:
        try:
            dpool = Pool(nproc)
            res = dpool.starmap(download_file_multi_local, todl)
        except ImportError:
            nproc = 1
    if nproc <= 1:
        res = starmap(download_file_multi_local,todl)
    if 1 in res:
        print("download failed somewhere, redownloading suggested")
        return 1
    g = open(Path(prefix) / "oftoast.json",'w')
    g.write(dbs[0])
    g.close()
main()
