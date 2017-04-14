#!/usr/bin/env python3
import subprocess, csv, os, argparse
from ly_parsing import vsn_compare, less_than, greater_than, get_all_lilypond_filenames
from console_utils import run_command, log_lines, print_lines

parser = argparse.ArgumentParser()
# convert-ly any files BETWEEN the low and high versions
parser.add_argument("--lowvsn", help="The lowest version to convert", default='0.0.0')
parser.add_argument("--highvsn", help="The highest version to convert", default='100.0.0')

parser.add_argument("mode", help="The mode for parsing ly files, e.g. 'mutopia' or 'thesession'")
parser.add_argument("logfile", help = "Log console output to this file")
parser.add_argument("errorfile", help="Log errors to this file")
parser.add_argument("csvpath", help = "Path to the CSV file input")
parser.add_argument("indir", help="Read files from this directory")

# TODO: maybe add option to write converted files to a new directory
# parser.add_argument("outdir", help = "Write the converted files to this directory")

def get_ly_paths(indir_path):
    # get list of all .ly and .ily files in directory and subdirectories
    lypaths = []
    for dirpath, subdirnames, filenames in os.walk(indir_path):
        for f in get_all_lilypond_filenames(filenames):
            lypaths.append(os.path.join(dirpath, f))
    return lypaths

def get_command(fromvsn, tovsn, filepath):
    return [
        'convert-ly',
        '-e',
        '--from=' + fromvsn,
        '--to=' + tovsn,
        filepath
    ]

def main(args):
    error_summary = ['', 'ERROR SUMMARY', '']
    muto = args.mode == 'mutopia'
    with open(args.csvpath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            vsn = row['ly-version']

            if (vsn_compare(vsn, greater_than, args.lowvsn) and
                vsn_compare(vsn, less_than, args.highvsn) and
                row['omit?'] != 'T'):

                if muto:
                    lypaths = get_ly_paths(os.path.join(args.indir, row['path']))
                else:
                    lypaths = [os.path.join(args.indir, row['path'], row['filename'])]

                print('____________________________')
                print(row['id'])
                mutocomp = row['mutopiacomposer'] if muto else ''
                print(row['parse-order'], ': ', mutocomp, row['cn-title'])

                for filepath in lypaths:
                    command = get_command(row['ly-version'], args.highvsn, filepath)
                    returncode, console_out = run_command(command)

                    console_out_returncode = console_out + [str(returncode)]
                    log_lines(console_out_returncode, args.logfile)
                    print_lines(console_out_returncode)

                    if returncode == 1:
                        error_summary.append(filepath)
                        log_lines(console_out, args.errorfile)

    log_lines(error_summary, args.errorfile)


if __name__ == "__main__":
    main(parser.parse_args())
