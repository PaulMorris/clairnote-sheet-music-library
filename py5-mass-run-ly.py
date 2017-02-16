#!/usr/bin/env python3
from subprocess import Popen, PIPE, STDOUT
import csv, os, re, argparse, subprocess

parser = argparse.ArgumentParser()

# default (-d) is to not render omitted items
parser.add_argument("-d", "--notomitted", help="render only items that are not omitted", action="store_true")
parser.add_argument("--omitted", help="render only items that are omitted", action="store_true")

parser.add_argument("--new", help="render only new items", action="store_true")
parser.add_argument("--old", help="render only old items", action="store_true")

parser.add_argument("--error", help="render only items that have serious errors", action="store_true")
parser.add_argument("--minorerror", help="render only items that have minor errors", action="store_true")
parser.add_argument("--noerror", help="render only items that have no errors", action="store_true")

parser.add_argument("--flagged", help="render only items that have been flagged", action="store_true")

parser.add_argument("--noa4", help="don't do a4 format output", action="store_true")
parser.add_argument("--noletter", help="don't do letter format output", action="store_true")
parser.add_argument("--midi", help="include midi output", action="store_true")
parser.add_argument("--midionly", help="only midid output, no visual output", action="store_true")

args = parser.parse_args()

rootDir = '../../The-Mutopia-Project/ftp/'

# Possibilities for sourceCSV
# sourceCSV = 'out/new-adds.csv'
# sourceCSV = 'out/previous-final-none-omitted.csv'
# sourceCSV = 'out/test-one.csv'
# sourceCSV = 'out/from-repo.csv'

sourceCSV = 'out/previous-final.csv'
targetCSV = 'out/errors-marked.csv'

logfile = 'out/auto-log-file.txt'
errorFile = 'out/error-log.txt'

tempLogFile = 'out/temp-log-file.txt'

# old paths to executables from previous laptop
# '/Applications/LilyPond-dev-version/LilyPond-2-19-36.app/Contents/Resources/bin/lilypond'
# '/Applications/lilypond-stable/LilyPond.app/Contents/Resources/bin/lilypond'

devExecutable = 'lilypond'
stableExecutable = 'lilypond-stable'
# this should be only first 4 digits of version string
currentStableVersion = "2.18"


#### delete the log files if they already exist
if os.path.isfile(errorFile):
    os.remove(errorFile)

if os.path.isfile(logfile):
    os.remove(logfile)

with open(errorFile, "a") as aErrorFile:
    aErrorFile.write('Error Log\n\n')


################################################################
#### error detection

warn = re.compile('.*warning:')
err = re.compile('.*error:')
clairnote = re.compile('.*clairnote-code.ly.*')

midi1 = re.compile(r'.*programming error\: Impossible or ambiguous \(de\)crescendo in MIDI.*')
midi2 = re.compile(r'.*warning\: \(De\)crescendo with unspecified starting volume in MIDI.*')
midi3 = re.compile(r'.*warning\: MIDI channel wrapped around.*')
midi4 = re.compile(r'.*warning\: remapping modulo 16.*')

compression1 = re.compile('.*warning: compressing over-full page.*')
compression2 = re.compile('.*warning: page.*has been compressed.*')

ambitus = re.compile('.*Ambitus_engraver.*')

# 3 files out of 480 files have this:
# programming error: number of pages is out of bounds
# continuing, cross fingers
# Fitting music on 3 pages...
# programming error: number of pages is out of bounds
# continuing, cross fingers

problemFileIDs = set()

def errorCheck(aLogFile, mutoId, path, aErrorFile):
    with open(aLogFile, newline='') as logFile, open(aErrorFile, "a") as errorFile:
        for line in logFile:

            if midi1.search(line) or midi2.search(line) or midi3.search(line) or midi4.search(line):
                # print('midi issue:', mutoId)
                continue
            elif compression1.search(line):
                errorFile.write('compression warning: ' + mutoId + ' ' + path + '\n')
                continue
            elif compression2.search(line):
                continue
            elif warn.search(line):
                problemFileIDs.add(mutoId)
                errorFile.write('warning: ' + mutoId + ' ' + path + '\n' + line + '\n')
            elif err.search(line):
                problemFileIDs.add(mutoId)
                errorFile.write('error: ' + mutoId + ' ' + path + '\n' + line + '\n')
            elif clairnote.search(line):
                problemFileIDs.add(mutoId)
                errorFile.write('clairnote-code problem: ' + mutoId + ' ' + path + '\n')
                if ambitus.search(line):
                    errorFile.write('Ambitus engraver: ' + mutoId + ' ' + path + '\n')


def runLilyPond(size, suffix, midiYes, pathToFileNoExtension, pathToLy, executable):
    if midiYes:
        cmd = [executable,
                      '-dno-point-and-click',
                      '-dpaper-size=\"' + size + '\"',
                      '-dmidi-extension=\"mid\"',
                      '-o',
                      pathToFileNoExtension,
                      pathToLy]
    else:
        cmd = [executable,
                      '-dno-point-and-click',
                      '-dpaper-size=\"' + size + '\"',
                      '-o',
                      pathToFileNoExtension,
                      '-e',
                      '(set! write-performances-midis (lambda (performances basename . rest) 0))',
                      pathToLy]

    #### open subprocesses to run the command and to write result to log files
    #### one temporary for error checking and another the full log of running lilypond
    # TODO there's probably a better way than writing to a temp file

    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT)

    # '-a', makes tee append rather than overwrite the file
    teeProc = Popen(['tee', tempLogFile], stdin=proc.stdout)

    proc.stdout.close()
    teeProc.communicate()

    with open(logfile, "a") as aLogFile, open(tempLogFile) as temp:
        for line in temp:
            aLogFile.write(line)

    #### rename pdf files with -a4 and -let suffix
    try:
        os.rename(pathToFileNoExtension + '.pdf', pathToFileNoExtension + suffix + '.pdf')
        print('renamed to: ' + pathToFileNoExtension + suffix + '.pdf\n')
    except OSError as e:
        print(e)
        stringout = 'manual -let or -a4 suffix needs to be added'
        with open(logfile, "a") as myfile:
            myfile.write(stringout)
        print(stringout)


    # code for other piping approaches
    # p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    # stdout, stderr = p.communicate()

    # p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    # output = p.stdout.read()
    # print(output)



def runLilyPondForMidiOnly(pathToFileNoExtension, pathToLy, executable):
    output = subprocess.call([executable,
                                      '-dno-print-pages',
                                      '-dmidi-extension=\"mid\"',
                                      '-o',
                                      pathToFileNoExtension,
                                      pathToLy])
    print(output)


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

with open(sourceCSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if includeRow(row):
            triagedRows.append(row)

print('About to run LilyPond on', len(triagedRows), 'items...')
if input('Continue? If so type y.') == 'y':
    for row in triagedRows:
        pathToDir = os.path.join(rootDir, row['path'])
        lyfilenames = row['filename'].split(',,, ')
        version = row['ly-version']
        executable = stableExecutable if version[:4] == currentStableVersion else devExecutable

        for lyfile in lyfilenames:
            pathToLy = os.path.join(pathToDir, lyfile)
            stripFileName = lyfile.split('.')
            fileNoExtension = stripFileName[0]
            pathToFileNoExtension = os.path.join(pathToDir, fileNoExtension)
            thisMidi = args.midi
            mutoId = row['mutopia-id']

            stringout = '----------------------------\n' + '____________________________\n' + \
                mutoId + '\n' + row['parse-order'] + '\n' + \
                row['cn-title'] + '\n' + os.path.join(row['path'], lyfile) + '\n'

            print(stringout)

            with open(logfile, "a") as myfile:
                myfile.write(stringout)

            # LETTER PDF
            if not (args.noletter or args.midionly):
                runLilyPond("letter", "-let", thisMidi, pathToFileNoExtension, pathToLy, executable)
                thisMidi = False
                errorCheck(tempLogFile, mutoId, row['path'] + lyfile, errorFile)

            # A4 PDF
            if not (args.noa4 or args.midionly):
                runLilyPond("a4", "-a4", thisMidi, pathToFileNoExtension, pathToLy, executable)
                errorCheck(tempLogFile, mutoId, row['path'] + lyfile, errorFile)

            # MIDI
            if args.midionly:
                runLilyPondForMidiOnly(pathToFileNoExtension, pathToLy, executable)
                # TODO errorCheck(tempLogFile, mutoId, errorFile)


with open(errorFile, "a") as aErrorFile:
    aErrorFile.write('\nList of error files:\n')
    aErrorFile.write(repr(sorted(problemFileIDs)))
    aErrorFile.write('\nLength of list: ' + str(len(problemFileIDs)))

if os.path.isfile(tempLogFile):
    os.remove(tempLogFile)


################################################################
# indicate error files in csv

# convert-ly
# convertlyErrIds = set([])

'''
csvKeys = ['mutopia-id', 'parse-order', 'omit?', 'omit-reason', 'new?', 'error-status?', 'flagged?'
    'cn-code', 'ly-version', 'mutopiacomposer', 'cn-title', 'cn-opus', 'cn-style', 'cn-instrument',
    'cn-poet', 'license-type', 'license-vsn', 'cn-license', 'filename', 'path', 'mtime',
    'arranger', 'date', 'source', 'copyright', 'tagline',
    'footer', 'composer', 'mutopiatitle', 'title', 'mutopiaopus', 'opus', 'mutopiastyle', 'style',
    'mutopiainstrument', 'instrument', 'mutopiapoet', 'poet', 'mutopialicense', 'license']
'''

stringout2 = 'omitting problem files in CSV file...\nIDs of problem files:\n'
print(stringout2)
with open(logfile, "a") as myfile:
    myfile.write(stringout2)

with open(sourceCSV, newline='') as csvfileA, open(targetCSV, 'w') as csvfileB:
    reader = csv.DictReader(csvfileA)
    writer = csv.DictWriter(csvfileB, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        # for rows with empty str '' as ids, better to fix upstream
        if len(row['mutopia-id']) > 0:
            # print('foo', problemFileIDs)
            if row['mutopia-id'] in problemFileIDs:
                print(row['mutopia-id'])
                # DON'T OMIT AUTOMATICALLY
                # row['cn-omit'] = 'T'
                # row['cn-omit-reason'] = 'ly error or warn'
                row['error-status?'] = 'error'
                problemFileIDs.discard(row['mutopia-id'])
            '''
            elif int(row['mutopia-id']) in convertlyErrIds:
                print(row['mutopia-id'])
                row['cn-omit'] = 'T'
                row['cn-omit-reason'] = 'convert-ly error'
                convertlyErrIds.discard(row['mutopia-id'])
            '''
        writer.writerow(row)
    print('done with CSV file')
