#!/usr/bin/python3

import sys
import xml.etree.ElementTree as ET
import argparse
import os
import shutil


def main():
    #parse arguments
    parser = argparse.ArgumentParser(description="""\
    Converts a tag with optional class to a different tag with a different optional class.
    Original file is saved with extension .old.""")
    parser.add_argument("from",
                        help="tagname or tagname.class to convert from (e.g. 'div' or 'div.para').")
    parser.add_argument("to",
                        help="tagname or tagname.class to convert to (e.g. 'p' or 'p.noindent' or ''.")
    parser.add_argument("input",
                        help="Input file (xhtml format)")
    args = vars(parser.parse_args())
    if not os.path.isfile(args["input"]):
        print("Error:", args["input"], "is not a file")
        sys.exit(-1)
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    shutil.copyfile(args["input"], args["input"] + ".old")
    i = args["from"].split(".")
    o = args["to"].split(".")
    itree = ET.parse(args["input"])
    if len(i) == 2:
        xpath = ".//{http://www.w3.org/1999/xhtml}%s[@class='%s']" % tuple(i)
    else:
        xpath = ".//{http://www.w3.org/1999/xhtml}%s" % i[0]
    tag = None
    if o[0] != '': tag = "{http://www.w3.org/1999/xhtml}" + o[0]
    for e in itree.findall(xpath):
        e.tag = tag
        del e.attrib["class"]
        if len(o) == 2:
            e.set("class", o[1])
    itree.write(args["input"],
            encoding="unicode",
            xml_declaration=True)


if __name__ == "__main__": main()
