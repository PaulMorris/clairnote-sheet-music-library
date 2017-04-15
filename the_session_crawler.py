import os, argparse, urllib.request
from time import sleep
from ly_parsing import create_directories

parser = argparse.ArgumentParser()
parser.add_argument("fromid", help="Start with this tune id number")
parser.add_argument("toid", help="End with this tune id number")
parser.add_argument("errorfile", help="Log errors to this file")
parser.add_argument("outdir", help = "The output directory to save the abc files to")

# The abc files are named with 'file_name-1.abc', 'file_name-2.abc' corresponding
# to urls like https://thesession.org/tunes/26/abc/1 where 26 is the tune id and
# /1, /2 at the end corresponds to '-1' '-2' in the file name (the setting).
# For each tune we start with urls at '/1' and count up.  We check the name of
# the file returned and when it doesn't have a '-' but is just
# 'file_name.abc' then we have run out of settings.
# 'file_name.abc' is the same as 'file_name-1.abc'

# returns the file name for a given url
def get_file_name (url):
    try:
        response = urllib.request.urlopen(url)
        # <http.client.HTTPResponse object at 0x7ff8ff7efef0>

        disposition = response.info()['Content-Disposition']
        # 'attachment; filename=lovelyloughsheelin-1.abc'

        file_name = disposition.split('filename=')[1]
        return file_name
    except:
        return None

def main(args):
    # create directories takes a full path to a file, but does nothing with the file name part
    create_directories(os.path.join(args.outdir, 'no-file.txt'))
    create_directories(args.errorfile)

    for i in range(int(args.fromid), int(args.toid) + 1):
        tune_url = "https://thesession.org/tunes/" + str(i) + "/abc/"
        counter = 1

        while counter != 0:
            sleep(2)
            setting_url = tune_url + str(counter)
            file_name = get_file_name(setting_url)

            # TODO: if a setting fails, the next settings for that tune will not be tried.
            # So far most errors are on setting 1, so usually it is whole tunes that are missing.
            if not file_name:
                with open(args.errorfile, 'a') as f:
                    f.write(setting_url + " :Failed at get_file_name\n")
                print('ERROR: ' + str(i), str(counter) + ' - ' + setting_url)
                counter = 0

            # see above, identify files with one or two digit setting numbers,
            # and save them to disk
            elif file_name[-6] == "-" or file_name[-7] == "-":
                saveto = os.path.join(args.outdir, file_name)
                urllib.request.urlretrieve(setting_url, saveto)
                print(str(i), str(counter), file_name)
                counter += 1

            else:
                counter = 0

if __name__ == "__main__":
    main(parser.parse_args())
