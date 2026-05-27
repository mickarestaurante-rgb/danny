#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Widgets reutilizables para CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
from .styles import (C_PRIMARY, C_WHITE, C_BG, C_BORDER, C_SECONDARY,
                     C_TEXT, C_TEXT_LIGHT, FONT_NORMAL, FONT_HEADER,
                     FONT_SMALL, col_fmt)


class ScrollableFrame(ttk.Frame):
    """Frame con scrollbar vertical"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        canvas = tk.Canvas(self, bg=C_BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)
        self.inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


class LabeledEntry(ttk.Frame):
    """Label + Entry en una fila"""
    def __init__(self, parent, label, var=None, width=20, required=False, **kw):
        super().__init__(parent, style="White.TFrame")
        lbl_text = label + (" *" if required else "")
        ttk.Label(self, text=lbl_text, style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        if var is None:
            var = tk.StringVar()
        self.var = var
        self.entry = ttk.Entry(self, textvariable=var, width=width, **kw)
        self.entry.pack(side="left", fill="x", expand=True)

    def get(self):
        return self.var.get().strip()

    def set(self, v):
        self.var.set(v)

    def focus(self):
        self.entry.focus()


class LabeledCombo(ttk.Frame):
    """Label + Combobox en una fila"""
    def __init__(self, parent, label, values, var=None, width=20, **kw):
        super().__init__(parent, style="White.TFrame")
        ttk.Label(self, text=label, style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        if var is None:
            var = tk.StringVar()
        self.var = var
        self.combo = ttk.Combobox(self, textvariable=var,
                                   values=values, width=width, **kw)
        self.combo.pack(side="left", fill="x", expand=True)

    def get(self):
        return self.var.get()

    def set(self, v):
        self.var.set(v)


class DataTable(ttk.Frame):
    """Tabla con Treeview + scrollbars"""
    def __init__(self, parent, columns, show_index=False, **kw):
        super().__init__(parent, **kw)
        self.columns = columns
        cols = [c[0] for c in columns]

        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  selectmode="browse")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for c in columns:
            cid, label = c[0], c[1]
            w = c[2] if len(c) > 2 else 100
            anchor = c[3] if len(c) > 3 else "w"
            self.tree.heading(cid, text=label,
                              command=lambda col=cid: self._sort(col, False))
            self.tree.column(cid, width=w, anchor=anchor, minwidth=40)

        self.tree.tag_configure("odd",  background="#eaf0f6")
        self.tree.tag_configure("even", background=C_WHITE)
        self.tree.tag_configure("total", background="#d6eaf8", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("danger", background="#fadbd8")
        self.tree.tag_configure("success", background="#d5f5e3")

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def insert(self, values, tags=None):
        n = len(self.tree.get_children())
        tag = tags or ("odd" if n % 2 else "even",)
        self.tree.insert("", "end", values=values, tags=tag)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def get_selected(self):
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0])["values"]
        return None

    def _sort(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0].replace(".", "").replace(",", "").replace("$", "").strip()), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for idx, (_, k) in enumerate(data):
            self.tree.move(k, "", idx)
        self.tree.heading(col, command=lambda: self._sort(col, not reverse))


class SummaryCard(tk.Frame):
    """Tarjeta resumen con título, valor y color"""
    def __init__(self, parent, title, value="$0", color=C_SECONDARY, **kw):
        super().__init__(parent, bg=color, padx=14, pady=10, **kw)
        tk.Label(self, text=title, bg=color, fg=C_WHITE,
                 font=FONT_SMALL).pack(anchor="w")
        self.val_lbl = tk.Label(self, text=value, bg=color, fg=C_WHITE,
                                 font=("Segoe UI", 16, "bold"))
        self.val_lbl.pack(anchor="w")

    def update_value(self, v):
        self.val_lbl.config(text=v)


class SectionHeader(ttk.Frame):
    """Barra de título de sección"""
    def __init__(self, parent, title, **kw):
        super().__init__(parent, **kw)
        self.config(style="TFrame")
        tk.Frame(self, bg=C_PRIMARY, height=3).pack(fill="x")
        tk.Frame(self, bg=C_PRIMARY, height=32).pack(fill="x")
        self.lbl = tk.Label(self, text=f"  {title}", bg=C_PRIMARY, fg=C_WHITE,
                             font=FONT_HEADER, anchor="w")
        self.lbl.place(x=0, y=3, relwidth=1, height=32)


class ToolBar(tk.Frame):
    """Barra de herramientas con botones de acción"""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C_BG, pady=4, **kw)
        self.buttons = {}

    def add_button(self, key, text, command, style="TButton"):
        btn = ttk.Button(self, text=text, command=command, style=style)
        btn.pack(side="left", padx=3)
        self.buttons[key] = btn
        return btn

    def add_separator(self):
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=6)


class StatusBar(tk.Frame):
    """Barra de estado inferior"""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C_PRIMARY, height=24, **kw)
        self._msg = tk.Label(self, text="Listo", bg=C_PRIMARY, fg=C_WHITE,
                              font=FONT_SMALL, anchor="w", padx=8)
        self._msg.pack(side="left", fill="x", expand=True)
        self._info = tk.Label(self, text="", bg=C_PRIMARY, fg=C_WHITE,
                               font=FONT_SMALL, padx=8)
        self._info.pack(side="right")

    def set(self, msg, info=""):
        self._msg.config(text=msg)
        self._info.config(text=info)


def ask_confirm(title, msg):
    from tkinter import messagebox
    return messagebox.askyesno(title, msg)


def show_error(msg):
    from tkinter import messagebox
    messagebox.showerror("Error", msg)


def show_info(msg):
    from tkinter import messagebox
    messagebox.showinfo("Información", msg)


def show_warning(msg):
    from tkinter import messagebox
    messagebox.showwarning("Advertencia", msg)
