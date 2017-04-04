#!/usr/bin/env python3
import csv, json, re, argparse
from py_composers_etc import composer_list, instrument_list, style_list, two_word_insts
from py_ly_parsing import regexes

parser = argparse.ArgumentParser()
parser.add_argument("mode", help = "The mode for input and output e.g. 'mutopia' or 'thesession'")
parser.add_argument("csvfile", help = "Path to the CSV file (input)")
parser.add_argument("jsfile", help = "Path to the new JS file (output)")
parser.add_argument("--htmlfile", help = "Path to the new HTML file (output)")

# GENERATE NEW ADDS REPORT

def report_new_additions_session(csvfile):
    count = 0
    additions = set()
    with open(csvfile, newline='') as source:
        reader = csv.DictReader(source)
        for row in reader:

            if row['omit?'] != 'T' and row['new?'] == 'T':
                additions.add(row['cn-title'])
                count += 1

    # TODO: distinguish new tune additions and new settings of existing tunes

    for a in sorted(additions):
        print(a)

    print(str(len(additions)) + ' new tunes. ' + str(count) + ' new settings.')
    print('Done with new additions report.\n')


def report_new_additions_mutopia(csvfile):
    composer_lookup = {}
    for c in composer_list:
        # no dates in this listing, keep it simple
        composer_lookup[c[0]] = '{0} {1}'.format(c[2], c[1])

    count = 0
    missing_composers = set()

    with open(csvfile, newline='') as source:
        reader = csv.DictReader(source)
        for row in reader:

            if row['mutopiacomposer'] not in composer_lookup:
                missing_composers.add(row['mutopiacomposer'])

            elif row['omit?'] != 'T' and row['new?'] == 'T':
                count += 1
                print(
                    # count,
                    # row['id'],
                    # int(row['id']) in oldIds,
                    # row['mutopiacomposer'],
                    composer_lookup[row['mutopiacomposer']] +  ' | ' +
                    row['cn-title'] + ' | ' +
                    row['cn-instrument'])

    print(str(count) + ' new additions.')
    if len(missing_composers) > 0:
        print('PROBLEM: MISSING COMPOSERS:')
        print(missing_composers)
    else:
        print('No missing composers.')
    print('Done with new additions report.\n')

# JSON GENERATION

def make_json_session(csvfile, jsfile):
    # dict/object has ids as keys that map to lists/arrays of data for each item
    items_dict = {}
    # a list/array of ids ordered into the default sort order for 'browsing'
    titles = []
    titles_to_ids = {}

    with open(csvfile, newline='') as csvf:
        reader = csv.DictReader(csvf)
        for row in reader:
            if row['omit?'] != 'T':

                ID = row['tune-id']
                print('ID', ID)
                if ID in items_dict:
                    items_dict[ID][4].append(int(row['setting-number']))
                else:
                    fname = regexes['session-filename'].search(row['filename']).group(1)
                    titles.append(row['cn-title'])
                    titles_to_ids[row['cn-title']] = ID
                    items_dict[ID] = [
                         row['cn-title'],
                         row['meter'],
                         fname,
                         row['setting-id'],
                         [int(row['setting-number'])]
                    ]

    titles.sort()
    sorted_ids = []
    for title in titles:
        sorted_ids.append(titles_to_ids[title])

    print('sorted titles', titles)
    print('sorted ids', sorted_ids)
    print('titles to ids', titles_to_ids)

    print('CSV data parsed.')

    with open(jsfile, 'w') as f:
        f.write('var sessionItems = ' + json.dumps(items_dict))
        f.write('\nvar sessionIdsSorted = ' + json.dumps(sorted_ids))
        print('JS file saved.')


# TODO: Lute isn't found
# 'Lute / Theorbo / Vihuela'
# Vihuela

def inst_classifier(mutopiainstrument, id):
    no_instrument_match = []
    unrecognized_inst_tokens = set()

    insts = []
    muto_inst = mutopiainstrument
    for i in two_word_insts:
        if i in muto_inst:
            hyphenated = i.replace(" ", "-")
            muto_inst = muto_inst.replace(i, hyphenated)

    tokens = regexes['instrument'].findall(muto_inst)
    for t in tokens:
        t = t.capitalize()
        if t.endswith('s') and not t.endswith('ss'):
            t = t[0:-1]
        if t in instrument_list:
            insts.append(t)
        else:
            unrecognized_inst_tokens.add(t)

    if insts == []:
        no_instrument_match.append([id, muto_inst])

    return insts, no_instrument_match, unrecognized_inst_tokens


def make_json_mutopia(csvfile, jsfile):
    instrument_tally = {}
    style_tally = {}
    composer_tally = {}
    # dict/object has ids as keys that map to lists/arrays of data for each item
    items_dict = {}
    # a list/array of ids ordered into the default sort order for 'browsing'
    items_sorted_ids = []

    with open(csvfile, newline='') as csvf:
        reader = csv.DictReader(csvf)
        for row in reader:
            if row['omit?'] != 'T':

                ID = int(row['id'])
                items_sorted_ids.append(ID);

                # INSTRUMENTS
                insts, no_instrument_match, unrecognized_inst_tokens = inst_classifier(row['cn-instrument'], row['id'])
                for i in insts:
                    if i in instrument_tally:
                        instrument_tally[i] += 1
                    else:
                        instrument_tally[i] = 1

                # STYLES
                # handle style 'Popular / Dance' that contains forward slash
                stl = row['cn-style'].replace(' / ', '')
                if stl in style_tally:
                    style_tally[stl] += 1
                else:
                    style_tally[stl] = 1

                # COMPOSERS
                comp = row['mutopiacomposer']
                if comp in composer_tally:
                    composer_tally[comp] += 1
                else:
                    composer_tally[comp] = 1

                multifile = (1 < len(row['filename'].split(',,, ')))

                items_dict[ID] = [
                     stl,
                     comp, # 1
                     row['cn-title'],
                     insts, # 3
                     row['path'], # 4
                     False if multifile else row['filename'][:-3],
                     row['license-type'] + row['license-vsn'], # 6
                     row['cn-opus'],
                     row['cn-poet'], # 8
                     row['date'],
                     row['arranger'], # 10
                ]

    json_out = json.dumps(items_dict)
    print('JSON parsed.')

    print('\nEach piece has to have at least one instrument that is recognized.')
    print('Pieces with no instrument recognized (fix these):', sorted(no_instrument_match))

    print('\nA piece may have other instruments that are not recognized.  (Optionally add these.)')
    print('Unrecognized Instruments:', sorted(unrecognized_inst_tokens))

    with open(jsfile, 'w') as f:
        f.write('var mutopiaItems = ' + json_out)
        f.write('\nvar mutopiaIdsSorted = ' + json.dumps(items_sorted_ids))
        print('JSON saved.')

        # composer lookup table also goes in json data file
        composer_lookup = {}
        composer_lookup_text = ''

        for c in composer_list:
            if c[0] in composer_tally:
                composer_lookup[c[0]] = ['{0} {1}'.format(c[2], c[1]), '{0}'.format(c[3])]

        composer_lookup_text = json.dumps(composer_lookup)
        f.write('\nvar composer_lookup = ' + composer_lookup_text)

        print('\nComposerLookup saved in JS file.')

    return style_tally, instrument_tally, composer_tally

# OUTPUT FILTERS CHECKBOXES HTML

def html_filter_div_start(div_id, h3_text, all_id, none_id, form_id):
    return (
        '<div id="' + div_id +'" class="filters">\n' +
        # todo: when needed handle PopularDance --> 'Popular / Dance'
        '<h3 class="filter-panel-header-main">' + h3_text + '</h3>\n' +
        '<span class="filter-panel-select-all">' +
        '<a id="' + all_id + '">Select All</a> &nbsp; <a id="' + none_id + '">Deselect All</a>' +
        '</span>\n' +
        '<form name="' + form_id + '" id="' + form_id + '">\n\n'
    )

def html_li(text, tally, name):
    return (
        '<li><input type="checkbox" name="' + name + '" id="' + text + '" />' +
        '<a class="f-link">' + text + ' [' + str(tally) + ']</a></li>\n'
    )

def html_checkboxes(ul_open, ul_close, form_close_div_close, tally, item_list, group_size, name_field):
    html = ul_open
    count = 0
    for n in item_list:
        html += html_li(n, tally[n], name_field)
        count += 1
        if count % group_size == 0:
            html += ul_close + ul_open
    html += ul_close + form_close_div_close
    return html

def html_checkboxes_composers(ul_open, ul_close, form_close_div_close, composer_tally, composer_list, group_size, name_field):
    li_alphabet_a = '<li class="filter-panel-header">'
    li_alphabet_b = '</li>\n'
    html = ''

    composer_short_list = list(filter(lambda x: x[0] in composer_tally, composer_list))
    composer_shortest_list  = list(map(lambda x: x[0], composer_short_list))

    # from_letters and to_letters contain lists of the letters that go in the alphabetical headings for each group
    # from_letters = the first letter and every nth letter beyond that
    # to_letters = the (nth - 1) letter and every nth letter beyond that
    # we just delete them off the front of the list as they are used
    from_letters = list(map(lambda x: x[0], composer_shortest_list[::group_size]))
    to_letters   = list(map(lambda x: x[0], composer_shortest_list[(group_size - 1)::group_size]))
    to_letters.append(composer_shortest_list[-1:][0][0])

    count = 0
    for c in composer_short_list:
        if count % group_size == 0 and len(from_letters) > 0 and len(to_letters) > 0:
            if count == 0:
                html += ul_open
            else:
                html += ul_close + ul_open

            html += li_alphabet_a + from_letters[0] + ' - ' + to_letters[0] + li_alphabet_b
            del from_letters[0]
            del to_letters[0]

        li_text = c[1] + ", " + c[2] + " " + c[3]
        html += html_li(li_text, composer_tally[c[0]], name_field)
        count += 1

    html += ul_close + form_close_div_close
    return html

def html_main(style_tally, style_list, instrument_tally, instrument_list, composer_tally, composer_list):
    ul_open = '<ul class="filter-panel">\n'
    ul_close = '</ul>\n\n'
    form_close_div_close = '</form>\n</div>\n\n'

    style_short_list = list(filter(lambda x: x in style_tally, style_list))
    instrument_short_list = list(filter(lambda x: x in instrument_tally, instrument_list))
    html = (
        html_filter_div_start('style-filters', 'Filter by Style', 's-all', 's-none', 'style-form') +
        html_checkboxes(ul_open, ul_close, form_close_div_close, style_tally, style_short_list, 6, 's-box') +
        html_filter_div_start('instrument-filters', 'Filter by Instrument', 'i-all', 'i-none', 'instrument-form') +
        html_checkboxes(ul_open, ul_close, form_close_div_close, instrument_tally, instrument_short_list, 9, 'i-box') +
        html_filter_div_start('composer-filters', 'Filter by Composer', 'c-all', 'c-none', 'composer-form') +
        html_checkboxes_composers(ul_open, ul_close, form_close_div_close, composer_tally, composer_list, 10, 'c-box')
    )
    return html


def main(args):
    try:
        if args.mode == 'mutopia':
            style_tally, instrument_tally, composer_tally = make_json_mutopia(args.csvfile, args.jsfile)
            html = html_main(style_tally, style_list, instrument_tally, instrument_list, composer_tally, composer_list)
            with open(args.htmlfile, 'w') as h:
                h.write(html)
            report_new_additions_mutopia(args.csvfile)

        elif args.mode == 'thesession':
            make_json_session(args.csvfile, args.jsfile)
            report_new_additions_session(args.csvfile)

        else:
            raise ValueError("Oops! We need a valid mode argument, either 'mutopia' or 'thesession'.")

    except ValueError as err:
        print(err.args)

if __name__ == "__main__":
    main(parser.parse_args())
