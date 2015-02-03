#!/usr/bin/python3

import sys
import subprocess
import xml.etree.ElementTree as ET
import argparse
import collections

bsp_template = """\
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>BSPs</title>
<style type="text/css">
div {border: 1px dotted green; padding:0.5em; color:green; margin:1em;}
p{color:black;}</style>
</head>
<body/>
</html>"""


skeleton_headers = """\
<skel-headers xmlns="http://www.w3.org/1999/xhtml">

<link rel="stylesheet" type="text/css" href="include/skel_styles.css"/>
<script src="include/jquery-1.10.2.min.js" type="text/javascript"/>
<script src="include/script.js" type="text/javascript" />
</skel-headers>
"""

title_page_template = """\
<div id="title_page" xmlns="http://www.w3.org/1999/xhtml">
  <h1><span class="title">title</span><br/>
  <span style="font-size:medium;">by</span><br/>
  <span class="author">author</span></h1>
</div>
"""


def make_bog_standard_para_p(args, fail_list):
    allowable_para_classes = []
    if args["class"]:
        allowable_para_classes = args["class"]
    allowable_tags = ["{http://www.w3.org/1999/xhtml}i",
                      "{http://www.w3.org/1999/xhtml}em",
                      "{http://www.w3.org/1999/xhtml}b",
                      "{http://www.w3.org/1999/xhtml}strong"]
    if args["tag"]:
        allowable_tags.extend(["{http://www.w3.org/1999/xhtml}" + X for X in args["tag"]])
    allowable_span_classes = [None, "smcap"]
    if args["span_class"]:
        allowable_span_classes.extend(args["span_class"])
    def bog_standard_para_p(e):
        if (e.tag != "{http://www.w3.org/1999/xhtml}p" or
            (e.get("class") and e.get("class") not in allowable_para_classes) or
            e.get("style")):
            fail_list.append(e)
            return False
        for c in list(e):
            for se in c.iter():
                if (se.tag not in allowable_tags and not
                    (se.tag == "{http://www.w3.org/1999/xhtml}span" and
                     se.get("class") in allowable_span_classes)):
                    fail_list.append(se)
                    return False
        return True
    return bog_standard_para_p


def process_bsps(r, bog_standard_para_p):
    bsp_elements = []
    nonbsp_elements = []
    def recursive_process(e):
        for c, se in enumerate(list(e)):
            if bog_standard_para_p(se):
                bsp_elements.append(se)
                ref = "bsp" + str(len(bsp_elements) - 1)
                ph = ET.Element("{http://www.w3.org/1999/xhtml}div",
                                {"id": ref, "class": "bsp_ph"})
                ph.tail = se.tail
                e.insert(c, ph)
                e.remove(se)
            else:
                recursive_process(se)
    recursive_process(r)
    return bsp_elements


def collapse_placeholders(r):
    def collapse(e, ph):
        if len(ph) == 0: return
        if len(ph) > 1:
            ph[0].text = ph[0].get("id") + "…" + ph[-1].get("id")
        else:
            ph[0].text = ph[0].get("id")
        ph[0].attrib["class"] = "bsp_block"
        del ph[0].attrib["id"]
        for p in ph[1:]: e.remove(p)
    def recursive_process(e):
        ph = []
        for se in list(e):
            if se.get("class") == "bsp_ph":
                ph.append(se)
            else:
                collapse(e, ph)
                ph = []
                recursive_process(se)
        collapse(e, ph)
    recursive_process(r)


def main():
    #parse arguments
    parser = argparse.ArgumentParser(description="""\
Seperate "bog standard paragraphs" to expose HTML skeleton.""")
    parser.add_argument("-c", "--class", action="append",
                        help="Allowable class for paragraph (multiple allowed)")
    parser.add_argument("-s", "--span_class", action="append",
                        help="Allowable class for any internal span tags (multiple allowed)")
    parser.add_argument("-t", "--tag", action="append",
                        help="Any additional tags that may be included (multiple allowed)")
    parser.add_argument("-o", "--skeleton", default="skeleton.xhtml",
                        help="Name of 'skeleton' output file")
    parser.add_argument("-b", "--bsps", default="bsps.xhtml",
                        help="Name of 'bog standard paragraphs' output file")
    parser.add_argument("-a", "--add_title", action="store_true",
                        help="Insert a title page block at the top of the skeleton")
    parser.add_argument("input", nargs="?", default="decruft.xhtml",
                        help="XML Input file")
    args = vars(parser.parse_args())
    #process
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    root = ET.parse(args["input"])
    head = root.find(".//{http://www.w3.org/1999/xhtml}head")
    body = root.find(".//{http://www.w3.org/1999/xhtml}body")
    #add skeleton headers
    skel_headers = [se for se in ET.XML(skeleton_headers)]
    skel_headers[-1].tail = head[-1].tail
    head[-1].tail = "\n\n"
    head.extend(skel_headers)
    #add title page
    if args.get("add_title"):
        title_page = ET.XML(title_page_template)
        title_page.tail = body.text
        body.text = "\n\n"
        body.insert(0, title_page)
    #split out bog standard paragraphs
    fail = []
    bog_standard_para_p = make_bog_standard_para_p(args, fail)
    bsp_el = process_bsps(body, bog_standard_para_p)
    collapse_placeholders(body)
    #write out modified xhtml
    root.write(args["skeleton"],
               encoding="unicode",
               xml_declaration=True)
    #create and write out bsps xhtml
    bsp_root = ET.fromstring(bsp_template)
    bsp_body = bsp_root.find("{http://www.w3.org/1999/xhtml}body")
    for c, el in enumerate(bsp_el):
        bsp = ET.Element("{http://www.w3.org/1999/xhtml}div",
                         {"id": "bsp" + str(c)})
        bsp.text = "bsp" + str(c)
        bsp.append(el)
        bsp.tail = "\n"
        bsp_body.append(bsp)
    ET.ElementTree(bsp_root).write(args["bsps"],
                                   encoding="unicode",
                                   xml_declaration=True)
    #report on nonbsp elements
    e = collections.Counter([(X.tag, X.get("class", ""), X.get("style", "")) for X in fail])
    print("Skeleton now contains:")
    for p, n in e.most_common():
        s = p[0].replace("{http://www.w3.org/1999/xhtml}", "")
        if p[1]: s += " class=\"" + p[1] + "\""
        if p[2]: s += " style=\"" + p[2] + "\""
        print(" ", n, ":", s)





if __name__ == "__main__":
    main()
