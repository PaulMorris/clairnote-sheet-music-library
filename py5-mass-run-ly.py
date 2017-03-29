#!/usr/bin/env python3
from subprocess import run, PIPE, STDOUT
import csv, os, re, argparse, subprocess
from py_ly_parsing import regexes, create_directories, remove_file

parser = argparse.ArgumentParser()

parser.add_argument("mode", help = "The mode for modifying ly files, e.g. 'mutopia' or 'thesession'")
parser.add_argument("oldcsv", help = "Path to the old CSV file (input)")
parser.add_argument("newcsv", help = "Path to the new CSV file (output)")
parser.add_argument("logfile", help = "The file which will contain log LilyPond console output")
parser.add_argument("errorfile", help = "The file where errors will be recorded")
# TODO: need code to handle outdir
# parser.add_argument("outdir", help = "The output directory to copy the files to")
parser.add_argument("rootdir", help = "The root directory that contains the ly files")

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
parser.add_argument("--midionly", help="only midi output, no visual output", action="store_true")

parser.add_argument("--dryrun", help="don't actually run LilyPond, just indicate how many files LilyPond would have been run on", action="store_true")

parser.add_argument("--ly-stable", help="Stable LilyPond executable", default='lilypond-stable')
parser.add_argument("--ly-dev", help="Development LilyPond executable", default='lilypond')
parser.add_argument("--stable-version", help="Should be only the first four characters (e.g. '2.18')", default='2.18')


## error detection notes
# 3 files out of 480 files have this:
# programming error: number of pages is out of bounds
# continuing, cross fingers
# Fitting music on 3 pages...
# programming error: number of pages is out of bounds
# continuing, cross fingers

def error_check(console_out, ID, path, errorfile):
    problem_file_ids = set()
    with open(errorfile, "a") as err:
        for line in console_out:

            if regexes['midi1'].search(line) or regexes['midi2'].search(line) or regexes['midi3'].search(line) or regexes['midi4'].search(line):
                # print('midi issue:', ID)
                continue
            elif regexes['compression1'].search(line):
                err.write('compression warning: ' + ID + ' ' + path + '\n')
                continue
            elif regexes['compression2'].search(line):
                continue
            elif regexes['warn'].search(line):
                problem_file_ids.add(ID)
                err.write('warning: ' + ID + ' ' + path + '\n' + line + '\n')
            elif regexes['err'].search(line):
                problem_file_ids.add(ID)
                err.write('error: ' + ID + ' ' + path + '\n' + line + '\n')
            elif regexes['clairnote'].search(line):
                problem_file_ids.add(ID)
                err.write('clairnote-code problem: ' + ID + ' ' + path + '\n')
                if regexes['ambitus'].search(line):
                    err.write('Ambitus engraver: ' + ID + ' ' + path + '\n')
    return problem_file_ids

def get_command(size, midi, file_path_no_extension, file_path_ly, executable):
    start = [
        executable,
        '-dno-point-and-click',
        '-dpaper-size=\"' + size + '\"',
        '-o',
        file_path_no_extension,
    ]
    midi_yes = ['-dmidi-extension=\"mid\"']
    midi_no = ['-e', '(set! write-performances-midis (lambda (performances basename . rest) 0))']
    midi_part =  midi_yes if midi else midi_no
    return start + midi_part + [file_path_ly]

def get_command_midi_only(file_path_no_extension, file_path_ly, executable):
    return [
        executable,
        '-dno-print-pages',
        '-dmidi-extension=\"mid\"',
        '-o',
        file_path_no_extension,
        file_path_ly
    ]

def run_command(command):
    ''' Use subprocess to run a command and return the console output.
        LilyPond's console output is via stderr not stdout. '''
    proc = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    console_out = proc.stderr.split('\n')
    return console_out

def log_lines(lines, logfile):
    ''' Write lines (a list of strings, e.g. console output) to logfile and
        print to console. '''
    with open(logfile, 'a') as log:
        for line in lines:
            log.write(line)
            log.write('\n')
            print(line)

def rename_pdf(file_path_no_extension, suffix, logfile):
    ''' Rename pdf files with -a4 and -let suffix. '''
    try:
        os.rename(file_path_no_extension + '.pdf', file_path_no_extension + suffix + '.pdf')
        print('renamed to: ' + file_path_no_extension + suffix + '.pdf\n')
    except OSError as e:
        print(e)
        stringout = 'manual -let or -a4 suffix needs to be added'
        with open(logfile, "a") as log:
            log.write(stringout)
        print(stringout)


def row_should_be_omitted(args, row):
    # all of these expressions are reasons to omit the row
    return (
        (args.new and row['new?'] != 'T') or
        (args.old and row['new?'] == 'T') or

        (args.error and row['error-status?'] != 'error') or
        (args.noerror and row['error-status?'] != '') or
        (args.minorerror and row['error-status?'] != 'minor') or

        (args.flagged and row['flagged?'] != 'T') or

        (args.omitted and row['omit?'] != 'T') or
        (args.notomitted and row['omit?'] == 'T')
    )

def triage_rows(args):
    rows = []
    with open(args.oldcsv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row_should_be_omitted(args, row):
                rows.append(row)
    return rows

def get_row_log_header(row, lyfile):
    return [
        '----------------------------',
        '____________________________',
        row['id'],
        row['parse-order'],
        row['cn-title'],
        os.path.join(row['path'], lyfile)
    ]

def run_lilypond_and_log(command, logfile, row, lyfile, errorfile):
    console_out = run_command(command)
    log_lines(console_out, logfile)
    problem_ids = error_check(console_out, row['id'], os.path.join(row['path'], lyfile), errorfile)
    return problem_ids

def handle_rows(rows, args):
    ''' args includes: rootdir, logfile, midi, midionly, noletter, noa4,
                       errorfile, ly_stable, ly_dev, stable_version '''
    problem_file_ids = set()
    for row in rows:
        lyfilenames = row['filename'].split(',,, ')
        version = row['ly-version']
        executable = args.ly_stable if version[:4] == args.stable_version else args.ly_dev

        for lyfile in lyfilenames:
            file_no_extension = lyfile.split('.')[0]
            file_path_ly = os.path.join(args.rootdir, row['path'], lyfile)
            file_path_no_extension = os.path.join(args.rootdir, row['path'], file_no_extension)

            # log 'header' details for this piece in console and args.logfile
            log_lines(get_row_log_header(row, lyfile), args.logfile)

            # MIDI ONLY
            if args.midionly:
                command = get_command_midi_only(file_path_no_extension, file_path_ly, executable)
                midi_problems = run_lilypond_and_log(command, args.logfile, row, lyfile, args.errorfile)
                problem_file_ids.update(midi_problems)

            else:
                midi_letter = args.midi
                midi_a4 = True if args.midi and args.noletter else False

                # LETTER PDF
                if not args.noletter:
                    command = get_command("letter", midi_letter, file_path_no_extension, file_path_ly, executable)
                    letter_problems = run_lilypond_and_log(command, args.logfile, row, lyfile, args.errorfile)
                    problem_file_ids.update(letter_problems)
                    rename_pdf(file_path_no_extension, "-let", args.logfile)

                # A4 PDF
                if not args.noa4:
                    command = get_command("a4", midi_a4, file_path_no_extension, file_path_ly, executable)
                    a4_problems = run_lilypond_and_log(command, args.logfile, row, lyfile, args.errorfile)
                    problem_file_ids.update(a4_problems)
                    rename_pdf(file_path_no_extension, "-a4", args.logfile)

    return problem_file_ids

def write_error_file(errorfile, problem_file_ids):
    with open(errorfile, "a") as err:
        err.write('Error Log\n\n')
        err.write('\nList of error files:\n')
        err.write(repr(sorted(problem_file_ids)))
        err.write('\nLength of list: ' + str(len(problem_file_ids)))

def update_csv(problem_file_ids, oldcsv, newcsv, logfile):
    ''' Indicate error files in csv. '''
    log_lines(['Omitting problem files in CSV file...', 'IDs of problem files:'], logfile)

    create_directories(newcsv)

    with open(oldcsv, newline='') as oldf, open(newcsv, 'w') as newf:
        reader = csv.DictReader(oldf)
        writer = csv.DictWriter(newf, fieldnames = reader.fieldnames)
        writer.writeheader()
        for row in reader:
            ID = row['id']
            # for rows with empty string '' as ids, better to fix upstream
            if len(ID) > 0:
                if ID in problem_file_ids:
                    log_lines([ID], logfile)
                    row['error-status?'] = 'error'
                    # problem_file_ids.discard(ID)
                    # DON'T OMIT AUTOMATICALLY
                    # row['omit?'] = 'T'
                    # row['omit-reason'] = 'ly error or warn'
            writer.writerow(row)
        print('Done with CSV file.')

def main(args):
    rows = triage_rows(args)
    if args.dryrun:
        print('Dry run: stopping, would otherwise run LilyPond on', len(rows), 'items.')
    else:
        remove_file(args.errorfile)
        remove_file(args.logfile)
        problem_file_ids = handle_rows(rows, args)
        write_error_file(args.errorfile, problem_file_ids)
        update_csv(problem_file_ids, args.oldcsv, args.newcsv, args.logfile)

if __name__ == "__main__":
    main(parser.parse_args())
