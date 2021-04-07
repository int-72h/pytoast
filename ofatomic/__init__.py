from Crypto.Hash import SHA384
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from multiprocessing import Pool,cpu_count
from os import stat, makedirs
from os.path import exists,getsize
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
keyfile = ''
nproc = cpu_count()
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

def argvparse():
	uhelp = """Usage: ofatomic -k file [-p (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing] [--disable-signing]
Command line launcher/installer for Open Fortress.
  -p: Choose desired path for installation. Default is the directory this script is located in.
  -k: Specify public key file to verify signatures against. Default is the current OF public key (ofpublic.pem).
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  -h: Displays this help message.
  --disable-hashing: Disables hash checking when downloading.
  --disable-signing: Disables signature checking when downloading."""
	if '-k' in argv:
		keyfile = argv[argv.index('-k') + 1]
	else:
		keyfile = "ofpublic.pem"
	if '-p' in argv:
		prefix = argv[argv.index('-p') + 1]
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
	global key
	key = RSA.import_key(open(keyfile).read())
		
def main():
	argvparse()
	rpath = prefix + 'launcher/remote/ofmanifest.db'
	lpath = prefix + 'launcher/local/ofmanifest.db'
	if not (exists(rpath) and getsize(rpath) > 0):
		 makedirs('/'.join(rpath.split('/')[:-1]), exist_ok=True)
		 download_db('/'.join(rpath.split('/')[:-1]))
	conn = sqlite3.connect('file:{}'.format(rpath), uri=True)
	c = conn.cursor()
	if not (exists(lpath) and getsize(lpath) > 0):
		 makedirs('/'.join(lpath.split('/')[:-1]), exist_ok=True)
		 nolocal = True
	else:
		nolocal = False
	conn_l = sqlite3.connect('file:{}'.format(lpath), uri=True)
	cl = conn.cursor()
	c.execute("select path,checksum,signature from files")
	remote = c.fetchall()
	todl = []
	if nolocal:
		todl = remote
	else:
		local = cl.execute("select path,checksum,signature from files").fetchall()
		for f in remote:
			if f[1] not in local:
				todl.append(f)
	dpool = Pool(nproc)
	dpool.map(download_file_multi, todl)
	cl.execute('ATTACH DATABASE "{}" AS remote'.format(rpath))
	cl.execute('INSERT OR REPLACE INTO files SELECT * FROM remote.files')
	conn_l.commit()
	conn_l.close()
	conn.close()
	print("Done!")
	
