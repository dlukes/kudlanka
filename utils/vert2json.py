#!/usr/bin/env python3

import sys
import argparse

import json
import xmltodict


def json_doc_generator(vert_file):
    """Yield input vertical one doc (as JSON) at a time.

    """
    with open(vert_file) as fh:
        doc = ""
        for line in fh:
            doc += line
            if line.startswith("</doc"):
                yield xmltodict.parse(doc)


def parse_argv(argv):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description = "Anonymize spoken corpus"
    " recordings in WAV format based on timestamps in corpus vertical.")
    parser.add_argument("vertical", help = "corpus in vertical format")
    return parser.parse_args(argv)


def main(argv = None):
    args = parse_argv(argv)
    for json_doc in json_doc_generator(args.vertical):
        print(json.dumps(json_doc, indent = 2))
        break
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
