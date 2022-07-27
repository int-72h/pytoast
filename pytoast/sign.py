from sys import argv
from pathlib import Path
from subprocess import Popen
if len(argv) < 3:
    print("sign.py toast_dir private_key")
toastdir = argv[1]
privkey = argv[2]
revpath = Path(toastdir)/ "revisions"
with open( revpath / "latest",'r') as x:
    last_rev = x.read()
Popen("openssl dgst -sha256 -sign {0} -out {1}.sig {1}".format(privkey,revpath/"latest"),shell=True)
for x in range(0,int(last_rev)+1):
    Popen("openssl dgst -sha256 -sign {0} -out {1}.sig {1}".format(privkey,revpath/str(x)),shell=True)
