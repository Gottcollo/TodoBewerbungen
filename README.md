# TodoBewerbungen

Ein kleines Tkinter-Programm zum Verwalten von Bewerbungen.

Funktionen:
- Neue Bewerbung anlegen (Firma, Position, Ansprechpartner, Datum, Status, Notizen)
- Anzeigen, Bearbeiten, Löschen
- Suche nach Firma/Position
- Filtern nach Status
- Sortieren nach Firma oder Datum
- Export als CSV
- Einfache Erinnerungs-Funktion (Follow-up Datum)

Starten:

1. Python 3.8+ verwenden
2. Installation der Abhängigkeiten:
   ```powershell
   pip install customtkinter
   ```
3. Im Projektverzeichnis ausführen:

```powershell
python .\main.py
```

Datei `data/bewerbungen.json` enthält die gespeicherten Einträge.

Weiteres:
- Wenn Sie eine Kalenderauswahl möchten, können Sie `tkcalendar` installieren und zusätzliche UI-Verbesserungen vornehmen.
# TodoBewerbungen