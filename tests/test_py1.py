import unittest, subprocess, tempfile, os, csv

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# takes a csv file path and returns a list of dicts of the csv data
def readCSV(file_path):
    with open(file_path) as f:
        return list(csv.DictReader(f))

class py1Test(unittest.TestCase):

    maxDiff = None

    def test_runscript(self):
        _, path_temp = tempfile.mkstemp()
        subprocess.run(["python3", "py1-csv-from-repo.py", "tests/data/test-repo", "-o", path_temp])

        expected = readCSV(os.path.join(DATA_DIR, "expected-csv-for-test-repo", "py1-output.csv"))
        result = readCSV(path_temp)

        for d in expected:
            d['mtime'] = None
        for d in result:
            d['mtime'] = None

        self.assertEqual(expected, result)
