#!/usr/bin/env python3
import os, argparse
from py_ly_parsing import (get_all_lilypond_filenames, get_version,
    header_data_from_string, vsn_greater_than_or_equals)

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("rootdir", help="The root directory that contains the ly files") # e.g. '../../The-Mutopia-Project/ftp/' or 'test-ly-files'
parser.add_argument("-o", "--output", help="Path and name for an optional output file") # e.g. 'out/from-repo.csv'
parser.add_argument("-l", "--earliest-ly-version", help="The earliest LilyPond version to include in CSV file") # e.g. '2.14.0'


def header_keys_from_file(dirpath, name):
    with open(os.path.join(dirpath, name), 'r') as f:
        header_data = header_data_from_string(f.read())
        return header_data.keys()

def get_all_header_fields(rootdir, earliest_ly_version):
    header_fields = set()

    for dirpath, dirnames, filenames in os.walk(rootdir):
        if filenames != []:
            # get list of all .ly .ily .lyi files in directory
            lyfilenames = get_all_lilypond_filenames(filenames)

            if lyfilenames != []:
                for name in lyfilenames:
                    version = get_version([name], dirpath)

                    # if there earliest_ly_version is supplied then we use it
                    if earliest_ly_version:
                        if version != None and vsn_greater_than_or_equals(earliest_ly_version, version):
                            header_fields.update(header_keys_from_file(dirpath, name))
                    else:
                        header_fields.update(header_keys_from_file(dirpath, name))

    return header_fields

def main(args):
    # args are rootdir, output, earliest_ly_version

    header_fields = get_all_header_fields(args.rootdir, args.earliest_ly_version)
    fields_str = str(header_fields)
    print(fields_str)

    if args.output:
        f = open(args.output, "a")
        f.write(fields_str)
        f.close()

if __name__ == "__main__":
    main(parser.parse_args())
