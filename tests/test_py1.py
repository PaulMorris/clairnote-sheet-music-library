import unittest, subprocess, tempfile, os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class py1Test(unittest.TestCase):

    maxDiff = None

    def test_runscript(self):
        _, path_temp = tempfile.mkstemp()
        subprocess.run(["python3", "py1-csv-from-repo.py", "tests/data/test-repo", "-o", path_temp])

        with open(os.path.join(DATA_DIR, "expected-csv-for-test-repo", "py1-output.csv")) as f:
            expected = f.read()

        with open(path_temp) as f:
            result = f.read()

        self.assertEqual(expected, result)
