"""Native X Playground window: replay, tickets, predictions and drawn ticks."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import UTC, date, datetime
from functools import partial
from tkinter import messagebox, ttk
from typing import Any

from losslens.mt4 import export
from losslens.ticks.store import TickStore

from .playground_model import PERIOD_ORDER, PERIODS, PlaygroundModel, Tick

PANEL = "#f0f0f0"
PANEL_DARK = "#e4e4e4"
WHITE = "#ffffff"
CHART_BG = "#000000"
UP = "#00c000"
DOWN = "#ff4040"
ASK = "#ff9090"
GRID = "#1a1a1a"
TEXT = "#d0d0d0"
MUTED = "#888888"
DRAWN = "#e0e0e0"
PREDICT = "#4a9eff"
FONT = ("Tahoma", 9)
FONT_SMALL = ("Tahoma", 8)
FONT_BOLD = ("Tahoma", 9, "bold")
PERIOD_LABELS = {
    "tick": "Tick",
    "t1": "1T",
    "t10": "10T",
    "t100": "100T",
    "t500": "500T",
    "t1000": "1K",
    "m1": "M1",
    "m5": "M5",
    "m15": "M15",
    "m30": "M30",
    "h1": "H1",
}


class PlaygroundWindow(tk.Toplevel):
    """A native Playground inside X, using the real tick store."""

    def __init__(
        self,
        master: tk.Misc,
        symbol: str,
        day: date,
        inputs: tuple[Any, ...] = (),
    ) -> None:
        super().__init__(master)
        self.title("X - Playground")
        self.geometry("1400x900")
        self.minsize(1000, 650)
        self.configure(bg=PANEL)
        self.symbol = symbol
        self.day = day
        self.inputs = inputs
        self.digits = export.SYMBOL_PRECISION.get(symbol.upper(), 3)
        self.model: PlaygroundModel
        self.view_start = 0
        self.view_count = 42
        self.follow = True
        self.hover: int | None = None
        self.hover_y = 0
        self.drag_from: int | None = None
        self.drag_start = 0
        self.drag_moved = False
        self.draw_prediction = False
        self.draw_ticks = False
        self.tick_stroke = False
        self.both_ways = False
        self.stroke_view_start = 0
        self.stroke_view_count = 0
        self.stroke_start_count = 0
        self._stroke_x = 0
        self._stroke_y = 0
        self.period_buttons: dict[str, tk.Button] = {}
        self.message = ""
        self._load_data()
        self._build_menu()
        self._build_status()
        self._build_terminal()
        self._build_toolbar()
        self._build_main()
        self.bind("<Left>", self._on_left)
        self.bind("<Right>", self._on_right)
        self.bind("<End>", self._on_end)
        self.bind("<plus>", self._on_plus)
        self.bind("<minus>", self._on_minus)
        self.bind("<space>", self._on_space)
        self.bind("d", self._on_draw_key)
        self.bind("t", self._on_ticks_key)
        self.after(60, self._fit_and_redraw)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _load_data(self) -> None:
        store = TickStore(symbol=self.symbol)
        table = store.read_day(self.day)
        if table is None or table.num_rows == 0:
            raise ValueError(f"{self.day.isoformat()} has no stored ticks")
        ts_values = table["ts_ms"].to_pylist()
        bid_values = table["bid"].to_pylist()
        ask_values = table["ask"].to_pylist()
        ticks = [
            Tick(int(ts), float(bid), float(ask))
            for ts, bid, ask in zip(ts_values, bid_values, ask_values, strict=True)
        ]
        self.model = PlaygroundModel(ticks, start_ms=self._default_start(ticks))

    @staticmethod
    def _default_start(ticks: list[Tick]) -> int:
        first_ts = ticks[0].ts_ms
        last_ts = ticks[-1].ts_ms
        moment = datetime.fromtimestamp(first_ts / 1000, tz=UTC).date()
        midnight = int(
            datetime(moment.year, moment.month, moment.day, tzinfo=UTC).timestamp() * 1000
        )
        preferred = midnight + 14 * 60 * 60_000
        if not (first_ts <= preferred <= last_ts):
            preferred = max(first_ts, last_ts - 30 * 60_000)
        return preferred

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Expert Inputs...", command=self._open_inputs)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Quick start", command=self._about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self, bg=PANEL, bd=1, relief="raised")
        bar.pack(side="top", fill="x")
        for key in PERIOD_ORDER:
            button = tk.Button(
                bar,
                text=PERIOD_LABELS[key],
                width=4,
                relief="sunken" if key == self.model.period else "raised",
                command=partial(self._set_period, key),
            )
            button.pack(side="left", padx=1, pady=2)
            self.period_buttons[key] = button
        tk.Button(bar, text="Reset", width=6, command=self._reset).pack(
            side="left", padx=(8, 1), pady=2
        )
        tk.Button(bar, text="Next tick", width=8, command=lambda: self._advance(1)).pack(
            side="left", padx=1, pady=2
        )
        tk.Button(bar, text="+10", width=4, command=lambda: self._advance(10)).pack(
            side="left", padx=1, pady=2
        )
        tk.Button(bar, text="+100", width=5, command=lambda: self._advance(100)).pack(
            side="left", padx=1, pady=2
        )
        tk.Button(bar, text="Next bar", width=8, command=self._next_bar).pack(
            side="left", padx=1, pady=2
        )
        self.predict_button = tk.Button(
            bar, text="Draw prediction", width=13, command=self._toggle_prediction
        )
        self.predict_button.pack(side="left", padx=(8, 1), pady=2)
        self.ticks_button = tk.Button(bar, text="Draw ticks", width=9, command=self._toggle_ticks)
        self.ticks_button.pack(side="left", padx=1, pady=2)
        self.clear_ticks_button = tk.Button(
            bar, text="Clear ticks", width=9, command=self._clear_ticks, state="disabled"
        )
        self.clear_ticks_button.pack(side="left", padx=1, pady=2)
        self.both_button = tk.Button(bar, text="Both ways", width=9, command=self._toggle_both)
        self.both_button.pack(side="left", padx=1, pady=2)
        tk.Label(bar, text="Grid", bg=PANEL, fg=MUTED).pack(side="left", padx=(8, 1))
        self.grid_var = tk.StringVar(self, value=f"{self.model.grid_step:.2f}")
        grid = ttk.Combobox(
            bar,
            textvariable=self.grid_var,
            values=("0.01", "0.05", "0.10", "0.25", "0.50", "1.00"),
            width=5,
            state="readonly",
        )
        grid.pack(side="left", pady=2)
        grid.bind("<<ComboboxSelected>>", self._on_grid)
        self.time_var = tk.StringVar(self, value="14:00")
        time_entry = tk.Entry(bar, textvariable=self.time_var, width=6)
        time_entry.pack(side="left", padx=(8, 1), pady=2)
        time_entry.bind("<Return>", lambda _event: self._jump_to_time())
        tk.Button(bar, text="Go", width=3, command=self._jump_to_time).pack(
            side="left", padx=1, pady=2
        )

    def _build_status(self) -> None:
        status = tk.Frame(self, bg=PANEL, bd=1, relief="raised")
        status.pack(side="bottom", fill="x")
        tk.Label(status, text="Local only · nothing is sent", bg=PANEL, fg=MUTED).pack(
            side="left", padx=6
        )
        self.status_center = tk.Label(status, text="", bg=PANEL, fg=MUTED)
        self.status_center.pack(side="left", padx=12)
        self.status_right = tk.Label(status, text="", bg=PANEL, fg=MUTED)
        self.status_right.pack(side="right", padx=6)

    def _build_terminal(self) -> None:
        frame = tk.Frame(self, height=230, bg=WHITE, bd=1, relief="raised")
        frame.pack(side="bottom", fill="x")
        frame.pack_propagate(False)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)
        self._build_trade_tab(notebook)
        self._build_prediction_tab(notebook)
        self._build_scenarios_tab(notebook)
        self._build_expert_tab(notebook)
        self._build_help_tab(notebook)

    def _tab(self, notebook: ttk.Notebook, title: str) -> tk.Frame:
        frame = tk.Frame(notebook, bg=WHITE)
        notebook.add(frame, text=title)
        return frame

    def _build_trade_tab(self, notebook: ttk.Notebook) -> None:
        frame = self._tab(notebook, "Trade")
        order = tk.Frame(frame, bg=WHITE)
        order.pack(fill="x", padx=6, pady=3)
        tk.Label(order, text="Volume", bg=WHITE).pack(side="left")
        self.volume_var = tk.StringVar(self, value="0.01")
        tk.Entry(order, textvariable=self.volume_var, width=7).pack(side="left", padx=(2, 8))
        tk.Label(order, text="S/L", bg=WHITE).pack(side="left")
        self.sl_var = tk.StringVar(self)
        tk.Entry(order, textvariable=self.sl_var, width=10).pack(side="left", padx=(2, 8))
        tk.Label(order, text="T/P", bg=WHITE).pack(side="left")
        self.tp_var = tk.StringVar(self)
        tk.Entry(order, textvariable=self.tp_var, width=10).pack(side="left", padx=(2, 8))
        tk.Button(order, text="Buy", width=6, command=lambda: self._open_ticket("buy")).pack(
            side="left", padx=2
        )
        tk.Button(order, text="Sell", width=6, command=lambda: self._open_ticket("sell")).pack(
            side="left", padx=2
        )
        self.trade_message = tk.Label(frame, text="", bg=WHITE, fg=MUTED, anchor="w")
        self.trade_message.pack(fill="x", padx=6)
        table_frame = tk.Frame(frame, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=6, pady=(2, 0))
        columns = ("time", "type", "size", "price", "sl", "tp", "profit", "state")
        self.ticket_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        for name, title, width in (
            ("time", "Time", 72),
            ("type", "Type", 44),
            ("size", "Size", 44),
            ("price", "Price", 72),
            ("sl", "S/L", 68),
            ("tp", "T/P", 68),
            ("profit", "Profit", 76),
            ("state", "State", 70),
        ):
            self.ticket_tree.heading(name, text=title)
            self.ticket_tree.column(name, width=width, anchor="e" if name != "time" else "w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.ticket_tree.yview)
        self.ticket_tree.configure(yscrollcommand=scroll.set)
        self.ticket_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        bottom = tk.Frame(frame, bg=WHITE)
        bottom.pack(fill="x", padx=6, pady=2)
        tk.Button(bottom, text="Close selected", command=self._close_selected).pack(side="left")
        self.balance_label = tk.Label(bottom, text="", bg=WHITE, fg=MUTED)
        self.balance_label.pack(side="right", padx=8)
        self.equity_label = tk.Label(bottom, text="", bg=WHITE, fg=MUTED)
        self.equity_label.pack(side="right", padx=8)
        self.floating_label = tk.Label(bottom, text="", bg=WHITE, fg=MUTED)
        self.floating_label.pack(side="right", padx=8)

    def _build_prediction_tab(self, notebook: ttk.Notebook) -> None:
        frame = self._tab(notebook, "Prediction")
        row = tk.Frame(frame, bg=WHITE)
        row.pack(fill="x", padx=6, pady=3)
        tk.Button(row, text="Undo", command=self._undo_prediction).pack(side="left", padx=2)
        tk.Button(row, text="Clear", command=self._clear_prediction).pack(side="left", padx=2)
        tk.Label(row, text="Fixed move +/-$", bg=WHITE).pack(side="left", padx=(12, 2))
        self.move_var = tk.StringVar(self, value="1.00")
        tk.Entry(row, textvariable=self.move_var, width=7).pack(side="left")
        self.move_preview = tk.Label(frame, text="", bg=WHITE, fg=MUTED, anchor="w")
        self.move_preview.pack(fill="x", padx=6)
        self.prediction_label = tk.Label(frame, text="", bg=WHITE, fg=MUTED, anchor="w")
        self.prediction_label.pack(fill="x", padx=6, pady=2)
        tk.Label(
            frame,
            text="Draw prediction: click future chart points. Draw ticks: drag a light-grey "
            "path into the future. Everything snaps to the price grid.",
            bg=WHITE,
            fg=MUTED,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=6, pady=2)

    def _build_scenarios_tab(self, notebook: ttk.Notebook) -> None:
        frame = self._tab(notebook, "Scenarios")
        row = tk.Frame(frame, bg=WHITE)
        row.pack(fill="x", padx=6, pady=3)
        self.scenario_var = tk.StringVar(self)
        self.scenario_combo = ttk.Combobox(
            row, textvariable=self.scenario_var, state="readonly", width=28
        )
        self.scenario_combo.pack(side="left", padx=2)
        self.scenario_combo.bind("<<ComboboxSelected>>", self._on_scenario_selected)
        for label, command in (
            ("+ Add", self._add_scenario),
            ("Rename", self._rename_scenario),
            ("Duplicate", self._duplicate_scenario),
            ("Delete", self._delete_scenario),
            ("Run to end", self._run_to_end),
        ):
            tk.Button(row, text=label, command=command).pack(side="left", padx=2)
        table_frame = tk.Frame(frame, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=6, pady=(2, 0))
        columns = ("name", "equity", "drawdown", "tickets", "win", "mae", "hit")
        self.scenario_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=4)
        for name, title, width in (
            ("name", "Scenario", 220),
            ("equity", "Final equity", 110),
            ("drawdown", "Max drawdown", 110),
            ("tickets", "Tickets", 70),
            ("win", "Win rate", 80),
            ("mae", "Prediction MAE", 110),
            ("hit", "Direction hit", 100),
        ):
            self.scenario_tree.heading(name, text=title)
            self.scenario_tree.column(name, width=width, anchor="e" if name != "name" else "w")
        self.scenario_tree.pack(fill="both", expand=True)

    def _build_expert_tab(self, notebook: ttk.Notebook) -> None:
        frame = self._tab(notebook, "Expert")
        row = tk.Frame(frame, bg=WHITE)
        row.pack(fill="x", padx=6, pady=3)
        tk.Button(row, text="Expert Inputs...", command=self._open_inputs).pack(side="left", padx=2)
        tk.Label(
            row,
            text="Loaded from X at launch; the Playground never runs MT4.",
            bg=WHITE,
            fg=MUTED,
        ).pack(side="left", padx=8)
        if not self.inputs:
            tk.Label(
                frame,
                text="No expert inputs loaded. Start X with:  x desktop --inputs expert.set",
                bg=WHITE,
                fg=MUTED,
                anchor="w",
            ).pack(fill="x", padx=8, pady=8)
            return
        table_frame = tk.Frame(frame, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=6, pady=(2, 0))
        columns = ("name", "value", "start", "step", "stop")
        self.expert_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=4)
        for name, title, width in (
            ("name", "Input", 210),
            ("value", "Value", 120),
            ("start", "Start", 100),
            ("step", "Step", 100),
            ("stop", "Stop", 100),
        ):
            self.expert_tree.heading(name, text=title)
            self.expert_tree.column(name, width=width, anchor="w")
        for item in self.inputs:
            self.expert_tree.insert(
                "",
                "end",
                values=(item.name, item.value, item.start or "", item.step or "", item.stop or ""),
            )
        self.expert_tree.pack(fill="both", expand=True)

    def _build_help_tab(self, notebook: ttk.Notebook) -> None:
        frame = self._tab(notebook, "Help")
        text = tk.Text(frame, height=5, borderwidth=0, font=FONT, bg=WHITE, fg="#222")
        text.insert(
            "1.0",
            "Start a period at the top. The Playground starts with five minutes of real tape "
            "revealed and follows the cursor.\n"
            "Wheel zooms; drag pans; Follow (End) returns. Space reveals one tick.\n"
            "Type a UTC time such as 14:00 in the toolbar and press Go to jump there.\n"
            "Trade: Buy at ask, Sell at bid; S/L and T/P are checked on every revealed tick.\n"
            "Draw prediction: click future points; Both ways mirrors the path.\n"
            "Draw ticks: drag a light-grey future path; Clear ticks restores the real tape.\n"
            "All scenarios share the cursor; each has its own tickets and prediction.",
        )
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, padx=8, pady=6)

    def _build_main(self) -> None:
        main = tk.Frame(self, bg=PANEL)
        main.pack(side="top", fill="both", expand=True)
        left = tk.Frame(main, width=220, bg=WHITE, bd=1, relief="raised")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._watch(left)
        self.canvas = tk.Canvas(main, bg=CHART_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Double-Button-1>", self._on_double)

    def _watch(self, parent: tk.Frame) -> None:
        self.symbol_var = tk.StringVar(self, value=self.symbol)
        self.bid_var = tk.StringVar(self, value="-")
        self.ask_var = tk.StringVar(self, value="-")
        self.spread_var = tk.StringVar(self, value="-")
        self.dw_vars: dict[str, tk.StringVar] = {
            "period": tk.StringVar(self),
            "time": tk.StringVar(self),
            "open": tk.StringVar(self),
            "high": tk.StringVar(self),
            "low": tk.StringVar(self),
            "close": tk.StringVar(self),
            "change": tk.StringVar(self),
            "ticks": tk.StringVar(self),
        }
        self.rp_vars: dict[str, tk.StringVar] = {
            "cursor": tk.StringVar(self),
            "tick": tk.StringVar(self),
            "revealed": tk.StringVar(self),
            "view": tk.StringVar(self),
        }
        self.dw_labels: dict[str, tk.Label] = {}
        self._watch_header(parent, "Market Watch")
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=6, pady=(4, 0))
        tk.Label(row, textvariable=self.symbol_var, bg=WHITE, width=6, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 4)
        )
        tk.Label(row, textvariable=self.bid_var, bg=WHITE, width=8, anchor="e").grid(
            row=0, column=1, sticky="e", padx=(0, 4)
        )
        tk.Label(row, textvariable=self.ask_var, bg=WHITE, width=8, anchor="e").grid(
            row=0, column=2, sticky="e"
        )
        row.columnconfigure(1, weight=1)
        tk.Label(parent, textvariable=self.spread_var, bg=WHITE, fg=MUTED, anchor="w").pack(
            fill="x", padx=6, pady=(2, 0)
        )
        self._watch_header(parent, "Data Window")
        for key, label in (
            ("period", "Period"),
            ("time", "Bar time"),
            ("open", "Open"),
            ("high", "High"),
            ("low", "Low"),
            ("close", "Close"),
            ("change", "Change"),
            ("ticks", "Ticks"),
        ):
            line = tk.Frame(parent, bg=WHITE)
            line.pack(fill="x", padx=6)
            widget = tk.Label(line, text=label, bg=WHITE, fg=MUTED, anchor="w", width=9)
            widget.grid(row=0, column=0, sticky="w")
            tk.Label(line, textvariable=self.dw_vars[key], bg=WHITE, anchor="e").grid(
                row=0, column=1, sticky="e"
            )
            line.columnconfigure(1, weight=1)
            self.dw_labels[key] = widget
        self._watch_header(parent, "Replay")
        for key, label in (
            ("cursor", "Cursor"),
            ("tick", "Tick"),
            ("revealed", "Revealed"),
            ("view", "View"),
        ):
            line = tk.Frame(parent, bg=WHITE)
            line.pack(fill="x", padx=6)
            tk.Label(line, text=label, bg=WHITE, fg=MUTED, anchor="w", width=9).grid(
                row=0, column=0, sticky="w"
            )
            tk.Label(line, textvariable=self.rp_vars[key], bg=WHITE, anchor="e").grid(
                row=0, column=1, sticky="e"
            )
            line.columnconfigure(1, weight=1)
        tk.Label(
            parent,
            text="Source: Dukascopy ticks stored on this PC.",
            bg=WHITE,
            fg=MUTED,
            wraplength=206,
            justify="left",
        ).pack(fill="x", padx=6, pady=(6, 0))

    def _watch_header(self, parent: tk.Frame, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg=PANEL_DARK,
            anchor="w",
            padx=6,
            pady=4,
            font=FONT_BOLD,
        ).pack(fill="x")

    def _plot_box(self) -> tuple[int, int, int, int, int, int]:
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        left, right, top, bottom = 8, 78, 30, 24
        return left, top, max(1, width - left - right), max(1, height - top - bottom), width, height

    def _fit_view(self) -> None:
        length = self.model.series_length()
        if self.model.period == "tick":
            future = 120
            count = min(900, max(30, length + future))
        else:
            future = 10
            count = min(90, max(12, length + future))
        reserved = min(future, max(0, count - 10))
        self.view_count = count
        self.view_start = max(0, length - (count - reserved))
        self.follow = True

    def _fit_custom(self) -> None:
        if not self.model.custom_ticks:
            return
        end = self.model.n - 1
        start = max(0, self.model.cursor - 15)
        count = min(900, max(30, end - start + 16))
        self.view_count = count
        self.view_start = max(0, end - count + 1)
        self.follow = False

    def _set_period(self, key: str) -> None:
        if key not in PERIODS:
            return
        self.model.set_period(key)
        for value, button in self.period_buttons.items():
            button.configure(relief="sunken" if value == key else "raised")
        self._fit_view()
        self._refresh_all()

    def _advance(self, count: int) -> None:
        closed = self.model.advance(count)
        if self.follow:
            self._fit_view()
        if closed:
            self.message = f"{closed} ticket(s) closed by S/L or T/P."
        else:
            self.message = ""
        self._refresh_all()

    def _next_bar(self) -> None:
        self.model.next_bar()
        if self.follow:
            self._fit_view()
        self._refresh_all()

    def _reset(self) -> None:
        if any(s.tickets or s.prediction.points for s in self.model.scenarios):
            if not messagebox.askyesno("X", "Reset the replay and clear tickets/prediction?"):
                return
        self.model.reset()
        self._fit_view()
        self.message = "Replay reset to the opening warm-up."
        self._refresh_all()

    def _toggle_prediction(self) -> None:
        self.draw_prediction = not self.draw_prediction
        if self.draw_prediction:
            self.draw_ticks = False
            self.tick_stroke = False
        self.predict_button.configure(relief="sunken" if self.draw_prediction else "raised")
        self.ticks_button.configure(relief="raised")
        self.message = (
            "Draw prediction on. Click future chart points."
            if self.draw_prediction
            else "Draw prediction off."
        )
        self._refresh_all()

    def _toggle_ticks(self) -> None:
        self.draw_ticks = not self.draw_ticks
        self.tick_stroke = False
        if self.draw_ticks:
            self.draw_prediction = False
            if not self.model.custom_ticks:
                self.model.custom_branch = None
                self.model.custom_spread = 0.0
            self.model.set_custom_branch()
            self._set_period("tick")
            self.message = (
                "Draw ticks: drag a light-grey future path. Clear ticks restores the real tape."
            )
        else:
            self.message = "Draw ticks off."
        self.predict_button.configure(relief="sunken" if self.draw_prediction else "raised")
        self.ticks_button.configure(relief="sunken" if self.draw_ticks else "raised")
        self._refresh_all()

    def _clear_ticks(self) -> None:
        if not self.model.custom_ticks:
            return
        if not messagebox.askyesno(
            "X", "Clear the drawn ticks and restore the real tape? Tickets are cleared."
        ):
            return
        self.model.clear_custom()
        self.draw_ticks = False
        self.tick_stroke = False
        self.ticks_button.configure(relief="raised")
        self.clear_ticks_button.configure(state="disabled")
        self._fit_view()
        self.message = "Drawn ticks cleared; real tape restored."
        self._refresh_all()

    def _toggle_both(self) -> None:
        self.both_ways = not self.both_ways
        self.both_button.configure(relief="sunken" if self.both_ways else "raised")
        self._refresh_all()

    def _jump_to_time(self) -> None:
        text = self.time_var.get().strip()
        try:
            hour_text, minute_text = text.split(":", 1)
            hour = int(hour_text)
            minute = int(minute_text)
        except ValueError:
            self.message = "Go needs a UTC time like 14:00."
            self._refresh_status()
            return
        if not (0 <= hour < 24 and 0 <= minute < 60):
            self.message = "Go needs a UTC time like 14:00."
            self._refresh_status()
            return
        midnight = int(
            datetime(self.day.year, self.day.month, self.day.day, tzinfo=UTC).timestamp() * 1000
        )
        target = midnight + (hour * 60 + minute) * 60_000
        self.model.cursor = self.model.index_at_or_after(target)
        self.hover = None
        self._fit_view()
        self.message = f"Jumped to {hour:02d}:{minute:02d} UTC."
        self._refresh_all()

    def _grid_price(self, price: float) -> float:
        return round(round(price / self.model.grid_step) * self.model.grid_step, 6)

    def _on_grid(self, _event: tk.Event) -> None:
        try:
            step = float(self.grid_var.get())
        except ValueError:
            return
        if step > 0:
            self.model.grid_step = step
            self._refresh_all()

    def _open_ticket(self, side: str) -> None:
        try:
            lots = float(self.volume_var.get())
        except ValueError:
            self.message = "Volume must be a number."
            self._refresh_all()
            return
        try:
            sl = float(self.sl_var.get()) if self.sl_var.get().strip() else None
            tp = float(self.tp_var.get()) if self.tp_var.get().strip() else None
        except ValueError:
            self.message = "S/L and T/P must be prices or blank."
            self._refresh_all()
            return
        try:
            ticket = self.model.open_ticket(side, lots, sl, tp)
        except ValueError as exc:
            self.message = str(exc)
            self._refresh_all()
            return
        if ticket.status == "closed":
            self.message = f"Ticket closed by {ticket.close_reason} on the entry tick."
        else:
            self.message = "Buy opened at the ask." if side == "buy" else "Sell opened at the bid."
        self._refresh_all()

    def _close_selected(self) -> None:
        selection = self.ticket_tree.selection()
        if not selection:
            return
        ticket = self.model.close_ticket(int(selection[0]))
        if ticket is not None:
            self.message = f"Ticket closed at the current {ticket.side} price."
            self._refresh_all()

    def _undo_prediction(self) -> None:
        self.model.undo_prediction()
        self._refresh_all()

    def _clear_prediction(self) -> None:
        self.model.clear_prediction()
        self._refresh_all()

    def _add_scenario(self) -> None:
        self.model.add_scenario()
        self._refresh_all()

    def _rename_scenario(self) -> None:
        scenario = self.model.active()
        name = self._ask_string("Rename scenario", scenario.name)
        if name:
            scenario.name = name[:40]
            self._refresh_all()

    def _duplicate_scenario(self) -> None:
        self.model.duplicate_scenario()
        self._refresh_all()

    def _delete_scenario(self) -> None:
        if len(self.model.scenarios) == 1:
            return
        if messagebox.askyesno("X", f"Delete {self.model.active().name}?"):
            self.model.delete_scenario()
            self._refresh_all()

    def _on_scenario_selected(self, _event: tk.Event) -> None:
        name = self.scenario_var.get()
        for index, scenario in enumerate(self.model.scenarios):
            if scenario.name == name:
                self.model.active_index = index
                break
        self._refresh_all()

    def _run_to_end(self) -> None:
        self.model.run_to_end()
        self._fit_view()
        self._refresh_all()
        self._show_scoreboard()

    def _ask_string(self, title: str, initial: str) -> str | None:
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.configure(bg=PANEL)
        value = tk.StringVar(self, value=initial)
        tk.Label(dialog, text=title, bg=PANEL).pack(padx=8, pady=(8, 2))
        entry = tk.Entry(dialog, textvariable=value, width=32)
        entry.pack(padx=8)
        entry.focus_set()
        result: list[str | None] = [None]

        def ok() -> None:
            result[0] = value.get()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        buttons = tk.Frame(dialog, bg=PANEL)
        buttons.pack(pady=8)
        tk.Button(buttons, text="OK", width=8, command=ok).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=8, command=cancel).pack(side="left", padx=4)
        dialog.bind("<Return>", lambda _event: ok())
        dialog.bind("<Escape>", lambda _event: cancel())
        dialog.grab_set()
        self.wait_window(dialog)
        return result[0]

    def _show_scoreboard(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("X - Scoreboard")
        dialog.transient(self)
        dialog.geometry("980x420")
        dialog.configure(bg=PANEL)
        columns = ("name", "equity", "drawdown", "tickets", "win", "mae", "hit")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")
        for name, title, width in (
            ("name", "Scenario", 240),
            ("equity", "Final equity", 120),
            ("drawdown", "Max drawdown", 120),
            ("tickets", "Tickets", 80),
            ("win", "Win rate", 90),
            ("mae", "Prediction MAE", 120),
            ("hit", "Direction hit", 110),
        ):
            tree.heading(name, text=title)
            tree.column(name, width=width, anchor="e" if name != "name" else "w")
        for row in self.model.summaries():
            tree.insert(
                "",
                "end",
                values=(
                    row.name,
                    self._money(row.equity),
                    self._money(row.max_drawdown),
                    row.tickets,
                    "-" if row.win_rate is None else f"{row.win_rate * 100:.1f}%",
                    "-" if row.mae is None else self._price_text(row.mae),
                    "-" if row.hit_rate is None else f"{row.hit_rate * 100:.1f}%",
                ),
            )
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(
            dialog,
            text="All scenarios share the replay cursor. Win rate counts closed trades.",
            bg=PANEL,
            fg=MUTED,
        ).pack(anchor="w", padx=8, pady=(0, 6))
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(anchor="e", padx=8, pady=8)

    def _open_inputs(self) -> None:
        opener: Callable[[], Any] | None = getattr(self.master, "open_inputs", None)
        if callable(opener):
            opener()
        else:
            messagebox.showinfo("X", "Expert inputs are available from X's File menu.")

    def _about(self) -> None:
        messagebox.showinfo(
            "X - Playground",
            "X Playground: replay real ticks, freeze simulated tickets, draw predictions and "
            "drawn tick tapes. Local only; no server and no network.",
        )

    def _fit_and_redraw(self) -> None:
        self._fit_view()
        self._refresh_all()

    def _on_configure(self, _event: tk.Event) -> None:
        self._redraw()

    def _on_left(self, _event: tk.Event) -> None:
        self._pan(-1)

    def _on_right(self, _event: tk.Event) -> None:
        self._pan(1)

    def _on_end(self, _event: tk.Event) -> None:
        self._fit_view()
        self._redraw()

    def _on_plus(self, _event: tk.Event) -> None:
        self._zoom(0.8)

    def _on_minus(self, _event: tk.Event) -> None:
        self._zoom(1.25)

    def _on_space(self, _event: tk.Event) -> None:
        self._advance(1)

    def _on_draw_key(self, _event: tk.Event) -> None:
        self._toggle_prediction()

    def _on_ticks_key(self, _event: tk.Event) -> None:
        self._toggle_ticks()

    def _on_double(self, _event: tk.Event) -> None:
        self._fit_view()
        self._redraw()

    def _pan(self, direction: int) -> None:
        step = max(1, self.view_count // 10)
        self.view_start = max(0, self.view_start + direction * step)
        self.follow = False
        self._redraw()

    def _zoom(self, factor: float) -> None:
        count = max(20, min(900, round(self.view_count * factor)))
        centre = self.view_start + self.view_count // 2
        self.view_start = max(0, centre - count // 2)
        self.view_count = count
        self.follow = False
        self._redraw()

    def _on_wheel(self, event: tk.Event) -> None:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        if plot_w <= 0:
            return
        fraction = max(0.0, min(1.0, (event.x - left) / plot_w))
        anchor = self.view_start + fraction * self.view_count
        factor = 1.2 if event.delta < 0 else 0.8
        count = max(20, min(900, round(self.view_count * factor)))
        self.view_start = max(0, round(anchor - fraction * count))
        self.view_count = count
        self.follow = False
        self.hover = None
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.drag_from is None and self.hover is not None:
            self.hover = None
            self._refresh_data_window()
            self._redraw()

    def _on_motion(self, event: tk.Event) -> None:
        if self.tick_stroke:
            self._add_tick_point(event.x, event.y)
            return
        if self.drag_from is not None:
            _left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
            if plot_w <= 0:
                return
            shift = round((event.x - self.drag_from) / (plot_w / self.view_count))
            self.view_start = max(0, self.drag_start - shift)
            self.follow = False
            self.hover = None
            self.drag_moved = self.drag_moved or abs(event.x - self.drag_from) > 2
            self._redraw()
            return
        index = self._series_index_at(event.x)
        if index != self.hover or abs(event.y - self.hover_y) > 3:
            self.hover = index
            self.hover_y = event.y
            self._refresh_data_window()
            self._redraw()

    def _on_press(self, event: tk.Event) -> None:
        if self.draw_ticks:
            self.tick_stroke = True
            self.stroke_view_start = self.view_start
            self.stroke_view_count = self.view_count
            self.stroke_start_count = len(self.model.custom_ticks)
            self._add_tick_point(event.x, event.y)
            return
        self.drag_from = event.x
        self.drag_start = self.view_start
        self.drag_moved = False
        self.canvas.configure(cursor="fleur")

    def _on_drag(self, event: tk.Event) -> None:
        self._on_motion(event)

    def _on_release(self, event: tk.Event) -> None:
        if self.tick_stroke:
            self.tick_stroke = False
            if len(self.model.custom_ticks) > self.stroke_start_count:
                self._fit_custom()
                self.message = "Drawn ticks added. Step forward to replay them."
            else:
                self.message = "Drag right into the future to draw ticks."
            self._refresh_all()
            return
        was_drag = self.drag_from is not None
        moved = self.drag_moved
        self.drag_from = None
        self.canvas.configure(cursor="crosshair")
        if was_drag and not moved and self.draw_prediction:
            self._add_prediction_at(event.x, event.y)

    def _series_index_at(self, x: int) -> int | None:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        if plot_w <= 0 or x < left or x > left + plot_w:
            return None
        raw = self.view_start + (x - left) / plot_w * self.view_count
        high = self.model.series_length() - 1
        return max(0, min(high, int(raw)))

    def _tick_index_at(self, x: int) -> int:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        raw = self.view_start + (x - left) / plot_w * self.view_count
        if self.model.period == "tick":
            return max(0, min(self.model.n - 1, int(raw)))
        spec = PERIODS[self.model.period]
        kind = str(spec["kind"])
        if kind == "tickbar":
            return max(0, min(self.model.n - 1, int(raw) * int(spec["count"])))
        bars = self.model.bars()
        if not bars:
            return 0
        bar_index = max(0, min(len(bars) - 1, int(raw)))
        span = int(spec["ms"])
        target_time = bars[bar_index].t + span // 2
        low = 0
        high = self.model.n
        while low < high:
            mid = (low + high) // 2
            if self.model.ticks[mid].ts_ms < target_time:
                low = mid + 1
            else:
                high = mid
        return max(0, min(self.model.n - 1, low))

    def _price_at(self, y: int) -> float:
        _left, top, _plot_w, plot_h, _width, _height = self._plot_box()
        low, high = self._range()
        return self._grid_price(low + (top + plot_h - y) / plot_h * (high - low))

    def _add_prediction_at(self, x: int, y: int) -> None:
        if not self.draw_prediction:
            return
        target = self._tick_index_at(x)
        if target <= self.model.cursor:
            self.message = "Draw ahead of the cursor; click farther right."
            self._refresh_status()
            return
        try:
            self.model.add_prediction(target, self._price_at(y))
        except ValueError as exc:
            self.message = str(exc)
            self._refresh_status()
            return
        self.message = "Prediction point added."
        self._refresh_all()

    def _add_tick_point(self, x: int, y: int) -> None:
        if not self.draw_ticks:
            return
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        if plot_w <= 0:
            return
        raw = self.stroke_view_start + (x - left) / plot_w * self.stroke_view_count
        end = self.model.custom_end_index()
        target = min(self.model.n + 200, int(raw))
        if target < end + 4:
            return
        self.model.add_custom_ticks(target, self._price_at(y))
        self.message = "Drawing ticks..."
        self._refresh_status()
        self._refresh_data_window()
        self._redraw()

    def _range(self) -> tuple[float, float]:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        low = float("inf")
        high = float("-inf")
        if self.model.period == "tick":
            start = max(0, self.view_start)
            end = min(self.model.cursor, self.view_start + self.view_count - 1)
            for index in range(start, end + 1):
                tick = self.model.ticks[index]
                low = min(low, tick.bid, tick.ask)
                high = max(high, tick.bid, tick.ask)
        else:
            bars = self.model.bars()
            start = max(0, self.view_start)
            end = min(len(bars) - 1, self.view_start + self.view_count - 1)
            for index in range(start, end + 1):
                bar = bars[index]
                low = min(low, bar.lo, bar.ac)
                high = max(high, bar.h, bar.ac)
        for index, price in self.model.active().prediction.points:
            if index <= self.model.n - 1:
                x = self._x(self.model.bar_index_for_tick(index))
                if left <= x <= left + plot_w:
                    low = min(low, price)
                    high = max(high, price)
        for index, tick in self.model.custom_preview():
            x = self._x(self.model.bar_index_for_tick(index))
            if left <= x <= left + plot_w:
                low = min(low, tick.bid)
                high = max(high, tick.bid)
        tick = self.model.tick()
        low = min(low, tick.ask)
        high = max(high, tick.ask)
        if not (low < float("inf") and high > float("-inf")):
            low = tick.bid - 1
            high = tick.bid + 1
        if high - low < 0.000001:
            low -= 0.5
            high += 0.5
        pad = (high - low) * 0.08
        return low - pad, high + pad

    def _x(self, index: float) -> float:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        return left + (index - self.view_start + 0.5) * (plot_w / self.view_count)

    def _y(self, price: float, low: float, high: float) -> float:
        _left, top, _plot_w, plot_h, _width, _height = self._plot_box()
        return top + (high - price) / (high - low) * plot_h

    def _time_text(self, ts_ms: int) -> str:
        moment = datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
        if self.model.period in ("tick", "t1", "t10", "t100", "t500", "t1000"):
            return moment.strftime("%H:%M:%S")
        return moment.strftime("%H:%M")

    def _price_text(self, value: float) -> str:
        return f"{value:.{self.digits}f}"

    def _money(self, value: float) -> str:
        return f"${value:,.2f}"

    def _tag(self, x: float, y: float, text: str, fill: str, color: str) -> None:
        left, _top, plot_w, _plot_h, width, _height = self._plot_box()
        left_edge = left + plot_w + 2
        tag_width = width - left_edge - 2
        self.canvas.create_rectangle(
            left_edge, y - 8, left_edge + tag_width, y + 8, fill=fill, outline=fill
        )
        self.canvas.create_text(
            left_edge + tag_width / 2,
            y,
            text=text,
            fill=color,
            font=FONT_SMALL,
        )

    def _redraw(self) -> None:
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        left, top, plot_w, plot_h, width, height = self._plot_box()
        if width < 80 or height < 80 or plot_w <= 0 or plot_h <= 0:
            return
        low, high = self._range()
        if self.model.period == "tick":
            start = max(0, self.view_start)
            end = min(self.model.cursor, self.view_start + self.view_count - 1)
        else:
            bars = self.model.bars()
            start = max(0, self.view_start)
            end = min(len(bars) - 1, self.view_start + self.view_count - 1)
        for step in range(7):
            gy = top + plot_h * step / 6
            self.canvas.create_line(left, gy, left + plot_w, gy, fill=GRID)
            price = high - (high - low) * step / 6
            self.canvas.create_text(
                left + plot_w + 6,
                gy,
                text=self._price_text(price),
                fill="#a8a8a8",
                font=FONT_SMALL,
                anchor="w",
            )
        step_bars = max(1, self.view_count // 8)
        for index in range(
            (self.view_start // step_bars) * step_bars,
            min(self.model.series_length(), self.view_start + self.view_count),
            step_bars,
        ):
            if index < 0:
                continue
            gx = self._x(index)
            if gx < left or gx > left + plot_w:
                continue
            self.canvas.create_line(gx, top, gx, top + plot_h, fill=GRID)
            ts = (
                self.model.ticks[index].ts_ms
                if self.model.period == "tick"
                else self.model.bars()[index].t
            )
            self.canvas.create_text(
                gx,
                top + plot_h + 4,
                text=self._time_text(ts),
                fill="#a8a8a8",
                font=FONT_SMALL,
                anchor="n",
            )
        if self.model.period == "tick":
            points: list[float] = []
            for index in range(start, end + 1):
                points.extend([self._x(index), self._y(self.model.ticks[index].bid, low, high)])
            if len(points) >= 4:
                self.canvas.create_line(*points, fill=UP, width=1)
        else:
            bars = self.model.bars()
            for index in range(start, end + 1):
                bar = bars[index]
                cx = self._x(index)
                color = UP if bar.c >= bar.o else DOWN
                self.canvas.create_line(
                    cx, self._y(bar.h, low, high), cx, self._y(bar.lo, low, high), fill=color
                )
                half = max(2.0, min(7.0, plot_w / self.view_count * 0.35))
                self.canvas.create_rectangle(
                    cx - half,
                    min(self._y(bar.o, low, high), self._y(bar.c, low, high)),
                    cx + half,
                    max(self._y(bar.o, low, high), self._y(bar.c, low, high)),
                    fill=color,
                    outline=color,
                )
            ask_points: list[float] = []
            for index in range(start, end + 1):
                ask_points.extend([self._x(index), self._y(bars[index].ac, low, high)])
            if len(ask_points) >= 4:
                self.canvas.create_line(*ask_points, fill=ASK, width=1)
        self._draw_custom(left, top, plot_w, plot_h, low, high)
        self._draw_prediction(left, top, plot_w, plot_h, low, high)
        if getattr(self, "both_ways", False):
            self._draw_both(left, top, plot_w, plot_h, low, high)
        tick = self.model.tick()
        bid_y = self._y(tick.bid, low, high)
        self.canvas.create_line(left, bid_y, left + plot_w, bid_y, fill="#707070", dash=(3, 3))
        self._tag(0, bid_y, self._price_text(tick.bid), UP, "#000000")
        cursor_x = self._x(self.model.series_length() - 1)
        self.canvas.create_line(cursor_x, top, cursor_x, top + plot_h, fill="#4a9eff", dash=(3, 3))
        self.canvas.create_text(
            cursor_x,
            top + 2,
            text="NOW",
            fill="#4a9eff",
            font=FONT_SMALL,
            anchor="n",
        )
        if self.hover is not None and start <= self.hover <= end:
            hx = self._x(self.hover)
            if self.model.period == "tick":
                price = self.model.ticks[self.hover].bid
            else:
                price = self.model.bars()[self.hover].c
            hy = self._y(price, low, high)
            self.canvas.create_line(hx, top, hx, top + plot_h, fill="#808080", dash=(2, 3))
            self.canvas.create_line(left, hy, left + plot_w, hy, fill="#808080", dash=(2, 3))
            self._tag(0, hy, self._price_text(price), "#505050", "#ffffff")
        self._draw_overlay(left, low, high)
        self._draw_draw_preview(left, top, plot_w, plot_h, low, high)

    def _draw_overlay(self, left: int, low: float, high: float) -> None:
        self.canvas.create_text(
            left + 4,
            4,
            text=f"{self.symbol}, {PERIOD_LABELS[self.model.period]}",
            fill=TEXT,
            anchor="nw",
            font=("Tahoma", 10, "bold"),
        )
        if self.model.period == "tick":
            tick = self.model.tick()
            self.canvas.create_text(
                left + 4,
                19,
                text=f"B {self._price_text(tick.bid)}  A {self._price_text(tick.ask)}  "
                f"S {self._price_text(tick.ask - tick.bid)}",
                fill=ASK,
                anchor="nw",
                font=FONT_SMALL,
            )
            return
        bars = self.model.bars()
        if not bars:
            return
        shown = bars[self.hover] if self.hover is not None and self.hover < len(bars) else bars[-1]
        self.canvas.create_text(
            left + 4,
            19,
            text=(
                f"O {self._price_text(shown.o)}  H {self._price_text(shown.h)}  "
                f"L {self._price_text(shown.lo)}  C {self._price_text(shown.c)}  V {shown.v}"
            ),
            fill="#b0b0b0",
            anchor="nw",
            font=FONT_SMALL,
        )
        self.canvas.create_text(
            left + 4,
            32,
            text=(
                f"B {self._price_text(shown.c)}  A {self._price_text(shown.ac)}  "
                f"S {self._price_text(shown.ac - shown.c)}"
            ),
            fill=ASK,
            anchor="nw",
            font=FONT_SMALL,
        )

    def _draw_custom(
        self, left: int, top: int, plot_w: int, plot_h: int, low: float, high: float
    ) -> None:
        preview = self.model.custom_preview()
        if not preview:
            return
        points: list[float] = []
        start_x = self._x(self.model.series_length() - 1)
        start_y = self._y(self.model.tick().bid, low, high)
        points.extend([start_x, start_y])
        for index, tick in preview:
            points.extend(
                [self._x(self.model.bar_index_for_tick(index)), self._y(tick.bid, low, high)]
            )
        if len(points) >= 4:
            self.canvas.create_line(*points, fill=DRAWN, width=1, dash=(4, 4))
        for index, tick in preview:
            x = self._x(self.model.bar_index_for_tick(index))
            y = self._y(tick.bid, low, high)
            self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=DRAWN, outline=DRAWN)

    def _draw_prediction(
        self, left: int, top: int, plot_w: int, plot_h: int, low: float, high: float
    ) -> None:
        scenario = self.model.active()
        prediction = scenario.prediction
        if not prediction.points:
            return
        anchor_index = prediction.anchor_index or 0
        anchor_price = prediction.anchor_price or self.model.ticks[anchor_index].bid
        points = [
            self._x(self.model.bar_index_for_tick(anchor_index)),
            self._y(anchor_price, low, high),
        ]
        for index, price in prediction.points:
            points.extend(
                [self._x(self.model.bar_index_for_tick(index)), self._y(price, low, high)]
            )
        if len(points) >= 4:
            self.canvas.create_line(*points, fill=PREDICT, width=2, dash=(5, 4))
        scored = {item.point: item for item in self.model.scored()}
        for index, price in prediction.points:
            x = self._x(self.model.bar_index_for_tick(index))
            y = self._y(price, low, high)
            item = scored.get((index, price))
            if item is None:
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, outline=PREDICT, fill=CHART_BG)
            else:
                color = UP if item.hit else DOWN
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)

    def _draw_both(
        self, left: int, top: int, plot_w: int, plot_h: int, low: float, high: float
    ) -> None:
        prediction = self.model.active().prediction
        future = [(i, p) for i, p in prediction.points if i > self.model.cursor]
        current = self.model.tick()
        start_x = self._x(self.model.series_length() - 1)
        start_y = self._y(current.bid, low, high)
        up = [(start_x, start_y)]
        down = [(start_x, start_y)]
        if future:
            for index, price in future:
                x = self._x(self.model.bar_index_for_tick(index))
                up.append((x, self._y(price, low, high)))
                mirror = current.bid - (price - current.bid)
                down.append((x, self._y(mirror, low, high)))
        else:
            right = left + plot_w - 2
            up.append((right, self._y(current.bid + 1, low, high)))
            down.append((right, self._y(current.bid - 1, low, high)))
        flat_up = [value for point in up for value in point]
        flat_down = [value for point in down for value in point]
        if len(flat_up) >= 4:
            self.canvas.create_line(*flat_up, fill=UP, width=1, dash=(3, 5))
        if len(flat_down) >= 4:
            self.canvas.create_line(*flat_down, fill=DOWN, width=1, dash=(3, 5))

    def _draw_draw_preview(
        self, left: int, top: int, plot_w: int, plot_h: int, low: float, high: float
    ) -> None:
        if not self.draw_prediction or self.hover is None:
            return
        if self.hover <= self.model.cursor:
            return
        price = self._price_at(self.hover_y)
        x = self._x(self.model.bar_index_for_tick(self.hover))
        y = self._y(price, low, high)
        prediction = self.model.active().prediction
        if prediction.points:
            index, last_price = prediction.points[-1]
            start_x = self._x(self.model.bar_index_for_tick(index))
            start_y = self._y(last_price, low, high)
        else:
            start_x = self._x(self.model.series_length() - 1)
            start_y = self._y(self.model.tick().bid, low, high)
        self.canvas.create_line(start_x, start_y, x, y, fill=PREDICT, width=1, dash=(2, 3))
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, outline=PREDICT)
        self.canvas.create_text(
            x,
            y - 12,
            text="ADD " + self._price_text(price),
            fill=PREDICT,
            font=FONT_SMALL,
        )

    def _refresh_all(self) -> None:
        tick = self.model.tick()
        self.bid_var.set(self._price_text(tick.bid))
        self.ask_var.set(self._price_text(tick.ask))
        self.spread_var.set("Spread " + self._price_text(tick.ask - tick.bid))
        self._refresh_data_window()
        self._refresh_replay()
        self._refresh_tickets()
        self._refresh_prediction()
        self._refresh_scenarios()
        self._refresh_status()
        self._redraw()

    def _refresh_data_window(self) -> None:
        period = PERIODS[self.model.period]
        self.dw_vars["period"].set(str(period["label"]))
        if self.model.period == "tick":
            index = self.hover if self.hover is not None else self.model.cursor
            tick = self.model.ticks[index]
            self.dw_labels["time"].configure(text="Tick time")
            self.dw_labels["open"].configure(text="Bid")
            self.dw_labels["high"].configure(text="Ask")
            self.dw_labels["low"].configure(text="Spread")
            self.dw_labels["close"].configure(text="Tick")
            self.dw_labels["change"].configure(text="Revealed")
            self.dw_labels["ticks"].configure(text="Day")
            self.dw_vars["time"].set(self._time_text(tick.ts_ms) + " UTC")
            self.dw_vars["open"].set(self._price_text(tick.bid))
            self.dw_vars["high"].set(self._price_text(tick.ask))
            self.dw_vars["low"].set(self._price_text(tick.ask - tick.bid))
            self.dw_vars["close"].set(str(index + 1))
            self.dw_vars["change"].set(f"{self.model.cursor + 1} / {self.model.n}")
            self.dw_vars["ticks"].set(str(self.day))
            return
        bars = self.model.bars()
        if not bars:
            return
        index = self.hover if self.hover is not None and self.hover < len(bars) else len(bars) - 1
        bar = bars[index]
        self.dw_labels["time"].configure(text="Bar time")
        self.dw_labels["open"].configure(text="Open")
        self.dw_labels["high"].configure(text="High")
        self.dw_labels["low"].configure(text="Low")
        self.dw_labels["close"].configure(text="Close")
        self.dw_labels["change"].configure(text="Change")
        self.dw_labels["ticks"].configure(text="Ticks")
        self.dw_vars["time"].set(self._time_text(bar.t) + " UTC")
        self.dw_vars["open"].set(self._price_text(bar.o))
        self.dw_vars["high"].set(self._price_text(bar.h))
        self.dw_vars["low"].set(self._price_text(bar.lo))
        self.dw_vars["close"].set(self._price_text(bar.c))
        self.dw_vars["change"].set(f"{bar.c - bar.o:+.{self.digits}f}")
        self.dw_vars["ticks"].set(str(bar.v))

    def _refresh_replay(self) -> None:
        self.rp_vars["cursor"].set(self._time_text(self.model.tick().ts_ms) + " UTC")
        self.rp_vars["tick"].set(f"{self.model.cursor + 1:,} / {self.model.n:,}")
        self.rp_vars["revealed"].set(f"{self.model.cursor + 1:,} of {self.model.n:,}")
        unit = "ticks" if self.model.period == "tick" else "bars"
        self.rp_vars["view"].set(f"{self.view_count} {unit}")

    def _refresh_tickets(self) -> None:
        self.ticket_tree.delete(*self.ticket_tree.get_children())
        scenario = self.model.active()
        tick = self.model.tick()
        for ticket in reversed(scenario.tickets):
            if ticket.status == "open":
                profit = self.model.ticket_pnl(
                    ticket, tick.bid if ticket.side == "buy" else tick.ask
                )
                state = "open"
            else:
                profit = ticket.realized
                state = ticket.close_reason or "closed"
            self.ticket_tree.insert(
                "",
                "end",
                iid=str(ticket.id),
                values=(
                    self._time_text(self.model.ticks[ticket.open_index].ts_ms),
                    ticket.side,
                    f"{ticket.lots:.2f}",
                    self._price_text(ticket.entry),
                    "-" if ticket.sl is None else self._price_text(ticket.sl),
                    "-" if ticket.tp is None else self._price_text(ticket.tp),
                    self._money(profit),
                    state,
                ),
            )
        balance = self.model.balance()
        floating = self.model.floating()
        self.balance_label.configure(text="Balance " + self._money(balance))
        self.floating_label.configure(text="Floating " + self._money(floating))
        self.equity_label.configure(text="Equity " + self._money(balance + floating))
        self.trade_message.configure(text=self.message)

    def _refresh_prediction(self) -> None:
        summary = self.model.prediction_summary()
        points = len(self.model.active().prediction.points)
        if points == 0:
            self.prediction_label.configure(
                text="No prediction points. Draw prediction and click ahead."
            )
        else:
            mae = "-" if summary.mae is None else self._price_text(summary.mae)
            hit = "-" if summary.hit_rate is None else f"{summary.hit_rate * 100:.1f}%"
            self.prediction_label.configure(
                text=f"Points {points} · reached {summary.count} · MAE {mae} · direction {hit}"
            )
        scenario = self.model.active()
        open_tickets = [ticket for ticket in scenario.tickets if ticket.status == "open"]
        if not open_tickets:
            self.move_preview.configure(text="No open tickets to preview.")
        else:
            try:
                move = abs(float(self.move_var.get()))
            except ValueError:
                move = 1.0
            tick = self.model.tick()
            up = sum(
                self.model.ticket_pnl(
                    ticket, tick.bid + move if ticket.side == "buy" else tick.ask + move
                )
                for ticket in open_tickets
            )
            down = sum(
                self.model.ticket_pnl(
                    ticket, tick.bid - move if ticket.side == "buy" else tick.ask - move
                )
                for ticket in open_tickets
            )
            self.move_preview.configure(
                text=f"At +${move:.2f}: {self._money(up)}   At -${move:.2f}: {self._money(down)}"
            )

    def _refresh_scenarios(self) -> None:
        names = [scenario.name for scenario in self.model.scenarios]
        self.scenario_combo.configure(values=names)
        self.scenario_var.set(self.model.active().name)
        self.scenario_tree.delete(*self.scenario_tree.get_children())
        for row in self.model.summaries():
            self.scenario_tree.insert(
                "",
                "end",
                values=(
                    row.name,
                    self._money(row.equity),
                    self._money(row.max_drawdown),
                    row.tickets,
                    "-" if row.win_rate is None else f"{row.win_rate * 100:.1f}%",
                    "-" if row.mae is None else self._price_text(row.mae),
                    "-" if row.hit_rate is None else f"{row.hit_rate * 100:.1f}%",
                ),
            )

    def _refresh_status(self) -> None:
        period = PERIODS[self.model.period]
        center = (
            f"{self.symbol} · {period['label']} · {self.model.series_length()} "
            f"{'ticks' if self.model.period == 'tick' else 'bars'} · tick "
            f"{self.model.cursor + 1:,} / {self.model.n:,}"
        )
        if self.model.custom_ticks:
            center += " · drawn tape"
        self.status_center.configure(text=self.message or center)
        if self.model.custom_ticks:
            self.status_right.configure(
                text=f"{len(self.model.real_ticks):,} real + {len(self.model.custom_ticks):,} drawn"
            )
        else:
            self.status_right.configure(text=f"{self.model.n:,} Dukascopy ticks · UTC")
        self.clear_ticks_button.configure(state="normal" if self.model.custom_ticks else "disabled")
