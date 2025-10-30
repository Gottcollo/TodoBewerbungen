import tempfile
import unittest
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):
    def test_add_update_delete(self):
        orig = database.DATA_PATH
        tmpdir = tempfile.TemporaryDirectory()
        try:
            p = Path(tmpdir.name) / "bewerbungen.json"
            database.DATA_PATH = p
            # start empty
            self.assertEqual(database.load_data(), [])
            e = database.add_entry({"firma": "X", "position": "Dev", "datum": "2025-01-01", "status": "Gesendet"})
            all_ = database.get_all()
            self.assertTrue(any(it.get("firma") == "X" for it in all_))
            eid = e.get("id")
            database.update_entry(eid, {"firma": "Y", "position": "Dev", "datum": "2025-01-02", "status": "Gesendet"})
            all_ = database.get_all()
            self.assertTrue(any(it.get("firma") == "Y" for it in all_))
            database.delete_entry(eid)
            self.assertEqual(database.get_all(), [])
        finally:
            database.DATA_PATH = orig


if __name__ == "__main__":
    unittest.main()
