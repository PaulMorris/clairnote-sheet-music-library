import re, os

# bulk lilypond collection functions

regexes = {
    'raw_version': re.compile("\\\\version.*?\".*?\""),
    'version_digits': re.compile("[0-9]*\.[0-9]*\.[0-9]*"),
    'header': re.compile("\\\\header.*", re.DOTALL),
    'quote': re.compile("\".*\""),
    'header_fields': re.compile("\S.*?=.*?\".*?\""),
    'header_field_key': re.compile(".*?[\s|=]"),
    'header_field_val': re.compile("\".*\""),
    'muto_id': re.compile("[0-9]*$"),
    'the_session_id': re.compile("([0-9]*)#setting([0-9]*)"), # https://thesession.org/tunes/
    'footer': re.compile("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]"),
    'clairnote_code': re.compile('\\\\include.*?\"clairnote-code.ly\"'),
    'include': re.compile('\\\\include.*?\".*?\"'),
    'score': re.compile('\\\\score'),
    'mutopiacomposer': re.compile('.*mutopiacomposer.*', re.DOTALL),
    'copyright': re.compile('copyright.*?='),
    'tagline': re.compile('tagline.*?='),
    'spaces': re.compile('^.*?\S')
}

def regex_search(r, s):
    """ r is a regex, s is a string to search """
    if s == None:
        return None
    a = r.search(s)
    if a == None:
        return None
    else:
        return a.group()

def balanced_brackets(arg):
    """ Takes a string (e.g. starting with "\header" and ending at the end of
        the .ly file).  Returns the outermost brackets and their contents "{ ... }" """
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

def vsn_int(vsn):
    vsn_list = vsn.split('.')
    vsn_num = int(vsn_list[0]) * 1000000 + int(vsn_list[1]) * 1000 + int(vsn_list[2])
    return vsn_num

def vsn_greater_than_or_equals(ref, vsn):
    return vsn_int(vsn) >= vsn_int(ref)

def get_all_lilypond_filenames(filenames):
    lynames = []
    for f in filenames:
        if f[-3:] == '.ly' or f[-4:] == '.ily' or f[-4:] == '.lyi':
            lynames.append(f)
    return lynames

def get_ly_filenames(filenames):
    lynames = []
    for f in filenames:
        if f[-3:] == '.ly':
            lynames.append(f)
    return lynames

def get_version(lyfilenames, dirpath):
    """ Returns the first version found in a list of ly files. """
    vsn = None
    for name in lyfilenames:
        with open(os.path.join(dirpath, name), 'r') as f:
            # go through file line by line until we get the version
            for line in f:
                raw_vsn = regex_search(regexes['raw_version'], line)
                vsn = regex_search(regexes['version_digits'], raw_vsn)
                if vsn != None: break
        if vsn != None: break
    return vsn

def included_files_from_string(filestring):
    incs = regexes['include'].findall(filestring)
    incs2 = []
    for i in incs:
        x = regex_search(regexes['quote'], i)
        incs2.append(x[1:-1])
    return incs2

def get_included_files(lyfilenames, dirpath):
    # get list of included files
    included_files = set()
    for fname in lyfilenames:
        with open(os.path.join(dirpath, fname), 'r') as f:
            includes = included_files_from_string(f.read())
            for i in includes:
                included_files.add(i)
    return included_files

def dictify_header(fields):
    result = []
    for f in fields:
        key = regex_search(regexes['header_field_key'], f)
        val = regex_search(regexes['header_field_val'], f)
        if key == None:
            print('Missing key: ', f)
        elif val == None:
            print('Missing val: ', f)
        result.append(( key[0:-1], val[1:-1] ))
    return dict(result)

# get all header data from a file string and return it as a dict
def header_data_from_string(filestring):
    hdr1 = regex_search(regexes['header'], filestring)
    hdr2 = balanced_brackets(hdr1)
    hdr3 = regexes['header_fields'].findall(hdr2)
    hdr4 = dictify_header(hdr3)
    return hdr4

# get header data for only the keys in csv_keys, return it as a dict
def header_data_for_keys(filestring, csv_keys):
    header_data = header_data_from_string(filestring)
    row = {}
    for key in csv_keys:
        row[key] = header_data.pop(key, '')
    return row

def get_header_data(lyfilenames, dirpath, csv_keys):
    header_data = {}
    inconsistent_keys = set()
    for fname in lyfilenames:
        with open(os.path.join(dirpath, fname), 'r') as f:
            header = header_data_for_keys(f.read(), csv_keys)

            # merge this file's header fields into header_data
            # the keys of inconsistent values are stored
            irrelevant_conflicts = ['footer', 'filename', 'source', 'subtitle']
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
            c = regexes['clairnote_code'].search(f.read())
            if c:
                result.add(True)
            else:
                result.add(False)
    return result

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


# unused functions
"""
def create_full_paths(dirpath, filenames):
    paths = []
    for f in filenames:
        paths.append(os.path.join(dirpath, f))
    return paths

def get_all_dir_ly_paths(rootdir):
    lypaths = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        lyfiles = get_all_lilypond_filenames(filenames)
        lypaths.append(create_full_paths(dirpath, lyfiles))
    return lypaths

def extract_multi_data(filestring, parseOrder, fname):
    incs = regexes['include'].findall(filestring)
    incs2 = []
    for i in incs:
        incs2.append(regex_search(regexes['quote'], i))
    scrs = regexes['score'].findall(filestring)
    print(fname, scrs, incs2)
"""
