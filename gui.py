"""Tkinter GUI for Bewerbungen management.

Provides list view, add/edit/delete, search, filter, sort and CSV export.
Modern UI using customtkinter.
"""
from __future__ import annotations

import csv
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional

import customtkinter as ctk
import database

# Set appearance mode and default color theme
ctk.set_appearance_mode("light")  # Modes: "light" (default), "dark", "system"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

STATUS_OPTIONS = ["Gesendet", "Absage", "Einladung", "In Bearbeitung", "Andere"]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bewerbungen")
        self.geometry("1000x650")
        
        # Configure grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        self.status_filter = tk.StringVar()
        self.sort_by = tk.StringVar(value="firma")

        self._build_ui()
        self.load_items()
        self.check_reminders_on_start()

    def _build_ui(self):
        # Top controls frame with search, filter, sort
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        top.grid_columnconfigure(8, weight=1)  # Make last column expand

        # Search
        ctk.CTkLabel(top, text="Suche:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = ctk.CTkEntry(top, textvariable=self.search_var, width=140)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.bind("<Return>", lambda e: self.load_items())

        # Status filter
        ctk.CTkLabel(top, text="Status:").grid(row=0, column=2, padx=5, pady=5)
        status_combo = ctk.CTkOptionMenu(top, variable=self.status_filter, 
                                       values=[""] + STATUS_OPTIONS,
                                       command=lambda _: self.load_items())
        status_combo.grid(row=0, column=3, padx=5, pady=5)

        # Sort
        ctk.CTkLabel(top, text="Sortiere nach:").grid(row=0, column=4, padx=5, pady=5)
        sort_combo = ctk.CTkOptionMenu(top, variable=self.sort_by,
                                     values=["firma", "datum"],
                                     command=lambda _: self.load_items())
        sort_combo.grid(row=0, column=5, padx=5, pady=5)

        # Buttons
        ctk.CTkButton(top, text="Suchen", command=self.load_items).grid(row=0, column=6, padx=5, pady=5)
        ctk.CTkButton(top, text="Export CSV", command=self.export_csv).grid(row=0, column=7, padx=5, pady=5)        # Main area: tree + form in grid
        main = ctk.CTkFrame(self)
        main.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        main.grid_columnconfigure(0, weight=3)  # Tree gets more space
        main.grid_columnconfigure(1, weight=1)  # Form takes less space
        main.grid_rowconfigure(0, weight=1)

        # Tree view
        tree_frame = ctk.CTkFrame(main)
        tree_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("firma", "position", "ansprechpartner", "datum", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, anchor=tk.W, width=140)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Form in its own frame
        form = ctk.CTkFrame(main)
        form.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.form_values = {
            "id": tk.StringVar(),
            "firma": tk.StringVar(),
            "position": tk.StringVar(),
            "ansprechpartner": tk.StringVar(),
            "datum": tk.StringVar(),
            "status": tk.StringVar(),
            "notizen": tk.StringVar(),
        }

        form.grid_columnconfigure(1, weight=1)
        
        # Form fields
        for idx, (label, varname) in enumerate([
            ("Firma", "firma"),
            ("Position", "position"),
            ("Ansprechpartner", "ansprechpartner"),
            ("Datum (YYYY-MM-DD)", "datum"),
            ("Status", "status"),
            ("Notizen", "notizen"),
        ]):
            ctk.CTkLabel(form, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            if varname == "status":
                cb = ctk.CTkOptionMenu(form, variable=self.form_values[varname], 
                                     values=STATUS_OPTIONS, width=200)
                cb.grid(row=idx, column=1, sticky="ew", padx=5, pady=5)
            else:
                entry = ctk.CTkEntry(form, textvariable=self.form_values[varname], width=200)
                entry.grid(row=idx, column=1, sticky="ew", padx=5, pady=5)

        # Buttons at bottom of form
        btn_frame = ctk.CTkFrame(form)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=15, sticky="ew")
        btn_frame.grid_columnconfigure((0,1,2), weight=1)

        ctk.CTkButton(btn_frame, text="Neu anlegen", command=self.on_new).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Speichern", command=self.on_save).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="Löschen", command=self.on_delete).grid(row=0, column=2, padx=5)
        
        remind_btn = ctk.CTkButton(btn_frame, text="Erinnere in 7 Tagen", 
                                 command=self.set_remind_7days,
                                 fg_color="transparent", border_width=1)
        remind_btn.grid(row=1, column=0, columnspan=3, pady=(10,0), sticky="ew")

    def load_items(self):
        # fetch
        q = self.search_var.get().strip()
        status = self.status_filter.get().strip()
        if q:
            items = database.find_by_query(q)
        else:
            items = database.get_all()
        if status:
            items = [it for it in items if (it.get("status") or "") == status]

        # sort
        key = self.sort_by.get()
        if key == "datum":
            def keyfunc(it):
                return it.get("datum") or ""
        else:
            def keyfunc(it):
                return (it.get("firma") or "").lower()
        items = sorted(items, key=keyfunc)

        # populate tree
        for i in self.tree.get_children():
            self.tree.delete(i)
        for it in items:
            vals = (it.get("firma", ""), it.get("position", ""), 
                   it.get("ansprechpartner", ""), it.get("datum", ""), 
                   it.get("status", ""))
            self.tree.insert("", tk.END, iid=it.get("id"), values=vals)

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        entry_id = sel[0]
        items = database.get_all()
        for it in items:
            if it.get("id") == entry_id:
                for k in self.form_values:
                    self.form_values[k].set(it.get(k, ""))
                break

    def on_new(self):
        for k in self.form_values:
            self.form_values[k].set("")

    def on_save(self):
        entry = {k: (v.get() if isinstance(v, tk.Variable) else v) for k, v in self.form_values.items()}
        
        # Validate required fields
        required_fields = ["firma", "position", "datum", "status"]
        for field in required_fields:
            if not entry.get(field):
                messagebox.showerror("Fehler", f"Das Feld '{field}' muss ausgefüllt sein.")
                return
                
        # normalize empty id => add
        if not entry.get("id"):
            added = database.add_entry({
                "firma": entry.get("firma"),
                "position": entry.get("position"),
                "ansprechpartner": entry.get("ansprechpartner", ""),
                "datum": entry.get("datum"),
                "status": entry.get("status"),
                "notizen": entry.get("notizen", ""),
            })
            if added:
                self.form_values["id"].set(added.get("id"))
                messagebox.showinfo("Info", "Eintrag erfolgreich gespeichert")
        else:
            updated = database.update_entry(entry["id"], entry)
            if updated is None:
                messagebox.showerror("Fehler", "Konnte Eintrag nicht aktualisieren")
            else:
                messagebox.showinfo("Info", "Eintrag erfolgreich aktualisiert")
        self.load_items()

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Keine Auswahl")
            return
        entry_id = sel[0]
        if messagebox.askyesno("Löschen", "Eintrag wirklich löschen?"):
            database.delete_entry(entry_id)
            self.on_new()
            self.load_items()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        items = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            items.append({"firma": vals[0], "position": vals[1], "ansprechpartner": vals[2], "datum": vals[3], "status": vals[4]})
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["firma", "position", "ansprechpartner", "datum", "status"])
            writer.writeheader()
            writer.writerows(items)
        messagebox.showinfo("Export", f"Exportiert {len(items)} Einträge\n{path}")

    def set_remind_7days(self):
        # set follow_up_date = today + 7 for selected
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Keine Auswahl")
            return
        eid = sel[0]
        items = database.get_all()
        for it in items:
            if it.get("id") == eid:
                it["follow_up_date"] = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
                database.update_entry(eid, it)
                messagebox.showinfo("Erinnerung", "Erinnerung für 7 Tage gesetzt")
                self.load_items()
                return

    def check_reminders_on_start(self):
        items = database.get_all()
        today = datetime.date.today()
        due = []
        upcoming = []
        
        for it in items:
            fud = it.get("follow_up_date")
            if fud:
                try:
                    d = datetime.date.fromisoformat(fud)
                    if d <= today:
                        due.append(it)
                    else:
                        upcoming.append(it)
                except Exception:
                    continue
        
        # Show all reminders (both due and upcoming)
        all_reminders = []
        if due:
            all_reminders.append("Fällige Erinnerungen:")
            for d in due:
                all_reminders.append(f"⚠️ {d.get('firma','')} - {d.get('position','')} (fällig seit {d.get('follow_up_date')})")
        
        if upcoming:
            if all_reminders:
                all_reminders.append("\n")
            all_reminders.append("Kommende Erinnerungen:")
            for d in upcoming:
                reminder_date = datetime.date.fromisoformat(d.get('follow_up_date'))
                days_left = (reminder_date - today).days
                all_reminders.append(f"📅 {d.get('firma','')} - {d.get('position','')} (in {days_left} Tagen am {d.get('follow_up_date')})")
        
        if all_reminders:
            messagebox.showinfo("Bewerbungen - Erinnerungen", "\n".join(all_reminders))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
