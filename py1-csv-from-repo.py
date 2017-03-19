#!/usr/bin/env python3
import os, re, csv, argparse

# walks through a directory and all subdirectories creating a csv file with data from the ly files

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("rootdir", help="The root directory that contains the ly files") # e.g. '../../The-Mutopia-Project/ftp/' or 'test-ly-files'
parser.add_argument("-o", "--csv-output", help="Path and name for the CSV file output") # e.g. 'out/from-repo.csv'
parser.add_argument("-p", "--csv-previous", help="Path and name of the previous CSV file") # e.g. 'out/previous-final.csv'
parser.add_argument("-l", "--earliest-ly-version", help="The earliest LilyPond version to include in CSV file") # e.g. '2.14.0'
args = parser.parse_args()

csvKeys = ['mutopia-id', 'parse-order', 'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
    'cn-code', 'ly-version', 'mutopiacomposer', 'cn-title', 'cn-opus', 'path', 'filename',
    'cn-style', 'cn-instrument',
    'cn-poet', 'license-type', 'license-vsn', 'cn-license', 'mtime',
    'arranger', 'date', 'source', 'copyright', 'tagline',
    'footer', 'composer', 'mutopiatitle', 'title', 'mutopiaopus', 'opus', 'mutopiastyle', 'style',
    'mutopiainstrument', 'instrument', 'mutopiapoet', 'poet', 'mutopialicense', 'license']

def balancedBraces(arg):
    '''
    takes a string starting with "\header" and ending
    at the end of the .ly file.  Returns just the
    header brackets and contents "{ ... }"
    '''
    result = ""
    n = 0
    before_first_brace = True
    if arg == None:
        return ""
    for c in arg:
        if before_first_brace:
            if c == '{':
                before_first_brace = False
                n = 1
                result = c
        else:
            if c == '{':
                n += 1
            elif c == '}':
                n -= 1
            if n > 0:
                result = result + c
            else:
                return result
    return "NOPE"

hdr_regex = re.compile("\\\\header.*", re.DOTALL)

quote_regex = re.compile("\".*\"")
hdr_fields_regex = re.compile("\S.*?=.*?\".*?\"")
hdr_field_key_regex = re.compile(".*?[\s|=]")

hdr_field_val_regex = re.compile("\".*\"")
muto_id_regex = re.compile("[0-9]*$")
footer_regex = re.compile("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]")

clairnote_code_regex = re.compile('\\\\include.*?\"clairnote-code.ly\"')
include_regex = re.compile('\\\\include.*?\".*?\"')
score_regex = re.compile('\\\\score')

mutopiacomposer_regex = re.compile('.*mutopiacomposer.*', re.DOTALL)

def regexSearch(r, s):
    if s == None:
        return None
    a = r.search(s)
    if a == None:
        return None
    else:
        return a.group()

def dictifyHeader (fields):
    result = []
    for f in fields:
        key = regexSearch(hdr_field_key_regex, f)
        val = regexSearch(hdr_field_val_regex, f)
        if key == None:
            print('Missing key: ', f)
        elif val == None:
            print('Missing val: ', f)
        result.append(( key[0:-1], val[1:-1] ))
    return dict(result)


def vsnGreaterThanOrEqualTo(ref, vsn):
    vsnList = vsn.split('.')
    refList = ref.split('.')
    vsnNum = int(vsnList[0]) * 1000000 + int(vsnList[1]) * 1000 + int(vsnList[2])
    refNum = int(refList[0]) * 1000000 + int(refList[1]) * 1000 + int(refList[2])
    return vsnNum >= refNum


def header_data_from_string(filestring):
    hdr1 = regexSearch(hdr_regex, filestring)
    hdr2 = balancedBraces(hdr1)
    hdr3 = hdr_fields_regex.findall(hdr2)
    hdr4 = dictifyHeader(hdr3)
    row = {}
    for key in csvKeys:
        row[key] = hdr4.pop(key, '')
    return row

"""
# unused
def extractMultiData(filestring, parseOrder, fname):
    incs = include_regex.findall(filestring)
    incs2 = []
    for i in incs:
        incs2.append(regexSearch(quote_regex, i))
    scrs = score_regex.findall(filestring)
    print(fname, scrs, incs2)
"""

def getLyFilenames(filenames):
    lynames = []
    for f in filenames:
        if f[-3:] == '.ly' or f[-4:] == '.ily' or f[-4:] == '.lyi':
            lynames.append(f)
    return lynames

def createFullPaths(dirpath, filenames):
    paths = []
    for f in filenames:
        paths.append(os.path.join(dirpath, f))
    return paths

def getAllDirLyPaths(rootdir):
    lypaths = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        lyfiles = getLyFilenames(filenames)
        lypaths.append(createFullPaths(dirpath, lyfiles))
    return lypaths

def get_version(lyfilenames, dirpath):
    """ Returns the first version found in a list of ly files. """
    raw_vsn_regex = re.compile("\\\\version.*?\".*?\"")
    vsn_regex_digits = re.compile("[0-9]*\.[0-9]*\.[0-9]*")
    vsn = None
    for name in lyfilenames:
        with open(os.path.join(dirpath, name), 'r') as f:
            # go through file line by line until we get the version
            for line in f:
                raw_vsn = regexSearch(raw_vsn_regex, line)
                vsn = regexSearch(vsn_regex_digits, raw_vsn)
                if vsn != None: break
        if vsn != None: break
    return vsn

def included_files_from_string(filestring):
    incs = include_regex.findall(filestring)
    incs2 = []
    for i in incs:
        x = regexSearch(quote_regex, i)
        incs2.append(x[1:-1])
    return incs2

def get_included_files(lyfilenames, dirpath):
    # get list of included files
    included_files = set()
    for fname in lyfilenames:
        with open(os.path.join(dirpath, fname), 'r') as f:
            incs = included_files_from_string(f.read())
            for i in incs:
                included_files.add(i)
    return included_files

def get_header_data(lyfilenames, dirpath):
    header_data = {}
    inconsistent_keys = set()
    for fname in lyfilenames:
        with open(os.path.join(dirpath, fname), 'r') as f:
            header = header_data_from_string(f.read())

            # extract mutopia-id from footer
            header['mutopia-id'] = regexSearch(muto_id_regex, header['footer'])
            if header['mutopia-id'] == None:
                header['mutopia-id'] = ''

            # merge this file's header fields into header_data
            # the keys of inconsistent values are stored
            irrelevant_conflicts = ['footer', 'filename', 'source']
            for k, v in header.items():

                if k not in header_data or header_data[k] == '':
                    header_data[k] = v

                elif v != '' and header_data[k] != v:
                    header_data[k] += ', ' + v
                    if k not in irrelevant_conflicts:
                        inconsistent_keys.add(k)
            '''
            # TODO: ? track files that have headers
            if mutoHdr != None and header_data != None:
                # hdrFiles.add(fname)
                print('\nTWO MUTO HEADERS: ', dirpath[len(rootdir):], fname)

            if mutoHdr != None and header_data == None:
                print('muto header: ', fname)
                header_data = mutoHdr
            '''
    return header_data, inconsistent_keys

def check_for_clairnote_code(files, dirpath):
    result = set()
    for fname in files:
        with open(os.path.join(dirpath, fname), 'r') as f:
            c = clairnote_code_regex.search(f.read())
            if c:
                result.add(True)
            else:
                result.add(False)
    return result

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
    licenseLookup = {
        'Public Domain': ['pd', 0],
        'Creative Commons Attribution 4.0': ['by', 4],
        'Creative Commons Attribution 3.0': ['by', 3],
        'Creative Commons Attribution-ShareAlike 3.0': ['by-sa', 3],
        'Creative Commons Attribution-ShareAlike 4.0': ['by-sa', 4]
    }
    row['license-type'] = licenseLookup.get(row['cn-license'], ['', ''])[0]
    row['license-vsn'] = licenseLookup.get(row['cn-license'], ['', 0])[1]
    return row

def get_most_recent_mtime(files, dirpath):
    """ Return the most recent mtime for a list of files in a directory """
    most_recent = None
    for fname in files:
        mtime = os.path.getmtime(os.path.join(dirpath, fname))
        if most_recent == None or most_recent < mtime:
            most_recent = mtime
    return most_recent
    # not used currently, but kept for future reference
    # ctime = last time a file's metadata was changed (owner, permissions, etc.)
    # row['ctime'] = os.path.getctime(os.path.join(dirpath, fname))

def process_ly_names(lyfilenames, dirpath, rootdir):

    # GET HEADER DATA ETC
    # print('\n\n', version, dirpath[len(rootdir):], '\n', lyfilenames)

    included_files = get_included_files(lyfilenames, dirpath)
    row, diff_keys = get_header_data(lyfilenames, dirpath)

    # the files that are not included are top level files (ideally just one file)
    not_included_files = list(set(lyfilenames).difference(included_files))

    # print('included: ', included_files)
    # print('not-included: ', not_included_files)

    # check for clairnote-code.ly in top-level files
    clntSet = check_for_clairnote_code(not_included_files, dirpath)

    if len(clntSet) > 1:
        diff_keys.add('cn-code')
        # TODO: confirm this output is what we want in the CSV file
        row['cn-code'] = list(clntSet)
    else:
        row['cn-code'] = list(clntSet)[0]

    # Handle conflicting data in different files
    # first prune irrelevant conflicts
    # some are handled earlier, not even added to diff_keys
    if diff_keys:
        for k in ['composer', 'title', 'instrument', 'style', 'license', 'opus', 'poet']:
            if k in diff_keys and row['mutopia' + k] != '':
                diff_keys.discard(k)

    # second deal with remaining relevant conflicts
    if diff_keys:
        print('omit! conflicting data:', dirpath[len(rootdir):], list(diff_keys), '\n')
        row['cn-omit'] = 'T'
        row['cn-omit-reason'] = 'conflicting header data: ' + repr(diff_keys)

    row = add_cn_fields(row)
    row = add_license_data(row)

    row['mtime'] = get_most_recent_mtime(lyfilenames, dirpath)

    row['filename'] = ',,, '.join(list(not_included_files))

    # strip slash on the left for good measure, for tests etc.
    row['path'] = dirpath[len(rootdir):].lstrip(os.path.sep)

    print(dirpath, "   ", rootdir, "   ", row['path'])

    # not currently used
    # ftr = row['footer']
    # row['mutopia-id'] = regexSearch(muto_id_regex, ftr)
    # strip footer to just the date
    # row['footer'] = regexSearch(footer_regex, ftr)
    # remove footer
    # row.pop('footer', False)

    return row, diff_keys

def walk_the_tree(rootdir):
    """ Walk through rootdir and subdirectories parsing data from ly files.
        rootdir (string) is path to the root directory """
    csv_data = []
    parse_order = 0
    diff_keys_count = 0
    subdir_skips = 0

    for dirpath, dirnames, filenames in os.walk(rootdir):

        if filenames != []:
            # get list of all .ly and .ily files in directory
            lyfilenames = getLyFilenames(filenames)

            if lyfilenames != []:
                if dirnames == []:
                    version = get_version(lyfilenames, dirpath)

                    if version != None and vsnGreaterThanOrEqualTo(args.earliest_ly_version, version):

                        row, diff_keys = process_ly_names(lyfilenames, dirpath, rootdir)
                        row['ly-version'] = version

                        parse_order += 1
                        row['parse-order'] = parse_order
                        csv_data.append(row)
                        if (len(diff_keys) > 0):
                            diff_keys_count += 1

                else:
                    subdir_skips += 1
                    # print('skip! subdirectories:', dirpath[len(rootdir):], dirnames, '\n')

                    # clear dirnames to prevent os.walk from going deeper
                    # we have to do it like this, delete in place:
                    dirnames.clear()

    print('LilyPond files parsed, data gathered.',
        '\n  Total works:', parse_order,
        '\n  diff_keys_count:', diff_keys_count,
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
    writer = csv.DictWriter(csvfile, fieldnames=csvKeys)
    writer.writeheader()
    for line in final_csv_data:
        writer.writerow(line)
    print('CSV file created: ' + args.csv_output)
