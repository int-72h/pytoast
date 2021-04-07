from Crypto.Hash import SHA384
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from multiprocessing import Pool,cpu_count
from os import path, stat, makedirs
from sys import argv, exit
import sqlite3
import urllib.request
from zstd import decompress

global prefix
global key
global signing
global hashing
global url
signing = True
hashing = True
prefix = ''
nproc = cpu_count()
keyfile = "ofpublic.pem"
url = 'https://svn.openfortress.fun/launcher/files/'


def download_db(path):
    req = url + "ofmanifest.db"
    req_sig = url + "ofmanifest.sig"
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    rs = urllib.request.Request(req_sig, headers={'User-Agent': 'Mozilla/5.0'})
    print("downloading db...")
    memfile = urllib.request.urlopen(r).read()
    sig = urllib.request.urlopen(rs).read()
    mfhash = SHA384.new(memfile)
    pkcs1_15.new(key).verify(mfhash, sig)
    makedirs(path, exist_ok=True)
    f = open(path + "/ofmanifest.db", 'wb')
    f.write(memfile)
    f.close()
    print("done!")


def download_file_multi(arr):
    filename = arr[0]
    hash = arr[1]
    sig = arr[2]
    req = url + filename
    print(req)
    r = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
    u = urllib.request.urlopen(r)
    if '/' in filename:
        spath = prefix + filename[:filename.rfind('/')]
        makedirs(spath, exist_ok=True)
    memfile = u.read()
    u.close()
    if memfile:
        memfile = decompress(memfile)
    new_hash = SHA384.new(memfile)
    if new_hash.hexdigest() != hash and hashing == True:
        raise ArithmeticError("HASH INVALID for file {}".format(filename))
    if sig and signing == True:
        pkcs1_15.new(key).verify(new_hash, sig)
        print("Signature valid!")
    f = open(filename, 'wb')
    f.write(memfile)
    f.close()
    print("done!")


if __name__ == '__main__':
	uhelp = """Usage: ofatomic -k file [-p (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing] [--disable-signing]
Command line launcher/installer for Open Fortress.
  -p: Choose desired path for installation. Default is the directory this script is located in.
  -k: Specify public key file to verify signatures against. Default is the current OF public key (ofpublic.pem).
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  --disable-hashing: Disables hash checking when downloading.
  --disable-signing: Disables signature checking when downloading."""
	if '-k' in argv:
	    keyfile = argv[argv.index('-k') + 1]
	if '-p' in argv:
	    prefix = argv[argv.index('-k') + 1]
	    if prefix[-1:] != '/':
	        prefix = prefix + '/'
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
	if '-h' in argv:
	    print(uhelp)
	    exit(1)
	key = RSA.import_key(open(keyfile).read())
	try:
	    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
	    c = conn.cursor()
	    if not path.exists('launcher/remote/ofmanifest.db'):
	        raise sqlite3.OperationalError
	    elif stat('launcher/remote/ofmanifest.db').st_size == 0:
	        raise sqlite3.OperationalError
	except sqlite3.OperationalError:
	    makedirs("launcher/remote", exist_ok=True)
	    download_db("launcher/remote")
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
	
