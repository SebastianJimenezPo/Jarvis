import re
import unicodedata


def normalize(text):
    text=unicodedata.normalize('NFC',text.casefold())
    return re.sub(r'[^\w\s]','',text).strip()


def distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1):
            nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]


def error_counts(reference,hypothesis):
    a,b=normalize(reference),normalize(hypothesis)
    return {'word_errors':distance(a.split(),b.split()),'reference_words':len(a.split()),
            'character_errors':distance(a,b),'reference_characters':len(a)}
