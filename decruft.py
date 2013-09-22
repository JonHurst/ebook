#!/usr/bin/python3

import sys
import subprocess
import xml.etree.ElementTree as ET


def remove_pagenums(r):
    def recursive_process(e):
        for pne in e.findall("{http://www.w3.org/1999/xhtml}span[@class='pagenum']"):
            e.remove(pne)
        for se in e:
            recursive_process(se)
    recursive_process(r)


def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    #run tidy on file to get xhtml utf-8 output
    args = ["tidy", "-asxhtml", "-utf8", "-q",
            "--quote-nbsp", "no",
            sys.argv[1]]
    sp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    tidy_output = str(out, encoding="utf-8")
    #parse tidy's output
    root = ET.fromstring(tidy_output)
    #remove DP page numbers
    remove_pagenums(root)
    #sort out title
    head = root.find("{http://www.w3.org/1999/xhtml}head")
    title = head.find("{http://www.w3.org/1999/xhtml}title")
    title_split = title.text.split(", by ")
    title.text = title_split[0].replace("The Project Gutenberg eBook of ", "")
    if len(title_split) == 2:
        author_meta = ET.Element("{http://www.w3.org/1999/xhtml}meta",
                                 {"name": "author", "content": title_split[1]})
        head.append(author_meta)
    #remove PG boilerplate
    body = root.find("{http://www.w3.org/1999/xhtml}body")
    pre = body.findall("{http://www.w3.org/1999/xhtml}pre")
    if len(pre) > 1:
        body.remove(pre[0])
        body.remove(pre[-1])
    #write out modified xhtml
    ET.ElementTree(root).write("decruft.xhtml",
                               encoding="unicode",
                               xml_declaration=True)


if __name__ == "__main__":
    main()
