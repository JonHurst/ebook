#!/usr/bin/python3

import sys
import xml.etree.ElementTree as ET
import argparse
import collections
import os


def parse_command_line():
    #parse arguments
    parser = argparse.ArgumentParser(description="""\
Inventory an xhtml file.""")
    parser.add_argument("input",
                        help="XML Input file")
    return vars(parser.parse_args())


def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    args = parse_command_line()
    root = ET.parse(args["input"])
    body = root.find(".//{http://www.w3.org/1999/xhtml}body")
    e = collections.Counter([(X.tag, X.get("class", ""), X.get("style", "")) for X in body.iter()])
    print("The following tags were found as descendants of body:")
    for p, n in e.most_common():
        s = p[0].replace("{http://www.w3.org/1999/xhtml}", "")
        if p[1]: s += " class=\"" + p[1] + "\""
        if p[2]: s += " style=\"" + p[2] + "\""
        print(" ", n, ":", s)


if __name__ == "__main__":
    main()
