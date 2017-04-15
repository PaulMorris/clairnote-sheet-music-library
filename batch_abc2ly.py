#!/usr/bin/env python3
import subprocess, os, argparse
from console_utils import run_command, log_lines, print_lines
from ly_parsing import create_directories

parser = argparse.ArgumentParser()
parser.add_argument("--filecount", help="Only convert this many files")
parser.add_argument("logfile", help = "Log console output to this file")
parser.add_argument("errorfile", help="Log errors to this file")
parser.add_argument("indir", help="Read files from this directory")
parser.add_argument("outdir", help = "Write the converted files to this directory")

def main(args):
    if not os.path.exists(args.indir):
        print('Oops, bad path given for the directory that should contain the abc files.')
        return

    # create_directories takes a full path to a file, but does nothing with the file name part
    create_directories(os.path.join(args.outdir, 'no-file.txt'))
    create_directories(args.errorfile)
    create_directories(args.logfile)

    error_summary = ['', 'ERROR SUMMARY', '']
    for dirpath, dirnames, filenames in os.walk(args.indir):
        if filenames:
            # get list of all .abc files in directory
            abcs = filter(lambda name: name[-4:] == '.abc', filenames)
            abc_filenames = list(abcs)[:int(args.filecount)] if args.filecount else abcs

            for name in abc_filenames:
                readpath = os.path.join(dirpath, name)
                writepath = os.path.join(args.outdir, name[0:-4] + '.ly')

                returncode, console_out = run_command([
                    'abc2ly',
                    '--output=' + writepath,
                    '--strict',
                    readpath
                ])

                console_out_returncode = console_out[:-1] + [str(returncode)]
                log_lines(console_out_returncode, args.logfile)
                print_lines(console_out_returncode)

                if returncode == 1:
                    error_summary.append(readpath)
                    log_lines(console_out, args.errorfile)

    log_lines(error_summary, args.errorfile)

if __name__ == "__main__":
    main(parser.parse_args())
