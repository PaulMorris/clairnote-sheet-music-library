from subprocess import run, PIPE, STDOUT

def run_command(command):
    ''' Use subprocess to run a command and return the console output.
        LilyPond's console output is via stderr not stdout. '''
    proc = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    console_out = proc.stderr.split('\n')
    return proc.returncode, console_out

def log_lines(lines, logfile):
    ''' Write lines (a list of strings, e.g. console output) to logfile and
        print to console. '''
    with open(logfile, 'a') as log:
        for line in lines:
            log.write(line)
            log.write('\n')

def print_lines(lines):
    for line in lines:
        print(line)
