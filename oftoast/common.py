from typing import TypedDict
from typing import Union
from typing import List
from pathlib import Path
import urllib
import json

TYPE_WRITE = 0
TYPE_MKDIR = 1
TYPE_DELETE = 2

class Change(TypedDict):
	type: int
	path: str
	hash: bytes
	object: str

def replay_changes(changesets: list[list[Change]]) -> list[Change]:
	cumlmap = {}
	if changesets == None:
		return []
	for revision in changesets:
		for change in revision:
			if change["type"] == TYPE_WRITE or TYPE_MKDIR:
				cumlmap[change["path"]] = change
			if change["type"] == TYPE_DELETE:
				cumlmap.pop(change["path"])
	
	return map_to_changes(cumlmap)

# Convert list of changes to dictonary with path as key,
# used for performance reasons.
def changes_to_map(changes: list[Change]) -> dict[str, Change]:
	d = {}
	if changes == None:
		return d
	for x in changes:
		d[x["path"]] = x
	return d

# Inverse of above.
def map_to_changes(changes: dict[str, Change]) -> list[Change]:
	d = []
	for key in changes:
		d.append(changes[key])
	return d

def invert_change(change: Change) -> Change:
	if change["type"] == 0 or 1:
		newchange = change
		newchange["type"] = 2
		return newchange
	else:
		newchange = change
		newchange["type"] = 0
		return newchange

# Returns -1 if nothing is installed.
def get_installed_revision(dir: Path) -> int:
	try: 
		file = open(dir / '.revision', "r")
		return int(file.read())
	except (FileNotFoundError, ValueError):
		return -1

def fetch_latest_revision(url: str) -> int:
	r = urllib.request.urlopen(url + "revisions/latest")
	return int(r.read())

def fetch_revisions(url:str, first: int, last: int) -> list[list[Change]]:
	revisions: List[Change] = []
	for x in range(first, last):
		if not (x < 0):
			r = urllib.request.urlopen(url + "revisions/" + str(x))
			revisions.append(json.load(r))
	return revisions
