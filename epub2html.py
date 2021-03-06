#!/usr/bin/python3

import sys
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import shutil
import hashlib
import html.entities
import re

def unzip_epub(epub, tmpdir):
    """An epub is packaged as a zip file. This function extracts it
    into the tmpdir directory."""
    try:
        with zipfile.ZipFile(epub) as z:
            zipinfo = z.infolist()
            for i in zipinfo:
                z.extract(i, path=tmpdir.name)
    except zipfile.BadZipfile:
        print(epub, "is not an epub")
    except FileNotFoundError:
        print(epub, "is not a file")


def process_opf(opf_filename):
    """Extracts data from the content.opf file found in
    tmpdir. Returns a tuple consisting of (spine_list, copy_list)
    where spine_list is a list of the form [(idref, fullpath), ..] and
    copy_list is a simple list of relevant files that do not appear in
    the spine and thus will need copying."""
    tree = ET.parse(opf_filename)
    manifest = tree.find(".//{http://www.idpf.org/2007/opf}manifest")
    id_dict = {}
    filelist = set()
    for item in manifest.findall("{http://www.idpf.org/2007/opf}item"):
        filename = item.get("href")
        i = item.get("id")
        id_dict[i] = filename
        filelist.add(i)
    spine = tree.find(".//{http://www.idpf.org/2007/opf}spine")
    retval = []
    for itemref in spine.findall("{http://www.idpf.org/2007/opf}itemref"):
        idref = itemref.get("idref")
        retval.append((idref, id_dict[idref]))
        filelist.remove(idref)
    return retval, [id_dict[X] for X in filelist]


def head_text_digest(filename):
    """Creates a sha1 hash of the head section of an xhtml file. This
    allows comparison of the heads on a purely text basis. Note that
    files with exactly equivalent heads in terms of xhtml may not have
    identical heads in terms of text."""
    text = open(filename).read()
    head_start = text.find("<head")
    head_end = text.find("/head>")
    h = ET.XML(fix_entities(text[head_start:head_end + 6]))
    s = []
    for el in h:
        if el.tag == "title": continue
        s.append((el.tag,
                 sorted([(X, el.attrib[X]) for X in el.attrib]),
                 el.text))
    s.sort()
    return hashlib.sha1(str(s).encode()).digest()


def group_spine(spine, input_dir):
    """Takes the spine list and reorganises it to group together xhtml
    files with identical head sections. The output is of the form
    [[(idref, filename), ..], ..] where all items in the second level
    lists have identical head sections."""
    current_group = [spine[0]]
    spine_groups = [current_group]
    current_digest = head_text_digest(os.path.join(input_dir, spine[0][1]))
    for s in spine[1:]:
        digest = head_text_digest(os.path.join(input_dir, s[1]))
        if digest == current_digest:
            current_group.append(s)
        else:
            current_group = [s]
            current_digest = digest
            spine_groups.append(current_group)
    return spine_groups


def modify_ids(el, idref):
    """Modify all the id attributes in el and its subelements by
    prepending idref."""
    for e in el.findall(".//*[@id]"):
        ident = e.get("id")
        e.set("id", idref + ident)


def modify_links(el, prefix_map):
    """Modify all internal links found in el's subelements using prefix
    map. The prefix map maps a filename to the filename of the joined
    file plus the idref of the original file."""
    for e in el.findall(".//{http://www.w3.org/1999/xhtml}a"):
        href = e.get("href")
        if not href or href.startswith("http://") or href.startswith("https://"):
            continue
        parts = href.split("#")
        parts.append("")
        if parts[0] in prefix_map.keys():
            e.set("href", prefix_map[parts[0]] + parts[1])


def fix_entities(text):
    entities = set(re.findall(r"&(\w+);", text))
    entities -= set(("quot", "amp", "apos", "lt", "gt"))
    for e in entities:
        text = text.replace("&" + e +";",
                            chr(html.entities.name2codepoint[e]))
    return text


def parse_xhtml(filename):
    """Parses an xhtml file with conversion of named entities to utf-8 characters"""
    text = open(filename, encoding="utf-8").read()
    text = fix_entities(text)
    return ET.XML(text)


def output_group_file(spine_group, input_dir, output_dir, prefix_map):
    """Takes a spine group and combines the sub-files into outputs a
    single file with the filename of the first file to the output_dir
    directory. ids and links are fixed up, and a new anchor with the
    id equal to the sub-file's idref is placed at the start of each
    sub-file."""
    print("Reading", spine_group[0][1])
    first_file = parse_xhtml(os.path.join(input_dir, spine_group[0][1]))
    body = first_file.find(".//{http://www.w3.org/1999/xhtml}body")
    body.insert(0, ET.Element("{http://www.w3.org/1999/xhtml}a",
                              {"id": "", "class": "epub_break"}))
    modify_ids(body, spine_group[0][0])
    modify_links(body, prefix_map)
    for se in spine_group[1:]:
        print("Reading", se[1])
        next_file = parse_xhtml(os.path.join(input_dir, se[1]))
        additional_body = next_file.find(".//{http://www.w3.org/1999/xhtml}body")
        additional_body.insert(0, ET.Element(
            "{http://www.w3.org/1999/xhtml}a",
            {"id": "", "class": "epub_break"}))
        modify_ids(additional_body, se[0])
        modify_links(additional_body, prefix_map)
        for e in additional_body:
            body.append(e)
    #output file
    output_filename = os.path.join(output_dir, spine_group[0][1])
    print("Writing", output_filename)
    dest_directory = os.path.dirname(output_filename)
    if dest_directory and not os.path.isdir(dest_directory):
        os.makedirs(dest_directory)
    ET.ElementTree(first_file).write(
        output_filename,
        encoding="unicode",
        xml_declaration=True)


def prefix_map(spine_groups):
    """Build a map of the form {filename: new_filename#original_idref,
    ...} based on how the spine_groups will be output."""
    prefix_map = {}
    for sg in spine_groups:
        base_prefix = os.path.basename(sg[0][1])
        for s in sg:
            prefix_map[os.path.basename(s[1])] = base_prefix + "#" + s[0]
    return prefix_map


def get_contents(dir_name):
    tree = ET.parse(os.path.join(dir_name, "META-INF/container.xml"))
    rf = tree.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    return rf.attrib["full-path"]


def main():
    if len(sys.argv) != 2 or sys.argv[1][0] == "-":
        print("Usage:", sys.argv[0], "epubfile")
        sys.exit(-1)
    epub = sys.argv[1]
    tmpdir = tempfile.TemporaryDirectory()
    unzip_epub(epub, tmpdir)
    opf = os.path.join(tmpdir.name, get_contents(tmpdir.name))
    spine, copylist = process_opf(opf)
    spine_groups = group_spine(spine, os.path.dirname(opf))
    #build output files
    ET.register_namespace("", "http://www.w3.org/1999/xhtml")
    output_dirname = os.path.dirname(epub)
    pm = prefix_map(spine_groups)
    for sg in spine_groups:
        output_group_file(sg, os.path.dirname(opf), output_dirname, pm)
    #copy other files
    for f in copylist:
        copy_filename = os.path.join(output_dirname, f)
        dest_directory = os.path.dirname(copy_filename)
        if dest_directory and not os.path.isdir(dest_directory):
            os.makedirs(dest_directory)
        print("Copying", copy_filename)
        shutil.copy(os.path.join(os.path.dirname(opf), f), copy_filename)



if __name__ == "__main__": main()
