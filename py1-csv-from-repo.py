#!/usr/bin/env python3
import os, csv, argparse
from py_ly_parsing import (regexes, regex_search, vsn_greater_than_or_equals,
    get_ly_filenames, get_version, get_included_files, get_header_data,
    check_for_clairnote_code, get_most_recent_mtime)

# walks through a directory and all subdirectories creating a csv file with data from the ly files

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("rootdir", help="The root directory that contains the ly files") # e.g. '../../The-Mutopia-Project/ftp/' or 'test-ly-files'
parser.add_argument("-o", "--csv-output", help="Path and name for the CSV file output") # e.g. 'out/from-repo.csv'
parser.add_argument("-p", "--csv-previous", help="Path and name of the previous CSV file") # e.g. 'out/previous-final.csv'
parser.add_argument("-l", "--earliest-ly-version", help="The earliest LilyPond version to include in CSV file") # e.g. '2.14.0'
args = parser.parse_args()

csv_keys = ['mutopia-id', 'parse-order', 'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
    'cn-code', 'ly-version', 'mutopiacomposer', 'cn-title', 'cn-opus', 'path', 'filename',
    'cn-style', 'cn-instrument',
    'cn-poet', 'license-type', 'license-vsn', 'cn-license', 'mtime',
    'arranger', 'date', 'source', 'copyright', 'tagline',
    'footer', 'composer', 'mutopiatitle', 'title', 'mutopiaopus', 'opus', 'mutopiastyle', 'style',
    'mutopiainstrument', 'instrument', 'mutopiapoet', 'poet', 'mutopialicense', 'license']

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

def process_ly_names(lyfilenames, dirpath, rootdir):

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
        for k in ['composer', 'title', 'instrument', 'style', 'license', 'opus', 'poet']:
            if k in conflicting_data and row['mutopia' + k] != '':
                conflicting_data.discard(k)

    # second deal with remaining relevant conflicts
    if conflicting_data:
        print('omit! conflicting data:', dirpath[len(rootdir):], list(conflicting_data), '\n')
        row['cn-omit'] = 'T'
        row['cn-omit-reason'] = 'conflicting header data: ' + repr(conflicting_data)

    # extract mutopia-id from footer field
    row['mutopia-id'] = regex_search(regexes['muto_id'], row['footer']) or ''

    row = add_cn_fields(row)
    row = add_license_data(row)
    row['mtime'] = get_most_recent_mtime(lyfilenames, dirpath)
    row['filename'] = ',,, '.join(list(not_included_files))
    # strip slash on the left for good measure, for tests etc.
    row['path'] = dirpath[len(rootdir):].lstrip(os.path.sep)

    print(dirpath, "   ", rootdir, "   ", row['path'])

    # not currently used
    # ftr = row['footer']
    # row['mutopia-id'] = regex_search(regexes['muto_id'], ftr)
    # strip footer to just the date
    # row['footer'] = regex_search(regexes['footer'], ftr)
    # remove footer
    # row.pop('footer', False)

    return row, conflicting_data

def walk_the_tree(rootdir):
    """ Walk through rootdir and subdirectories parsing data from ly files.
        Descends until it finds a directory with ly files. If there are
        subdirectories, then it bails out and skips that work.  Otherwise it
        does its work on the ly files in that directory.
        rootdir (string) is path to the root directory """
    csv_data = []
    parse_order = 0
    conflicting_data_count = 0
    subdir_skips = 0

    for dirpath, dirnames, filenames in os.walk(rootdir):

        if filenames != []:
            # get list of all .ly and .ily files in directory
            lyfilenames = get_ly_filenames(filenames)

            if lyfilenames != []:
                if dirnames == []:
                    version = get_version(lyfilenames, dirpath)

                    if version != None and vsn_greater_than_or_equals(args.earliest_ly_version, version):

                        row, conflicting_data = process_ly_names(lyfilenames, dirpath, rootdir)
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

    print('\nLilyPond files parsed, data gathered.',
        '\n  Total works:', parse_order,
        '\n  conflicting_data_count:', conflicting_data_count,
        '\n  subdir_skips:', subdir_skips)

    return csv_data


csv_data = walk_the_tree(args.rootdir)

# GET OLD META DATA, MERGE IT IN, AND MARK NEW ITEMS

def merge_csv_data(old_csv, new_csv_data, id_field_name):
    """ Merge data from previous csv and mark which items are new.
        old_csv (string) is the path to the previous csv file
        new_csv_data (list) data destined for the new csv file
        id_field_name (string) key for the id value for items in new_csv_data
        returns (list) merged data """

    # get old meta data
    old_meta_data = {}

    with open(old_csv, newline='') as old_csv_read:
        reader = csv.DictReader(old_csv_read)
        for row in reader:
            item_id = int(row[id_field_name])

            if row['new?'] == 'T':
                print('\nOOPS! - There is an item marked as NEW in the OLD csv file... ID: ' + str(item_id))

            old_meta_data[item_id] = {
                'omit?': row['omit?'],
                'omit-reason': row['omit-reason'],
                'new?': row['new?'],
                'error-status?': row['error-status?']
            }

    # merge old meta data into new data and mark new items as new
    # the meta data fields should be empty in the new data, so nothing is overwritten
    old_total = len(old_meta_data)
    new_total = len(new_csv_data)
    merged_csv_data = []

    for item in new_csv_data:
        # note: item is a dict so it is appended by reference not by value
        merged_csv_data.append(item)
        item_id = int(item[id_field_name])

        if item_id in old_meta_data:
            merged_csv_data[-1].update(old_meta_data[item_id])
            # remove the item from old_meta_data so we can identify any orphaned works
            del old_meta_data[item_id]
        else:
            merged_csv_data[-1]['new'] = 'T'

    print('\n' + str(old_total), 'Works in previous CSV file.')
    print(new_total, 'Works in current CSV file.')
    print(str(new_total - old_total), 'Total new works.\n')

    if len(old_meta_data) > 0:
        print("Orphaned works that were in previous CSV file but were not in current CSV file:", sorted(old_meta_data.keys()))
    else:
        print("There were no orphaned works, all items in previous CSV are in current CSV.")

    return merged_csv_data


final_csv_data = None
if args.csv_previous:
    final_csv_data = merge_csv_data(args.csv_previous, csv_data, 'mutopia-id')
else:
    final_csv_data = csv_data


# GENERATE CSV FILE

with open(args.csv_output, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_keys)
    writer.writeheader()
    for line in final_csv_data:
        writer.writerow(line)
    print('CSV file created: ' + args.csv_output)
