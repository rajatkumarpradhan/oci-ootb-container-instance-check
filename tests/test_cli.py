import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from ci_checker.cli import main

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


class TestCli(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_messy_sample_exits_2_and_covers_rules(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "instances_messy.json")])
        self.assertEqual(code, 2)
        for rule in ("CINS001", "CINS002", "CINS003", "CINS004"):
            self.assertIn(rule, out)

    def test_clean_sample_exits_0(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "instances_clean.json")])
        self.assertEqual(code, 0)
        self.assertIn("RESULT: clean", out)

    def test_bad_policy_rejected(self):
        doc = '{"instances": [{"name": "i", "restart_policy": "SOMETIMES"}]}'
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(doc)
            path = fh.name
        try:
            code, _, err = self.run_cli([path])
            self.assertEqual(code, 2)
            self.assertIn("unknown policy", err)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
