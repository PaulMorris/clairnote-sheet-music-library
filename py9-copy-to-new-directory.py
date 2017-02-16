#!/usr/bin/env python3
import os, csv, shutil, argparse

# other possibilities for sourceCSV
# sourceCSV = 'out/full-final.csv'
# sourceCSV = 'out/new-omitted.csv'

sourceCSV = 'out/errors-marked.csv'
rootDir = '../../The-Mutopia-Project/ftp/'
targetDir = '../../mutopia-clairnote-out-1-16-2017/'

# ARGUMENT PARSING

parser = argparse.ArgumentParser()

# default (-d) is to not render omitted items
parser.add_argument("-d", "--notomitted", help="copy only items that are not omitted", action="store_true")
parser.add_argument("--omitted", help="copy only items that are omitted", action="store_true")

parser.add_argument("--new", help="copy only new items", action="store_true")
parser.add_argument("--old", help="copy only old items", action="store_true")

parser.add_argument("--error", help="copy only items that have serious errors", action="store_true")
parser.add_argument("--minorerror", help="copy only items that have minor errors", action="store_true")
parser.add_argument("--noerror", help="copy only items that have no errors", action="store_true")

parser.add_argument("--flagged", help="copy only items that have been flagged", action="store_true")

args = parser.parse_args()

def includeRow(row):
    if (
    # these expressions are all reasons to not include the row/item
    (args.new == True and row['new?'] != 'T') or
    (args.old == True and row['new?'] == 'T') or

    (args.error == True and row['error-status?'] != 'error') or
    (args.noerror == True and row['error-status?'] != '') or
    (args.minorerror == True and row['error-status?'] != 'minor') or

    (args.flagged == True and row['flagged?'] != 'T') or

    (args.omitted == True and row['omit?'] != 'T') or
    (args.notomitted == True and row['omit?'] == 'T')
    ):
        return False
    else:
        return True


triagedRows = []

with open(sourceCSV, newline='') as sourceCSVFile:
    reader = csv.DictReader(sourceCSVFile)

    for row in reader:
        if includeRow(row):
            triagedRows.append(row)

    if 'y' == input('About to copy ' + str(len(triagedRows)) + ' pieces. Type y to continue.'):
        count = 0
        for row in triagedRows:
            count += 1
            pathToSourceDir = os.path.join(rootDir, row['path'])
            pathToTargetDir = os.path.join(targetDir, row['path'])
            # print(pathToSourceDir)
            print(str(count) + ' ' + pathToTargetDir)
            shutil.copytree(pathToSourceDir, pathToTargetDir)

print('Done.', count, 'pieces copied.')
