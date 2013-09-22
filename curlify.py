#!/usr/bin/python3

import sys
import re

opening_microformat_char = "{"


def process_doubles(p):
    #double a start of line, not followed by space is an opening double
    p = re.sub(r'^"(\S)', r'“\1', p, flags=re.MULTILINE)
    #double at end of line, preceded by a character that is neither
    #space nor digit is a closing double
    p = re.sub(r'([^\s\d])"$', r'\1”', p, flags=re.MULTILINE)
    #double preceded by space or ' and followed by word character is an opening double
    p = re.sub('(\\s+|\')\"([\\w' + opening_microformat_char + '])', r'\1“\2', p)
    #double preceded by a character that is neither word character nor
    #space and followed by space or ' is a closing double
    p = re.sub('([^\\s\\w])\"(\\s+|\')', r'\1”\2', p)
    return p


def process_singles(p):
    #single preceded by a character that is neither word character nor
    #space and followed by space or eol is a closing single
    p = re.sub(r"([^\s\w])'(\s+|$)", r'\1’\2', p)
    #break the para into sections on closing single quotes. If there
    #is only one candidate opening quote convert it. If more, leave
    #them for manual intervention (one of the assumed apostrophes is
    #likely a closing single). If none, we have a problem so set all
    #singles and apostrophes back to straight.
    sections = p.split("’")
    for c, s in enumerate(sections[:-1]):
        candidate_openers = re.findall(r"(^|\s)'[\w" +
                                       opening_microformat_char +"]",
                                       s, flags=re.MULTILINE)
        if len(candidate_openers) == 1:
            sections[c] = s.replace("'", "‘")
        elif len(candidate_openers) == 0:
            #a closing single without any candidate opening single is
            #a sign of trouble, so put everything back and move on
            p = re.sub(r"[‘’\u20bc]", "'", p)
            break
    return "’".join(sections)


def process_para(p):
    #temporarily replace suspected apostrophes with \u02bc
    #single preceded by a word characters is a suspected apostrophe
    p = re.sub(r"(\w)'", r"\1ʼ", p)
    #do optimistic processing
    p = process_doubles(p)
    p = process_singles(p)
    #do double quote balance checking, resetting to straight in failure cases
    quote_counter = 0
    for c in p:
        if c == "“": quote_counter += 1
        elif c == "”": quote_counter -= 1
        if quote_counter not in (0, 1):
            p = re.sub(r'[“”]', '"', p)
            break
    #replace \u02bc with closing single
    p = p.replace("\u02bc", "’")
    return p


def main():
    text = sys.stdin.read()
    if text[0] == "\n":
        text = text[1:]
        print()
    paras = text.split("\n\n")
    for c, p in enumerate(paras):
        print(process_para(p) + "\n")


if __name__ == "__main__":
    main()
