#!/usr/bin/python3

import xml.etree.ElementTree as ET
import sys


def process_bsps(r, bsp_dict):
    def recursive_process(e):
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
                se.text = ""
                for bsp in bsps:
                    se.append(bsp_dict[bsp])
            else:
                recursive_process(se)
    recursive_process(r)



def main():
    ET.register_namespace('', "http://www.w3.org/1999/xhtml")
    main_tree = ET.parse(sys.argv[1])
    bsp_tree = ET.parse(sys.argv[2])
    bsp_dict = {}
    for e in bsp_tree.iter("{http://www.w3.org/1999/xhtml}div"):
        bsp_dict[e.attrib["id"]] = e.find("{http://www.w3.org/1999/xhtml}p")
    process_bsps(main_tree.getroot(), bsp_dict)
    main_tree.write("recombined.xhtml",
                    encoding="unicode",
                    xml_declaration=True)





if __name__ == "__main__":
    main()

