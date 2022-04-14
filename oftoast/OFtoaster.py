# A Change is an operation to a filesystem, such as writen file, or deleted one.
# A Changeset is a list of changes. Cumulative changes are a list of changes
# that are the result of applying a range of changesets (referred to as playback).
# In practice, it represents a complete filesystem and is used as such.
#
# Typing is used heavily because correctness of objects is a massive concern,
# and unfortunately Python is a bit flimsy in that regard.
#
# The filesyste/format is as follows, assuming "tvs" is the root:
# 
# tvs/cumlcache contains a cache of the cumulative changeset of the latest
# revision. This is used for internal processing, is not a part of the spec, 
# and should not be made accessible to the client.
#
# tvs/objects/ contains file objects, each with a unique ID. Changes refer to
# these files mapped to a path. The ID format is an arbitrary ASCII string
# (in this implementation it's a UUID.) Objects ending in ".sig" are reserved
# for signatures. This isn't likely to be implemented since objects are likely 
# going to be served over a secure connection anyways.
# 
# tvs/revisions/ contains sequential enumerated files representing revisions.
# Each of them contains an array of Change, which has information stored in
# JSON.
#
# "path" is the relative path to the root of the installation. It must use
# forward slashes, and cannot start with "./", and must be POSIX compliant. 
# For example: "resources/merc.png". "type" represents the type of operation as a number.
# Zero is write representing added and modified files, one represents new directories, and two represents a
# deleted file/directory.
# "object" is the ID of the object avaliable under tvs/objects. May be omitted or
# null if the type is a created directory.
# "hash" is the md5 hash of the object, used for checking for incidential file
# corruption and internally for comparing files.

from typing import TypedDict
from typing import Union
import uuid
import os
import pathlib
import shutil
import uuid
import posixpath
import sys
import hashlib
import json

TYPE_WRITE = 0
TYPE_MKDIR = 1
TYPE_DELETE = 2

class Change(TypedDict):
	type: int
	path: str
	hash: bytes
	object: str

def invert_change(change: Change) -> Change:
	if change["type"] == 0 or 1:
		newchange = change
		newchange["type"] = 2
		return newchange
	else:
		newchange = change
		newchange["type"] = 0
		return newchange

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

# Compares two cumulative changesets (which is used as a representation of
# the filesystem) and generates a changeset with the differences between
# the two.
def compare_cuml_changes(old: list[Change], new: list[Change]) -> list[Change]:
	oldmap = changes_to_map(old)
	newmap = changes_to_map(new)
	changes = []
	if new is not None:
		for x in new:
			if x["path"] not in oldmap or x["path"] != TYPE_MKDIR and oldmap[x["path"]]["hash"] != x["hash"]:
				changes.append(x)

	if old != None:
		for x in old:
			if x["path"] not in newmap:
				changes.append(invert_change(x))

	return changes

# Converts a filesystem to a cumulative changelist.
def fs_to_accu_changes(path: pathlib.PosixPath) -> list[Change]:
	changes = []
	def errhandler(exception):
		print(exception, file=sys.stderr)
		exit(1)
	for dirpath, directories, files in os.walk(path, onerror=errhandler):
		for name in files:
			b = open(posixpath.join(dirpath,name), 'rb').read()
			hash = hashlib.md5(b)
			changes.append({ 
				"type": TYPE_WRITE,
				"path": posixpath.relpath(posixpath.join(dirpath,  name), path),
				"hash": hash.hexdigest(),
				"object": None
			})

		for name in directories:
			changes.append({
				"type": TYPE_MKDIR,
				"path": posixpath.relpath(posixpath.join(dirpath,  name), path),
				"hash": None,
				"object": None
			}
			)

	return changes

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

def read_file(path: Union[str, pathlib.PosixPath]) -> list[Change]:
	file = open(path, "r")
	revision = json.load(file)
	return revision

def print_usage():
	print(sys.argv[0] + " <source toasted directory> <game files>", file=sys.stderr)
	exit(1)

def main():
	if len(sys.argv) != 3:
		print_usage()

	tvsdir = pathlib.PosixPath(sys.argv[1])
	srcfs = pathlib.PosixPath(sys.argv[2])
	
	# Make the tvs directories if they don't exist.
	os.umask(0)
	os.makedirs(tvsdir / 'objects', 0o777, exist_ok=True)
	os.makedirs(tvsdir / 'revisions', 0o777, exist_ok=True)

	cumlcache = []
	head_version = 0

	# Try to open the cumlcache
	try: 
		file = open(tvsdir / 'cumlcache', "r")
		cumlcache = json.load(file)
		file.close()
	# If it doesn't exist, or it's empty, generate it.
	except:
		(tvsdir / 'cumlcache').touch()
		i = 0
		revisions = []
		# Read files under tvs/revisions number by number until
		# we reach a revision that doesn't exist.
		while 1 == 1:
			dir = tvsdir / 'revisions' / str(i)
			if not os.path.isfile(dir):
				break

			revision = read_file(dir)

			revisions.append(revision)
			
			i = i + 1
		
		head_version = i

		cumlcache = {
			"revision": head_version - 1,
			"changes": replay_changes(revisions)
		}

	fscuml = fs_to_accu_changes(srcfs)
	changes = compare_cuml_changes(cumlcache["changes"], fscuml)
	
	if len(changes) == 0:
		print("No changes found.", file=sys.stderr)
		exit(0)

	# Iterate over new revision
	for x in changes:
		# Print changes to stdout for piping.
		if x["type"] is TYPE_WRITE:
			print("W ", end='')
		if x["type"] is TYPE_MKDIR:
			print("F ")
		if x["type"] is TYPE_DELETE:
			print("D ", end='')

		print(x["path"])

		# Populate changes with uuids and copy files to tvs/objects/.
		if x["type"] is TYPE_WRITE:
			object_id = str(uuid.uuid1())
			shutil.copy2(srcfs / x["path"], tvsdir / 'objects' / object_id)
			x["object"] = object_id

	# Save new revision
	new_version_dir = tvsdir / 'revisions' / str(head_version)
	new_version_dir.touch(0o777)
	file = open(new_version_dir, "w")
	json.dump(changes, file)

	# Update cache
	cache_dir  = tvsdir / 'cumlcache'
	cache_dir.touch(0o777)
	cumlcache = {
		"version": head_version,
		"changes": replay_changes([cumlcache["changes"], changes])
	}

	file = open(cache_dir, "w")
	json.dump(cumlcache, file)

if __name__ == "__main__":
	main()
