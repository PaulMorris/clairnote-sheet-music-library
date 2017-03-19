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

preCsvData = []
parseOrder = 1
totalWorks = 0
diffKeysCount = 0
subdirectorySkips = 0


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


raw_vsn_regex = re.compile("\\\\version.*?\".*?\"")
vsn_regex_digits = re.compile("[0-9]*\.[0-9]*\.[0-9]*")
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


def getMutopiaHeader(filetext):
    hdr1 = regexSearch(hdr_regex, filetext)
    hdr2 = balancedBraces(hdr1)
    hdr3 = hdr_fields_regex.findall(hdr2)
    hdr4 = dictifyHeader(hdr3)
    fdata = {}
    for key in csvKeys:
        fdata[key] = hdr4.pop(key, '')
    return fdata


def extractData(fdata, vsn, notIncludedFiles, dirpath, rootdir, fname):

    # use separate 'cn-' fields so we can see what's going on in the .ly files
    fdata['cn-title'] = fdata['mutopiatitle'] or fdata['title']
    fdata['cn-opus'] = fdata['mutopiaopus'] or fdata['opus']
    fdata['cn-style'] = fdata['mutopiastyle'] or fdata['style']
    fdata['cn-instrument'] = fdata['mutopiainstrument'] or fdata['instrument']
    fdata['cn-poet'] = fdata['mutopiapoet'] or fdata['poet']
    fdata['cn-license'] = fdata['mutopialicense'] or fdata['license'] or fdata['copyright']

    licenseLookup = {
        'Public Domain': ['pd', 0],
        'Creative Commons Attribution 4.0': ['by', 4],
        'Creative Commons Attribution 3.0': ['by', 3],
        'Creative Commons Attribution-ShareAlike 3.0': ['by-sa', 3],
        'Creative Commons Attribution-ShareAlike 4.0': ['by-sa', 4]
    }

    fdata['license-type'] = licenseLookup.get(fdata['cn-license'], ['', ''])[0]
    fdata['license-vsn'] = licenseLookup.get(fdata['cn-license'], ['', 0])[1]

    fdata['ly-version'] = vsn

    fdata['filename'] = ',,, '.join(list(notIncludedFiles))

    # strip slash on the left for good measure, for tests etc.
    fdata['path'] = dirpath[len(rootdir):].lstrip(os.path.sep)

    print(dirpath, "   ", rootdir, "   ", fdata['path'])

    # store the file's 'last-modified' time stamp
    # TODO: how to handle for multi ly files?
    fdata['mtime'] = os.path.getmtime(dirpath + '/' + fname)

    # not used currently, but kept for future reference
    # ctime = last time a file's metadata was changed (owner, permissions, etc.)
    # fdata['ctime'] = os.path.getctime(dirpath + '/' + fname)

    # not currently used
    # ftr = fdata['footer']
    # fdata['mutopia-id'] = regexSearch(muto_id_regex, ftr)
    # strip footer to just the date
    # fdata['footer'] = regexSearch(footer_regex, ftr)
    # remove footer
    # fdata.pop('footer', False)

    fdata['parse-order'] = parseOrder
    preCsvData.append(fdata)



def extractMultiData(filetext, parseOrder, fname):
    incs = include_regex.findall(filetext)
    incs2 = []
    for i in incs:
        incs2.append(regexSearch(quote_regex, i))
    scrs = score_regex.findall(filetext)
    print(fname, scrs, incs2)


def getIncludedFiles(filetext):
    incs = include_regex.findall(filetext)
    incs2 = []
    for i in incs:
        x = regexSearch(quote_regex, i)
        incs2.append(x[1:-1])
    return incs2



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


def processLyNames(lyfilenames, dirpath, rootdir):
    # GET THE VERSION
    vsn = None
    for fname in lyfilenames:

        # use os.path.join here?
        with open(dirpath + "/" + fname, 'r') as f:
            # go through file line by line until we get the version
            for line in f:
                vsn = regexSearch(vsn_regex_digits, regexSearch(raw_vsn_regex, line))
                if vsn != None: break
        if vsn != None: break

    # GET HEADER DATA ETC
    if vsn != None and vsnGreaterThanOrEqualTo(args.earliest_ly_version, vsn):
        global totalWorks
        totalWorks += 1
        # print('\n\n', vsn, dirpath[len(rootdir):], '\n', lyfilenames)

        # get list of included files
        includedFiles = set()
        hdrDict = {}
        diffKeys = set()

        for fname in lyfilenames:
            with open(dirpath + '/' + fname, 'r') as f:
                incs = getIncludedFiles(f.read())
                for i in incs:
                    includedFiles.add(i)

                f.seek(0)
                hdr = getMutopiaHeader(f.read())

                # extract mutopia-id from footer
                hdr['mutopia-id'] = regexSearch(muto_id_regex, hdr['footer'])
                if hdr['mutopia-id'] == None:
                    hdr['mutopia-id'] = ''

                someIrrelevantConflicts = ['footer', 'filename', 'source']
                for k, v in hdr.items():
                    if k not in hdrDict or hdrDict[k] == '':
                        hdrDict[k] = v
                    elif v != '' and hdrDict[k] != v:
                        hdrDict[k] += ', ' + v
                        if k not in someIrrelevantConflicts:
                            diffKeys.add(k)

                '''
                # TODO? track files that have headers
                if mutoHdr != None and hdrDict != None:
                    # hdrFiles.add(fname)
                    print('\nTWO MUTO HEADERS: ', dirpath[len(rootdir):], fname)

                if mutoHdr != None and hdrDict == None:
                    print('muto header: ', fname)
                    hdrDict = mutoHdr
                '''

        # print('included: ', includedFiles)
        notIncludedFiles = list(set(lyfilenames).difference(includedFiles))
        # print('not-included: ', notIncludedFiles)

        # check for clairnote-code.ly in top-level files
        clntSet = set()
        for fname in notIncludedFiles:
            with open(dirpath + '/' + fname, 'r') as f:
                c = clairnote_code_regex.search(f.read())
                if c:
                    clntSet.add(True)
                else:
                    clntSet.add(False)
        if len(clntSet) > 1:
            diffKeys.add('cn-code')
            # TODO: confirm this output is what we want in the CSV file
            hdrDict['cn-code'] = list(clntSet)
        else:
            hdrDict['cn-code'] = list(clntSet)[0]

        # Handle conflicting data in different files
        # first prune irrelevant conflicts
        # some are handled earlier, not even added to diffKeys
        if diffKeys:
            for k in ['composer', 'title', 'instrument', 'style', 'license', 'opus', 'poet']:
                if k in diffKeys and hdrDict['mutopia' + k] != '':
                    diffKeys.discard(k)

        # second deal with remaining relevant conflicts
        if diffKeys:
            global diffKeysCount
            diffKeysCount += 1
            print('omit! conflicting data:', dirpath[len(rootdir):], list(diffKeys), '\n')
            hdrDict['cn-omit'] = 'T'
            hdrDict['cn-omit-reason'] = 'conflicting header data: ' + repr(diffKeys)

        global parseOrder
        parseOrder += 1
        extractData(hdrDict, vsn, notIncludedFiles, dirpath, rootdir, fname)


def walkTheTree(rootdir):
    for dirpath, dirnames, filenames in os.walk(rootdir):

        if filenames != []:
            # get list of all .ly and .ily files in directory
            lyfilenames = getLyFilenames(filenames)

            # if (len(lyfilenames) > 1 and len(lyfilenames) < 15000)
            # or (len(lyfilenames) == 1 and len(dirnames) > 0):
            if lyfilenames != []:
                # print('M:', dirpath[len(rootdir):], lyfilenames, '\n')
                # print('G:', dirpath[len(rootdir):], ": greater than one file")

                if dirnames == []:
                    # lypaths = createFullPaths(dirpath, lyfilenames)
                    processLyNames(lyfilenames, dirpath, rootdir)
                else:
                    global subdirectorySkips
                    subdirectorySkips += 1
                    # print('skip! subdirectories:', dirpath[len(rootdir):], dirnames, '\n')
                    # lypaths = getAllDirLyPaths(dirpath)
                    # clear dirnames to prevent os.walk from going deeper
                    # we have to do it like this, delete in place:
                    dirnames.clear()


walkTheTree(args.rootdir)

print('LilyPond files parsed, data gathered.\n  Total works:', totalWorks,
    '\n  diffKeysCount:', diffKeysCount, '\n  subdirectorySkips:', subdirectorySkips)


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


final_csv_data = []
if args.csv_previous:
    final_csv_data = merge_csv_data(args.csv_previous, preCsvData, 'mutopia-id')
else:
    final_csv_data = preCsvData


# GENERATE CSV FILE

with open(args.csv_output, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csvKeys)
    writer.writeheader()
    for line in final_csv_data:
        writer.writerow(line)
    print('CSV file created: ' + args.csv_output)
