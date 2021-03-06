#!/usr/bin/python3

import xml.etree.ElementTree as et
import sys
import html.entities
import re
import shutil
import argparse
import os
import tty
import termios

#note unicode escapes:
#\u2018 is left single quote ‘
#\u2019 is right single quote ’
#\u02bc is apostrophe ʼ
#\u201c is left double quote
#\u201d id right double quote


def process_doubles(p):
    #double touching a letter will face that letter. For closing, some punctuation
    #is equivalent to a letter
    p = re.sub(r'"(\w)', '\u201c\\1', p)
    p = re.sub(r'([\w.,;:?!\'])"', '\\1\u201d', p)
    #double touching space (or equivalently start or end of line) will
    #face away from that space
    p = re.sub(r'(^|\s)"', '\\1\u201c', p, flags=re.MULTILINE)
    p = re.sub(r'"($|\s)', '\u201d\\1', p, flags=re.MULTILINE)
    #error case of spaces on both sides - restore "
    p = re.sub('\u201c($|\\s)', '"\\1', p, flags=re.MULTILINE)
    return p


def query_single(s, start, end, dialect):
    context = 200#change this to show more or less context for query
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin)
        while True:
            s = replace_dialect(s, dialect)
            pos = s.find("'", start, end)
            if pos == -1: return s
            t = ""
            while t not in ("<", ">", "m", "d", ",", "."):
                query_line = (s[max(pos - context, 0):pos] +
                              "\033[31m[\033[0m" + s[pos] + "\033[31m]\033[0m" +
                              s[pos + 1:min(pos + context, len(s))])
                print(re.sub(r"\s+", " ", query_line))
                sys.stdout.write("[<,>,m,d,?] : ")
                sys.stdout.flush()
                t = sys.stdin.read(1)
                if t == ",": t = "<"
                if t == ".": t = ">"
                sys.stdout.write(t + "\n")
                if t == "?":
                    print("\n<:opening single   >:closing single/apostrophe   m:mark   d:dialect\n")
            if t == "<":
                s = s[:pos] + "\u2018" + s[pos + 1:]
            elif t == ">":
                s = s[:pos] + "\u2019" + s[pos + 1:]
            elif t == "d":
                s = s[:pos] + "\u02bc" + s[pos + 1:]
                #record dialect word
                e = re.search(r"\w+$", s[:pos])
                m = re.search(r"^\w+", s[pos + 1:])
                dialect_word_start = e.group(0) if e else ""
                dialect_word_end = m.group(0) if m else ""
                dialect[dialect_word_start + "'" + dialect_word_end] = (
                    dialect_word_start + u"\u02bc" + dialect_word_end)
            print()
            start = pos + 1
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)



def replace_dialect(p, dialect):
    for k in dialect:
        p = re.sub("(^|\\W)%s($|\\W)" % k, "\\1%s\\2" % dialect[k], p)
    return p


def process_singles(p, dialect):
    """Process a paragraph to curl single quotes. It is assumed that apostrophes and
    double quotes are already curled before calling this function."""
    re_close = re.compile("'([\\s\u201d.,;:!]|$)")
    p = replace_dialect(p, dialect)
    #single followed by space, \u201d etc. or end of line is likely a closing single
    #(although it may turn out to be an apostrophe)
    p = re_close.sub('\u2019\\1', p)
    #break the para into sections on these closing single quotes.
    sections = p.split("\u2019")
    pos = 0
    for s in sections[:-1]:
        #any remaining quotes in section are candidates for being openers -- anything
        #inside or at the end a word should already have been turned into an apostrophe and
        #known dialect will already have been replaced
        candidate_openers = s.count("'")
        #if we only find one candidate, assume it is the paired opening quote and hence we've
        #correctly split on a closing quote
        if candidate_openers == 1:
            s = s.replace("'", "\u2018")
            s += "\u2019"
            p = p[:pos] + s + p[pos + len(s):]
        #if there is no candidate opening quote, we've likely mistaken an apostrophe
        #for a closing quote - put the straight quote back to trigger query
        else:
            if candidate_openers == 0:
                s += "'"
            else:
                #if we have more than one candidate opening quote, one of them is probably an
                #apostrophe.  Assume that we were correct in the original diagnosis of a closing
                #single, but leave the candidates unchanged
                s += "\u2019"
            #splice s back into p and hand it off for interactive query
            p = p[:pos] + s + p[pos + len(s):]
            p = query_single(p, pos, pos + len(s), dialect)
        pos += len(s)
    #anything in last section needs querying
    p = query_single(p, pos, pos + len(sections[-1]), dialect)
    return p


def process_para(p, dialect):
    if p.find("'") == -1 and p.find('"') == -1:
        return p
    #replace suspected apostrophes with \u02bc
    #intraword replacement - do it a twice to catch overlapping cases
    for i in range(2): p = re.sub(r"(\w)'(\w)", "\\1\u02bc\\2", p)
    p = re.sub(r"s'", "s\u02bc", p)
    #do processing
    p = process_doubles(p)
    p = process_singles(p, dialect)
    return p


def curlify_element(e, dialect, skip_quote_count=False):
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
    text = process_para(text, dialect)
    if not skip_quote_count:
        text = quote_balance_check(text)
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
    for se in e.iter():
        c_text, c_tail = 0, 0
        for r in rep_map:
            if se.text: se.text, c_text = re.subn(r[0], r[1], se.text)
            if se.tail: se.tail, c_tail = re.subn(r[0], r[1], se.tail)
            if len(r) == 3:
                r[2] += c_text + c_tail


def quote_balance_check(qb_text):
    """Checks double quotes are balanced, allowing for one extra opening
    double at start of paragraph. If there is an uncurled double in the text,
    it will not process it."""
    if len(qb_text) and qb_text.find('"') == -1:
        quote_counter = 0
        for c in qb_text:
            if c == "“": quote_counter += 1
            elif c == "”": quote_counter -= 1
            if quote_counter < 0 or quote_counter > 1: break
        if quote_counter == 1 and qb_text[0] == "“":
            quote_counter -= 1
        if quote_counter != 0:
            return qb_text.replace("“", '"').replace("”", '"')
    return qb_text


def parse_command_line():
    parser = argparse.ArgumentParser(
        description=("Process an xhtml file containing straight quotes into "
                     "one containing curly quotes. Old file copied with .old suffix."))
    parser.add_argument("-u", "--uncurl", action="store_true",
                        help="Uncurl quotes and undo ndash spacing prior to processing.")
    parser.add_argument("--skip-quote-count", action="store_true",
                        help="Don't run quote counting check.")
    parser.add_argument("--skip-curl", action="store_true",
                        help="Don't attempt to curl quotes, leave them as they are.")
    parser.add_argument("--skip-dashes", action="store_true",
                        help="Don't attempt to change dashes to ndash system.")
    parser.add_argument("--skip-ellipses", action="store_true",
                        help="Don't attempt to change ellipses to utf-8 character method.")
    parser.add_argument("-i", "--include", action="append",
                        help="Include additional block with form tag[.class] (e.g. div or div.poem)")
    parser.add_argument("filename", nargs="?", default="bsps.xhtml",
                        help="File to process (xhtml format, utf-8 encoding)")
    args = vars(parser.parse_args())
    if not os.path.isfile(args["filename"]):
        print("Error: ", args["filename"], "is not a file")
        sys.exit(-1)
    return args


def build_block_list(tree, args):
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
    return blocks


def fix_dialect_errors(blocks, dialect):
    for b in blocks:
        for e in b.iter():
            for k in dialect:
                if k[0] != "'": continue
                dialect_error = "\u2018" + k[1:]
                e.text = re.sub("(^|\\W)%s($|\\W)" % dialect_error,
                                "\\1%s\\2" % dialect[k], e.text)
                e.tail = re.sub("(^|\\W)%s($|\\W)" % dialect_error,
                                "\\1%s\\2" % dialect[k], e.tail)


def main():
    et.register_namespace("", "http://www.w3.org/1999/xhtml")
    args = parse_command_line()
    text = open(args["filename"], encoding="utf-8").read()
    text = fix_entities(text)
    tree = et.XML(text)
    if args.get("uncurl"):
        rmap = (
            [r"\s?–\s?", "—"],
            [r"“\s‘", "\"'"], ["’\s”", "'\""],
            [r"‘\s“", "'\""], ["”\s’", "\"'"],
            [r"[“”]", '"'],
            [r"[‘’]", "'"],
            [r"\{(['\"])\}", "\\1"]
        )
        replace_text(tree.find(".//{http://www.w3.org/1999/xhtml}body"), rmap)
    if not args.get("skip_curl"):
        #process the tree into a list of blocks to process
        blocks = build_block_list(tree, args)
        #process the blocks
        dialect = {}
        ble = len(blocks)
        for c, se in enumerate(blocks):
            print(c + 1, "of", ble)
            curlify_element(se, dialect, args.get("skip_quote_count"))
        #one more round of dialect replacement to catch fixable errors
        fix_dialect_errors(blocks, dialect)
        print("Dialect: ", " : ".join(sorted(dialect.keys())))
        rmap = (
            #mark remaining straight quotes and replace apostrophes with right singles
            ['"', '{"}', 0], ["'", "{'}", 0], ["\u02bc", "\u2019"]
        )
        replace_text(tree.find(".//{http://www.w3.org/1999/xhtml}body"), rmap)
        print("Need to fix", rmap[0][2], rmap[0][1], "and",
              rmap[1][2], rmap[1][1])
    if not args.get("skip_ellipses"):
        print("Fixing ellipses")
        rmap = (
            [r"\s?\.\s?\.\s?\.\s?\.", "…."],
            [r"\.\s?\.\s?\.", "…"],
            [r"…\s+([”’])", "… \\1"]
        )
        replace_text(tree.find(".//{http://www.w3.org/1999/xhtml}body"), rmap)
    if not args.get("skip_dashes"):
        print("Fixing dashes")
        rmap = (
            ["(----)|(——)", "&dmdash;"],
            ["--", "—"],
            ["—", " – "], [r"– (\w)", "– \\1"],
            ["([“‘])–", "\\1 –"], ["–([”’])", "– \\1"],
            ["&dmdash;", "——"]
        )
        replace_text(tree.find(".//{http://www.w3.org/1999/xhtml}body"), rmap)
    #output file
    c, backup_filename = 0, args["filename"] + ".old"
    while os.path.exists(backup_filename):
        c += 1
        backup_filename = args["filename"] + ".old(%s)" % c
    shutil.copyfile(args["filename"], backup_filename)
    et.ElementTree(tree).write(args["filename"],
                               encoding="unicode",
                               xml_declaration=True)
    print("Wrote", args["filename"])



if __name__ == "__main__":
    main()
