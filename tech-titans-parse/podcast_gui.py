#!/usr/bin/env python3
"""
podcast_gui.py

A Tkinter GUI for browsing the Tech Titans Podcast Master Sheet data --
one tab per sheet, a search box, a "view by" grouping option, a table,
and a detail pane for the selected record. Read-only: this is a viewer,
it never writes back to the source.

Can open either:
  - the .xlsx directly (reuses podcast_sheet_parser.py's parsing logic,
    so needs that file -- and openpyxl -- available alongside this one), or
  - a .json file that podcast_sheet_parser.py already produced (zero extra
    dependencies -- this is the fast path if you've already run the parser).

Usage:
    python3 podcast_gui.py                      # shows a welcome screen
    python3 podcast_gui.py Master_Sheet.xlsx     # loads directly
    python3 podcast_gui.py Master_Sheet.json     # loads directly
    python3 podcast_gui.py -v Master_Sheet.json  # debug logging

Dependency: stdlib only (tkinter, json, webbrowser, threading, queue).
See above re: .xlsx.

Design notes for less-technical users:
  - The app opens to a plain "Open a File" screen rather than an
    unexplained file picker or an empty window.
  - Loading runs on a background thread with a "Loading..." dialog (with
    a progress spinner and live status text pulled straight from the
    parser's own logging) so the window never looks frozen.
  - Every sheet has a "View by" dropdown that groups records under
    whichever column you pick -- e.g. Project List by Student In Charge
    (who's running which projects) or by Project Title (episodes grouped
    under their series) -- built generically from that sheet's own
    columns, not hardcoded to one sheet.
  - A legend at the bottom explains the checkmark / incomplete / invalid
    icons so they aren't just unexplained symbols.
"""

from __future__ import annotations

import argparse
import json
import logging
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Any

LOG = logging.getLogger("podcast_gui")

# Cell text longer than this gets truncated ("...") in the table; the full
# value always still shows in the detail pane below.
CELL_TRUNCATE_LENGTH = 60

STATUS_OK = "\u2713"
STATUS_INCOMPLETE = "\u25fb Incomplete"
STATUS_INVALID = "\u26a0 Invalid"
NO_GROUPING_LABEL = "All records (no grouping)"


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
# Normalizes to one shape regardless of source:
#   {sheet_key: {"sheet_name": str, "records": [dict, ...]}}
# which is exactly the shape of podcast_sheet_parser's build_json_payload()
# "data" field -- so a previously-exported JSON loads as-is, and an xlsx
# gets run through the same parser and reshaped to match.

def load_data(path: Path) -> dict[str, dict[str, Any]]:
    if path.suffix.lower() == ".json":
        LOG.info("Reading %s...", path.name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        LOG.info("Finished reading %s", path.name)
        return payload["data"]

    if path.suffix.lower() in (".xlsx", ".xlsm"):
        LOG.info("Opening workbook %s...", path.name)
        try:
            import podcast_sheet_parser as parser
        except ImportError as exc:
            raise RuntimeError(
                "Opening an .xlsx directly needs podcast_sheet_parser.py "
                "(and openpyxl) available alongside podcast_gui.py. Either "
                "put them next to each other, or open a .json file that "
                "podcast_sheet_parser.py already produced instead."
            ) from exc

        raw_data = parser.parse_workbook(path)
        sheet_key_map = parser.compute_sheet_keys(list(raw_data.keys()))
        parser.postprocess_records(raw_data, sheet_key_map)
        LOG.info("Finished parsing %s", path.name)
        return {
            sheet_key_map[name]: {"sheet_name": name, "records": records}
            for name, records in raw_data.items()
        }

    raise ValueError(f"Unsupported file type '{path.suffix}' (expected .xlsx or .json)")


# --------------------------------------------------------------------------
# Record helpers -- pure logic, no Tk, easy to test on their own
# --------------------------------------------------------------------------

def visible_fields(record: dict[str, Any]) -> list[str]:
    """Field keys to show as table/detail rows: skip metadata (_complete,
    _validation_warnings) and hyperlink companions (*_link) -- links are
    rendered separately, right under their parent field."""
    return [k for k in record.keys() if not k.startswith("_") and not k.endswith("_link")]


def record_status(record: dict[str, Any]) -> str:
    if record.get("_validation_warnings"):
        return STATUS_INVALID
    if not record.get("_complete", True):
        return STATUS_INCOMPLETE
    return STATUS_OK


def truncate(value: Any, length: int = CELL_TRUNCATE_LENGTH) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= length else text[: length - 1] + "\u2026"


def record_matches(record: dict[str, Any], query: str) -> bool:
    """Case-insensitive substring search across every non-metadata field,
    so this works the same regardless of which sheet/columns are in play."""
    if not query:
        return True
    query = query.strip().lower()
    if not query:
        return True
    return any(
        query in str(v).lower()
        for k, v in record.items()
        if not k.startswith("_") and v is not None
    )


def group_records(records: list[dict[str, Any]], group_key: str) -> dict[str, list[dict[str, Any]]]:
    """Buckets records by the (case-preserving) value of group_key. Missing
    values land in a single '(Blank)' bucket rather than being dropped."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        value = record.get(group_key)
        label = "(Blank)" if value is None or str(value).strip() == "" else str(value)
        groups.setdefault(label, []).append(record)
    return groups


# --------------------------------------------------------------------------
# Loading dialog + background loading
# --------------------------------------------------------------------------

class _QueueLogHandler(logging.Handler):
    """Forwards log records into a queue so a background thread can report
    live progress text to the main (Tk) thread without touching Tk itself."""

    def __init__(self, target_queue: "queue.Queue[tuple[str, Any]]"):
        super().__init__()
        self.target_queue = target_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.target_queue.put(("log", self.format(record)))
        except Exception:
            pass  # a logging hiccup should never crash the load


class LoadingDialog(tk.Toplevel):
    """A small modal 'please wait' window with a spinner and live status
    text. Closing via the window's X button is disabled on purpose --
    there's nothing useful to cancel into mid-load."""

    def __init__(self, parent: tk.Tk, filename: str):
        super().__init__(parent)
        self.title("Loading...")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        pad = ttk.Frame(self, padding=20)
        pad.pack(fill="both", expand=True)
        ttk.Label(pad, text=f"Opening {filename}", font=("TkDefaultFont", 11, "bold")).pack(pady=(0, 8))
        self.status_var = tk.StringVar(value="Starting...")
        ttk.Label(pad, textvariable=self.status_var, wraplength=340).pack(pady=(0, 10))
        self.progress = ttk.Progressbar(pad, mode="indeterminate", length=320)
        self.progress.pack()
        self.progress.start(12)

        self.update_idletasks()
        self._center_over(parent)
        self.grab_set()

    def _center_over(self, parent: tk.Tk) -> None:
        parent.update_idletasks()
        width, height = 380, 140
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def close(self) -> None:
        self.progress.stop()
        self.grab_release()
        self.destroy()


# --------------------------------------------------------------------------
# GUI: one sheet's tab
# --------------------------------------------------------------------------

class SheetTab(ttk.Frame):
    """One notebook tab: a search box, a "view by" grouping dropdown, a
    table of records, and a detail pane for the selected record."""

    def __init__(self, parent: ttk.Notebook, sheet_name: str, records: list[dict[str, Any]]):
        super().__init__(parent)
        self.sheet_name = sheet_name
        self.records = records
        self.columns = self._compute_columns()
        self._row_records: dict[str, dict[str, Any]] = {}
        self._group_label_to_key: dict[str, str] = {}
        self._next_iid = 0

        self._build_widgets()
        self._populate(self.records)

    def _compute_columns(self) -> list[str]:
        columns: list[str] = ["Status"]
        seen = set(columns)
        for record in self.records:
            for field in visible_fields(record):
                if field not in seen:
                    columns.append(field)
                    seen.add(field)
        return columns

    def _build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=(8, 0))

        ttk.Label(toolbar, text="\U0001F50D Search:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._on_change())
        ttk.Entry(toolbar, textvariable=self.filter_var, width=26).pack(side="left", padx=(6, 4))
        ttk.Label(toolbar, text="(matches any column)", foreground="#6b7280").pack(side="left", padx=(0, 16))

        ttk.Label(toolbar, text="View by:").pack(side="left")
        group_options = [NO_GROUPING_LABEL]
        for col in self.columns[1:]:
            nice = col.replace("_", " ").title()
            group_options.append(nice)
            self._group_label_to_key[nice] = col
        self.group_by_var = tk.StringVar(value=NO_GROUPING_LABEL)
        group_combo = ttk.Combobox(
            toolbar, textvariable=self.group_by_var, values=group_options, state="readonly", width=24
        )
        group_combo.pack(side="left", padx=(6, 0))
        group_combo.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        self.count_label = ttk.Label(toolbar, text="")
        self.count_label.pack(side="right")

        paned = ttk.PanedWindow(self, orient="vertical")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        table_frame = ttk.Frame(paned)
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=90 if col == "Status" else 160, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        self.tree.tag_configure("invalid", background="#fddede")
        self.tree.tag_configure("incomplete", background="#fff3cd")
        self.tree.tag_configure("group", background="#e5e7eb", font=("TkDefaultFont", 10, "bold"))

        detail_frame = ttk.Frame(paned)
        self.detail = tk.Text(detail_frame, wrap="word", height=10, state="disabled", cursor="arrow")
        detail_vsb = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail.yview)
        self.detail.configure(yscrollcommand=detail_vsb.set)
        self.detail.pack(side="left", fill="both", expand=True)
        detail_vsb.pack(side="right", fill="y")
        self.detail.tag_configure("field_name", font=("TkDefaultFont", 10, "bold"))
        self.detail.tag_configure("link", foreground="#1a56db", underline=True)
        self.detail.tag_configure("warning", foreground="#b91c1c")
        self.detail.tag_configure("incomplete_note", foreground="#92400e")
        self.detail.tag_configure("muted", foreground="#6b7280")

        paned.add(table_frame, weight=3)
        paned.add(detail_frame, weight=2)

        legend = ttk.Label(
            self,
            text=f"Legend:   {STATUS_OK} Complete      {STATUS_INCOMPLETE} \u2014 missing some information"
                 f"      {STATUS_INVALID} \u2014 an unexpected value (see details below)",
            foreground="#4b5563",
        )
        legend.pack(fill="x", padx=8, pady=(0, 8))

    # -- populating the table -------------------------------------------------

    def _current_group_key(self) -> str | None:
        return self._group_label_to_key.get(self.group_by_var.get())

    def _on_change(self) -> None:
        query = self.filter_var.get()
        self._populate([r for r in self.records if record_matches(r, query)])

    def _row_tags(self, record: dict[str, Any]) -> tuple[str, ...]:
        if record.get("_validation_warnings"):
            return ("invalid",)
        if not record.get("_complete", True):
            return ("incomplete",)
        return ()

    def _row_values(self, record: dict[str, Any]) -> list[str]:
        return [record_status(record)] + [truncate(record.get(c)) for c in self.columns[1:]]

    def _populate(self, records: list[dict[str, Any]]) -> None:
        self.tree.delete(*self.tree.get_children())
        self._row_records = {}
        self._next_iid = 0

        group_key = self._current_group_key()
        if group_key is None:
            self.tree.configure(show="headings")
            self._insert_flat(records)
        else:
            self.tree.configure(show="tree headings")
            self.tree.heading("#0", text="Group")
            self.tree.column("#0", width=220, minwidth=140, stretch=False)
            self._insert_grouped(records, group_key)

        self.count_label.configure(text=f"Showing {len(records)} of {len(self.records)} record(s)")
        self._clear_detail()

    def _insert_flat(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            iid = str(self._next_iid)
            self._next_iid += 1
            self.tree.insert("", "end", iid=iid, values=self._row_values(record), tags=self._row_tags(record))
            self._row_records[iid] = record

    def _insert_grouped(self, records: list[dict[str, Any]], group_key: str) -> None:
        groups = group_records(records, group_key)
        for group_label in sorted(groups.keys(), key=str.lower):
            group_items = groups[group_label]
            parent_iid = f"group-{self._next_iid}"
            self._next_iid += 1
            self.tree.insert(
                "", "end", iid=parent_iid,
                text=f"{group_label}  ({len(group_items)})",
                values=[""] * len(self.columns), open=True, tags=("group",),
            )
            for record in group_items:
                iid = str(self._next_iid)
                self._next_iid += 1
                self.tree.insert(
                    parent_iid, "end", iid=iid,
                    values=self._row_values(record), tags=self._row_tags(record),
                )
                self._row_records[iid] = record

    # -- detail pane ------------------------------------------------------

    def _on_select(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self._clear_detail()
            return
        record = self._row_records.get(selection[0])
        if record is not None:
            self._show_detail(record)
        else:
            self._show_group_summary(self.tree.item(selection[0], "text"))

    def _clear_detail(self) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", "Select a row above to see its full details.", "muted")
        self.detail.configure(state="disabled")

    def _show_group_summary(self, group_text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", f"{group_text}\n\n", "field_name")
        self.detail.insert(
            "end", "This is a group heading. Click the arrow to expand it, then select a row inside for details.",
            "muted",
        )
        self.detail.configure(state="disabled")

    def _show_detail(self, record: dict[str, Any]) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")

        for key in visible_fields(record):
            value = record.get(key)
            self.detail.insert("end", f"{key.replace('_', ' ').title()}: ", "field_name")
            self.detail.insert("end", "(empty)\n" if value is None else f"{value}\n")

            link = record.get(f"{key}_link")
            if link:
                tag_name = f"link_{key}"
                self.detail.insert("end", "    \u2192 ")
                self.detail.insert("end", f"{link}\n", ("link", tag_name))
                self.detail.tag_bind(tag_name, "<Button-1>", lambda e, url=link: webbrowser.open(url))
                self.detail.tag_bind(tag_name, "<Enter>", lambda e: self.detail.configure(cursor="hand2"))
                self.detail.tag_bind(tag_name, "<Leave>", lambda e: self.detail.configure(cursor="arrow"))

        if not record.get("_complete", True):
            self.detail.insert(
                "end", f"\n{STATUS_INCOMPLETE} This record has one or more empty required fields.\n",
                "incomplete_note",
            )

        warnings = record.get("_validation_warnings") or []
        if warnings:
            self.detail.insert("end", f"\n{STATUS_INVALID} Validation warnings:\n", "warning")
            for w in warnings:
                self.detail.insert("end", f"   - {w}\n", "warning")

        self.detail.configure(state="disabled")


# --------------------------------------------------------------------------
# GUI: welcome screen (shown before anything is loaded)
# --------------------------------------------------------------------------

class WelcomeScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, on_open: Any):
        super().__init__(parent)
        box = ttk.Frame(self)
        box.place(relx=0.5, rely=0.42, anchor="center")

        ttk.Label(box, text="Tech Titans Podcast Sheet Browser", font=("TkDefaultFont", 18, "bold")).pack(
            pady=(0, 10)
        )
        ttk.Label(
            box,
            text="Open the podcast master sheet to browse Members, Projects, and Meeting Dates.",
            wraplength=440, justify="center", foreground="#374151",
        ).pack(pady=(0, 22))
        open_button = ttk.Button(box, text="\U0001F4C2  Open a File...", command=on_open)
        open_button.pack(ipadx=14, ipady=8)
        ttk.Label(
            box,
            text="Works with the .xlsx master sheet, or a .json file exported earlier.",
            foreground="#6b7280",
        ).pack(pady=(16, 0))


# --------------------------------------------------------------------------
# GUI: main window
# --------------------------------------------------------------------------

class PodcastSheetApp(tk.Tk):
    def __init__(self, initial_path: Path | None = None):
        super().__init__()
        self.title("Tech Titans Podcast Sheet Browser")
        self.geometry("1150x680")
        self.minsize(760, 480)
        self._current_path: Path | None = None

        self._apply_style()
        self._build_toolbar()
        self._build_menu()

        self.content = ttk.Frame(self)
        self.content.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(self.content)
        self.welcome = WelcomeScreen(self.content, on_open=self._open_dialog)

        self.status_var = tk.StringVar(value="No file loaded yet.")
        ttk.Label(self, textvariable=self.status_var, anchor="w", foreground="#4b5563").pack(
            fill="x", padx=10, pady=(0, 6)
        )

        self._show_welcome()

        if initial_path:
            self.after(50, lambda: self.load_file(initial_path))

    def _apply_style(self) -> None:
        style = ttk.Style(self)
        style.configure(".", font=("TkDefaultFont", 10))
        style.configure("Treeview", rowheight=24, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(fill="x")
        ttk.Button(bar, text="\U0001F4C2  Open File", command=self._open_dialog).pack(side="left")
        self.reload_button = ttk.Button(bar, text="\U0001F504  Reload", command=self._reload, state="disabled")
        self.reload_button.pack(side="left", padx=(8, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(bar, text="Browse the podcast master sheet below.", foreground="#6b7280").pack(side="left")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open...", command=self._open_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Reload", command=self._reload, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)
        self.bind("<Control-o>", lambda e: self._open_dialog())
        self.bind("<Control-r>", lambda e: self._reload())

    def _show_welcome(self) -> None:
        self.notebook.pack_forget()
        self.welcome.pack(fill="both", expand=True)

    def _show_notebook(self) -> None:
        self.welcome.pack_forget()
        self.notebook.pack(fill="both", expand=True)

    def _open_dialog(self) -> None:
        filename = filedialog.askopenfilename(
            title="Open podcast sheet data",
            filetypes=[("Excel or JSON", "*.xlsx *.xlsm *.json"), ("All files", "*.*")],
        )
        if filename:
            self.load_file(Path(filename))

    def _reload(self) -> None:
        if self._current_path:
            self.load_file(self._current_path)

    # -- threaded loading with progress feedback ---------------------------

    def load_file(self, path: Path) -> None:
        dialog = LoadingDialog(self, path.name)
        result_queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()

        log_handler = _QueueLogHandler(result_queue)
        log_handler.setFormatter(logging.Formatter("%(message)s"))
        watched_loggers = [LOG, logging.getLogger("podcast_sheet_parser")]
        for logger in watched_loggers:
            # Guarantee INFO-level progress messages reach the dialog even if
            # nothing configured logging (default root level is WARNING,
            # which would otherwise silently swallow them). A more verbose
            # level set elsewhere (e.g. -v => DEBUG) is left alone.
            if logger.getEffectiveLevel() > logging.INFO:
                logger.setLevel(logging.INFO)
            logger.addHandler(log_handler)

        def worker() -> None:
            try:
                data = load_data(path)
                result_queue.put(("done", data))
            except Exception as exc:
                LOG.exception("Failed to load %s", path)
                result_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(50, lambda: self._poll_load_queue(result_queue, path, log_handler, watched_loggers, dialog))

    def _poll_load_queue(
        self,
        result_queue: "queue.Queue[tuple[str, Any]]",
        path: Path,
        log_handler: _QueueLogHandler,
        watched_loggers: list[logging.Logger],
        dialog: LoadingDialog,
    ) -> None:
        try:
            while True:
                kind, payload = result_queue.get_nowait()
                if kind == "log":
                    dialog.set_status(payload)
                else:
                    for logger in watched_loggers:
                        logger.removeHandler(log_handler)
                    dialog.close()
                    if kind == "done":
                        self._finish_load(path, payload)
                    else:
                        messagebox.showerror(
                            "Couldn't open that file",
                            f"Something went wrong opening:\n{path.name}\n\n{payload}",
                        )
                    return
        except queue.Empty:
            pass
        self.after(50, lambda: self._poll_load_queue(result_queue, path, log_handler, watched_loggers, dialog))

    def _finish_load(self, path: Path, data: dict[str, dict[str, Any]]) -> None:
        self._current_path = path
        self.reload_button.configure(state="normal")

        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        for sheet in data.values():
            tab = SheetTab(self.notebook, sheet["sheet_name"], sheet["records"])
            self.notebook.add(tab, text=sheet["sheet_name"])
        self._show_notebook()

        total = sum(len(s["records"]) for s in data.values())
        self.status_var.set(f"{path.name}  \u2014  {len(data)} sheet(s), {total} record(s) total")
        LOG.info("Loaded %s: %d sheet(s), %d record(s)", path, len(data), total)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Browse the podcast master sheet data in a GUI.")
    parser.add_argument("file", nargs="?", type=Path, help="An .xlsx or parser-produced .json file to open")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.file and not args.file.exists():
        LOG.error("File not found: %s", args.file)
        return 1

    app = PodcastSheetApp(initial_path=args.file)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
