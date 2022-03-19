import hashlib
import json
import os
import lzma
from glob import iglob
from sys import argv
from pathlib import Path
from os import makedirs
def main(newdir,targetdir='.'):
    try:
        targetdir = Path(targetdir)
        newdir = Path(newdir)
        z = open(newdir / 'oftoast.json', 'r')
        oldtable = json.load(z)
        z.close()
    except:
        oldtable = {}
    jarray = {}
    for file in iglob(str(targetdir / '**'),recursive=True):
        file = Path(file)
        if Path(file).is_dir():
            continue
        print(file)
        fi = open(file, 'rb')
        comp = lzma.compress(fi.read())
        fi.close()
        hash = hashlib.sha512(comp).hexdigest()
        try:
            if oldtable[file][0] == hash:
                print('its already there')
                jarray[file] = oldtable[file]
            else:
                print('its changed')
                rev = oldtable[file][1] + 1
                jarray[file] = [hash, rev]
        except KeyError:
            print('not there')
            jarray[str(file)] = [hash, 0]
        makedirs((newdir / file).parents[0], exist_ok=True)
        n = open((newdir / file),'wb')
        n.write(comp)
        n.close()
    f = open(newdir / 'oftoast.json' , 'w')
    json.dump(jarray, f)
    f.close()
if len(argv) < 2:
    print("Needs at least a path to place the compressed files!")
elif '--help' in argv:
    print("oftoaster dest src\nCompresses all the files, and generates a tasty JSON file.")
else:
    main(argv[1],argv[2])

# file: [hash,rev]
