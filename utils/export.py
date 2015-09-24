#!/usr/bin/env python3

"""Summarize results of manual disambiguation using Kudlanka.

Output: either as a single csv file, or as a set of linked html files.

"""

import os
import sys
import argparse
import logging

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, ".."))

from collections import defaultdict
from sortedcontainers import SortedListWithKey
from textwrap import dedent
from functools import lru_cache
from mongoengine import connect
from kudlanka.config import MONGODB_DB
from kudlanka.models import Seg, User


@lru_cache(maxsize=None)
def uid2username(id):
    return User.objects(id=id).first().email


def csv_output():
    import csv
    out = csv.writer(sys.stdout, delimiter="\t")
    fields = ["uid", "sid", "idx", "word", "lemma", "tag", "flag", "note"]
    out.writerow(fields)
    for seg in Seg.objects(users_size__gt=0):
        for idx, pos in enumerate(seg.utt):
            by_user = defaultdict(dict)
            word = pos.get("word", None)
            for field in ["lemmas", "tags", "flags", "notes"]:
                for uid, value in pos.get(field, {}).items():
                    by_user[uid][field[:-1]] = value
                    by_user[uid]["word"] = word
            for uid, fields in by_user.items():
                out.writerow([uid2username(uid), seg.sid, idx, fields["word"],
                              fields.get("lemma", None), fields.get("tag", None),
                              fields.get("flag", None), fields.get("note", None)])


def html_output(outdir):
    by_word = defaultdict(dict)
    for seg in Seg.objects(users_size__gt=0):
        utt = [pos["word"] for pos in seg.utt]
        for idx, pos in enumerate(seg.utt):
            lemmas = set([lemma for lemma in pos.get("lemmas", {}).values()])
            tags = set([tag for tag in pos.get("tags", {}).values()])
            flags = [1 for flag in pos.get("flags", {}).values() if flag]
            notes = [note for note in pos.get("notes", {}).values()]
            # - 2 because there will always be at least one lemma and tag
            pos_cont = len(lemmas) + len(tags) + len(flags) + len(notes) - 2
            if pos_cont > 0:
                by_user = defaultdict(dict)
                word = pos["word"]
                for field in ["lemmas", "tags", "flags", "notes"]:
                    for uid, value in pos.get(field, {}).items():
                        by_user[uid2username(uid)][field[:-1]] = value
                by_word[word].setdefault("cont", 0)
                by_word[word]["cont"] += pos_cont
                by_word[word].setdefault("inst", [])
                by_word[word]["inst"].append(
                    dict(sid=seg.sid, idx=idx, utt=utt, annot=by_user))
    render_html(by_word, outdir)


def render_html(by_word, outdir):

    def boilerplate(template):
        return dedent("""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
        table {
          border-collapse: collapse;
        }
        table, th, td {
          border: 1px solid lightgray;
        }
        th {
          text-align: left;
        }
        </style>
        </head>
        <body>
        """ + template + """
        </body>
        </html>
        """)

    from jinja2 import Template

    cont_html = Template(boilerplate(dedent("""
    <ul>
    {% for word in by_cont %}
    <li>
    <a href="{{ word.word }}__.html">{{ word.word }}</a>: {{ word.cont }}
    </li>
    {% endfor %}
    </ul>
    """)))
    word_html = Template(boilerplate(dedent("""
    {% for inst in word.inst %}
    <h3>
    <a href="https://trnka.korpus.cz/kudlanka/edit/{{ inst.sid }}">Věta</a>
    </h3>
    <p>
    {% for pos in inst.utt %}
    {% if loop.index - 1 == inst.idx %}
    <span style="color: red">{{ pos }}</span>
    {% else %}
    {{ pos }}
    {% endif %}
    {% endfor %}
    </p>
    <h3>Anotace</h3>
    <table>
    <thead>
    <tr>
    <th>user</th>
    <th>lemma</th>
    <th>tag</th>
    <th>flag</th>
    <th>note</th>
    </thead>
    </tr>
    <tbody>
    {% for user, field2value in inst.annot.items() %}
    <tr>
    <td><b>{{ user }}</b></td>
    <td><code>{{ field2value.lemma }}</code></td>
    <td style="white-space: nowrap"><code>{{ field2value.tag }}</code></td>
    <td>{{ field2value.flag }}</td>
    <td>{{ field2value.note }}</td>
    </tr>
    {% endfor %}
    </tbody>
    </table>
    <hr>
    {% endfor %}
    """)))
    by_cont = SortedListWithKey(key=lambda dic: -dic["cont"])
    for word, dic in by_word.items():
        dic["word"] = word
        by_cont.add(dic)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    with open(os.path.join(outdir, "index.html"), "w") as fh:
        print(cont_html.render(by_cont=by_cont), file=fh)
    for word in by_cont:
        with open(os.path.join(outdir, word["word"] + "__.html"), "w") as fh:
            print(word_html.render(word=word), file=fh)


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
    parser.add_argument("-o", "--outdir", help="output directory", default=".")
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
    elif args.format == "html":
        html_output(args.outdir)
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
