import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("monitor", ROOT / "monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        monitor.HOME = Path(self.tmp.name)
        monitor.DB = monitor.HOME / "events.sqlite3"
    def tearDown(self):
        self.tmp.cleanup()
    def test_ingest_and_read(self):
        event = {"hook_event_name":"SubagentStart","session_id":"s1","agent_id":"a1","prompt":"SECRET"}
        self.assertTrue(monitor.ingest(json.dumps(event)))
        result = monitor.latest()
        self.assertEqual(result[0]["agent_id"], "a1")
        self.assertNotIn("SECRET", json.dumps(result))
    def test_ignore_unknown_event(self):
        self.assertFalse(monitor.ingest('{"hook_event_name":"Unknown"}'))
        self.assertEqual(monitor.latest(), [])
    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            monitor.ingest("not json")
    def test_escape_newlines(self):
        self.assertEqual(monitor.clean("a\nb"), "a b")
    def test_limit(self):
        self.assertEqual(monitor.latest(10000), [])
if __name__ == "__main__":
    unittest.main()
