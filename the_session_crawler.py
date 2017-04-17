import os, argparse, urllib.request, urllib.error
from time import sleep
from ly_parsing import makedirs_filepath, makedirs_dirpath

parser = argparse.ArgumentParser()
parser.add_argument("fromid", help="Start with this tune id number")
parser.add_argument("toid", help="End with this tune id number")
parser.add_argument("errorfile", help="Log errors to this file")
parser.add_argument("outdir", help = "The output directory to save the abc files to")

def tune_page_exists(tune):
    ''' Tries a given session url (that points to a tune page).
        Returns a tuple: a boolean indicating success and either
        a boolean indicating whether the page exists or not, or an error message. '''
    url = "https://thesession.org/tunes/" + str(tune)
    try:
        response = urllib.request.urlopen(url)
        info = response.info()
        return True, True if info else False
    except urllib.error.URLError as error:
        return False, error

def check_errors(errors, errorfile):
    ''' Check if the tune page exists at all, for all errors that occurred when
        fetching abc files. '''
    print('Checking for page existence for error files...')
    with open(errorfile, 'a') as f:
        f.write('\n---- Check whether tune pages exist ----\n\n')
        for item in errors:
            tune, setting = item
            tune_setting = str(tune) + '-' + str(setting)
            success, page_exists = tune_page_exists(tune)

            if success and page_exists == True:
                str_out = tune_setting + ' Tune page exists.\n'
                print(str_out)
                f.write(str_out)
            elif success and page_exists == False:
                str_out = tune_setting + ' Tune page DOES NOT exist.\n'
                print(str_out)
                f.write(str_out)
            else:
                str_out = tune_setting + ' ' + str(page_exists) + '\n'
                print(str_out)
                f.write(str_out)
            sleep(2)

def get_file_name (url):
    ''' Gets the file name for a given session url (that points to an abc file).
        Returns a tuple: a boolean indicating success and either
        the file name or the error message. '''
    try:
        response = urllib.request.urlopen(url)
        # <http.client.HTTPResponse object at 0x7ff8ff7efef0>

        disposition = response.info()['Content-Disposition']
        # 'attachment; filename=lovelyloughsheelin-1.abc'

        file_name = disposition.split('filename=')[1]
        return True, file_name

    except urllib.error.URLError as error:
        return False, error

# The abc files are named with 'file_name-1.abc', 'file_name-2.abc' corresponding
# to urls like https://thesession.org/tunes/26/abc/1 where 26 is the tune id and
# /1, /2 at the end corresponds to '-1' '-2' in the file name (the setting).
# For each tune we start with urls at '/1' and count up.  We check the name of
# the file returned and when it doesn't have a '-' but is just
# 'file_name.abc' then we have run out of settings.
# 'file_name.abc' is the same as 'file_name-1.abc'

def download_abc_files(tune_numbers, outdir, errorfile):
    errors = []
    for tune in tune_numbers:
        tune_url = "https://thesession.org/tunes/" + str(tune) + "/abc/"
        setting = 1

        while setting != 0:
            setting_url = tune_url + str(setting)
            success, file_name_or_error = get_file_name(setting_url)
            sleep(1)

            # identify files with one or two digit setting numbers,
            # and save them to disk (see above)
            if success and (file_name_or_error[-6] == "-" or
                            file_name_or_error[-7] == "-"):
                saveto = os.path.join(outdir, file_name_or_error)
                urllib.request.urlretrieve(setting_url, saveto)
                print(str(tune), str(setting), file_name_or_error)
                setting += 1
                sleep(1)

            # TODO: if a setting fails, the next settings for that tune will not be tried.
            # So far most errors are on setting 1, so usually it is whole tunes that are missing.
            elif not success or not file_name_or_error:
                errors.append([tune, setting])
                str_out = str(tune) + '-' + str(setting) + ' ' + setting_url + ' ' + str(file_name_or_error) + '\n'
                with open(errorfile, 'a') as f:
                    f.write(str_out)
                print('ERROR:', str_out)
                setting = 0

            else:
                setting = 0

    return errors

def main(args):
    makedirs_dirpath(args.outdir)
    makedirs_filepath(args.errorfile)
    tune_numbers = range(int(args.fromid), int(args.toid) + 1)
    errors = download_abc_files(tune_numbers, args.outdir, args.errorfile)
    check_errors(errors, args.errorfile)

if __name__ == "__main__":
    main(parser.parse_args())
