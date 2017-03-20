#!/usr/bin/env python3
import csv, os, re
from py_ly_parsing import get_ly_filenames, regexes

sourceCSV = 'out/from-repo.csv'

rootDir = '../../The-Mutopia-Project/ftp/'

cc1 = r'copyright = \markup { \vspace #1.8 \sans \abs-fontsize #7.5 \wordwrap {Sheet music in \with-url #"http://clairnote.org" {Clairnote music notation} published by Paul Morris using \with-url #"http://www.lilypond.org" {LilyPond.} Original typesetting by \maintainer for the \with-url #"http://www.mutopiaproject.org" {Mutopia Project.} '

cc2 = r'Free to distribute, modify, and perform.}}'

ccLookup = {
    'pd0': r'Placed in the \with-url #"http://creativecommons.org/publicdomain/zero/1.0/" {public domain} by the typesetter. ',
    'by3': r'Licensed under \with-url #"http://creativecommons.org/licenses/by/3.0/" {Creative Commons Attribution 3.0.} ',
    'by4': r'Licensed under \with-url #"http://creativecommons.org/licenses/by/4.0/" {Creative Commons Attribution 4.0.} ',
    'by-sa3': r'Licensed under \with-url #"http://creativecommons.org/licenses/by-sa/3.0/" {Creative Commons Attribution-ShareAlike 3.0} ',
    'by-sa4': r'Licensed under \with-url #"http://creativecommons.org/licenses/by-sa/4.0/" {Creative Commons Attribution-ShareAlike 4.0} '
    }

# count = 0

with open(sourceCSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:

        # if count > 2000: break
        # count += 1

        if row['omit?'] != 'T' and row['cn-code'] == 'False' and row['new?'] == 'T':

            ccKey = row['license-type'] + row['license-vsn']
            if ccKey in ccLookup:
                newcc = cc1 + ccLookup[ccKey] + cc2
            else:
                print('Copyright problem, Mutopia ID: ', row['mutopia-id'])
                continue

            pathToDir = os.path.join(rootDir, row['path'])


            # CLAIRNOTE CODE ITEM
            topfiles = row['filename'].split(',,, ')

            for file in topfiles:
                pathToLy = os.path.join(pathToDir, file)
                pathToRenamedLy = pathToLy + "~"

                os.rename(pathToLy, pathToRenamedLy)

                # create new file and copy old file to it, changing as needed
                with open(pathToRenamedLy, 'r') as oldf, open(pathToLy, 'w') as newf:
                    for line in oldf:
                        # clairnote-code
                        if regexes['raw_version'].search(line):
                            newf.write(line)
                            newf.write(r'\include "clairnote-code.ly"' + '\n')
                        else:
                            newf.write(line)
                # move old file out of repo
                os.rename(pathToRenamedLy, 'delete-later/' + file)
            #  + os.path.join(row['path'], file)


            # HEADER/FOOTER ITEMS
            # all ly files in directory, not just top level ones

            # old mutopia footers have no license field
            if row['license'] == "": oldMutopiaFooter = True
            else: oldMutopiaFooter = False

            files = [f for f in os.listdir(pathToDir) if os.path.isfile(os.path.join(pathToDir, f))]
            lyfiles = get_ly_filenames(files)

            for file in lyfiles:
                pathToLy = os.path.join(pathToDir, file)
                pathToRenamedLy = pathToLy + "~"

                # print(row['mutopia-id'])
                # if not row['mutopia-id'] == '439':
                #   continue

                # BAIL OUT
                # continue

                # rename current file
                print(pathToLy)
                os.rename(pathToLy, pathToRenamedLy)

                # create new file and copy old file to it, changing as needed
                with open(pathToRenamedLy, 'r') as oldf, open(pathToLy, 'w') as newf:
                    for line in oldf:

                        # copyright and license
                        if regexes['copyright'].search(line):
                            sp = regexes['spaces'].search(line)
                            s = sp.group()[0:-1]

                            if oldMutopiaFooter:
                                newf.write(s + 'license = "' + row['copyright'] + '"\n')
                            elif not oldMutopiaFooter:
                                newf.write(s + newcc + '\n')

                        # tagline
                        elif regexes['tagline'].search(line) and oldMutopiaFooter:
                            sp = regexes['spaces'].search(line)
                            s = sp.group()[0:-1]
                            newf.write(s + newcc + '\n')
                            newf.write(s + 'tagline = ##f\n')

                        # else straight copy
                        else:
                            newf.write(line)

                # move old file out of repo
                os.rename(pathToRenamedLy, 'delete-later/' + file)

                #  + os.path.join(row['path'], file)
