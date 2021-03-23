import urllib.request, sqlite3
from zstd import decompress
from os import path, stat, makedirs
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA384
from sys import argv,exit
from Crypto.PublicKey import RSA
from multiprocessing import Pool

global prefix
global key
nproc = 4
help = "ofatomic -p . -k file [-n 4] [--disable-hash] [--disable-signing]\n" \
       "Minimal Launcher/installer for Open Fortress.\n" \
       "-p Choose desired path for installation. Default is the directory this script is located in.\n" \
       "NOTE: Do not specify trailing slash!\n" \
       "-k Specify public key file to verify signatures against.\n" \
       "--disable-hash Disables hash checking when downloading.\n" \
       "-n Amount of threads to be used - choose 1 to disable multithreading. Default is 4."
if '-k' in argv:
    keyfile = argv[argv.index('-k') + 1]
    key = RSA.import_key(open(keyfile).read())
else:
    print("No key file specified!")
    exit(256)
if '-p' in argv:
    prefix = argv[argv.index('-k') + 1] + '/'
if '-n' in argv:
    nproc = int(argv[argv.index('-n') + 1])


def download_db(path):
    req = "https://svn.openfortress.fun/launcher/files/ofmanifest.db"
    req_sig = "https://svn.openfortress.fun/launcher/files/ofmanifest.db"
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    rs = urllib.request.Request(req_sig, headers={'User-Agent': 'Mozilla/5.0'})
    print("downloading db...")
    memfile = urllib.request.urlopen(r).read()
    sig = urllib.request.urlopen(rs).read()
    mfhash = SHA384.new(memfile)
    pkcs1_15.new(key).verify(mfhash, sig)
    makedirs(path, exist_ok=True)
    f = open(path, 'wb')
    f.write(memfile)
    f.close()
    print("done!")


def download_file_multi(arr):
    filename = arr[0]
    hash = arr[1]
    sig = arr[2]
    req = "https://svn.openfortress.fun/launcher/files/{}".format(filename)
    print(req)
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    u = urllib.request.urlopen(r)
    if '/' in filename:
        spath = prefix + filename[:filename.rfind('/')]
        makedirs(spath, exist_ok=True)
    f = open(filename, 'wb')
    memfile = u.read()
    u.close()
    if memfile:
        memfile = decompress(memfile)
    new_hash = SHA384.new(memfile)
    if new_hash.hexdigest() != hash:
        raise ArithmeticError("HASH INVALID for file {}".format(filename))
    print("Hash valid!")
    if sig:
        pkcs1_15.new(key).verify(new_hash, sig)
        print("Signature valid!")
    f.write(memfile)
    f.close()
    print("done!")


try:
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()
    if not path.exists('launcher/remote/ofmanifest.db'):
        raise sqlite3.OperationalError
    elif stat('launcher/remote/ofmanifest.db').st_size == 0:
        raise sqlite3.OperationalError
except sqlite3.OperationalError:
    makedirs("launcher/remote", exist_ok=True)
    download_db("launcher/remote/ofmanifest.db")
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()

try:
    conn_l = sqlite3.connect('file:launcher/local/ofmanifest.db', uri=True)
    cl = conn_l.cursor()
    nolocal = False
    if not path.exists('launcher/local/ofmanifest.db'):
        raise sqlite3.OperationalError
    elif stat('launcher/local/ofmanifest.db').st_size == 0:
        raise sqlite3.OperationalError
except sqlite3.OperationalError:
    makedirs("launcher/local", exist_ok=True)
    conn_l = sqlite3.connect('launcher/local/ofmanifest.db')
    cl = conn_l.cursor()
    nolocal = True
c.execute("select path,checksum,signature from files")
remote = c.fetchall()
todl = []
if nolocal:
    todl = remote
else:
    print("getting local")
    local = cl.execute("select path,checksum,signature from files").fetchall()
    for f in remote:
        if f[1] not in local:
            todl.append(f)
dpool = Pool(nproc)
dpool.map(download_file_multi, todl)
cl.execute('ATTACH DATABASE "launcher/remote/ofmanifest.db" AS remote')
cl.execute('INSERT OR REPLACE INTO files SELECT * FROM remote.files')
conn_l.commit()
conn_l.close()
conn.close()
print("Done!")
