import unittest, subprocess, tempfile, os, csv
import csv_data_from_files as csv_script

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# takes a csv file path and returns a list of dicts of the csv data
def readCSV(file_path):
    with open(file_path) as f:
        return list(csv.DictReader(f))

class py1Test(unittest.TestCase):

    maxDiff = None

    def test_runscript(self):
        _, path_temp = tempfile.mkstemp()
        subprocess.run(["python3", "csv_data_from_files.py", "mutopia", "tests/data/test-mutopia-trad-repo", "-o", path_temp])

        expected = readCSV(os.path.join(DATA_DIR, "expected-csv-for-test-mutopia-trad-repo", "py1-output.csv"))
        result = readCSV(path_temp)

        for d in expected:
            d['mtime'] = None
        for d in result:
            d['mtime'] = None

        self.assertEqual(expected, result)

    def test_version_check(self):
        comparison_function = csv_script.version_check('2.18.2')
        cases = [
            ('2.19.2', True),
            ('2.6.2', False),
            ('2.18.2', True)
        ]
        for case_in,case_out in cases:
            result = comparison_function({ 'version': case_in })
            self.assertEqual(result, case_out)
