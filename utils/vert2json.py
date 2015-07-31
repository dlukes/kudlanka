#!/usr/bin/env python3

import os
import sys
import argparse
import logging

import re
import json
from lxml import etree


def doc_generator(vert_file):
    """Yield input vertical one doc (as JSON) at a time."""
    with open(vert_file) as fh:
        doc = ""
        for line in fh:
            doc += line
            if line.startswith("</doc"):
                try:
                    doc = valid_xml(doc)
                    yield etree.fromstring(doc)
                except etree.XMLSyntaxError as e:
                    dump = "__dump__.xml"
                    with(open(dump, "w")) as fh:
                        fh.write(doc)
                    logging.error("An XMLSyntaxError occurred while processing "
                                  "a document. It has been dumped to {} for "
                                  "inspection.".format(dump))
                    logging.error(e)
                    sys.exit(1)
                finally:
                    doc = ""


def valid_xml(doc):
    """Transform vertical to valid XML."""
    doc = re.sub("&", "&amp;", doc)
    doc = re.sub("<(\d+)>", "&lt;\\1&gt;", doc)
    return doc


def xml2dict(xml):
    doc = {
        "id": xml.attrib.get("id", "ID_MISSING"),
        "oral": xml.attrib.get("oral", "ORAL_MISSING"),
        "segs": []
    }
    for sp in xml:
        num = sp.attrib.get("num", "NUM_MISSING")
        for seg in sp:
            utterance = []
            doc["segs"].append({
                "num": num,
                "utt": utterance
            })
            for pos in seg.text.strip().split("\n"):
                tab_sep = pos.split("\t")
                word = tab_sep.pop(0)
                pool = []
                utterance.append({
                    "word": word,
                    "pool": pool
                })
                for lemtag in tab_sep:
                    space_sep = lemtag.split()
                    lemma, tags = space_sep[0], space_sep[1:]
                    pool.append({
                        "lemma": lemma,
                        "tags": tags
                    })
    return doc


def parse_argv(argv):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description = "Anonymize spoken corpus"
    " recordings in WAV format based on timestamps in corpus vertical.")
    parser.add_argument("vertical", help = "corpus in vertical format")
    parser.add_argument("-o", "--outdir", help = "path to directory where "
                        "output JSON files will be saved", default = ".")
    logging.basicConfig(level = logging.INFO)
    return parser.parse_args(argv)


def main(argv = None):
    args = parse_argv(argv)
    for doc in doc_generator(args.vertical):
        doc = xml2dict(doc)
        id = doc["id"]
        out = os.path.join(args.outdir, id + ".json")
        logging.info("Processed {}.".format(id))
        with open(out, "w") as fh:
            print(json.dumps(doc, indent = 2), file = fh)
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
