#!/usr/bin/python3

import sys
import subprocess
import xml.etree.ElementTree as ET

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
<!--Start BSP headers-->
<link rel="stylesheet" type="text/css" href="include/skel_styles.css"/>
<script src="include/jquery-1.10.2.min.js" type="text/javascript"/>
<script src="include/script.js" type="text/javascript" />
<!--End BSP headers-->
</head>"""

title_page_template = """\
<div id="title_page">
<h1><span class="title">title</span><br/>
<span style="font-size:medium;">by</span><br/>
<span class="author">author</span></h1>
</div>"""

def bog_standard_para_p(e):
    if e.tag != "{http://www.w3.org/1999/xhtml}p" or e.get("class"):
        return False
    for c in list(e):
        for se in c.iter():
            if ((se.tag not in [
                        "{http://www.w3.org/1999/xhtml}i",
                        "{http://www.w3.org/1999/xhtml}b"]) and not
                (se.tag == "{http://www.w3.org/1999/xhtml}span" and
                 se.get("class") == "smcap")):
                return False
    return True


def process_bsps(r):
    bsp_elements = []
    def recursive_process(e):
        for c, se in enumerate(list(e)):
            if bog_standard_para_p(se):
                bsp_elements.append(se)
                ref = "bsp" + str(len(bsp_elements) - 1)
                ph = ET.Element("{http://www.w3.org/1999/xhtml}div",
                                {"id": ref, "class": "bsp_ph"})
                ph.tail = "\n"
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
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    txt = open(sys.argv[1], "r", encoding="utf-8").read()
    txt = txt.replace("</head>", skeleton_headers)
    txt = txt.replace("<body>", "<body>" + "\n" + title_page_template)
    root = ET.fromstring(txt)
    #split out bog standard paragraphs
    bsp_el = process_bsps(root)
    collapse_placeholders(root)
    #write out modified xhtml
    ET.ElementTree(root).write("skeleton.xhtml",
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
    ET.ElementTree(bsp_root).write("bsps.xhtml",
                                   encoding="unicode",
                                   xml_declaration=True)




if __name__ == "__main__":
    main()

