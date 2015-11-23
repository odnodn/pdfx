#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command line tool to get metadata and URLs from a local or remote PDF,
and optionally download all referenced PDFs.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
# import logging
import argparse
import json
import codecs
import locale

import pdfx

if sys.version_info < (3, 0):
    # Python 2
    parse_str = unicode
else:
    # Python 3
    parse_str = str


def exit_with_error(code, *objs):
    print("ERROR %s:" % code, *objs, file=sys.stderr)
    exit(code)

# Error Status Codes
ERROR_FILE_NOT_FOUND = 1
ERROR_DOWNLOAD = 2
ERROR_PDF_INVALID = 4


def create_parser():
    parser = argparse.ArgumentParser(
        description="Extract metadata and references from a PDF, and "
        "optionally download all referenced PDFs. Visit "
        "http://www.metachris.com/pdfx for more information.",
        epilog="")

    parser.add_argument("pdf", help="Filename or URL of a PDF file")

    parser.add_argument(
        "-d",
        "--download-pdfs",
        metavar="OUTPUT_DIRECTORY",
        help="Download all referenced PDFs into specified directory")

    parser.add_argument("-j",
                        "--json",
                        action='store_true',
                        help="Output infos as json (instead of plain text)")

    parser.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=0,
                        help="Print all urls (instead of only PDF urls)")

    # parser.add_argument("--debug",
    #                     action='store_true',
    #                     help="Output debug infos")

    parser.add_argument("-t", "--text",
                        action='store_true',
                        help="Only output text (no metadata or references)")

    parser.add_argument("-o", "--output-file",
                        help="Output metadata to specified file")

    parser.add_argument("--version",
                        action="version",
                        version="%(prog)s v{version}".format(
                            version=pdfx.__version__))
    return parser


def get_text_output(pdf, args):
    """ Normal output of infos of PDFx instance """
    # Metadata
    ret = ""
    ret += "Document infos:\n"
    for k, v in sorted(pdf.get_metadata().items()):
        if v:
            ret += "- %s = %s\n" % (k, parse_str(v).strip("/"))

    # References
    ref_cnt = pdf.get_references_count()
    ret += "\nReferences: %s\n" % ref_cnt
    refs = pdf.get_references_as_dict()
    for k in refs:
        ret += "- %s: %s\n" % (k.upper(), len(refs[k]))

    if args.verbose == 0:
        if "pdf" in refs:
            ret += "\nPDF References:\n"
            for ref in refs["pdf"]:
                ret += "- %s\n" % ref
    else:
        if ref_cnt:
            for reftype in refs:
                ret += "\n%s References:\n" % reftype.upper()
                for ref in refs[reftype]:
                    ret += "- %s\n" % ref
    return ret


def print_to_console(text):
    enc = locale.getdefaultlocale()[1]
    try:
        print(text.encode(enc, errors="backslashreplace"))
    except LookupError:
        # Unknown encoding. Use ascii
        print(text.encode("ascii", errors="backslashreplace"))


def main():
    parser = create_parser()
    args = parser.parse_args()

    # if args.debug:
    #     logging.basicConfig(
    #             level=logging.DEBUG,
    #             format='%(levelname)s - %(module)s - %(message)s')

    try:
        pdf = pdfx.PDFx(args.pdf)
    except pdfx.exceptions.FileNotFoundError as e:
        exit_with_error(ERROR_FILE_NOT_FOUND, str(e))
    except pdfx.exceptions.DownloadError as e:
        exit_with_error(ERROR_DOWNLOAD, str(e))
    except pdfx.exceptions.PDFInvalidError as e:
        exit_with_error(ERROR_PDF_INVALID, str(e))

    # Perhaps only output text
    if args.text:
        print_to_console(pdf.get_text())
        return

    # Print Metadata
    if args.json:
        # in JSON format
        text = json.dumps(pdf.summary, indent=4)
        if args.output_file:
            # to file (in utf-8)
            with codecs.open(args.output_file, "w", "utf-8") as f:
                f.write(text)
        else:
            # to console
            print_to_console(text)
    else:
        # in text format
        text = get_text_output(pdf, args)
        if args.output_file:
            # to file (in utf-8)
            with codecs.open(args.output_file, "w", "utf-8") as f:
                f.write(text)
        else:
            # to console
            print_to_console(text)

    try:
        if args.download_pdfs:
            print("\nDownloading %s pdfs to '%s'..." %
                  (len(pdf.get_references("pdf")), args.download_pdfs))
            pdf.download_pdfs(args.download_pdfs)
            print("All done!")
    except Exception as e:
        exit_with_error(ERROR_DOWNLOAD, str(e))


if __name__ == "__main__":
    main()
