#!/usr/bin/env python3
import os, csv, shutil, argparse
from ly_parsing import row_should_be_omitted, read_csv
from ftplib import FTP
from retrying import retry

parser = argparse.ArgumentParser()

parser.add_argument("csvfile", help = "Path to the CSV file (input)")
parser.add_argument("ftpaddress", help = "The address of the ftp server")
parser.add_argument("ftppath", help="Path to root directory on ftp server")
parser.add_argument("login", help="User login for ftp server")
parser.add_argument("pwd", help="Password")
parser.add_argument("rootdir", help = "The root directory that contains the files")

# default (-d) is to not render omitted items
parser.add_argument("-d", "--notomitted", help="copy only items that are not omitted", action="store_true")
parser.add_argument("--omitted", help="copy only items that are omitted", action="store_true")

parser.add_argument("--new", help="copy only new items", action="store_true")
parser.add_argument("--old", help="copy only old items", action="store_true")

parser.add_argument("--error", help="copy only items that have serious errors", action="store_true")
parser.add_argument("--minorerror", help="copy only items that have minor errors", action="store_true")
parser.add_argument("--noerror", help="copy only items that have no errors", action="store_true")

parser.add_argument("--flagged", help="copy only items that have been flagged", action="store_true")

parser.add_argument("--dryrun", help="Don't actually copy files, just indicate how many rows would have been copied", action="store_true")


# Wait 2^x * 1000 milliseconds between each retry,
# up to 10 seconds, then 10 seconds afterwards
@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def make_ftp_connection(ftpaddress, login, pwd, ftppath):
    # connect to host on default port and switch directories
    connection = FTP(ftpaddress, login, pwd)
    connection.cwd(ftppath)
    return connection

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def quit_ftp_connection(connection):
    connection.quit()

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def change_ftp_directory(connection, path):
    connection.cwd(path)

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def upload_file(rootdir_path, filename, connection):
    with open(rootdir_path, 'rb') as f:
        connection.storbinary('STOR ' + filename, f)


def upload_row(rootdir, row, connection):
    extensions = ['.ly', '-let.pdf', '-a4.pdf', '.mid']
    # get filename without extension
    fname = row['filename'][:-3]

    for ext in extensions:
        file_ext = fname + ext
        rootdir_path = os.path.join(rootdir, row['path'], file_ext)

        if os.path.isfile(rootdir_path):
            upload_file(rootdir_path, file_ext, connection)
        else:
            # TODO: log to an error file
            print("ERROR: File not found:", rootdir_path)

def upload_rows(rootdir, ftppath, rows, connection):
    row_count = str(len(rows) - 1)

    for i, row in enumerate(rows):
        if row['path']:
            # for mutopia files in nested directories
            change_ftp_directory(connection, os.path.join(ftppath, row['path']))
            upload_row(rootdir, row, connection)
            change_ftp_directory(connection, ftppath)
        else:
            upload_row(rootdir, row, connection)

        print(str(i) + ' of ' + row_count + ' uploaded: ' + row['filename'])


def main(args):
    if not os.path.exists(args.rootdir):
        print('Oops, bad path given for the directory that should contain the files to upload.')
        return
    if not os.path.exists(args.csvfile):
        print('Oops, bad path given for the csv input file.')
        return

    rows_to_upload = []

    for row in read_csv(args.csvfile):
        if not row_should_be_omitted(args, row):
            rows_to_upload.append(row)

    if (args.dryrun):
        print('Dry run: stopping, would otherwise copy', len(rows_to_upload), 'items.')
    else:
        connection = make_ftp_connection(args.ftpaddress, args.login, args.pwd, args.ftppath)
        upload_rows(args.rootdir, args.ftppath, rows_to_upload, connection)
        quit_ftp_connection(connection)
        print('Done uploading.')

if __name__ == "__main__":
    main(parser.parse_args())
