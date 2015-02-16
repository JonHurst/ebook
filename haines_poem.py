#!/usr/bin/python3

import sys
import subprocess
import xml.etree.ElementTree as ET
import argparse
import collections
import copy
import os
import shutil
import re


def parse_command_line():
    #parse arguments
    parser = argparse.ArgumentParser(description="""\
Replace Al Haines poem markup with something better.""")
    parser.add_argument("input", nargs="?", default="skeleton.xhtml",
                        help="XML Input file")
    return vars(parser.parse_args())


def replace_poem(e):
    old_e = copy.deepcopy(e)
    e.clear()
    e.tag = "{http://www.w3.org/1999/xhtml}div"
    e.attrib["class"] = "poem"
    e.text = "\n"
    s = ET.SubElement(e, "{http://www.w3.org/1999/xhtml}div", {"class": "stanza"})
    s.text = "\n"
    curr_el = ET.SubElement(s, "{http://www.w3.org/1999/xhtml}div")
    curr_el.text = old_e.text
    for el in old_e:
        if el.tag == "{http://www.w3.org/1999/xhtml}br":
            if curr_el.tail:
                curr_el.tail += "\n"
            else:
                curr_el.tail = "\n"
            curr_el = ET.SubElement(s, "{http://www.w3.org/1999/xhtml}div")
            if el.tail and el.tail[0] == "\n":
                curr_el.text = el.tail[1:]
            else:
                curr_el.text = el.tail or ""
        else:
            curr_el.append(el)
    #if last line is empty, remove it
    if not curr_el.text and not curr_el:
        s.remove(curr_el)
    #get indents
    indents = []
    for l in s:
        mo = re.search(r"^ *( *)", l.text)
        indents.append(len(mo.group(1)))
    indent_types = list(set(indents))
    indent_types.sort()
    class_dict = {}
    for c, i in enumerate(indent_types):
        class_dict[i] = "line_i" + str(c)
    for c, l in enumerate(s):
        l.text = l.text.lstrip()
        l.attrib["class"] = class_dict[indents[c]]


def group_stanzas(e):
    for p in e.iter():
        curr_poem = None
        for ch in p:
            if (ch.tag == "{http://www.w3.org/1999/xhtml}div" and
                ch.attrib.get("class") == "poem"):
                if not curr_poem:
                    curr_poem = ch
                else:
                    curr_poem.append(copy.deepcopy(ch[0]))
                    ch.tag = None
                    ch.clear()
            else:
                curr_poem = None



def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    args = parse_command_line()
    root = ET.parse(args["input"])
    body = root.find(".//{http://www.w3.org/1999/xhtml}body")
    for se in body.findall(".//{http://www.w3.org/1999/xhtml}p[@class='poem']"):
        replace_poem(se)
    group_stanzas(body)
    c, backup_filename = 0, args["input"] + ".old"
    while os.path.exists(backup_filename):
        c += 1
        backup_filename = args["input"] + ".old(%s)" % c
    shutil.copyfile(args["input"], backup_filename)
    root.write(args["input"],
               encoding="unicode",
               xml_declaration=True)



if __name__ == "__main__":
    main()
