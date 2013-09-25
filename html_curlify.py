#!/usr/bin/python3

import curlify
import xml.etree.ElementTree as et
import sys
import html.entities
import re

def XHTML(tag):
    return "{http://www.w3.org/1999/xhtml}" + tag


def curlify_element(e):
    text_blocks = [e.text or ""]
    for se in e:
        curlify_element(se)
        text_blocks.append(se.text or "")
        text_blocks.append(se.tail or "")
    text = "".join(text_blocks)
    if not text: return
    text = curlify.process_para(text)
    processed_text_blocks = []
    for c, b in enumerate(text_blocks):
        if c % 2 == 0:
            processed_text_blocks.append(text[:len(b)])
        text = text[len(b):]
    for c, b in enumerate(processed_text_blocks):
        processed_text_blocks[c] = b.replace('"', '{"}').replace("'", "{'}")
    e.text = processed_text_blocks[0]
    for c, se in enumerate(e):
        se.tail = processed_text_blocks[c + 1]


def main():
    et.register_namespace("", "http://www.w3.org/1999/xhtml")
    regexp_dialect = re.compile(r"(^|\s){\'}(\w+)")
    text = sys.stdin.read()
    repl = html.entities.entitydefs
    for e in ["quot", "amp", "apos", "lt", "gt"]:
        if e in repl: del repl[e]
    for e in repl:
        text = text.replace("&" + e + ";", repl[e])
    #process dialect if required
    if len(sys.argv) == 3 and sys.argv[1] == "-d":
        for l in open(sys.argv[2]).readlines():
            text = text.replace(l[:-1], "\u02bc" + l[1:-1])
    #process the tree
    tree = et.XML(text)
    curlify_element(tree)
    outstr = et.tostring(tree, encoding="unicode")
    sys.stdout.write(outstr)
    #output list of possible dialect
    poss_dialect_occurences = {}
    for mo in regexp_dialect.finditer(outstr):
        p = mo.group(2)
        if p in poss_dialect_occurences:
            poss_dialect_occurences[p] += 1
        else:
            poss_dialect_occurences[p] = 1
    p = open("poss_dialect", "w", encoding="utf-8")
    for s in sorted(poss_dialect_occurences):
        if poss_dialect_occurences[s] > 1:
            p.write("'" + s + "\n")

if __name__ == "__main__":
    main()


