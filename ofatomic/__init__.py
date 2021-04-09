from Crypto.Hash import SHA384
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from multiprocessing import Pool, cpu_count
from os import makedirs
from os.path import exists, getsize
from sys import argv, exit
import sqlite3
import urllib.request
from zstd import decompress
from pathlib import Path, PurePosixPath

global prefix
global keyfile
global signing
global hashing
global url
signing = True
hashing = True
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


def download_file_multi(arr_p):
    prefix = arr_p[1]
    arr = arr_p[0]
    filename = Path(arr[0])
    hash = arr[1]
    sig = arr[2]
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
    if new_hash.hexdigest() != hash and hashing == True:
        raise ArithmeticError("HASH INVALID for file {}".format(filename))
    if sig and signing == True:
        keydata = Path(arr_p[2])
        key = RSA.import_key(keydata)
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
    uhelp = """\
Usage: ofatomic -p . [-k (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing] [--disable-signing]
Command line launcher/installer for Open Fortress.
  -p: Choose desired path for installation. Mandatory.
  -k: Specify public key file to verify signatures against. Default is the current OF public key (ofpublic.pem).
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  -h: Displays this help message.
  --disable-hashing: Disables hash checking when downloading.
  --disable-signing: Disables signature checking when downloading."""
    if len(argv) == 1:
        print(uhelp)
        exit()
    if '-h' in argv:
        print(uhelp)
        exit()
    if '-p' in argv:
        prefix = Path(argv[argv.index('-p') + 1])
    if '-k' in argv:
        keyfile = Path(argv[argv.index('-k') + 1])
    else:
        keyfile = Path("ofpublic.pem")
    if '-n' in argv:
        nproc = int(argv[argv.index('-n') + 1])
    if '--disable-hashing' in argv:
        hashing = False
    if '--disable-signing' in argv:
        signing = False
    if '-u' in argv:
        url = argv[argv.index('-u') + 1]
        if url[-1:] != '/':
            url += '/'


def main():
    global keyfile
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
    cl = conn.cursor()
    c.execute("select path,checksum,signature from files")
    remote = c.fetchall()
    todl = []
    keydata = open(keyfile).read()
    if nolocal:
        for f in remote:
            if f[2]:
                todl.append([f, str(prefix), str(keydata)])
            else:
                todl.append([f, str(prefix)])
    else:
        local = cl.execute("select path,checksum,signature from files").fetchall()
        for f in remote:
            if f[1] not in local:
                if f[2]:
                    todl.append([f, str(prefix), str(keydata)])
                else:
                    todl.append([f, str(prefix)])
    dpool = Pool(nproc)
    dpool.map(download_file_multi, todl)
    cl.execute('ATTACH DATABASE "{}" AS remote'.format(rpath))
    cl.execute('INSERT OR REPLACE INTO files SELECT * FROM remote.files')
    conn_l.commit()
    conn_l.close()
    conn.close()
    with open("gameinfo.txt", 'r') as gd:
        gd_l = open(prefix / Path("gameinfo.txt"), 'w')
        gd_l.write(gd.read())
        gd_l.close()
    print("OF download completed!")
