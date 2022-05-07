import hashlib
import lzma
import argparse
import os
import json
import validators
import urllib.request
import tempfile
from os import makedirs
from itertools import starmap
from pathlib import Path, PurePosixPath
import PySimpleGUI as sg
from sys import exit
from pathos.helpers import cpu_count
from pathos.multiprocessing import ProcessPool as Pool
import pyglet
from common import *


sg.LOOK_AND_FEEL_TABLE['MercPurple'] = {'BACKGROUND': '#443785',
                                        'TEXT': '#FFF4E5',
                                        'INPUT': '#74675F',
                                        'TEXT_INPUT': '#FFF4E5',
                                        'SCROLL': '#FFF4E5',
                                        'BUTTON': ('#FFF4E5', '#74675F'),
                                        'PROGRESS': ('#FFF4E5', '#74675F'),
                                        'BORDER': 1, 'SLIDER_DEPTH': 0,'PROGRESS_DEPTH': 0, }
sg.theme('MercPurple')
def pbar_sg(iter,num_cpus=12,bar_length=80):
    length = len(iter)
    layout = [[sg.Text('Downloading...'),sg.P(),sg.T(key='file')],
              [sg.ProgressBar(max_value=length, orientation='h', size=(bar_length,20), key='progress')]]
    window = sg.Window('OFtoast', layout, finalize=True)
    progress_bar = window['progress']
    file = window['file']
    pool = Pool(num_cpus)
    map_func = getattr(pool, 'uimap')
    z = 0
    for item,it in zip(map_func(download_file_multi, iter),iter):
        z = z+1
        file.update(it[0])
        progress_bar.update(z)
        yield item
    pool.clear()

def sbar_sg(iter,bar_length=80):
    length = len(iter)
    layout = [[sg.Text('Downloading...'),sg.P(),sg.T(key='file')],
              [sg.ProgressBar(max_value=length, orientation='h', size=(bar_length,20), key='progress')]]
    window = sg.Window('OFtoast', layout, finalize=True)
    progress_bar = window['progress']
    file = window['file']
    z = 0
    for item in iter:
        t = download_file_multi(item)
        z = z+1
        file.update(item[0])
        progress_bar.update(z)
        yield t
    pool.clear()

def download_files(arr: list[Change]):
    path, hash, local = arr
    filename = Path(path)
    path = prefix / filename
    if not local:
        req = url + str(PurePosixPath(filename))
        print(req)
        try:
            r = urllib.request.Request(req, headers={'User-Agent': 'oftoast/0.0.1'})
            u = urllib.request.urlopen(r)
        except ConnectionResetError:
            print("Timed out! you're going to have to redownload...")
            return 1
    else:
        u = open(Path(url) / filename,'rb')
    if str(path.parents[0]) != '.':
        spath = path.parents[0]
        makedirs(spath, exist_ok=True)
    memfile = u.read()
    u.close()
    if memfile:
        new_hash = hashlib.sha512(memfile).hexdigest()
        memfile = lzma.decompress(memfile)
        if new_hash != hash:
            raise ArithmeticError("HASH INVALID for file {}".format(filename))
    f = open(path, 'wb')
    f.write(memfile)
    f.close()

def get_revision(url: str, revision: int) -> list[Change]:
	r = urllib.request.urlopen(url + "/" + str(revision), headers={'User-Agent': 'oftoast/0.0.1'}).read()
	return json.loads(r)

def download_db(path,local=False):
    if not local:
        req = url + "oftoast.json"
        r = urllib.request.Request(req, headers={'User-Agent': 'oftoast/0.0.1'})
        print("downloading db...")
        memfile = urllib.request.urlopen(r).read()
    else:
        f = open(Path(url) / "oftoast.json",'r')
        memfile = f.read()
        f.close()
    if (path / "oftoast.json").exists():
        f = open(path / "oftoast.json", 'r')
        old = f.read()
        f.close()
        return [memfile, old]
    else:
        makedirs(path, exist_ok=True)
        return [memfile, None]

def gui_loop():
    global prefix
    global url
    global nproc
    global local
    global font

    http_warning = \
"""Using an insecure connection! Files may be maliciously 
modified in transit by third-parties. Please use an 
HTTPS-compatible site unless you know what you're doing.

We are not responsible for any viruses or evil things
that may happen if you ignore this warning."""

    window = sg.Window('OFtoast',
                            [
                                [sg.Image(source=toast_image)],
                                [
                                    sg.T('Installed Revision:'), 
                                    sg.T('None', key="installed_revision")
                                ],
                                [
                                    sg.T('File Destination',font=font, key="destination"),
                                    sg.Input(key="folder", enable_events=True, visible=False),
                                    sg.FolderBrowse(font=font, target="folder", key="browse"),
                                ],
                                [sg.pin(sg.T(http_warning, visible=False, key="http_warning"))],
                                [
                                    sg.Push(),
                                    sg.T('Download URL',font=font),sg.I(key="url", enable_events=True)
                                ],
                                [
                                    sg.B('Update',font=font,disabled=True,enable_events=True), 
                                    sg.B('Cancel',font=font,enable_events=True)
                                ]
                            ] 
                            ,element_justification='c')

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Cancel":
            exit(1)
        if event == "url":
            if validators.url(values["url"]) and values["url"].endswith("/"):
                window["Update"].update(disabled=False)
                if values["url"].startswith("http://"):
                    window["http_warning"].update(visible=True)
                else:
                    window["http_warning"].update(visible=False)

            else:
                window["Update"].update(disabled=True)
                window["http_warning"].update(visible=False)

        if event == "folder":
            revision = get_installed_revision(Path(values["folder"]))
            if revision >= 0:
                window["installed_revision"].update(str(revision))
            else:
                window["installed_revision"].update("None")

            window["destination"].update(values["folder"])
        
        if event == "Update":
            window["Update"].update(disabled=True)
            window["Cancel"].update(disabled=True)
            window["browse"].update(disabled=True)

            game_path = Path(values["folder"])

            installed_revision = -1

            installed_revision = get_installed_revision(game_path)

            latest_revision = fetch_latest_revision(values["url"])

            revisions = fetch_revisions(values["url"], installed_revision, latest_revision)
            changes = replay_changes(revisions)

            temp_dir = tempfile.TemporaryDirectory()
            temp_path = Path(temp_dir.name)

            for x in changes:
                print(x)
                if x["type"] == TYPE_WRITE:
                    urllib.request.urlretrieve(values["url"] + "/objects/" + x["object"], temp_path / x["object"])
            
            try:
                os.remove(game_path / ".revision")
            except FileNotFoundError:
                pass

            for x in list(filter(lambda x: x["type"] == TYPE_DELETE, changes)):
                try:
                    os.remove(game_path / x["path"])
                except FileNotFoundError:
                    pass

            for x in list(filter(lambda x: x["type"] == TYPE_MKDIR, changes)):
                try:
                    os.mkdir(game_path / x["path"], 0o777)
                except FileExistsError:
                    pass
            
            for x in list(filter(lambda x: x["type"] == TYPE_WRITE, changes)):
                os.rename(temp_path / x["object"], str(game_path) + "/" + x["path"])
            
            (game_path / ".revision").touch(0o777)
            (game_path / ".revision").write_text(str(latest_revision))

            window["Update"].update(disabled=False)
            window["Cancel"].update(disabled=False)
            window["browse"].update(disabled=False)
            

def main():
    global prefix
    global hashing
    global url
    global nproc
    global local
    global font
    try:
        pyglet.font.add_file(r"./Staatliches-Regular.ttf")
        font = ("Staatliches Regular",15)
    except:
        font = ("Liberation Sans",15)
    print(font)
    gui_loop()

toast_image = b'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'

main()
