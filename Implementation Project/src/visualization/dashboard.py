"""
Drone Animal Detection — Desktop Dashboard
Place in: src/visualization/dashboard.py
Launched from yolo_prediction.py menu or run directly.

Dependencies (all standard except matplotlib + pandas):
    pip install matplotlib pandas
"""

import sys
import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path

# imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
try:
    from database.supabase_client import supabase
except ImportError:
    supabase = None
    print("  Could not import supabase_client — running with mock data.")

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import pandas as pd
except ImportError:
    print("\n  Missing dependencies. Install with:\n      pip install matplotlib pandas\n")
    sys.exit(1)

#Theme

C = {
    "bg":      "#0F1A14",
    "sidebar": "#0A1209",
    "card":    "#172214",
    "border":  "#2D6A4F",
    "accent":  "#52B788",
    "accent2": "#40916C",
    "text":    "#D8F3DC",
    "muted":   "#74C69D",
    "dim":     "#3A5A45",
    "row_alt": "#1B2D1F",
}

PALETTE = ["#2D6A4F","#40916C","#52B788","#74C69D",
           "#95D5B2","#B7E4C7","#1B4332","#081C12"]


def mpl_theme(fig, axes):
    fig.patch.set_facecolor(C["card"])
    ax_list = axes if hasattr(axes, "__iter__") else [axes]
    for ax in ax_list:
        ax.set_facecolor(C["card"])
        ax.tick_params(colors=C["muted"], labelsize=9)
        ax.xaxis.label.set_color(C["muted"])
        ax.yaxis.label.set_color(C["muted"])
        ax.title.set_color(C["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.grid(color=C["border"], linewidth=0.4, alpha=0.6)

# Dtaa layer

MOCK_DATA = [
    {"id": i+1, "species": s, "confidence": c, "created_at": t}
    for i, (s, c, t) in enumerate([
        ("fox",    0.91, "2025-04-01 08:12:00"),
        ("deer",   0.87, "2025-04-01 09:34:00"),
        ("fox",    0.95, "2025-04-02 07:50:00"),
        ("rabbit", 0.78, "2025-04-02 11:20:00"),
        ("deer",   0.82, "2025-04-03 14:05:00"),
        ("fox",    0.88, "2025-04-04 06:30:00"),
        ("rabbit", 0.80, "2025-04-04 16:45:00"),
        ("deer",   0.90, "2025-04-05 10:10:00"),
        ("fox",    0.93, "2025-04-05 13:22:00"),
        ("rabbit", 0.76, "2025-04-06 08:55:00"),
    ])
]


def fetch_detections() -> pd.DataFrame:
    if supabase is None:
        df = pd.DataFrame(MOCK_DATA)
    else:
        try:
            res = supabase.table("Detections").select("*").order("created_at").execute()
            df = pd.DataFrame(res.data) if res.data else pd.DataFrame(
                columns=["id", "species", "confidence", "created_at"])
        except Exception as e:
            print(f"  DB error: {e}")
            df = pd.DataFrame(columns=["id", "species", "confidence", "created_at"])

    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df

# building charts

def _embed(fig, parent) -> FigureCanvasTkAgg:
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    return canvas


def build_bar(parent, df: pd.DataFrame, figsize=(5, 3.2)) -> FigureCanvasTkAgg:
    fig, ax = plt.subplots(figsize=figsize, dpi=96)
    mpl_theme(fig, ax)
    if not df.empty:
        counts = df["species"].value_counts()
        bars = ax.bar(counts.index, counts.values,
                      color=PALETTE[:len(counts)], width=0.55, zorder=2)
        ax.bar_label(bars, fmt="%d", color=C["muted"], fontsize=9, padding=3)
    ax.set_title("Detections per species", fontsize=11, pad=8)
    ax.set_xlabel("Species")
    ax.set_ylabel("Count")
    ax.set_axisbelow(True)
    fig.tight_layout(pad=1.2)
    return _embed(fig, parent)


def build_confidence(parent, df: pd.DataFrame, figsize=(5, 3.2)) -> FigureCanvasTkAgg:
    fig, ax = plt.subplots(figsize=figsize, dpi=96)
    mpl_theme(fig, ax)
    if not df.empty:
        species_list = df["species"].unique()
        data_groups  = [df[df["species"] == s]["confidence"].values for s in species_list]
        bp = ax.boxplot(
            data_groups, patch_artist=True,
            medianprops=dict(color=C["text"], linewidth=1.5),
            whiskerprops=dict(color=C["muted"]),
            capprops=dict(color=C["muted"]),
            flierprops=dict(marker="o", color=C["muted"], markersize=4),
        )
        for patch, color in zip(bp["boxes"], PALETTE):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)
        ax.set_xticks(range(1, len(species_list) + 1))
        ax.set_xticklabels(species_list, fontsize=9)
    ax.set_title("Confidence distribution", fontsize=11, pad=8)
    ax.set_xlabel("Species")
    ax.set_ylabel("Confidence")
    ax.set_ylim(0, 1.05)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=1.2)
    return _embed(fig, parent)


def build_timeline(parent, df: pd.DataFrame, figsize=(8, 3.8)) -> FigureCanvasTkAgg:
    fig, ax = plt.subplots(figsize=figsize, dpi=96)
    mpl_theme(fig, ax)
    if not df.empty:
        df2 = df.copy()
        df2["date"] = df2["created_at"].dt.date
        for i, species in enumerate(df2["species"].unique()):
            sub = df2[df2["species"] == species].groupby("date").size()
            ax.plot(sub.index, sub.values, marker="o", markersize=5,
                    linewidth=1.8, color=PALETTE[i % len(PALETTE)], label=species)
        ax.legend(facecolor=C["card"], edgecolor=C["border"],
                  labelcolor=C["text"], fontsize=9)
        fig.autofmt_xdate(rotation=30, ha="right")
    ax.set_title("Detections over time", fontsize=11, pad=8)
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")
    ax.set_axisbelow(True)
    fig.tight_layout(pad=1.2)
    return _embed(fig, parent)


def build_heatmap(parent, df: pd.DataFrame, figsize=(8, 3.8)) -> FigureCanvasTkAgg:
    fig, ax = plt.subplots(figsize=figsize, dpi=96)
    mpl_theme(fig, ax)
    if not df.empty:
        df2 = df.copy()
        df2["hour"] = df2["created_at"].dt.hour
        df2["dow"]  = df2["created_at"].dt.dayofweek
        pivot = df2.groupby(["dow", "hour"]).size().unstack(fill_value=0)
        pivot = pivot.reindex(range(7), fill_value=0)
        pivot = pivot.reindex(columns=range(24), fill_value=0)
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "drone", [C["card"], C["accent2"], C["accent"]])
        im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=0)
        ax.set_yticks(range(7))
        ax.set_yticklabels(days, fontsize=9)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)], fontsize=8)
        cbar = fig.colorbar(im, ax=ax, pad=0.01)
        cbar.ax.tick_params(colors=C["muted"], labelsize=8)
        cbar.outline.set_edgecolor(C["border"])
    ax.set_title("Activity heatmap  (hour × day)", fontsize=11, pad=8)
    fig.tight_layout(pad=1.2)
    return _embed(fig, parent)

# UI layer

VIEWS = ["Overview", "Timeline", "Heatmap", "Recent detections"]


class DashboardApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Drone Animal Detection")
        self.geometry("1100x700")
        self.minsize(860, 560)
        self.configure(bg=C["bg"])

        self._df: pd.DataFrame = pd.DataFrame()
        self._canvases: list   = []
        self._current_view     = "Overview"

        self._setup_fonts()
        self._build_ui()
        self._load_and_render()

    # fonts and styles

    def _setup_fonts(self):
        self.fn    = tkfont.Font(family="Courier New", size=10)
        self.fn_sm = tkfont.Font(family="Courier New", size=9)
        self.fn_lg = tkfont.Font(family="Courier New", size=13, weight="bold")
        self.fn_hd = tkfont.Font(family="Courier New", size=10, weight="bold")

    # layout and components

    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self, bg=C["sidebar"], height=44)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="▶  DRONE ANIMAL DETECTION",
                 bg=C["sidebar"], fg=C["accent"],
                 font=self.fn_lg).pack(side=tk.LEFT, padx=16, pady=8)

        self._status_lbl = tk.Label(topbar, text="", bg=C["sidebar"],
                                     fg=C["muted"], font=self.fn_sm)
        self._status_lbl.pack(side=tk.RIGHT, padx=16)

        tk.Button(
            topbar, text="↺  Refresh",
            bg=C["sidebar"], fg=C["muted"],
            activebackground=C["card"], activeforeground=C["accent"],
            relief=tk.FLAT, bd=0, font=self.fn_sm, cursor="hand2",
            command=self._load_and_render,
        ).pack(side=tk.RIGHT, padx=4, pady=8)

        # body
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True)

        # sidebar
        sidebar = tk.Frame(body, bg=C["sidebar"], width=158)
        sidebar.pack(fill=tk.Y, side=tk.LEFT)
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=C["border"], height=1).pack(fill=tk.X, pady=(8, 0))

        self._nav_btns: dict = {}
        for view in VIEWS:
            btn = tk.Button(
                sidebar, text=view, anchor="w",
                bg=C["sidebar"], fg=C["muted"],
                activebackground=C["card"], activeforeground=C["accent"],
                relief=tk.FLAT, bd=0, font=self.fn,
                padx=16, pady=10, cursor="hand2",
                command=lambda v=view: self._switch_view(v),
            )
            btn.pack(fill=tk.X)
            self._nav_btns[view] = btn

        tk.Frame(sidebar, bg=C["border"], height=1).pack(fill=tk.X, pady=(0, 12))

        self._stat_total   = self._sidebar_stat(sidebar, "TOTAL")
        self._stat_species = self._sidebar_stat(sidebar, "SPECIES")
        self._stat_avg     = self._sidebar_stat(sidebar, "AVG CONF")
        self._stat_top     = self._sidebar_stat(sidebar, "TOP SPECIES")

        # main content
        self._main = tk.Frame(body, bg=C["bg"])
        self._main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._switch_view("Overview")

    def _sidebar_stat(self, parent, label: str) -> tk.Label:
        f = tk.Frame(parent, bg=C["sidebar"])
        f.pack(fill=tk.X, padx=12, pady=(0, 6))
        tk.Label(f, text=label, bg=C["sidebar"], fg=C["dim"],
                 font=self.fn_sm, anchor="w").pack(fill=tk.X)
        val = tk.Label(f, text="—", bg=C["sidebar"], fg=C["accent"],
                       font=self.fn_hd, anchor="w")
        val.pack(fill=tk.X)
        return val

    # view swtiching and rendering

    def _switch_view(self, view: str):
        self._current_view = view
        for v, btn in self._nav_btns.items():
            btn.configure(fg=C["accent"] if v == view else C["muted"],
                          bg=C["card"]   if v == view else C["sidebar"])
        self._render_view()

    def _render_view(self):
        for c in self._canvases:
            try:
                c.get_tk_widget().destroy()
                plt.close(c.figure)
            except Exception:
                pass
        self._canvases.clear()

        for w in self._main.winfo_children():
            w.destroy()

        df = self._df
        v  = self._current_view

        if v == "Overview":
            self._view_overview(df)
        elif v == "Timeline":
            self._view_full_chart(df, build_timeline, (10, 5.5))
        elif v == "Heatmap":
            self._view_full_chart(df, build_heatmap, (10, 5.5))
        elif v == "Recent detections":
            self._view_table(df)

    # overview 2x2

    def _view_overview(self, df):
        top = tk.Frame(self._main, bg=C["bg"])
        top.pack(fill=tk.BOTH, expand=True)
        bot = tk.Frame(self._main, bg=C["bg"])
        bot.pack(fill=tk.BOTH, expand=True)

        for f in (top, bot):
            f.columnconfigure(0, weight=1)
            f.columnconfigure(1, weight=1)
            f.rowconfigure(0, weight=1)

        tl = self._card(top, 0, 0)
        tr = self._card(top, 0, 1)
        bl = self._card(bot, 0, 0)
        br = self._card(bot, 0, 1)

        self._canvases.append(build_bar(tl, df))
        self._canvases.append(build_confidence(tr, df))
        self._canvases.append(build_timeline(bl, df))
        self._canvases.append(build_heatmap(br, df))

    def _card(self, parent, row, col) -> tk.Frame:
        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=C["border"], highlightthickness=1)
        f.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        return f

    # view single chart

    def _view_full_chart(self, df, builder_fn, figsize):
        card = tk.Frame(self._main, bg=C["card"],
                        highlightbackground=C["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._canvases.append(builder_fn(card, df, figsize=figsize))

    # view recent detections
    def _on_edit_cell(self, event):
        tree = self._tree
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)

        if not item or column == "#1":  # don't edit ID
            return

        col_index = int(column.replace("#", "")) - 1
        x, y, width, height = tree.bbox(item, column)

        value = tree.item(item, "values")[col_index]

        entry = tk.Entry(tree)
        entry.insert(0, value)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def save_edit(event=None):
            new_value = entry.get()
            entry.destroy()
            self._update_cell(item, col_index, new_value)

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())
    
    def _update_cell(self, item, col_index, new_value):
        tree = self._tree
        values = list(tree.item(item, "values"))
        record_id = values[0]

        field_map = {
            1: "species",
            2: "confidence",
            3: "created_at"
        }

        field = field_map.get(col_index)
        if field is None:
            return

        # validate input
        try:
            if field == "confidence":
                new_value = float(new_value)
                if not (0 <= new_value <= 1):
                    raise ValueError("Confidence must be 0–1")

            elif field == "created_at":
                new_value = pd.to_datetime(new_value)

            elif field == "species":
                if not new_value.strip():
                    raise ValueError("Species cannot be empty")

        except Exception as e:
            print(f"Invalid input: {e}")
            return

        # update UI
        values[col_index] = new_value
        tree.item(item, values=values)

        # update supabase
        if supabase is not None:
            try:
                update_data = {field: str(new_value)}
                supabase.table("Detections").update(update_data).eq("id", record_id).execute()
                print(f"✓ Updated record {record_id}")
            except Exception as e:
                print(f"✗ DB update failed: {e}")

    def _view_table(self, df):
        hdr = tk.Frame(self._main, bg=C["bg"])
        hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(hdr, text="Recent detections", bg=C["bg"],
                fg=C["text"], font=self.fn_hd).pack(side=tk.LEFT)

        card = tk.Frame(self._main, bg=C["card"],
                        highlightbackground=C["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.theme_use("default")

        style.configure("D.Treeview",
                        background=C["card"], fieldbackground=C["card"],
                        foreground=C["text"], rowheight=28,
                        font=("Courier New", 10), borderwidth=0)

        style.configure("D.Treeview.Heading",
                        background=C["sidebar"], foreground=C["muted"],
                        font=("Courier New", 9, "bold"), relief="flat")

        cols = ("id", "species", "confidence", "timestamp")

        tree = ttk.Treeview(card, columns=cols, show="headings", style="D.Treeview")
        for col, width in zip(cols, (60, 160, 120, 200)):
            tree.heading(col, text=col.upper())
            tree.column(col, width=width, anchor="w")

        sb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # store reference
        self._tree = tree

        if not df.empty:
            recent = df.sort_values("created_at", ascending=False)
            for _, row in recent.iterrows():
                tree.insert("", tk.END, values=(
                    row["id"],
                    row["species"],
                    f"{row['confidence']:.4f}",
                    str(row["created_at"])[:19],
                ))
        else:
            tree.insert("", tk.END, values=("—", "No data yet", "—", "—"))

        # bind edit
        tree.bind("<Double-1>", self._on_edit_cell)

    # dataloading

    def _load_and_render(self):
        self._status_lbl.configure(text="Loading…", fg=C["muted"])
        self.update_idletasks()
        self._df = fetch_detections()
        df = self._df

        if df.empty:
            self._stat_total.configure(text="0")
            self._stat_species.configure(text="0")
            self._stat_avg.configure(text="—")
            self._stat_top.configure(text="—")
        else:
            self._stat_total.configure(text=str(len(df)))
            self._stat_species.configure(text=str(df["species"].nunique()))
            self._stat_avg.configure(text=f"{df['confidence'].mean():.2f}")
            self._stat_top.configure(text=df["species"].value_counts().idxmax())

        from datetime import datetime
        self._status_lbl.configure(
            text=f"Updated {datetime.now().strftime('%H:%M:%S')}", fg=C["muted"])
        self._render_view()

    def destroy(self):
        for c in self._canvases:
            try:
                plt.close(c.figure)
            except Exception:
                pass
        super().destroy()

# entry

def run():
    app = DashboardApp()
    app.mainloop()


if __name__ == "__main__":
    run()