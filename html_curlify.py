#!/usr/bin/python3

import curlify
import xml.etree.ElementTree as et
import sys
import html.entities

def XHTML(tag):
    return "{http://www.w3.org/1999/xhtml}" + tag


def curlify_element(e):
    text_blocks = [e.text or ""]
    for se in e:
        text_blocks.append(se.tail or "")
        curlify_element(se)
    text = "".join(text_blocks)
    if not text: return
    text = curlify.process_para(text)
    processed_text_blocks = []
    for b in text_blocks:
        processed_text_blocks.append(text[:len(b)])
        text = text[len(b):]
    for c, b in enumerate(processed_text_blocks):
        processed_text_blocks[c] = b.replace('"', '{"}').replace("'", "{'}")
    e.text = processed_text_blocks[0]
    for c, se in enumerate(e):
        se.tail = processed_text_blocks[c + 1]


def main():
    et.register_namespace("", "http://www.w3.org/1999/xhtml")
    text = sys.stdin.read()
    repl = html.entities.entitydefs
    for e in ["quot", "amp", "apos", "lt", "gt"]:
        if e in repl: del repl[e]
    for e in repl:
        text = text.replace("&" + e + ";", repl[e])
    tree = et.XML(text)
    for e in tree:
        curlify_element(e)
    et.ElementTree(tree).write(sys.stdout, encoding="unicode", xml_declaration=True)


if __name__ == "__main__":
    main()


