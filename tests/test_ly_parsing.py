import unittest, tempfile, os
import ly_parsing

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class ly_parsing_test(unittest.TestCase):

    def test_vsn_tuple(self):
        cases = [
            ('2.19.2', (2,19,2)),
            ('2.18.2', (2,18,2)),
            ('2.6.2', (2,6,2))
        ]
        for case_in, case_out in cases:
            self.assertEqual(ly_parsing.vsn_tuple(case_in), case_out)

    def test_get_version_relation(self):
        cases = [
            ('1.0.0', '2.0.0', -1),
            ('0.1.0', '0.2.0', -1),
            ('0.0.1', '0.0.2', -1),

            ('2.0.0', '2.0.0', 0),
            ('0.2.0', '0.2.0', 0),
            ('0.0.2', '0.0.2', 0),

            ('3.0.0', '2.0.0', 1),
            ('0.3.0', '0.2.0', 1),
            ('0.0.3', '0.0.2', 1),

            ('2.18', '2.18.2', -1),
            ('2.18.2', '2.18', 1)
        ]
        for case_a, case_b, case_out in cases:
            self.assertEqual(ly_parsing.get_version_relation(case_a, case_b), case_out)

    def test_vsn_greater_or_equals(self):
        cases = [
            ('1.0.0', '2.0.0', False),
            ('0.1.0', '0.2.0', False),
            ('0.0.1', '0.0.2', False),

            ('2.0.0', '2.0.0', True),
            ('0.2.0', '0.2.0', True),
            ('0.0.2', '0.0.2', True),

            ('3.0.0', '2.0.0', True),
            ('0.3.0', '0.2.0', True),
            ('0.0.3', '0.0.2', True)
        ]
        for case_a, case_b, case_out in cases:
            self.assertEqual(ly_parsing.vsn_compare(case_a, ly_parsing.greater_or_equal, case_b), case_out)
