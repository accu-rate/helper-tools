#!/usr/bin/env python3

"""
GUI for scale_scenario.py.
Drag & drop a .crowdit file, set the scale factor, and run.

Requires tkinterdnd2 for drag & drop support:
    pip install tkinterdnd2
Without it, the app falls back to a click-to-browse button.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

# -- drag-and-drop support (optional) ----------------------------------------
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _HAS_DND = True
except ImportError:
    _HAS_DND = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -- import the scaling logic from the sibling module ------------------------
sys.path.insert(0, str(Path(__file__).parent))
from scale_scenario import scale_scenario


# ----------------------------------------------------------------------------
# Colours / fonts
# ----------------------------------------------------------------------------
C_BG        = "#f8f9fa"
C_DROP_BG   = "#e8f0fe"
C_DROP_OK   = "#e6f4ea"
C_DROP_LINE = "#4285f4"
C_OK        = "#137333"
C_ERR       = "#c62828"
C_MUTED     = "#5f6368"
FONT        = ("Segoe UI", 10)
FONT_LARGE  = ("Segoe UI", 11)
FONT_MONO   = ("Consolas", 9)


class ScaleGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("crowd:it Scenario Scaler")
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)

        self._crowdit_path: Path | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        p = {"padx": 14, "pady": 6}

        # ---- Drop zone -------------------------------------------------------
        drop_frame = tk.Frame(
            self.root, bg=C_DROP_BG,
            highlightbackground=C_DROP_LINE, highlightthickness=2,
            width=430, height=110,
        )
        drop_frame.pack(fill="x", padx=14, pady=(14, 4))
        drop_frame.pack_propagate(False)

        self._drop_label = tk.Label(
            drop_frame,
            text=".crowdit Datei hierher ziehen\noder klicken zum Auswählen",
            bg=C_DROP_BG, fg=C_MUTED, font=FONT_LARGE,
            cursor="hand2", justify="center",
        )
        self._drop_label.pack(expand=True, fill="both")

        for widget in (drop_frame, self._drop_label):
            widget.bind("<Button-1>", lambda _e: self._browse())
            if _HAS_DND:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)

        if not _HAS_DND:
            tk.Label(
                self.root,
                text="(Drag & Drop: pip install tkinterdnd2)",
                bg=C_BG, fg=C_MUTED, font=("Segoe UI", 8),
            ).pack()

        # ---- Scale factor ----------------------------------------------------
        scale_outer = tk.LabelFrame(
            self.root, text="Skalierungsfaktor", font=FONT,
            bg=C_BG, padx=10, pady=8,
        )
        scale_outer.pack(fill="x", **p)

        self._scale_var = tk.DoubleVar(value=70.0)

        self._slider = ttk.Scale(
            scale_outer, from_=10, to=200,
            variable=self._scale_var, orient="horizontal", length=320,
            command=self._slider_moved,
        )
        self._slider.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))

        tk.Label(scale_outer, text="10%", bg=C_BG, fg=C_MUTED, font=FONT).grid(row=1, column=0, sticky="w")
        tk.Label(scale_outer, text="200%", bg=C_BG, fg=C_MUTED, font=FONT).grid(row=1, column=2, sticky="e")

        entry_frame = tk.Frame(scale_outer, bg=C_BG)
        entry_frame.grid(row=1, column=1)
        self._entry = ttk.Entry(entry_frame, width=6, font=FONT_LARGE, justify="center")
        self._entry.insert(0, "70")
        self._entry.pack(side="left")
        tk.Label(entry_frame, text=" %", bg=C_BG, font=FONT_LARGE).pack(side="left")
        self._entry.bind("<Return>", self._entry_changed)
        self._entry.bind("<FocusOut>", self._entry_changed)

        scale_outer.columnconfigure(0, weight=1)
        scale_outer.columnconfigure(1, weight=0)
        scale_outer.columnconfigure(2, weight=1)

        # ---- Output mode -----------------------------------------------------
        mode_frame = tk.LabelFrame(
            self.root, text="Ausgabe", font=FONT,
            bg=C_BG, padx=10, pady=8,
        )
        mode_frame.pack(fill="x", **p)

        self._inplace_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            mode_frame,
            text="Neue Datei  (<name>_70pct.crowdit + <name>_70pct_res/)",
            variable=self._inplace_var, value=False,
        ).pack(anchor="w")
        ttk.Radiobutton(
            mode_frame,
            text="Originaldatei ersetzen (in-place)",
            variable=self._inplace_var, value=True,
        ).pack(anchor="w")

        # ---- Run button ------------------------------------------------------
        self._btn = ttk.Button(
            self.root, text="Skalieren", command=self._run, width=22,
        )
        self._btn.pack(pady=(4, 2))

        # ---- Status bar ------------------------------------------------------
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(
            self.root,
            textvariable=self._status_var,
            bg=C_BG, fg=C_OK, font=FONT_MONO,
            wraplength=430, justify="left",
        )
        self._status_lbl.pack(padx=14, pady=(2, 12), anchor="w")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_drop(self, event) -> None:
        # tkinterdnd2 wraps paths with braces when they contain spaces
        raw = event.data.strip()
        # multiple files → take the first one
        path = Path(raw.split("} {")[0].strip("{}"))
        self._set_file(path)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("crowd:it-Szenarien", "*.crowdit"), ("Alle Dateien", "*.*")]
        )
        if path:
            self._set_file(Path(path))

    def _set_file(self, path: Path) -> None:
        if path.suffix.lower() != ".crowdit":
            messagebox.showwarning("Falsches Format", "Bitte eine .crowdit Datei auswählen.")
            return
        res_dir = path.parent / (path.stem + "_res")
        if not res_dir.is_dir():
            messagebox.showwarning(
                "Fehlender _res-Ordner",
                f"Kein zugehöriger _res-Ordner gefunden:\n{res_dir}"
            )
            return
        self._crowdit_path = path
        self._drop_label.configure(
            text=f"[OK]  {path.name}",
            bg=C_DROP_OK, fg=C_OK,
        )
        self._status_var.set("")

    def _slider_moved(self, val: str) -> None:
        v = float(val)
        self._entry.delete(0, "end")
        self._entry.insert(0, f"{v:.1f}")

    def _entry_changed(self, _event=None) -> None:
        try:
            v = float(self._entry.get().replace(",", "."))
            v = max(10.0, min(200.0, v))
        except ValueError:
            v = self._scale_var.get()
        self._scale_var.set(v)
        self._entry.delete(0, "end")
        self._entry.insert(0, f"{v:.1f}")

    def _run(self) -> None:
        if self._crowdit_path is None:
            messagebox.showwarning("Keine Datei", "Bitte zuerst eine .crowdit Datei auswählen.")
            return

        self._entry_changed()          # flush any pending entry edit
        scale_pct = self._scale_var.get()
        inplace   = self._inplace_var.get()

        self._btn.configure(state="disabled")
        self._set_status("Skaliere ...", C_MUTED)

        def _worker() -> None:
            try:
                scale_scenario(self._crowdit_path, scale_pct, inplace=inplace)
                label = "in-place" if inplace else f"{self._crowdit_path.stem}_{int(scale_pct)}pct.*"
                self.root.after(0, self._set_status, f"Fertig  ({scale_pct:.0f}%)  ->  {label}", C_OK)
            except Exception as exc:
                self.root.after(0, messagebox.showerror, "Fehler", str(exc))
                self.root.after(0, self._set_status, f"Fehler: {exc}", C_ERR)
            finally:
                self.root.after(0, self._btn.configure, {"state": "normal"})

        threading.Thread(target=_worker, daemon=True).start()

    def _set_status(self, msg: str, colour: str = C_OK) -> None:
        self._status_var.set(msg)
        self._status_lbl.configure(fg=colour)


# ----------------------------------------------------------------------------

def main() -> None:
    if _HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    ScaleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
