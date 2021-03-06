import urllib.request,os,sqlite3
from multiprocessing import Pool

def download_file(filename,path=None):
    r = urllib.request.Request("https://svn.openfortress.fun/launcher/files/{}".format(filename), headers={'User-Agent': 'Mozilla/5.0'})
    print("downloading...")
    u = urllib.request.urlopen(r)
    os.makedirs(filename[:filename.rfind('/')],exist_ok=True)
    if path:
        f = open(path, 'wb')
    else:
        f = open(filename, 'wb')
    f.write(u.read())
    f.close()



def download_files_threaded(todownload,path=None,nproc=1):
    dpool = Pool(nproc)
    if path:
        dpool.map(download_file,todownload,path)
    else:
        dpool.map(download_file,todownload)

try:
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()
except sqlite3.OperationalError:
    os.makedirs("launcher/remote", exist_ok=True)
    download_files_threaded("ofmanifest.db","launcher/remote/ofmanifest.db")
    conn = sqlite3.connect('file:launcher/remote/ofmanifest.db', uri=True)
    c = conn.cursor()

