from Crypto.Hash import SHA384
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from multiprocessing import Pool, cpu_count
from itertools import starmap
from os import makedirs
from os.path import exists, getsize
from argparse import ArgumentParser
import sqlite3
import urllib.request
from zstd import decompress
from pathlib import Path, PurePosixPath

global prefix
global keyfile
global signing
global hashing
global url
global cfg_write
global mpath
mpath = Path(__file__).parents[0]
signing = True
hashing = True
cfg_write = False
prefix = ''
keyfile = ''
nproc = cpu_count()
url = 'https://svn.openfortress.fun/launcher/files/'


def download_db(path):
    global keyfile
    req = url + "ofmanifest.db"
    req_sig = url + "ofmanifest.sig"
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    rs = urllib.request.Request(req_sig, headers={'User-Agent': 'Mozilla/5.0'})
    print("downloading db...")
    memfile = urllib.request.urlopen(r).read()
    sig = urllib.request.urlopen(rs).read()
    mfhash = SHA384.new(memfile)
    key = RSA.import_key(open(keyfile).read())
    pkcs1_15.new(key).verify(mfhash, sig)
    makedirs(path, exist_ok=True)
    f = open(path / "ofmanifest.db", 'wb')
    f.write(memfile)
    f.close()
    print("done!")


def download_file_multi(path, fhash, sig, prefix, publickey):
    filename = Path(path)
    req = url + str(PurePosixPath(filename))
    path = prefix / filename
    print(req)
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    u = urllib.request.urlopen(r)
    if str(filename.parents[0]) != '.':
        spath = path.parents[0]
        makedirs(spath, exist_ok=True)
    memfile = u.read()
    u.close()
    if memfile:
        memfile = decompress(memfile)
    new_hash = SHA384.new(memfile)
    if new_hash.hexdigest() != fhash and hashing == True:
        raise ArithmeticError("HASH INVALID for file {}".format(filename))
    if sig and signing == True:
        key = RSA.import_key(publickey)
        pkcs1_15.new(key).verify(new_hash, sig)
        print("Signature valid!")
    f = open(path, 'wb')
    print(path)
    f.write(memfile)
    f.close()
    print("File download complete!")


def argvparse():
    global prefix
    global keyfile
    global signing
    global hashing
    global url
    global nproc
    global cfg_write
    uhelp = """\
Usage: ofatomic -p . [-k (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing] [--disable-signing]
Command line launcher/installer for Open Fortress.
  -p: Choose desired path for installation. Mandatory.
  -k: Specify public key file to verify signatures against. Default is the current OF public key (ofpublic.pem).
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  -h: Displays this help message.
  --disable-hashing: Disables hash checking when downloading.
  --disable-signing: Disables signature checking when downloading.
  --cfg-overwrite: Overwrite existing .cfg files. Off by default."""

    #
    parser = ArgumentParser()
    parser.add_argument("-p",
                        dest="path",
                        required=True,
                        action="store",
                        type=str,
                        help="Choose desired path for installation. Mandatory.")
    parser.add_argument("-k",
                        dest="key",
                        action="store",
                        type=str,
                        help="Specify public key file to verify signatures against. "
                             "Default is the current OF public key (ofpublic.pem).")
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

    parser.add_argument("--disable-hashing",
                        action="store_false",
                        help="Disables hash checking when downloading.")
    parser.add_argument("--disable-signing",
                        action="store_false",
                        help="Disables signature checking when downloading.")
    parser.add_argument("--cfg-overwrite",
                        action="store_true",
                        help="Overwrite existing .cfg files. Off by default.")

    args = parser.parse_args()
    prefix = args.path

    if args.key is not None:
        keyfile = Path(args.key)
    else:
        keyfile = mpath / Path("ofpublic.pem")

    if args.threads:
        nproc = args.threads

    hashing = args.disable_hashing
    signing = args.disable_signing
    cfg_write = args.cfg_overwrite

    if args.url is not None:
        url = args.url
        if url[-1:] != '/':
            url += '/'

def main():
    global keyfile
    global nproc
    global cfg_write
    global mpath
    argvparse()
    rpath = prefix / Path('launcher/remote/ofmanifest.db')
    lpath = prefix / Path('launcher/local/ofmanifest.db')
    if not (exists(rpath) and getsize(rpath) > 0):
        makedirs(rpath.parents[0], exist_ok=True)
        download_db(rpath.parents[0])
    conn = sqlite3.connect('file:{}'.format(rpath), uri=True)
    if not (lpath.exists() and lpath.stat().st_size > 0):
        makedirs(lpath.parents[0], exist_ok=True)
        nolocal = True
    else:
        nolocal = False
    conn_l = sqlite3.connect('file:{}'.format(lpath), uri=True)
    c = conn.cursor()
    cl = conn_l.cursor()
    c.execute("select path,checksum,signature from files")
    remote = c.fetchall()
    todl = []
    with open(keyfile, 'r') as w:
        keydata = w.read()
    if nolocal:
        todl = [(f[0], f[1], f[2], str(prefix), keydata) for f in remote]
    else:
        local = cl.execute("select path,checksum,signature from files").fetchall()
        for f in remote:
            if f in local:
                continue
            if cfg_write:
                if f[0] in local and ".cfg" in f[0]:
                    continue
            todl.append((f[0], f[1], f[2], str(prefix), keydata))
    if nproc > 1:
        try:
            dpool = Pool(nproc)
            dpool.starmap(download_file_multi, todl)
        except ImportError:
            nproc = 1
    if nproc <= 1:
        starmap(download_file_multi,todl)
    cl.execute('ATTACH DATABASE "{}" AS remote'.format(rpath))
    cl.execute('INSERT OR REPLACE INTO files SELECT * FROM remote.files')
    conn_l.commit()
    conn_l.close()
    conn.close()
    with open(mpath / Path("gameinfo.txt"), 'r') as gd:
        gd_l = open(prefix / Path("gameinfo.txt"), 'w')
        gd_l.write(gd.read())
        gd_l.close()
    print("OF download completed!")
