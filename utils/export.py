#!/usr/bin/env python3

# Export all corpus positions that have been disambiguated at least once as a
# simple tab-separated file.
#
# Usage: run w/o arguments; output goes to STDOUT.

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, ".."))

import csv
from collections import defaultdict
from mongoengine import connect
from kudlanka.config import MONGODB_DB
from kudlanka.models import Seg

connect(MONGODB_DB)
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
