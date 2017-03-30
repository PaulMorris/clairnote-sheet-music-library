#!/usr/bin/env python3
import csv, os, re, argparse, shutil
from collections import Counter
from py_ly_parsing import get_ly_filenames, regexes

# COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("mode", help = "The mode for modifying ly files, e.g. 'mutopia' or 'thesession'")
parser.add_argument("csvpath", help = "Path to the CSV file input")
parser.add_argument("outdir", help = "The output directory to copy the files to")
parser.add_argument("rootdir", help = "The root directory that contains the ly files")

def old_mutopia_cc(row):
    return 'license = "' + row['copyright'] + '"'

def mutopia_cc(row):
    cc1 = r'copyright = \markup { \vspace #1.8 \sans \abs-fontsize #7.5 \wordwrap {Sheet music in \with-url #"http://clairnote.org" {Clairnote music notation} published by Paul Morris using \with-url #"http://www.lilypond.org" {LilyPond.} Original typesetting by \maintainer for the \with-url #"http://www.mutopiaproject.org" {Mutopia Project.} '

    cc2 = r'Free to distribute, modify, and perform.}}'

    ccLookup = {
        'pd0': r'Placed in the \with-url #"http://creativecommons.org/publicdomain/zero/1.0/" {public domain} by the typesetter. ',
        'by3': r'Licensed under \with-url #"http://creativecommons.org/licenses/by/3.0/" {Creative Commons Attribution 3.0.} ',
        'by4': r'Licensed under \with-url #"http://creativecommons.org/licenses/by/4.0/" {Creative Commons Attribution 4.0.} ',
        'by-sa3': r'Licensed under \with-url #"http://creativecommons.org/licenses/by-sa/3.0/" {Creative Commons Attribution-ShareAlike 3.0} ',
        'by-sa4': r'Licensed under \with-url #"http://creativecommons.org/licenses/by-sa/4.0/" {Creative Commons Attribution-ShareAlike 4.0} '
    }

    ccKey = row['license-type'] + row['license-vsn']

    try:
        if ccKey in ccLookup:
            fullcc = cc1 + ccLookup[ccKey] + cc2
            return fullcc
        else:
            print('Copyright problem, Mutopia ID: ', row['id'])
            ValueError("Oops! Error with copyright problem...")
    # TODO: get a better error type
    except ValueError as err:
        print(err.args)

def handle_line_mutopia(line, newf, old_mutopia_footer, is_topfile, row):

    copyright_case = regexes['copyright'].search(line)
    tagline_case = old_mutopia_footer and regexes['tagline'].search(line)
    version_case = is_topfile and regexes['raw_version'].search(line)
    try:
        # make sure the line doesn't match more than one of these cases
        if Counter([copyright_case, tagline_case, version_case])[True] > 1:
            print('Oops! A file has too many header fields on one line.')
            print('id:', row['id'], 'path:', path_to_ly)
            ValueError("Oops!")

        # add spaces for these cases
        if copyright_case or tagline_case:
            sp = regexes['spaces'].search(line)
            s = sp.group()[0:-1]

        # copyright and license
        if copyright_case:
            cc = old_mutopia_cc(row) if old_mutopia_footer else mutopia_cc(row)
            newf.write(s + cc + '\n')

        # tagline - only for old mutopia footer
        elif tagline_case:
            cc = mutopia_cc(row)
            newf.write(s + cc + '\n')
            newf.write(s + 'tagline = ##f\n')

        # clairnote code - only if this is a topfile
        elif version_case:
            newf.write(line)
            newf.write(r'\include "clairnote-code.ly"' + '\n')

        # else straight copy
        else:
            newf.write(line)

    # TODO: find a better error type
    except ValueError as err:
        print(err.args)

def handle_row_mutopia(row, rootdir, outdir):
    topfiles = row['filename'].split(',,, ')

    # old mutopia footers have no license field
    old_mutopia_footer = True if row['license'] == "" else False

    root_dir_path = os.path.join(rootdir, row['path'])
    out_dir_path = os.path.join(outdir, row['path'])
    os.makedirs(out_dir_path, mode = 0o777, exist_ok = True)

    all_files = [f for f in os.listdir(root_dir_path) if os.path.isfile(os.path.join(root_dir_path, f))]
    lyfiles = get_ly_filenames(all_files)
    other_files = [f for f in all_files if f not in lyfiles]

    for ly in lyfiles:
        source = os.path.join(root_dir_path, ly)
        target = os.path.join(out_dir_path, ly)
        is_topfile = ly in topfiles

        # create new file and copy old file to it, changing as needed
        with open(source, 'r') as oldf, open(target, 'w') as newf:
            for line in oldf:
                handle_line_mutopia(line, newf, old_mutopia_footer, is_topfile, row)

    for f in other_files:
        # copy other files to the other directory
        if f[-4:] != '.pdf' and f[-4:] != '.mid' and f[-5:] != '.midi':
            source = os.path.join(root_dir_path, f)
            target = os.path.join(out_dir_path, f)
            shutil.copy2(source, target)

def session_tagline(subtitle):
    part1 = r'tagline = \markup { \vspace #1.8 \sans \abs-fontsize #7.5 \wordwrap {Sheet music in \with-url #"http://clairnote.org" {Clairnote music notation} published by Paul Morris using \with-url #"http://www.lilypond.org" {LilyPond.} '
    part2 = r'Automatically converted to LilyPond format from an ABC source file from \with-url #"https://thesession.org" {the Session} website: \with-url #"'
    part3 = r'" {"'
    part4 = '"}}}'
    result = part1 + part2 + subtitle + part3 + subtitle + part4
    return result

def handle_line_session(line, newf, row):

    subtitle_case = regexes['subtitle'].search(line)
    tagline_case = regexes['tagline'].search(line)
    version_case = regexes['raw_version'].search(line)
    try:
        # make sure the line doesn't match more than one of these cases
        if Counter([subtitle_case, tagline_case, version_case])[True] > 1:
            print('Oops! A file has too many header fields on one line.')
            print('id:', row['id'], 'path:', path_to_ly)
            ValueError("Oops!")

        # add spaces for these cases
        if subtitle_case or tagline_case:
            sp = regexes['spaces'].search(line)
            s = sp.group()[0:-1]

        # subtitle becomes a reference to the source url
        if subtitle_case:
            # TODO: a single space subtitle puts some space between the title and the first system... Ugh
            newf.write(s + 'subtitle = " "\n')
            newf.write(s + 'source = "' + row['subtitle'] + '"\n')
            newf.write(s + 'arranger = ' + 'Setting ' + str(row['setting-number']))

        # tagline
        elif tagline_case:
            tagline = session_tagline(row['subtitle'])
            newf.write(s + tagline + '\n')

        # clairnote code
        elif version_case:
            newf.write(line)
            newf.write(r'\include "clairnote-code.ly"' + '\n')

        # else straight copy
        else:
            newf.write(line)

    # TODO: find a better error type
    except ValueError as err:
        print(err.args)


def handle_row_session(row, rootdir, outdir):
    source = os.path.join(rootdir, row['filename'])
    target = os.path.join(outdir, row['filename'])

    # create new file and copy old file to it, changing as needed
    with open(source, 'r') as oldf, open(target, 'w') as newf:
        for line in oldf:
            handle_line_session(line, newf, row)


def handle_csv(csvpath, rootdir, outdir, mode):
    with open(csvpath, newline = '') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['omit?'] != 'T' and row['cn-code'] == 'False' and row['new?'] == 'T':
                if mode == 'mutopia':
                    handle_row_mutopia(row, rootdir, outdir)
                elif mode == 'thesession':
                    handle_row_session(row, rootdir, outdir)

def main(args):
    try:
        if args.mode == 'mutopia':
            handle_csv(args.csvpath, args.rootdir, args.outdir, args.mode)

        elif args.mode == 'thesession':
            os.makedirs(args.outdir, mode = 0o777, exist_ok = True)
            handle_csv(args.csvpath, args.rootdir, args.outdir, args.mode)

        else:
            raise ValueError("Oops! We need a valid mode argument, either 'mutopia' or 'thesession'.")

        print("LilyPond files copied to a new location and edited to include clairnote code and footer.")
    except ValueError as err:
        print(err.args)

if __name__ == "__main__":
    main(parser.parse_args())
