import urllib.request, os, sqlite3, zstd, hashlib
from multiprocessing import Pool
global prefix
prefix = ''

def download_db(path):
    req = "https://svn.openfortress.fun/launcher/files/ofmanifest.db"
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    print("downloading...")
    u = urllib.request.urlopen(r)
    os.makedirs(path, exist_ok=True)
    f = open(path, 'wb')
    f.write(u.read())
    f.close()
    print("done!")

def download_file_multi(arr):
    filename = arr[0]
    hash = arr[1]
    req = "https://svn.openfortress.fun/launcher/files/{}".format(filename)
    print(req)
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    u = urllib.request.urlopen(r)
    if '/' in filename:
        spath = prefix + filename[:filename.rfind('/')]
        os.makedirs(spath, exist_ok=True)
    f = open(filename, 'wb')
    memfile = u.read()
    memffile = zstd.decompress(memfile)
    newhash = hashlib.md5(memffile).hexdigest()
    if newhash != hash:
        print(hashlib.md5(memfile).hexdigest())
        print(hash)
        raise ArithmeticError("HASH INVALID for file {}".format(filename))
    print("Hash valid!")
    f.write(memfile)
    f.close()
    print("done!")

try:
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()
    if not os.path.exists('launcher/remote/ofmanifest.db'):
        raise sqlite3.OperationalError
    elif os.stat('launcher/remote/ofmanifest.db').st_size == 0:
        raise sqlite3.OperationalError
except sqlite3.OperationalError:
    os.makedirs("launcher/remote", exist_ok=True)
    download_db("launcher/remote/ofmanifest.db")
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()

try:
    conn_l = sqlite3.connect('file:launcher/local/ofmanifest.db', uri=True)
    cl = conn_l.cursor()
    nolocal = False
    if not os.path.exists('launcher/local/ofmanifest.db'):
        raise sqlite3.OperationalError
    elif os.stat('launcher/local/ofmanifest.db').st_size == 0:
        raise sqlite3.OperationalError
except sqlite3.OperationalError:
    os.makedirs("launcher/local", exist_ok=True)
    conn_l = sqlite3.connect('launcher/local/ofmanifest.db')
    cl = conn_l.cursor()
    nolocal = True
c.execute("select path,checksum from files")
remote = c.fetchall()
todl = []
if nolocal:
    todl = remote
else:
    print("getting local")
    local = cl.execute("select path,checksum from files").fetchall()
    for f in remote:
        if f[1] not in local:
            todl.append(f)
dpool = Pool(6)
dpool.map(download_file_multi, todl)
help = "ofatomic -p . [--disable-hash] [--disable-signing]\n" \
       "Minimal Launcher for Open Fortress.\n" \
       "-p Choose desired path for installation. Default is the directory this script is located in.\n" \
       "--disable-hash Disables hash checking when downloading."
