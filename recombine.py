#!/usr/bin/python3

import xml.etree.ElementTree as ET
import sys


def process_bsps(r, bsp_dict):
    out = ET.Element(r.tag, r.attrib)
    def recursive_process(e, cur):
        for c, se in enumerate(list(e)):
            if (se.tag == "{http://www.w3.org/1999/xhtml}div" and
                se.attrib.get("class") == "bsp_block"):
                bsps = se.text.split("…")
                if len(bsps) == 2:
                    #generate bsp list
                    bsp_start_i = int(bsps[0][3:]) + 1
                    bsp_end_i = int(bsps[1][3:])
                    del bsps[1]
                    for i in range(bsp_start_i, bsp_end_i + 1):
                        bsps.append("bsp" + str(i))
                for bsp in bsps:
                    cur.append(bsp_dict[bsp])
            else:
                n = ET.SubElement(cur, se.tag, se.attrib)
                n.text = se.text
                n.tail = se.tail
                recursive_process(se, n)
    recursive_process(r, out)
    return out



def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    main_tree = ET.parse(sys.argv[1])
    removeids = main_tree.findall(
        "./{http://www.w3.org/1999/xhtml}head/"
        "{http://www.w3.org/1999/xhtml}link[@href='include/skel_styles.css']")
    removeids += main_tree.findall(
        "./{http://www.w3.org/1999/xhtml}head/{http://www.w3.org/1999/xhtml}script")
    head = main_tree.find("./{http://www.w3.org/1999/xhtml}head")
    for r in removeids:
        head.remove(r)
    bsp_tree = ET.parse(sys.argv[2])
    bsp_dict = {}
    for e in bsp_tree.iter("{http://www.w3.org/1999/xhtml}div"):
        bsp_dict[e.attrib["id"]] = e.find("{http://www.w3.org/1999/xhtml}p")
    out = process_bsps(main_tree.getroot(), bsp_dict)
    ET.ElementTree(out).write("recombined.xhtml",
                              encoding="unicode",
                              xml_declaration=True)





if __name__ == "__main__":
    main()
