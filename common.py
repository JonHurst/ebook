#!/usr/bin/python3

import os
import shutil
import html
import xml.etree.ElementTree as et

def backup_file(f):
    if not os.path.exists(f): return
    c, bf = 0, f + ".old"
    while os.path.exists(bf):
        c += 1
        bf = f + ".old(%s)" % c
    shutil.copyfile(f, bf)


def fix_entities(text):
    repl = html.entities.entitydefs
    for e in ["quot", "amp", "apos", "lt", "gt"]:
        if e in repl: del repl[e]
    for e in repl:
        text = text.replace("&" + e + ";", repl[e])
    return text


def parse_xhtml(filename):
    text = open(filename).read()
    text = fix_entities(text)
    return et.ElementTree(et.XML(text))
