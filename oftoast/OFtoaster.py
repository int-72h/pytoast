import hashlib
import json
import lzma
from glob import iglob
from sys import argv
from pathlib import Path
from os import makedirs
from p_tqdm import p_uimap

def work(fil):
    file = fil[0]
    oldtable = fil[1]
    newdir = fil[2]
    jarray = {}
    pfile = Path(file)
    if pfile.is_dir():
        return jarray
    fi = open(pfile, 'rb')
    comp = lzma.compress(fi.read())
    fi.close()
    hash = hashlib.sha512(comp).hexdigest()
    try:
        if oldtable[file][0] == hash:
            jarray[file] = oldtable[file]
        else:
            rev = oldtable[file][1] + 1
            jarray[file] = [hash, rev]
    except KeyError:
        jarray[file] = [hash, 0]
    makedirs((newdir / pfile).parents[0], exist_ok=True)
    n = open((newdir / pfile), 'wb')
    n.write(comp)
    n.close()
    return jarray


def main(newdir, targetdir='.'):
    try:
        targetdir = Path(targetdir)
        newdir = Path(newdir)
        z = open(newdir / 'oftoast.json', 'r')
        oldtable = json.load(z)
        z.close()
    except:
        oldtable = {}
    jarray = {}
    iters = [(file,oldtable,newdir) for file in iglob(str(targetdir / '**'), recursive=True)]
    [jarray.update(x) for x in p_uimap(work,iters)]
    f = open(newdir / 'oftoast.json', 'w')
    json.dump(jarray, f)
    f.close()


if len(argv) < 2:
    print("Needs at least a path to place the compressed files!")
elif '--help' in argv:
    print("oftoaster dest src\nCompresses all the files, and generates a tasty JSON file.")
else:
    main(argv[1], argv[2])

# file: [hash,rev]
