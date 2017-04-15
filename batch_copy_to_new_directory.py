#!/usr/bin/env python3
import os, csv, shutil, argparse
from ly_parsing import row_should_be_omitted, read_csv

# ARGUMENT PARSING

parser = argparse.ArgumentParser()

parser.add_argument("mode", help = "The type of files we're working with, e.g. 'mutopia' or 'thesession'")
parser.add_argument("csvfile", help = "Path to the CSV file (input)")
parser.add_argument("outdir", help = "The output directory to copy the files to")
parser.add_argument("rootdir", help = "The root directory that contains the files")

# default (-d) is to not render omitted items
parser.add_argument("-d", "--notomitted", help="copy only items that are not omitted", action="store_true")
parser.add_argument("--omitted", help="copy only items that are omitted", action="store_true")

parser.add_argument("--new", help="copy only new items", action="store_true")
parser.add_argument("--old", help="copy only old items", action="store_true")

parser.add_argument("--error", help="copy only items that have serious errors", action="store_true")
parser.add_argument("--minorerror", help="copy only items that have minor errors", action="store_true")
parser.add_argument("--noerror", help="copy only items that have no errors", action="store_true")

parser.add_argument("--flagged", help="copy only items that have been flagged", action="store_true")

parser.add_argument("--dryrun", help="Don't actually copy files, just indicate how many rows would have been copied", action="store_true")

def copy_mutopia(rootdir, outdir, row):
    rootdir_path = os.path.join(rootdir, row['path'])
    outdir_path = os.path.join(outdir, row['path'])
    # print(rootdir_path)
    shutil.copytree(rootdir_path, outdir_path)
    return rootdir_path

def copy_session(rootdir, outdir, row):
    # get filename without extension
    fname = row['filename'][:-3]
    extensions = ['.ly', '-let.pdf', '-a4.pdf', '.mid']
    for ext in extensions:
        file_ext = fname + ext
        rootdir_path = os.path.join(rootdir, row['path'], file_ext)
        outdir_path = os.path.join(outdir, row['path'], file_ext)
        shutil.copy2(rootdir_path, outdir_path)
    return fname

def main(args):
    rows_to_copy = []
    for row in read_csv(args.csvfile):
        if not row_should_be_omitted(args, row):
            rows_to_copy.append(row)

    if (args.dryrun):
        print('Dry run: stopping, would otherwise copy', len(rows_to_copy), 'items.')
    else:
        count = 0
        for row in rows_to_copy:
            count += 1
            try:
                if (args.mode == 'mutopia'):
                    to_print_out = copy_mutopia(args.rootdir, args.outdir, row)
                elif (args.mode == 'thesession'):
                    to_print_out = copy_session(args.rootdir, args.outdir, row)
                else:
                    raise ValueError("Oops! We need a valid mode argument, either 'mutopia' or 'thesession'.")

                print(str(count) + ' ' + to_print_out)

            except ValueError as err:
                print(err.args)

        print('Done.', count, 'pieces copied.')

if __name__ == "__main__":
    main(parser.parse_args())
