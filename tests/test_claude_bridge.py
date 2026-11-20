import importlib.util
from pathlib import Path
import hashlib
import tempfile
import unittest
from argparse import Namespace


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "claude_bridge.py"
spec = importlib.util.spec_from_file_location("claude_bridge", SCRIPT)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class SignoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.canonical = base / "canonical_solution.md"
        self.response = base / "claude_signoff.txt"
        self.canonical.write_text("# Candidate\nUnverified example.\n", encoding="utf-8")
        self.digest = hashlib.sha256(self.canonical.read_bytes()).hexdigest()

    def verify(self):
        return bridge.run_verify(Namespace(
            response_file=str(self.response),
            canonical_file=str(self.canonical),
        ))

    def write_verdict(self, verdict, sha=None):
        self.response.write_text(
            f"VERDICT: {verdict}\nREVIEWED_SHA256: {sha or self.digest}\nReason\n",
            encoding="utf-8",
        )

    def test_sha256(self):
        self.assertEqual(bridge.sha256_of(self.canonical), self.digest)

    def test_accept_exact_document(self):
        self.write_verdict("AGREE")
        self.assertEqual(self.verify(), 0)

    def test_reject_requires_no_consensus(self):
        self.write_verdict("REJECT")
        self.assertEqual(self.verify(), 3)

    def test_wrong_sha_requires_no_consensus(self):
        self.write_verdict("AGREE", "0" * 64)
        self.assertEqual(self.verify(), 3)

    def test_changed_document_invalidates_approval(self):
        self.write_verdict("AGREE")
        self.canonical.write_text("Changed after approval", encoding="utf-8")
        self.assertEqual(self.verify(), 3)

    def test_missing_header_requires_no_consensus(self):
        self.response.write_text("I agree!\n", encoding="utf-8")
        self.assertEqual(self.verify(), 3)


if __name__ == "__main__":
    unittest.main()
