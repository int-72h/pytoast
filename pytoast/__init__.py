from pathlib import Path
import json
import httpx
from Crypto.Hash import SHA256
from Crypto.Signature import DSS
from Crypto.PublicKey import ECC
TYPE_WRITE = 0
TYPE_MKDIR = 1
TYPE_DELETE = 2


def replay_changes_nodel(changesets):
	return list(filter(lambda x: x["type"] != TYPE_DELETE, replay_changes(changesets)))

def replay_changes(changesets):
	cumlmap = {}
	if changesets == None:
		return []
	for revision in changesets:
		for change in revision:
			if type(change) == dict:
				cumlmap[change["path"]] = change
	return map_to_changes(cumlmap)

# Convert list of changes to dictonary with path as key,
# used for performance reasons.
def changes_to_map(changes):
	d = {}
	if changes == None:
		return d
	for x in changes:
		d[x["path"]] = x
	return d

# Inverse of above.
def map_to_changes(changes):
	d = []
	for key in changes:
		d.append(changes[key])
	return d

def invert_change(change):
	if change["type"] == 0 or 1:
		newchange = change
		newchange["type"] = 2
		return newchange
	else:
		newchange = change
		newchange["type"] = 0
		return newchange

# Returns -1 if nothing is installed.
def get_installed_revision(dir):
	try: 
		file = open(dir / '.revision', "r")
		return int(file.read())
	except (FileNotFoundError, ValueError):
		return -1

def fetch_latest_revision(url,key=None):
	r = httpx.get(url + "revisions/latest")
	if key:
			s = httpx.get(url + "revisions/latest.sig")
			h = SHA256.new(r.text.encode('utf-8'))
			DSS.new(key, 'fips-186-3').verify(h, s.read())
	return int(r.text)

def fetch_revisions(url,first,last,key=None):
	revisions = []
	for x in range(first+1, last+1):
		if not (x < 0):
			#r = urllib.request.urlopen(url + "revisions/" + str(x))
			r = httpx.get(url + "revisions/" + str(x))
			if key:
				s = httpx.get(url + "revisions/" + str(x) + '.sig')
				h = SHA256.new(r.text.encode('utf-8'))
				DSS.new(key,'fips-186-3').verify(h,s.read())
			j = json.loads(r.text)
			revisions.append(j)
	return revisions
