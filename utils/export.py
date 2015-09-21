#!/usr/bin/env python3

"""Export all corpus positions that have been disambiguated at least once.

default: as a simple tab-separated file.

Usage: run w/o arguments; output goes to STDOUT.

"""

import os
import sys
import argparse
import logging

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, ".."))

from collections import defaultdict
from mongoengine import connect
from kudlanka.config import MONGODB_DB
from kudlanka.models import Seg


def csv_output():
    import csv
    out = csv.writer(sys.stdout, delimiter="\t")
    fields = ["uid", "sid", "idx", "lemma", "tag", "flag", "note"]
    out.writerow(fields)
    for seg in Seg.objects(users_size__gt=0):
        for idx, pos in enumerate(seg.utt):
            by_user = defaultdict(dict)
            for field in ["lemmas", "tags", "flags", "notes"]:
                for uid, value in pos.get(field, {}).items():
                    by_user[uid][field[:-1]] = value
            for uid, fields in by_user.items():
                out.writerow([uid, seg.sid, idx, fields.get("lemma", None),
                            fields.get("tag", None), fields.get("flag", None),
                            fields.get("note", None)])


def parse_arguments(argv):
    """Return args list. `argv` is a list of arguments, or `None` for
    ``sys.argv[1:]``.

    """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Export all corpus positions that have been disambiguated "
        "at least once")
    # parser.add_argument("input_file", nargs="+")
    # parser.add_argument("-o", "--output", help="output file")
    parser.add_argument("-l", "--log", help="logging verbosity",
                        default="DEBUG",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("-f", "--format", help="output format", default="csv",
                        choices=["csv", "html"])
    # parser.add_argument("-n", "--num", type=int, default=25,
    #                     help="sample numeric argument")
    # parser.add_argument("-b", "--bool", action="store_true",
    #                     help="sample boolean argument")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log)
    # check number of arguments, verify values, etc.:
    # if args:
    #     parser.error('program takes no command-line arguments; '
    #                  '"%s" ignored.' % (args,))
    return args


def main(argv=None):
    args = parse_arguments(argv)
    connect(MONGODB_DB)
    if args.format == "csv":
        csv_output()
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
