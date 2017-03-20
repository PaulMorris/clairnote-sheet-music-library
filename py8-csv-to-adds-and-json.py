#!/usr/bin/env python3
import csv, json, re
from py_composers_etc import composer_list, instrument_list, style_list, two_word_insts

fullCSV = 'out/from-repo.csv' # 'out/errors-marked.csv'
targetJSON = 'out/sheet-music-lib-data-search.js'
targetHTML = 'out/html-checkboxes.html'

composerLookupNewAdds = {}
for c in composer_list:
    # no dates in this listing, keep it simple
    composerLookupNewAdds[c[0]] = '{0} {1}'.format(c[2], c[1])


count = 0
missingComposers = set()

with open(fullCSV, newline='') as source:
    reader = csv.DictReader(source)
    for row in reader:

        if row['mutopiacomposer'] not in composerLookupNewAdds:
            missingComposers.add(row['mutopiacomposer'])

        elif row['omit?'] != 'T' and row['new?'] == 'T':
            id = int(row['mutopia-id'])
            count += 1
            print(
                # count,
                # row['mutopia-id'],
                # int(row['mutopia-id']) in oldIds,
                # row['mutopiacomposer'],
                composerLookupNewAdds[row['mutopiacomposer']] +  ' | ' +
                row['cn-title'] + ' | ' +
                row['cn-instrument'])

print(str(count) + ' new additions.')
if len(missingComposers) > 0:
    print('PROBLEM: MISSING COMPOSERS:')
    print(missingComposers)
else:
    print('No missing composers.')
print('Done with new additions report, beginning JSON generation.\n')

# END OF NEW ADDS REPORT GENERATION


# BEGIN JSON GENERATION

inst_regex = re.compile('[a-zA-Z\-]+')

noInstrumentMatch = []
unrecognizedInstTokens = set()

# todo: Lute isn't found
# 'Lute / Theorbo / Vihuela'
# Vihuela

def instClassifier(mutopiainstrument, id):
    insts = []
    mutoInst = mutopiainstrument
    for i in two_word_insts:
        if i in mutoInst:
            hyphenated = i.replace(" ", "-")
            mutoInst = mutoInst.replace(i, hyphenated)

    tokens = inst_regex.findall(mutoInst)
    for t in tokens:
        t = t.capitalize()
        if t.endswith('s') and not t.endswith('ss'):
            t = t[0:-1]
        if t in instrument_list:
            insts.append(t)
        else:
            unrecognizedInstTokens.add(t)

    if insts == []:
        noInstrumentMatch.append([id, mutoInst])
    # print(insts)
    return insts


instrumentTally = {}
styleTally = {}
composerTally = {}

with open(fullCSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    # recsObject - an object with ids as keys that map to arrays of data for each item
    recsObject = {}
    # recsIdArray - an array of mutopia ids ordered into the default sort order for 'browsing'
    recsSortedIds = []

    for row in reader:
        if row['omit?'] != 'T':

            # IDs for the ordered array
            recsSortedIds.append(int(row['mutopia-id']));

            # INSTRUMENTS
            insts = instClassifier(row['cn-instrument'], row['mutopia-id'])
            for i in insts:
                if i in instrumentTally:
                    instrumentTally[i] += 1
                else:
                    instrumentTally[i] = 1

            # STYLES
            # handle style 'Popular / Dance'
            stl = row['cn-style'].replace(' / ', '')
            if stl in styleTally:
                styleTally[stl] += 1
            else:
                styleTally[stl] = 1

            # COMPOSERS
            comp = row['mutopiacomposer']
            if comp in composerTally:
                composerTally[comp] += 1
            else:
                composerTally[comp] = 1

            multifile = (1 < len(row['filename'].split(',,, ')))

            recsObject[ int(row['mutopia-id']) ] = [
                 stl,
                 comp, # 1
                 row['cn-title'],
                 insts, # 3
                 # instsCSS, # instrument classes
                 row['path'], # 4
                 False if multifile else row['filename'][:-3],
                 row['license-type'] + row['license-vsn'], # 6
                 row['cn-opus'],
                 row['cn-poet'], # 8
                 row['date'],
                 row['arranger'], # 10
                 ]

    out = json.dumps(recsObject)
    print('JSON parsed.')

    f = open(targetJSON, 'w')
    f.write('var recsjson = ' + out)
    f.write('\nvar recsSortedIds = ' + json.dumps(recsSortedIds))
    print('JSON saved.')


    # print(instrumentTally)
    print('\nEach piece has to have at least one instrument that is recognized.')
    print('Pieces with no instrument recognized (fix these):', sorted(noInstrumentMatch))

    print('\nA piece may have other instruments that are not recognized.  (Optionally add these.)')
    print('Unrecognized Instruments:', sorted(unrecognizedInstTokens))

    # composer lookup table also goes in json data file
    composerLookup = {}
    composerLookupText = ''

    for c in composer_list:
        if c[0] in composerTally:
            composerLookup[c[0]] = ['{0} {1}'.format(c[2], c[1]), '{0}'.format(c[3])]

    composerLookupText = json.dumps(composerLookup)
    f.write('\nvar composerLookup = ' + composerLookupText)

    print('\nComposerLookup saved in JS file.')



# OUTPUT CHECKBOXES HTML

htmlOut = ''
ulOpen = '<ul class="filter-panel">\n'
ulClose = '</ul>\n\n'
formCloseDivClose = '</form>\n</div>\n\n'
liAlphabetA = '<li class="filter-panel-header">'
liAlphabetB = '</li>\n'


## STYLES

styleGroupSize = 6
styleShortList = list(filter(lambda x: x in styleTally, style_list))
count = 0
htmlOut += '<div id="style-filters" class="filters">\n'
# todo: when needed handle PopularDance --> 'Popular / Dance'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Style</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="s-all">Select All</a> &nbsp; <a id="s-none">Deselect All</a></span>\n'
htmlOut += '<form name="style-form" id="style-form">\n\n'
htmlOut += ulOpen
for s in styleShortList:
    htmlOut += '<li><input type="checkbox" name="s-box" id="{0}" /><a class="f-link">{0} [{1}]</a></li>\n'.format(s, styleTally[s])
    count += 1
    if count % styleGroupSize == 0:
        htmlOut += ulClose + ulOpen
htmlOut += ulClose
htmlOut += formCloseDivClose


## INSTRUMENTS

instrumentGroupSize = 9
instrumentShortList = list(filter(lambda x: x in instrumentTally, instrument_list))
count = 0
htmlOut += '<div id="instrument-filters" class="filters">\n'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Instrument</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="i-all">Select All</a> &nbsp; <a id="i-none">Deselect All</a></span>\n'
htmlOut += '<form name="instrument-form" id="instrument-form">\n\n'
htmlOut += ulOpen
for i in instrumentShortList:
    htmlOut += '<li><input type="checkbox" name="i-box" id="{0}" /><a class="f-link">{0} [{1}]</a></li>\n'.format(i, instrumentTally[i])
    count += 1
    if count % instrumentGroupSize == 0:
        htmlOut += ulClose + ulOpen
htmlOut += ulClose
htmlOut += formCloseDivClose


## COMPOSERS

composerGroupSize = 10
composerShortList = list(filter(lambda x: x[0] in composerTally, composer_list))
compShortestList  = list(map(lambda x: x[0], composerShortList))

# fromLetters and toLetters contain lists of the letters that go in the alphabetical headings for each group
# fromLetters = the first letter and every nth letter beyond that
# toLetters = the (nth - 1) letter and every nth letter beyond that
# we just delete them off the front of the list as they are used
fromLetters       = list(map(lambda x: x[0], compShortestList[::composerGroupSize]))
toLetters         = list(map(lambda x: x[0], compShortestList[(composerGroupSize - 1)::composerGroupSize]))
toLetters.append(compShortestList[-1:][0][0])
count = 0

htmlOut += '<div id="composer-filters" class="filters">\n'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Composer</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="c-all">Select All</a> &nbsp; <a id="c-none">Deselect All</a></span>\n'
htmlOut += '<form name="composer-form" id="composer-form">\n\n'

for c in composerShortList:
    if count % composerGroupSize == 0 and len(fromLetters) > 0 and len(toLetters) > 0:
        if count == 0:
            htmlOut += ulOpen
        else:
            htmlOut += ulClose + ulOpen

        htmlOut += liAlphabetA + fromLetters[0] + ' - ' + toLetters[0] + liAlphabetB
        del fromLetters[0]
        del toLetters[0]

    htmlOut += '<li><input type="checkbox" name="c-box" id="{0}" /><a class="f-link">{1}, {2} {3} [{4}]</a></li>\n'.format(c[0], c[1], c[2], c[3], composerTally[c[0]])
    count += 1

htmlOut += ulClose
htmlOut += formCloseDivClose

h = open(targetHTML, 'w')
h.write(htmlOut)


'''
    unrecognized instrument tokens results:

    # April5-2016 ['Chamber', 'Male',
                   'Also', 'Alti', 'Amore', 'And', 'Baritone', 'Basset', 'Bassi', 'Basso', 'Classical', 'Clavichord', 'Continuo', 'D', 'Duet', 'F', 'For', 'French', 'In', 'Or', 'Sa', 'Satb', 'Solo', 'Soprani', 'Soprano', 'Tenor', 'Tenori', 'Transcribed', 'Triangle', 'Ttbb', 'Tttb', 'Two']

    # June17-2015 ['Also', 'Alti', 'Amore', 'And', 'Baritone', 'Basset', 'Bassi', 'Basso', 'Classical', 'Clavichord', 'Continuo', 'D', 'Duet', 'F', 'For', 'French', 'In', 'Or', 'Sa', 'Satb', 'Solo', 'Soprani', 'Soprano', 'Tenor', 'Tenori', 'Transcribed', 'Triangle', 'Ttbb', 'Tttb', 'Two']

    # June16-2015: {'Tttb', 'Soprano', 'Classical', 'F', 'Tenor', 'Alti', 'String', 'And', 'Clavichord', 'Ensemble', 'In', 'Satb', 'Baritone', 'D', 'Amore', 'For', 'Bassi', 'Basso', 'Continuo', 'Or', 'Ttbb', 'Transcribed', 'Tenori', 'French', 'Quartet', 'Sa', 'Basset', 'Two', 'Soprani', 'Also', 'Duet', 'Solo', 'Triangle'}

    # OLD {'Duet', 'For', 'Vihuela', 'Basso', 'Ttbb', 'Transcribed', 'Two', 'Sa', 'Tttb', 'And', 'Soprano', 'Clavichord', 'Satb', 'Continuo'}

'''


'''
#   "style", "mutopiacomposer", "composer", "mutopiatitle", "title", "mutopiainstrument", "instrument", "mutopia-id", "mutopiaopus", "opus", "mutopiapoet", "poet", "date", "source", "license-type", "license-vsn", "license", "copyright", "arranger", "footer", "version", "filename", "path"
'''

# see this script about csv to json in python
# http://www.andymboyle.com/2011/11/02/quick-csv-to-json-parser-in-python/
