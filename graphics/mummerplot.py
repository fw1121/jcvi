#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Wrapper for mummerplot. Selecting a subset of queries and references to plot
main features in the dot plot.
"""

import os.path as op
import sys
import logging

from jcvi.formats.coords import Coords, filter
from jcvi.formats.sizes import Sizes
from jcvi.formats.base import SetFile
from jcvi.apps.base import OptionParser, sh


def writeXfile(ids, dict, filename):
    fw = open(filename, "w")
    for q in ids:
        print >> fw, "\t".join(str(x) for x in (q, dict[q], "+"))

    logging.debug("{0} ids written to `{1}`.".format(len(ids), filename))
    fw.close()


def main(args):
    """
    %prog deltafile query.fasta ref.fasta

    Plot one query. Extract the references that have major matches to this
    query. Control "major" by option --refcov.
    """
    p = OptionParser(main.__doc__)
    p.add_option("--refids", help="Use subset of contigs in the ref")
    p.add_option("--refcov", default=.01, type="float",
                 help="Minimum reference coverage [default: %default]")
    p.add_option("--all", default=False, action="store_true",
                 help="Plot one pdf file per ref in refidsfile [default: %default]")
    p.add_option("--color", default="similarity",
                 choices=("similarity", "direction", "none"),
                 help="Color the dots based on")
    p.set_align(pctid=96, hitlen=500)
    opts, args = p.parse_args(args)

    if len(args) != 3:
        sys.exit(not p.print_help())

    deltafile, queryfasta, reffasta = args
    color = opts.color
    prefix = op.basename(deltafile).split(".")[0]
    qsizes = Sizes(queryfasta).mapping
    rsizes = Sizes(reffasta).mapping

    refs = SetFile(opts.refids) if opts.refids else set(rsizes.keys())
    refcov = opts.refcov
    pctid = opts.pctid
    hitlen = opts.hitlen
    deltafile = filter([deltafile, "--pctid={0}".format(pctid),
                        "--hitlen={0}".format(hitlen)])

    if opts.all:
        for r in refs:
            pdffile = plot_some_queries([r], qsizes, rsizes, deltafile, refcov,
                                        prefix=prefix, color=color)
            if pdffile:
                sh("mv {0} {1}.pdf".format(pdffile, r))
    else:
        plot_some_queries(refs, qsizes, rsizes,
                          deltafile, refcov,
                          prefix=prefix, color=color)


def plot_some_queries(refs, qsizes, rsizes, deltafile, refcov,
                      prefix="out", color="similarity"):

    Qfile, Rfile = "Qfile", "Rfile"
    coords = Coords(deltafile)
    queries = set()
    for c in coords:
        if c.refcov < refcov:
            continue
        if c.ref not in refs:
            continue
        queries.add(c.query)

    if not queries or not refs:
        logging.debug("Empty - {0} vs. {1}".format(queries, refs))
        return None

    writeXfile(queries, qsizes, Qfile)
    writeXfile(refs, rsizes, Rfile)

    cmd = "mummerplot {0}".format(deltafile)
    cmd += " -Rfile {0} -Qfile {1}".format(Rfile, Qfile)
    cmd += " --postscript --layout -p {0}".format(prefix)
    if color == "similarity":
        cmd += " --color"
    elif color == "none":
        cmd += " --nocolor"
    sh(cmd)

    cmd = "ps2pdf {0}.ps {0}.pdf".format(prefix)
    sh(cmd)

    return prefix + ".pdf"


if __name__ == '__main__':
    main(sys.argv[1:])
