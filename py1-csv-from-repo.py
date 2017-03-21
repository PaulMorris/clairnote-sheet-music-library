#!/usr/bin/env python3
import os, csv, argparse
from py_ly_parsing import (regexes, regex_search, vsn_greater_than_or_equals,
    get_all_lilypond_filenames, get_ly_filenames, get_version, get_included_files,
    get_header_data, check_for_clairnote_code, get_most_recent_mtime)
from py_csv_merging import merge_csv_data

# walks through a directory and all subdirectories creating a csv file with data from the ly files

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("rootdir", help="The root directory that contains the ly files") # e.g. '../../The-Mutopia-Project/ftp/' or 'test-ly-files'
parser.add_argument("-o", "--csv-output", help="Path and name for the CSV file output") # e.g. 'out/from-repo.csv'
parser.add_argument("-p", "--csv-previous", help="Path and name of the previous CSV file") # e.g. 'out/previous-final.csv'
parser.add_argument("-l", "--earliest-ly-version", help="The earliest LilyPond version to include in CSV file") # e.g. '2.14.0'
parser.add_argument("-m", "--mode", help="The mode for parsing ly files, e.g. 'mutopia' or 'thesession'")

csv_keys_mutopia = ['mutopia-id', 'parse-order', 'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
    'cn-code', 'ly-version', 'mutopiacomposer', 'cn-title', 'cn-opus', 'path', 'filename',
    'cn-style', 'cn-instrument',
    'cn-poet', 'license-type', 'license-vsn', 'cn-license', 'mtime',
    'arranger', 'date', 'source', 'copyright', 'tagline',
    'footer', 'composer', 'mutopiatitle', 'title', 'mutopiaopus', 'opus', 'mutopiastyle', 'style',
    'mutopiainstrument', 'instrument', 'mutopiapoet', 'poet', 'mutopialicense', 'license']


''' example of the session files' header fields:
\header {
	crossRefNumber = "1"
	footnotes = ""
	subtitle = "https://thesession.org/tunes/9#setting25918"
	tagline = "Lily was here 2.19.52 -- automatically converted from ABC"
	title = "Banish Misfortune"
}
'book' is also used in at least one file
'''

csv_keys_the_session = ['id', 'tune-id', 'setting-id', 'parse-order',
    'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
    'cn-code', 'ly-version', 'path', 'filename', 'mtime',
    # these are the actual header fields in the session ly files
    'title', 'subtitle', 'crossRefNumber', 'tagline', 'footnotes', 'book',
    # maybe some files use these, so add them for good measure?
    'composer']


def add_cn_fields(row):
    # use separate 'cn-' fields so we can see what's going on in the .ly files
    row['cn-title'] = row['mutopiatitle'] or row['title']
    row['cn-opus'] = row['mutopiaopus'] or row['opus']
    row['cn-style'] = row['mutopiastyle'] or row['style']
    row['cn-instrument'] = row['mutopiainstrument'] or row['instrument']
    row['cn-poet'] = row['mutopiapoet'] or row['poet']
    row['cn-license'] = row['mutopialicense'] or row['license'] or row['copyright']
    return row

def add_license_data(row):
    license_lookup = {
        'Public Domain': ['pd', 0],
        'Creative Commons Attribution 4.0': ['by', 4],
        'Creative Commons Attribution 3.0': ['by', 3],
        'Creative Commons Attribution-ShareAlike 3.0': ['by-sa', 3],
        'Creative Commons Attribution-ShareAlike 4.0': ['by-sa', 4]
    }
    row['license-type'] = license_lookup.get(row['cn-license'], ['', ''])[0]
    row['license-vsn'] = license_lookup.get(row['cn-license'], ['', 0])[1]
    return row

def process_ly_names(lyfilenames, dirpath, rootdir, mode, csv_keys):

    # print('\n\n', version, dirpath[len(rootdir):], '\n', lyfilenames)

    row, conflicting_data = get_header_data(lyfilenames, dirpath, csv_keys)

    # the files that are not included are top level files (usually just one file)
    included_files = get_included_files(lyfilenames, dirpath)
    not_included_files = list(set(lyfilenames).difference(included_files))

    # print('included: ', included_files)
    # print('not-included: ', not_included_files)

    # check for clairnote-code.ly in top-level files
    clntSet = check_for_clairnote_code(not_included_files, dirpath)

    if len(clntSet) > 1:
        conflicting_data.add('cn-code')
        # TODO: confirm this output is what we want in the CSV file
        row['cn-code'] = list(clntSet)
    else:
        row['cn-code'] = list(clntSet)[0]

    # Handle conflicting data in different files
    # first prune irrelevant conflicts
    # some are handled earlier, not even added to conflicting_data
    if conflicting_data:
        irrelevant_conflicts = ['composer', 'title', 'instrument', 'style', 'license', 'opus', 'poet']
        for k in irrelevant_conflicts:
            if k in conflicting_data and row['mutopia' + k] != '':
                conflicting_data.discard(k)

    # second deal with remaining relevant conflicts
    if conflicting_data:
        print('omit! conflicting data:', dirpath[len(rootdir):], list(conflicting_data), '\n')
        row['omit?'] = 'T'
        row['omit-reason'] = 'conflicting header data: ' + repr(conflicting_data)

    if mode == 'mutopia':
        # extract mutopia-id from footer field
        row['mutopia-id'] = regex_search(regexes['muto_id'], row['footer']) or ''
        row = add_cn_fields(row)
        row = add_license_data(row)
    elif mode == 'thesession':
        m = regexes['the_session_id'].search(row['subtitle'])
        row['tune-id'] = m.group(1)
        row['setting-id'] = m.group(2)
        row['id'] = m.group(1) + '-' + m.group(2)

    row['mtime'] = get_most_recent_mtime(lyfilenames, dirpath)
    row['filename'] = ',,, '.join(list(not_included_files))
    # strip slash on the left for good measure, for tests etc.
    row['path'] = dirpath[len(rootdir):].lstrip(os.path.sep)

    if mode == 'mutopia':
        print(dirpath, "   ", rootdir, "   ", row['path'])

    # not currently used
    # ftr = row['footer']
    # row['mutopia-id'] = regex_search(regexes['muto_id'], ftr)
    # strip footer to just the date
    # row['footer'] = regex_search(regexes['footer'], ftr)
    # remove footer
    # row.pop('footer', False)

    return row, conflicting_data

def walk(rootdir, earliest_ly_version, mode, csv_keys):
    """ Walk through rootdir and sub-directories parsing data from ly files.

        In 'mutopia' mode we descend until we find a directory with ly files.
        If there are subdirectories, we bail out and skip that piece.  Otherwise
        we work on the ly files in that directory as all part of a single piece.

        In 'thesession' mode we work with individual ly files as single pieces,
        at any level in the hierarchy (usually just a directory of ly files).

        rootdir (string) is path to the root directory
        earliest_ly_version (string) (e.g. "2.19.52") we omit any ly files earlier than this version
        mode (string) what mode we're in (e.g. 'mutopia', 'thesession')
        csv_keys (list) the keys to use in the csv file we will create, varies with mode """
    csv_data = []
    parse_order = 0
    conflicting_data_count = 0
    subdir_skips = 'not applicable' if mode == 'thesession' else 0

    for dirpath, dirnames, filenames in os.walk(rootdir):
        if filenames != []:

            if mode == 'mutopia':
                # get list of all ly, ily, lyi filnames in directory
                lyfilenames = get_all_lilypond_filenames(filenames)
                if lyfilenames != []:
                    if dirnames == []:
                        version = get_version(lyfilenames, dirpath)
                        if version != None and vsn_greater_than_or_equals(earliest_ly_version, version):

                            row, conflicting_data = process_ly_names(lyfilenames, dirpath, rootdir, mode, csv_keys)
                            row['ly-version'] = version
                            parse_order += 1
                            row['parse-order'] = parse_order
                            csv_data.append(row)

                            if (len(conflicting_data) > 0):
                                conflicting_data_count += 1

                    else:
                        # there are subdirectories and we can't handle them, so skip it.
                        subdir_skips += 1
                        # print('skip! subdirectories:', dirpath[len(rootdir):], dirnames, '\n')
                        # clear dirnames to prevent os.walk from going deeper
                        # we have to do it like this, delete in place:
                        dirnames.clear()

            elif mode == 'thesession':
                # get list of all ly filnames in directory
                lyfilenames = get_ly_filenames(filenames)
                if lyfilenames != []:
                    for name in lyfilenames:
                        version = get_version([name], dirpath)
                        if version != None and vsn_greater_than_or_equals(earliest_ly_version, version):

                            row, conflicting_data = process_ly_names([name], dirpath, rootdir, mode, csv_keys)
                            row['ly-version'] = version
                            parse_order += 1
                            row['parse-order'] = parse_order
                            csv_data.append(row)

                            if (len(conflicting_data) > 0):
                                conflicting_data_count += 1

    return csv_data, parse_order, conflicting_data_count, subdir_skips

def main(args):
    try:
        if args.mode == 'mutopia':
            csv_keys = csv_keys_mutopia
        elif args.mode == 'thesession':
            csv_keys = csv_keys_the_session
        else:
            raise ValueError("Need a valid mode argument, either 'mutopia' or 'thesession'.")

        csv_data, parse_order, conflicts, skips = walk(args.rootdir, args.earliest_ly_version, args.mode, csv_keys)

        print('\nLilyPond files parsed, data gathered.',
            '\n  Total works:', parse_order,
            '\n  conflicting_data_count:', conflicts,
            '\n  subdir_skips:', skips)

        # MERGE IN PREVIOUS CSV META DATA AND MARK NEW ITEMS
        id_field = 'mutopia-id' if args.mode == 'mutopia' else 'id'

        final_csv_data = merge_csv_data(args.csv_previous, csv_data, id_field) if args.csv_previous else csv_data

        # GENERATE CSV FILE
        with open(args.csv_output, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_keys)
            writer.writeheader()
            for line in final_csv_data:
                writer.writerow(line)
            print('CSV file created: ' + args.csv_output)

    except ValueError as err:
        print(err.args)

if __name__ == "__main__":
    main(parser.parse_args())
