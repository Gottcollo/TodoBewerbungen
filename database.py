"""Simple JSON-backed storage for Bewerbungen (applications).

Provides basic CRUD operations used by the GUI.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# When running as a bundled exe (PyInstaller --onefile) resources are
# extracted to a temporary folder pointed to by sys._MEIPASS. Use that
# location when present; otherwise fall back to the source tree.
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

# Choose a persistent storage location for user data when running as a
# frozen single-file executable. Writing into the extracted _MEIPASS
# folder is ephemeral; instead store user data in %APPDATA%/EasyBewerbungen
# on Windows so the data persists across runs and is writable.
if getattr(sys, "frozen", False):
	appdata = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
	PERSIST_DIR = Path(appdata) / "EasyBewerbungen"
else:
	# During development keep data next to the source tree for convenience
	PERSIST_DIR = Path(__file__).parent / "data"

DATA_PATH = PERSIST_DIR / "bewerbungen.json"


def _ensure_data_file():
	# Ensure the directory exists. If a packaged default data file exists
	# (bundled via PyInstaller --add-data) copy it into the persistent
	# location on first run so users get starter content.
	PERSIST_DIR.mkdir(parents=True, exist_ok=True)
	if not DATA_PATH.exists():
		# packaged default, if present
		packaged = BASE_DIR / "data" / "bewerbungen.json"
		if packaged.exists():
			try:
				DATA_PATH.write_text(packaged.read_text(encoding="utf-8"), encoding="utf-8")
			except Exception:
				# fallback to empty list
				DATA_PATH.write_text("[]", encoding="utf-8")
		else:
			DATA_PATH.write_text("[]", encoding="utf-8")


def load_data() -> List[Dict[str, Any]]:
	"""Load all entries from the JSON store.

	Returns a list of dicts. Each entry will have an 'id' string.
	"""
	_ensure_data_file()
	try:
		with DATA_PATH.open("r", encoding="utf-8") as f:
			data = json.load(f)
			if not isinstance(data, list):
				return []
			return data
	except Exception:
		return []


def save_data(items: List[Dict[str, Any]]) -> None:
	_ensure_data_file()
	tmp = DATA_PATH.with_suffix(".tmp")
	with tmp.open("w", encoding="utf-8") as f:
		json.dump(items, f, ensure_ascii=False, indent=2)
	tmp.replace(DATA_PATH)


def get_all() -> List[Dict[str, Any]]:
	return load_data()


def add_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
	items = load_data()
	entry = dict(entry)
	entry.setdefault("id", str(uuid4()))
	# ensure date string
	if "datum" in entry and isinstance(entry["datum"], date):
		entry["datum"] = entry["datum"].isoformat()
	items.append(entry)
	save_data(items)
	return entry


def update_entry(entry_id: str, new_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
	items = load_data()
	for i, it in enumerate(items):
		if it.get("id") == entry_id:
			updated = dict(new_entry)
			updated["id"] = entry_id
			if "datum" in updated and isinstance(updated["datum"], date):
				updated["datum"] = updated["datum"].isoformat()
			items[i] = updated
			save_data(items)
			return updated
	return None


def delete_entry(entry_id: str) -> bool:
	items = load_data()
	new_items = [it for it in items if it.get("id") != entry_id]
	if len(new_items) == len(items):
		return False
	save_data(new_items)
	return True


def find_by_query(query: str) -> List[Dict[str, Any]]:
	q = query.lower().strip()
	if not q:
		return load_data()
	out = []
	for it in load_data():
		if q in (it.get("firma", "") or "").lower() or q in (it.get("position", "") or "").lower():
			out.append(it)
	return out


def filter_by_status(status: str) -> List[Dict[str, Any]]:
	if not status:
		return load_data()
	return [it for it in load_data() if (it.get("status") or "") == status]

