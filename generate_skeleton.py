#!/usr/bin/python3

import sys
import xml.etree.ElementTree as ET
import argparse
import os
import shutil

template = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>%title</title>
  <meta name="author" content="%author"/>
  <link rel="stylesheet" type="text/css" href="gs_styles.css"/>

  <link href="include/skel_styles.css" rel="stylesheet" type="text/css" />
  <script src="include/jquery-1.10.2.min.js" type="text/javascript" />
  <script src="include/script.js" type="text/javascript" />
</head>
<body>
  <div id="title_page">
  <h1><span class="title">%title</span><br />
  <span style="font-size:medium;">by</span><br />
  <span class="author">%author</span></h1>
  </div>
  
  </body>
</html>
"""

def generate_chapters(el, n, sh, indent=""):
    """Generate n chapters under el"""
    for c in range(n):
        ch = ET.SubElement(el, "{http://www.w3.org/1999/xhtml}div", {"class": "chapter"})
        ch.text = "\n    " + indent
        ch.tail = "\n  " + indent
        hd = ET.SubElement(ch, "{http://www.w3.org/1999/xhtml}h1", {"class": "chapter_heading"})
        hd.text = "Chapter " + str(c + 1)
        if sh:
            br = ET.SubElement(hd, "{http://www.w3.org/1999/xhtml}br")
            br.tail = "\n    " + indent
            shd = ET.SubElement(hd, "{http://www.w3.org/1999/xhtml}span", {"class": "sub_heading"})
            shd.text = " "
        hd.tail = "\n\n   " + indent
    ch.tail = "\n\n" + indent


def generate_section(el, sn, nc, sh):
    """Generate section named "Section sn" and generate chapters under it"""
    s = ET.SubElement(el, "{http://www.w3.org/1999/xhtml}div", {"class": "section"})
    s.text = "\n    "
    s.tail = "\n\n  "
    hd = ET.SubElement(s, "{http://www.w3.org/1999/xhtml}h1", {"class": "section_heading"})
    hd.text = "Section " + str(sn)
    hd.tail = "\n    "
    generate_chapters(s, nc, sh, "  ")


def main():
    #parse arguments
    parser = argparse.ArgumentParser(
        description="Generates a sane skeleton.")
    parser.add_argument("-c", "--chapters", action="append", required=True,
                        help="Chapters to generate. If multiple, makes multiple sections.")
    parser.add_argument("-s", "--subheading", action="store_true",
                        help="Include template for sub-headings")
    parser.add_argument("output", nargs="?", default="genskel.xhtml",
                        help="Output file (xhtml format)")
    args = vars(parser.parse_args())
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    otree = ET.XML(template)
    body = otree.find(".//{http://www.w3.org/1999/xhtml}body")
    if len(args["chapters"]) == 1:
        generate_chapters(body, int(args["chapters"][0]), args["subheading"])
    else:
        for sn, c in enumerate(args["chapters"]):
            generate_section(body, int(sn) + 1, int(c), args["subheading"])
    ET.ElementTree(otree).write(args["output"],
                                encoding="unicode",
                                xml_declaration=True)




if __name__ == "__main__": main()
