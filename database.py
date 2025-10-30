"""Simple JSON-backed storage for Bewerbungen (applications).

Provides basic CRUD operations used by the GUI.
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

DATA_PATH = Path(__file__).parent / "data" / "bewerbungen.json"


def _ensure_data_file():
	DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
	if not DATA_PATH.exists():
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

