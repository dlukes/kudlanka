#!/usr/bin/env python3

r"""Prepare vertical for import into MongoDB for the Kudlanka manual desambiguation webapp.

The expected format of positions in the morphologically analyzed vertical is
"<word>\t<lemma>\t<tag>\t<lemma>\t<tag>...".

"""

import sys
import argparse
import logging
import fileinput

import re
import json
from collections import defaultdict


def getsattr(sattr, line):
    """Get value of structural attribute from vertical line."""
    return re.search(r' {}="(.*?)"'.format(sattr), line).group(1)


def new_seg(corpus, doc_id, seg_idx, seg_label):
    # even values which do not change (users, users_size) need to be
    # set in advance, because we will be querying them
    return {
        "num": seg_label,
        "sid": doc_id + "_" + str(seg_idx),
        "corpus": corpus,
        "utt": [],
        "users": [],
        "users_size": 0,
        "ambiguous": False
    }


def vert2segs(vert_file, doc_struct: str, seg_struct: str,
              corpus_name: str, corpus_attr: str, seg_label_attr: str, limit: int):
    """Extract segments from vertical."""
    doc_count = 0
    for line in fileinput.input(vert_file):
        line = line.strip("\r\n")
        if line.startswith("<" + doc_struct) and "\t" not in line:
            doc_count += 1
            # a global index counter for all seg elements in doc; incremented below
            seg_idx = 0
            doc_id = getsattr("id", line)
            if corpus_name is None:
                corpus_name = getsattr(corpus_attr, line)
                if corpus_name is None:
                    logging.warning("Unable to get corpus info, setting to `unknown`. Corpus + SID "
                                    "identification might not be unique as a result.")
                    corpus_name = "unknown"
        elif line.startswith("</" + doc_struct) and "\t" not in line:
            logging.info("Processed {}.".format(doc_id))
            if limit is not None and doc_count == limit:
                return
        elif line.startswith("<" + seg_struct) and "\t" not in line:
            seg_label = getsattr(seg_label_attr, line)
            seg = new_seg(corpus_name, doc_id, seg_idx, seg_label)
            positions = seg["utt"]
            seg_idx += 1
        elif line.startswith("</" + seg_struct) and "\t" not in line:
            yield seg
        elif "\t" in line:
            tab_sep = line.split("\t")
            word = tab_sep.pop(0)
            # just one lemma + tag tab-separated pair -> non-ambiguous position
            if len(tab_sep) == 2:
                lemma, tag = tab_sep
                positions.append({
                    "word": word,
                    "lemma": lemma,
                    "tag": tag
                })
            else:
                seg["ambiguous"] = True
                pool = defaultdict(list)
                positions.append({
                    "word": word,
                    "pool": pool
                })
                tab_sep = iter(tab_sep)
                for lemma in tab_sep:
                    tag = next(tab_sep)
                    pool[lemma].append(tag)


def parse_argv(argv):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vertical", help="corpus in vertical format, or - for "
                        "STDIN", nargs="+")
    parser.add_argument("-m", "--max", type=int,
                        help="process up to N documents and exit")
    parser.add_argument("-d", "--doc-struct", type=str, default="doc",
                        help="name of top-level structure in vertical")
    parser.add_argument("-c", "--corpus-attr", type=str,
                        help="--doc attribute from which to infer corpus name "
                        "(overridden by --corpus)")
    parser.add_argument("-C", "--corpus-name", type=str,
                        help="name of imported corpus (overrides --attr)")
    parser.add_argument("-s", "--seg-struct", type=str,
                        help="name of structure in vertical that will constitute segments")
    parser.add_argument("-l", "--label-attr", type=str,
                        help="--seg attribute used to label it in Kudlanka")
    logging.basicConfig(level=logging.INFO)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_argv(argv)
    try:
        for seg in vert2segs(args.vertical, args.doc_struct, args.seg_struct, args.corpus_name,
                             args.corpus_attr, args.label_attr, args.max):
            print(json.dumps(seg))
    except Exception as e:
        logging.fatal("An exception occurred which may be due to insufficient information about "
                      "the segment extraction procedure. Specify more information via options (see "
                      "-h for the full list) and retry.")
        raise e
    logging.info("You can now import the data with `sort -R data.json | mongoimport -d <database> "
                 "-c <collection>`. <collection> should be `segs` and <database> should correspond "
                 "to the MONGODB_DB config value. Use --drop if the `segs` collection should be "
                 "dropped first.")
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
