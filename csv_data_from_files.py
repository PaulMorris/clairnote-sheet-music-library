#!/usr/bin/env python3
import os, csv, argparse
from ly_parsing import (regexes, regex_search, vsn_compare, greater_or_equal,
    get_all_lilypond_filenames, get_ly_filenames, get_version, get_included_files,
    get_header_data, check_for_clairnote_ly, get_most_recent_mtime, makedirs_filepath)
from csv_merging import merge_csv_data

# walks through a directory and subdirectories creating a csv file with data from the ly files

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("mode", help = "The mode for parsing ly files, e.g. 'mutopia' or 'thesession'")
parser.add_argument("csvout", help="Path and file name for the CSV file output")
parser.add_argument("rootdir", help="The root directory that contains the ly files")
parser.add_argument("-p", "--csv-previous", help="Path and file name of the previous CSV file")
parser.add_argument("-l", "--earliest-ly-version", help="The earliest LilyPond version to include in CSV file (e.g. '2.14.0')", default='0.0.0')


''' example of header fields in 'the session' files:
\header {
	crossRefNumber = "1"
	footnotes = ""
	subtitle = "https://thesession.org/tunes/9#setting25918"
	tagline = "Lily was here 2.19.52 -- automatically converted from ABC"
	title = "Banish Misfortune"
}
'''

def get_csv_keys(mode):
    lookup = {
        'mutopia': ['id', 'parse-order', 'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
                    'cn-code', 'ly-version', 'mutopiacomposer', 'cn-title', 'cn-opus', 'path', 'filename',
                    'cn-style', 'cn-instrument',
                    'cn-poet', 'license-type', 'license-vsn', 'cn-license', 'mtime',
                    'arranger', 'date', 'source', 'copyright', 'tagline',
                    'footer', 'composer', 'mutopiatitle', 'title', 'mutopiaopus', 'opus', 'mutopiastyle', 'style',
                    'mutopiainstrument', 'instrument', 'mutopiapoet', 'poet', 'mutopialicense', 'license'],

        'thesession': ['id', 'tune-id', 'setting-number', 'setting-id', 'parse-order',
            'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?',
            'cn-code', 'ly-version', 'path', 'filename', 'mtime', 'cn-title',
            # these are the actual header fields in the session ly files,
            # book and footnotes are rarely used
            'title', 'subtitle', 'meter', 'abcTranscription', 'crossRefNumber', 'tagline', 'footnotes', 'book',
            # the url that contains the id data is originally in subtitle
            # but we move it to source, so we need a source key, for rescanning
            # files that have been updated, otherwise we can't get the id data
            'source',
            # maybe some files use these, so include them for good measure
            'composer']
    }
    return lookup[mode]

def add_cn_fields(row):
    # use separate 'cn-' fields so we can easily see what's going on in the .ly files
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

def omit_conflicts(row, conflicts):
    relevant_conflicts = conflicts.copy()
    # some conflicts have been omitted earlier
    irrelevant_conflicts = ['composer', 'title', 'instrument', 'style', 'license', 'opus', 'poet']
    for irr in irrelevant_conflicts:
        # don't bother with a conflict if there's a mutopia___ version of it
        if irr in relevant_conflicts and row['mutopia' + irr] != '':
            relevant_conflicts.discard(irr)
    return relevant_conflicts

def make_multi_digit(input, digit_count):
    'Convert an integer like 3 or 12 to a string like 0003 or 0012.'
    in_str = str(input)
    extra_zeros = digit_count - len(in_str)
    return '0' * extra_zeros + in_str

def make_row(lyfilenames, dirpath, rootdir, mode, csv_keys):
    # print('\n\n', dirpath[len(rootdir):], '\n', lyfilenames)
    row, conflicts = get_header_data(lyfilenames, dirpath, csv_keys)

    # the files that are not included are top level files (usually just one file)
    included_files = get_included_files(lyfilenames, dirpath)
    not_included_files = list(set(lyfilenames).difference(included_files))

    # check for clairnote.ly in top-level files
    clnt_set = check_for_clairnote_ly(not_included_files, dirpath)

    if len(clnt_set) > 1:
        conflicts.add('cn-code')
        # TODO: confirm this output is what we want in the CSV file
        row['cn-code'] = list(clnt_set)
    else:
        row['cn-code'] = list(clnt_set)[0]

    # Handle conflicting data in different files
    # omit irrelevant conflicts, then deal with remaining relevant conflicts
    relevant_conflicts = omit_conflicts(row, conflicts) if conflicts else []
    if relevant_conflicts:
        print('omit! conflicting data:', dirpath[len(rootdir):], list(relevant_conflicts), '\n')
        row['omit?'] = 'T'
        row['omit-reason'] = 'conflicting header data: ' + repr(relevant_conflicts)

    row['mtime'] = get_most_recent_mtime(lyfilenames, dirpath)
    row['filename'] = ',,, '.join(list(not_included_files))
    # strip slash on the left for good measure, for tests etc.
    row['path'] = dirpath[len(rootdir):].lstrip(os.path.sep)

    if mode == 'mutopia':
        # extract mutopia id from footer field
        row['id'] = regex_search(regexes['muto_id'], row['footer']) or ''
        row = add_cn_fields(row)
        row = add_license_data(row)
        print(dirpath, "   ", rootdir, "   ", row['path'])

    elif mode == 'thesession':
        row['setting-number'] = int(regexes['setting-number'].search(row['filename']).group(1))
        id_data_match = regexes['the_session_id'].search(row['subtitle'])

        if not id_data_match:
            # for re-scan of files that have already been processed, the url
            # with id data is now in source field, not subtitle
            id_data_match = regexes['the_session_id'].search(row['source'])

        if id_data_match:
            row['tune-id'] = id_data_match.group(1)
            row['setting-id'] = id_data_match.group(2)
            row['id'] = make_multi_digit(row['tune-id'], 7) + '-' + make_multi_digit(row['setting-number'], 3)
        else:
            # TODO: make this better
            print("Bad id_data_match:", "'" + row["title"] + "'", "'" + row["subtitle"] + "'", "'" + row["filename"] + "'")
            row['id'] = 'ERROR'
            row['omit?'] = 'T'
            row['omit-reason'] = 'bad subtitle/source, could not calculate id'
        # use title() to capitalize all words in the string, needed for Slip Jig
        row['meter'] = row['meter'].title()
        # use cn-title for consistency with mutopia csv key
        row['cn-title'] = row['title']

    return row, relevant_conflicts

def get_ly_file_paths(rootdir):
    result = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        if filenames != []:
            # get list of all ly filnames in directory
            lyfilenames = get_ly_filenames(filenames)
            if lyfilenames != []:

                for name in lyfilenames:
                    result.append({
                        'path': dirpath,
                        'lyfilenames': [name],
                        'version': get_version([name], dirpath)
                    })
    return result, None

def get_mutopia_ly_file_paths(rootdir):
    result = []
    subdir_skips = 0
    for dirpath, dirnames, filenames in os.walk(rootdir):
        if filenames != []:
            # get list of all ly, ily, lyi filenames in directory
            lyfilenames = get_all_lilypond_filenames(filenames)
            if lyfilenames != []:

                if dirnames == []:
                    result.append({
                        'path': dirpath,
                        'lyfilenames': lyfilenames,
                        'version': get_version(lyfilenames, dirpath)
                    })
                else:
                    # there are subdirectories and we can't handle that, so skip this piece.
                    subdir_skips += 1
                    # print('skip! subdirectories:', dirpath[len(rootdir):], dirnames, '\n')
                    # clear dirnames to prevent os.walk from going deeper
                    # this is how it's done, delete in place:
                    dirnames.clear()

    return result, subdir_skips

def version_check(earliest_ly_version):
    def vcheck(piece):
        vsn = piece['version']
        return vsn != None and vsn_compare(vsn, greater_or_equal, earliest_ly_version)
    return vcheck

def handle_pieces(pieces, rootdir, mode, csv_keys, csv_previous):
    csv_data = []
    parse_order = 0
    conflicts_count = 0
    for p in pieces:
        row, conflicts = make_row(p['lyfilenames'], p['path'], rootdir, mode, csv_keys)
        row['ly-version'] = p['version']
        parse_order += 1
        row['parse-order'] = parse_order
        if not csv_previous:
            row['new?'] = 'T'
        csv_data.append(row)

        if (len(conflicts) > 0):
            conflicts_count += 1
    return csv_data, parse_order, conflicts_count

def main(args):
    try:
        if args.mode == 'mutopia':
            file_paths_func = get_mutopia_ly_file_paths
        elif args.mode == 'thesession':
            file_paths_func = get_ly_file_paths
        else:
            raise ValueError("Oops! We need a valid mode argument, either 'mutopia' or 'thesession'.")

        if not os.path.exists(args.rootdir):
            print('Oops, bad path given for the directory that should contain the lilypond files.')
            return
        if args.csv_previous and not os.path.exists(args.csv_previous):
            print('Oops, bad path given for previous csv file.')
            return
        makedirs_filepath(args.csvout)

        csv_keys = get_csv_keys(args.mode)

        pieces, subdir_skips = file_paths_func(args.rootdir)
        pieces_version_checked = list(filter(version_check(args.earliest_ly_version), pieces))

        csv_data, parse_order, conflicts_count = handle_pieces(pieces_version_checked, args.rootdir, args.mode, csv_keys, args.csv_previous)

        print('\nLilyPond files parsed, data gathered.',
              '\nTotal works:', parse_order,
              '\nconflicting data count:', conflicts_count,
              '\nsubdirectory skips:', subdir_skips or 'not applicable', '(skipped pieces that have hierarchical directories of ly files)')

        # MERGE IN PREVIOUS CSV META DATA AND MARK NEW ITEMS
        final_csv_data = merge_csv_data(args.csv_previous, csv_data, 'id') if args.csv_previous else csv_data

        # GENERATE CSV FILE
        with open(args.csvout, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = csv_keys)
            writer.writeheader()
            for line in final_csv_data:
                writer.writerow(line)
            print('CSV file created: ' + args.csvout)

    except ValueError as err:
        print(err.args)

if __name__ == "__main__":
    main(parser.parse_args())
