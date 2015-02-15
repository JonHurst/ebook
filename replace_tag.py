#!/usr/bin/python3

import sys
import xml.etree.ElementTree as ET
import argparse
import os
import shutil


def parse_arguments():
    #parse arguments
    parser = argparse.ArgumentParser(description="""\
    Converts a tag with optional class to a different tag with a different optional class.
    Original file is saved with extension .old.""")
    parser.add_argument("input",
                        help="Input file (xhtml format)")
    parser.add_argument("from",
                        help="tagname or tagname.class to convert from (e.g. 'div' or 'div.para').")
    parser.add_argument("to", nargs="?", default=None,
                        help=("tagname or tagname.class to convert to "
                              "(e.g. 'p' or 'p.noindent'). "
                              "If not specified, from tag is removed rather than replaced."))
    args = vars(parser.parse_args())
    if not os.path.isfile(args["input"]):
        print("Error:", args["input"], "is not a file")
        sys.exit(-1)
    return args


def make_change_list(itree, f):
    i = f.split(".")
    xpath = ".//{http://www.w3.org/1999/xhtml}%s" % i[0]
    if len(i) == 1:
        return itree.findall(xpath)
    elif len(i) == 2:
        change_list = []
        for e in itree.findall(xpath):
            c = e.attrib.get("class", "")
            if c.find(i[1]) != -1:
                change_list.append(e)
        return change_list


def replace_tags(change_list, to):
    o = to.split(".")
    if len(o) == 2:
        for e in change_list:
            e.tag = o[0]
            e.attrib["class"] = O[1]
    elif len(o) == 1:
        for e in change_list:
            e.tag = o[0]
            if "class" in e.attrib: del e.attrib["class"]


def remove_tags(change_list):
    clear = False
    content = False
    for e in change_list:
        if len(e) or e.text:
            content = True
            break
    if content:
        ans = ""
        while ans != "y" and ans != "n":
            ans = input("Removed tag has content. Clear content? [y|n]: ")
        if ans == "y": clear = True
    for e in change_list:
        e.tag = None
    if clear:
        for e in change_list:
            t = e.tail
            e.clear()
            e.tail = t


def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    args = parse_arguments()
    shutil.copyfile(args["input"], args["input"] + ".old")
    itree = ET.parse(args["input"])
    change_list = make_change_list(itree, args["from"])
    if args["to"]:
        replace_tags(change_list, args["to"])
    else:
        remove_tags(change_list)
    itree.write(args["input"],
            encoding="unicode",
            xml_declaration=True)


if __name__ == "__main__": main()
