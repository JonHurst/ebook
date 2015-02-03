#!/usr/bin/python3

import xml.etree.ElementTree as et
import sys
import html.entities
import re
import shutil
import argparse
import os

#note unicode escapes:
#\u2018 is left single quote ‘
#\u2019 is right single quote ’
#\u02bc is apostrophe ʼ
#\u201c is left double quote
#\u201d id right double quote

context=200

def process_doubles(p):
    #double at start of line, not followed by space is an opening double
    p = re.sub(r'^"(\S)', '\u201c\\1', p, flags=re.MULTILINE)
    #double at end of line, preceded by a character that is neither
    #space nor digit is a closing double
    p = re.sub(r'([^\s\d])"$', '\\1\u201d', p, flags=re.MULTILINE)
    #double preceded by space or ' or \u2018 or ( and followed by
    #word character or ' or \u2018 is an opening double
    p = re.sub('(\\s+|[\(\'\u2018])\"([\\w\'\u2018])', '\\1\u201c\\2', p)
    #double preceded by a character that is not a space
    #and followed by space|'|[)—,:;.\u2019] is a closing double
    p = re.sub('([^\\s])\"(\\s+|[\)\'—\.,:;\u2019])', '\\1\u201d\\2', p)
    #double preceded by emdash and followed by word character is an opening double
    p = re.sub('—\"(\\w)', '—\u201c\\1', p)
    return p


def query_single(s, dialect, skip):
    #find the first ' not in skip
    startpos = 0
    while True:
        pos = s.find("'", startpos)
        if pos == -1: return None
        if pos not in skip: break
        startpos = pos + 1
    print(s[max(pos - context, 0):pos] +
          "\033[31m[\033[0m" + s[pos] + "\033[31m]\033[0m" +
          s[pos + 1:min(pos + context, len(s))])
    t = ""
    while t not in ("<", ">", "s", "d"):
        t = input("[<,>,s,d,?] :")
        if t == "?":
            print("<:opening single, >:closing single, s:skip, d:dialect")
    if t == "<":
        s = s[:pos] + "\u2018" + s[pos + 1:]
    elif t == ">":
        s = s[:pos] + "\u2019" + s[pos + 1:]
    elif t == "s":
        skip.add(pos)
    elif t == "d":
        s = s[:pos] + "\u02bc" + s[pos + 1:]
        m = re.search(r"^\w+", s[pos + 1:])
        dialect_word = m.group(0)
        dialect["'" + dialect_word] = u"\u02bc" + dialect_word
    print()
    return s


def process_singles(p, dialect):
    """Process a paragraph to curl single quotes. It is assumed that apostrophes and
    double quotes are already curled before calling this function."""
    skip = set()
    re_close = re.compile(r"([^\s])'(\s+|$|\u201d)")
    re_candidates = re.compile("(^|\\s|\u201c)'[\\w]", flags=re.MULTILINE)
    while True:
        #replace any dialect
        for k in dialect: p = p.replace(k, dialect[k])
        #single preceded by a character that is neither word character nor
        #space and followed by space or eol is a closing single
        p = re_close.sub(r'\1’\2', p)
        #break the para into sections on closing single quotes. If there
        #is only one candidate opening quote convert it. If more, leave
        #them for manual intervention (one of the assumed apostrophes is
        #likely a closing single). If none, we have a problem so set all
        #singles and apostrophes back to straight.
        sections = p.split(u"\u2019")
        for c, s in enumerate(sections[:-1]):
            #if there is already an opening single, it is likely that the
            #quote was indeed a closing single
            if s.find("\u2018") != -1:
                sections[c] += "\u2019"
                continue
            #look for anything that may be an opening quote. This means a quote
            #followed by a word character that is preceded either by space, the
            #beginning of the line or an opening double quote
            candidate_openers = re_candidates.findall(s)
            #if we only find one candidate, assume it is an opening quote and we've
            #correctly split on a closing quote
            if len(candidate_openers) == 1:
                sections[c] = s.replace("'", "\u2018")
                sections[c] += "\u2019"
            #if there is no candidate opening quote, we've likely mistaken an apostrophe
            #for a closing quote
            elif len(candidate_openers) == 0:
                sections[c] += "\u02bc"
            else:
            #if we have more than one opening quote, one of them is probably an apostrophe.
            #Assume that we were correct in the original diagnosis of a closing single.
                sections[c] += "\u2019"
        p = "".join(sections)
        r = query_single(p, dialect, skip)
        if r == None: break
        else: p = r
    return p


def process_para(p, dialect, strict):
    #replace suspected apostrophes with \u02bc
    #if strict single preceded by a word characters is a suspected apostrophe
    if strict:
        p = re.sub(r"(\w)'", "\\1\u02bc", p)
    else: #if not strict, ' in middle of work or xxxs' os an apostrophe
        p = re.sub(r"(\w)'(\w)", "\\1\u02bc\\2", p)
        p = re.sub(r"s'", "s\u02bc", p)
    #do optimistic processing
    p = process_doubles(p)
    p = process_singles(p, dialect)
    return p


def curlify_element(e, dialect, strict):
    #Text in element looks like e.g.:
    #el_text<se>se_text<sse>sse_text</sse>sse_tail</se>se_tail<se>se_text</se>se_tail
    #where <se> and <sse> represent the positions of sub(sub)-elements and don't contribute
    #text.
    text_blocks = []
    def flatten_text(e):
        text_blocks.append(e.text or "")
        for se in e:
            flatten_text(se)
        text_blocks.append(e.tail or "")
    flatten_text(e)
    text = "".join(text_blocks[:-1])
    if not text: return
    text = process_para(text, dialect, strict)
    #we now have a processed text string and need to fit the modified version back into
    #the tree.
    text += text_blocks[-1]
    c = 0
    def unflatten_text(e):
        nonlocal text, c
        e.text = text[:len(text_blocks[c])]
        text = text[len(text_blocks[c]):]
        c += 1
        for se in e:
            unflatten_text(se)
        e.tail = text[:len(text_blocks[c])]
        text = text[len(text_blocks[c]):]
        c += 1
    unflatten_text(e)


def fix_entities(text):
    repl = html.entities.entitydefs
    for e in ["quot", "amp", "apos", "lt", "gt"]:
        if e in repl: del repl[e]
    for e in repl:
        text = text.replace("&" + e + ";", repl[e])
    return text


def replace_text(e, rep_map):
    if e.text:
        for r in rep_map:
            r[2] += e.text.count(r[0])
            e.text = e.text.replace(r[0], r[1])
    for se in e:
        if se.tail:
            for r in rep_map:
                r[2] += se.tail.count(r[0])
                se.tail = se.tail.replace(r[0],r[1])
        replace_text(se, rep_map)


def quote_balance_check(el):
    """Checks double quotes are balanced excluding sub-element text, and
    allowing for opening quote on muliple paragraphs without closing"""
    for se in el: quote_balance_check(se) #apply recursively
    qb_text = el.text or ""
    for se in el:
        qb_text += se.tail or ""
    #do double quote balance checking, resetting to straight in failure cases
    quote_counter = 0
    for c in qb_text:
        if c == "“": quote_counter += 1
        elif c == "”": quote_counter -= 1
        if quote_counter not in (0, 1):
            replace_text(el, (["“", '"', 0], ["”", '"', 0]))
            break


def main():
    #parse arguments
    parser = argparse.ArgumentParser(
        description=("Process an xhtml file containing straight quotes into "
                     "one containing curly quotes. Old file copied with .old suffix."))
    parser.add_argument("-s", "--strict", action="store_true",
                        help="Apply stricter checking of generated quotes")
    parser.add_argument("-i", "--include", action="append",
                        help="Include additional block with form tag[.class] (e.g. div or div.poem)")
    parser.add_argument("filename", nargs="?", default="bsps.xhtml",
                        help="File to process (xhtml format, utf-8 encoding)")
    args = vars(parser.parse_args())
    if not os.path.isfile(args["filename"]):
        print("Error: ", args["filename"], "is not a file")
        sys.exit(-1)
    et.register_namespace("", "http://www.w3.org/1999/xhtml")
    text = open(args["filename"], encoding="utf-8").read()
    text = fix_entities(text)
    #process the tree
    tree = et.XML(text)
    blocks = []
    for tag in ("p", "h1", "h2", "h3"):
        blocks.extend(tree.findall(".//{http://www.w3.org/1999/xhtml}" + tag))
    inc = args["include"] or []
    for i in inc:
        s = i.split(".")
        t = tree.findall(
            ".//{http://www.w3.org/1999/xhtml}" + s[0])
        if len(s) == 1: #no class specified
            blocks.extend(t)
        else: #use substring to allow for multiple classes
            for e in t:
                c = e.attrib.get("class", "")
                if (c.find(s[1]) != -1):
                    blocks.append(e)
    dialect = {}
    ble = len(blocks)
    strict = args["strict"] or False
    for c, se in enumerate(blocks):
        print(c + 1, "of", ble)
        curlify_element(se, dialect, strict)
        if strict:
            quote_balance_check(se)
    #mark remaining straight quotes and replace apostrophes with right singles,
    #sort out dashes and ellipses
    rmap = (
        ['"', '{"}', 0],
        ["'", "{'}", 0],
        ["\u02bc", "\u2019", 0],
        [" . . . .", "….", 0],
        [" . . . ", " … ", 0],
        ["....", "….", 0],
        [" ... ", " … ", 0],
        ["… ”", "…”", 0],
        ["… ’", "…’", 0],
        ["----", "&dmdash;", 0],
        ["——", "&dmdash;", 0],
        ["--", " – ", 0],
        ["—", " – ", 0],
        ["&dmdash;", "——", 0],
        [" – ”", " –”", 0],
        [" – ’", " –’", 0]
    )
    replace_text(tree.find(".//{http://www.w3.org/1999/xhtml}body"), rmap)
    #output file
    shutil.copyfile(args["filename"], args["filename"] + ".old")
    et.ElementTree(tree).write(args["filename"],
                               encoding="unicode",
                               xml_declaration=True)
    print("Wrote", args["filename"])
    print("Need to fix", rmap[0][2], rmap[0][1], "and",
          rmap[1][2], rmap[1][1])



if __name__ == "__main__":
    main()
