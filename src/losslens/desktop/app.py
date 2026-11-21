"""The X desktop app: a native window, no browser and no server."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from losslens.mt4.presets import ExpertInput, read_inputs, render_set

from .chart import Bar, ChartData, aggregate, load_chart_data, price_text, time_text
from .playground import PlaygroundWindow

TF_LABEL = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4", 1440: "D1"}
CHART_BG = "#000000"
UP = "#00c000"
DOWN = "#ff4040"
ASK = "#ff9090"
GRID = "#1a1a1a"
TEXT = "#d0d0d0"
MUTED = "#888888"


class XApp(tk.Tk):
    def __init__(self, data: ChartData, inputs: tuple[ExpertInput, ...]) -> None:
        super().__init__()
        self.data = data
        self.inputs = inputs
        self.playground: PlaygroundWindow | None = None
        self.title("X")
        self.geometry("1400x900")
        self.minsize(900, 600)
        self.configure(bg="#f0f0f0")
        self.tf = 1
        self.bars: list[Bar] = list(data.bid_bars)
        self.ask_bars: list[Bar] = list(data.ask_bars)
        self.view_count = min(len(self.bars), 180)
        self.view_start = max(0, len(self.bars) - self.view_count)
        self.hover: int | None = None
        self.drag_from: int | None = None
        self.drag_start = 0
        self.tf_buttons: dict[int, tk.Button] = {}
        self._build_menu()
        self._build_toolbar()
        self._build_status()
        self._build_terminal()
        self._build_main()
        self.bind("<Left>", self._left)
        self.bind("<Right>", self._right)
        self.bind("<End>", self._end)
        self.bind("<plus>", self._plus)
        self.bind("<minus>", self._minus)
        self.after(60, self.redraw)

    def _left(self, _event: tk.Event) -> None:
        self._pan(-1)

    def _right(self, _event: tk.Event) -> None:
        self._pan(1)

    def _end(self, _event: tk.Event) -> None:
        self._jump_end()

    def _plus(self, _event: tk.Event) -> None:
        self._zoom(0.8)

    def _minus(self, _event: tk.Event) -> None:
        self._zoom(1.25)

    def _on_configure(self, _event: tk.Event) -> None:
        self.redraw()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Playground", command=self.open_playground)
        file_menu.add_command(label="Expert Inputs...", command=self.open_inputs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        view_menu = tk.Menu(menubar, tearoff=False)
        for minutes, label in TF_LABEL.items():
            view_menu.add_command(label=label, command=partial(self.set_tf, minutes))
        view_menu.add_separator()
        view_menu.add_command(label="End", command=self._jump_end)
        menubar.add_cascade(label="View", menu=view_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About X", command=self._about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self, bg="#f0f0f0", bd=1, relief="raised")
        bar.pack(side="top", fill="x")
        for minutes, label in TF_LABEL.items():
            button = tk.Button(
                bar,
                text=label,
                width=4,
                relief="sunken" if minutes == 1 else "raised",
                command=partial(self.set_tf, minutes),
            )
            button.pack(side="left", padx=1, pady=2)
            self.tf_buttons[minutes] = button
        tk.Button(bar, text="Playground", width=10, command=self.open_playground).pack(
            side="left", padx=(8, 1), pady=2
        )
        tk.Button(bar, text="Inputs", width=7, command=self.open_inputs).pack(
            side="left", padx=1, pady=2
        )
        tk.Label(
            bar,
            text="Wheel zoom  ·  drag to pan  ·  arrows move",
            bg="#f0f0f0",
            fg=MUTED,
        ).pack(side="left", padx=10)

    def _build_status(self) -> None:
        self.status = tk.Frame(self, bg="#f0f0f0", bd=1, relief="raised")
        self.status.pack(side="bottom", fill="x")
        self.status_left = tk.Label(
            self.status, text="Local only · nothing is sent", bg="#f0f0f0", fg=MUTED
        )
        self.status_left.pack(side="left", padx=6)
        self.status_right = tk.Label(self.status, text="", bg="#f0f0f0", fg=MUTED)
        self.status_right.pack(side="right", padx=6)
        self.status_center = tk.Label(self.status, text="", bg="#f0f0f0", fg=MUTED)
        self.status_center.pack(side="left", padx=12)

    def _build_terminal(self) -> None:
        frame = tk.Frame(self, height=150, bg="white", bd=1, relief="raised")
        frame.pack(side="bottom", fill="x")
        frame.pack_propagate(False)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)
        journal = tk.Text(notebook, height=5, borderwidth=0, font=("Tahoma", 9))
        journal.insert(
            "1.0",
            f"X · {self.data.symbol} · {self.data.day.isoformat()}\n"
            f"{self.data.ticks:,} stored ticks · server UTC+{self.data.offset_hours}\n"
            "Local desktop app. Nothing is downloaded and nothing is sent.",
        )
        journal.configure(state="disabled")
        notebook.add(journal, text="Journal")
        for name in ("Trade", "Exposure", "Account History", "News", "Alerts", "Experts"):
            empty = tk.Text(notebook, height=5, borderwidth=0, font=("Tahoma", 9))
            empty.insert("1.0", f"No {name.lower()} in this build.")
            empty.configure(state="disabled")
            notebook.add(empty, text=name)

    def _build_main(self) -> None:
        main = tk.Frame(self, bg="#f0f0f0")
        main.pack(side="top", fill="both", expand=True)
        left = tk.Frame(main, width=190, bg="white", bd=1, relief="raised")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(
            left,
            text="Market Watch",
            bg="#e4e4e4",
            anchor="w",
            padx=6,
            pady=4,
            font=("Tahoma", 9, "bold"),
        ).pack(fill="x")
        row = tk.Frame(left, bg="white")
        row.pack(fill="x", pady=(6, 0))
        tk.Label(row, text=self.data.symbol, bg="white", anchor="w", width=9).pack(
            side="left", padx=6
        )
        self.bid_label = tk.Label(
            row,
            text=price_text(self.data.last_bid, self.data.digits),
            bg="white",
            anchor="e",
            width=10,
        )
        self.bid_label.pack(side="left")
        self.ask_label = tk.Label(
            row,
            text=price_text(self.data.last_ask, self.data.digits),
            bg="white",
            anchor="e",
            width=10,
        )
        self.ask_label.pack(side="left")
        self.spread_label = tk.Label(
            left,
            text="Spread " + price_text(self.data.last_ask - self.data.last_bid, self.data.digits),
            bg="white",
            anchor="w",
            fg=MUTED,
        )
        self.spread_label.pack(fill="x", padx=6, pady=(4, 0))
        self.canvas = tk.Canvas(main, bg=CHART_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Leave>", self._on_leave)
        self._update_status()

    def set_tf(self, minutes: int) -> None:
        self.tf = minutes
        self.bars = aggregate(self.data.bid_bars, minutes)
        self.ask_bars = aggregate(self.data.ask_bars, minutes)
        self.view_count = min(len(self.bars), 180)
        self.view_start = max(0, len(self.bars) - self.view_count)
        self.hover = None
        for value, button in self.tf_buttons.items():
            button.configure(relief="sunken" if value == minutes else "raised")
        self._update_status()
        self.redraw()

    def _update_status(self) -> None:
        self.status_center.configure(
            text=f"{self.data.symbol} · {TF_LABEL[self.tf]} · {len(self.bars):,} bars"
        )
        self.status_right.configure(
            text=f"{self.data.ticks:,} ticks · server UTC+{self.data.offset_hours}"
        )

    def _plot_box(self) -> tuple[int, int, int, int, int, int]:
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        left, right, top, bottom = 8, 68, 30, 24
        return left, top, width - left - right, height - top - bottom, width, height

    def _index_at(self, x: int) -> int | None:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        if plot_w <= 0 or x < left or x > left + plot_w:
            return None
        index = self.view_start + int((x - left) / (plot_w / self.view_count))
        return max(0, min(len(self.bars) - 1, index))

    def _on_motion(self, event: tk.Event) -> None:
        if self.drag_from is not None:
            left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
            if plot_w <= 0:
                return
            shift = round((event.x - self.drag_from) / (plot_w / self.view_count))
            self.view_start = max(0, min(len(self.bars) - self.view_count, self.drag_start - shift))
            self.hover = None
            self.redraw()
            return
        index = self._index_at(event.x)
        if index != self.hover:
            self.hover = index
            self.redraw()

    def _on_press(self, event: tk.Event) -> None:
        self.drag_from = event.x
        self.drag_start = self.view_start
        self.canvas.configure(cursor="fleur")

    def _on_drag(self, event: tk.Event) -> None:
        self._on_motion(event)

    def _on_release(self, _event: tk.Event) -> None:
        self.drag_from = None
        self.canvas.configure(cursor="crosshair")

    def _on_leave(self, _event: tk.Event) -> None:
        if self.drag_from is None and self.hover is not None:
            self.hover = None
            self.redraw()

    def _on_wheel(self, event: tk.Event) -> None:
        left, _top, plot_w, _plot_h, _width, _height = self._plot_box()
        if plot_w <= 0:
            return
        fraction = max(0.0, min(1.0, (event.x - left) / plot_w))
        anchor = self.view_start + fraction * self.view_count
        factor = 1.2 if event.delta < 0 else 0.8
        minimum = min(20, len(self.bars))
        count = max(minimum, min(len(self.bars), round(self.view_count * factor)))
        self.view_start = max(0, min(len(self.bars) - count, round(anchor - fraction * count)))
        self.view_count = count
        self.hover = None
        self.redraw()

    def _pan(self, direction: int) -> None:
        step = max(1, self.view_count // 10)
        self.view_start = max(
            0,
            min(
                len(self.bars) - self.view_count,
                self.view_start + direction * step,
            ),
        )
        self.redraw()

    def _jump_end(self) -> None:
        self.view_start = max(0, len(self.bars) - self.view_count)
        self.redraw()

    def _zoom(self, factor: float) -> None:
        minimum = min(20, len(self.bars))
        count = max(minimum, min(len(self.bars), round(self.view_count * factor)))
        center = self.view_start + self.view_count // 2
        self.view_start = max(0, min(len(self.bars) - count, center - count // 2))
        self.view_count = count
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")
        left, top, plot_w, plot_h, width, height = self._plot_box()
        if width < 80 or height < 80 or plot_w <= 0 or plot_h <= 0 or not self.bars:
            return
        visible = self.bars[self.view_start : self.view_start + self.view_count]
        if not visible:
            return
        low = min(bar.lo for bar in visible)
        high = max(bar.h for bar in visible)
        span = high - low or 0.5
        low -= span * 0.08
        high += span * 0.08
        digits = self.data.digits

        def y(price: float) -> float:
            return top + (high - price) / (high - low) * plot_h

        def x(index: int) -> float:
            return left + (index - self.view_start + 0.5) * (plot_w / self.view_count)

        for step in range(7):
            gy = top + plot_h * step / 6
            self.canvas.create_line(left, gy, left + plot_w, gy, fill=GRID)
            price = high - (high - low) * step / 6
            self.canvas.create_text(
                left + plot_w + 6,
                gy,
                text=price_text(price, digits),
                fill="#a8a8a8",
                anchor="w",
                font=("Tahoma", 8),
            )
        step_bars = max(1, self.view_count // 8)
        for index in range(
            (self.view_start // step_bars) * step_bars,
            min(len(self.bars), self.view_start + self.view_count),
            step_bars,
        ):
            if index < 0:
                continue
            gx = x(index)
            if gx < left or gx > left + plot_w:
                continue
            self.canvas.create_line(gx, top, gx, top + plot_h, fill=GRID)
            self.canvas.create_text(
                gx,
                top + plot_h + 4,
                text=time_text(self.bars[index].t, self.tf),
                fill="#a8a8a8",
                anchor="n",
                font=("Tahoma", 8),
            )
        bar_width = plot_w / self.view_count
        body = max(1, min(14, bar_width * 0.68))
        for index in range(self.view_start, min(len(self.bars), self.view_start + self.view_count)):
            bar = self.bars[index]
            cx = x(index)
            color = UP if bar.c >= bar.o else DOWN
            self.canvas.create_line(cx, y(bar.h), cx, y(bar.lo), fill=color)
            self.canvas.create_rectangle(
                cx - body / 2,
                min(y(bar.o), y(bar.c)),
                cx + body / 2,
                max(y(bar.o), y(bar.c)),
                fill=color,
                outline=color,
            )
        if len(self.ask_bars) == len(self.bars):
            points: list[float] = []
            for index in range(
                self.view_start, min(len(self.bars), self.view_start + self.view_count)
            ):
                points.extend([x(index), y(self.ask_bars[index].c)])
            if len(points) >= 4:
                self.canvas.create_line(*points, fill=ASK, width=1)
        last = self.bars[-1]
        last_y = y(last.c)
        self.canvas.create_line(left, last_y, left + plot_w, last_y, fill="#707070", dash=(3, 3))
        self.canvas.create_rectangle(
            left + plot_w + 2,
            last_y - 8,
            width - 2,
            last_y + 8,
            fill=UP,
            outline=UP,
        )
        self.canvas.create_text(
            left + plot_w + 2 + (width - left - plot_w - 4) / 2,
            last_y,
            text=price_text(last.c, digits),
            fill="#000000",
            font=("Tahoma", 8),
        )
        if self.hover is not None and 0 <= self.hover < len(self.bars):
            hx = x(self.hover)
            hy = y(self.bars[self.hover].c)
            self.canvas.create_line(hx, top, hx, top + plot_h, fill="#808080", dash=(2, 3))
            self.canvas.create_line(left, hy, left + plot_w, hy, fill="#808080", dash=(2, 3))
            self.canvas.create_text(
                hx,
                top + plot_h + 4,
                text=time_text(self.bars[self.hover].t, self.tf),
                fill="#e0e0e0",
                anchor="n",
                font=("Tahoma", 8),
            )
            self.canvas.create_rectangle(
                left + plot_w + 2, hy - 8, width - 2, hy + 8, fill="#505050", outline="#505050"
            )
            self.canvas.create_text(
                left + plot_w + 2 + (width - left - plot_w - 4) / 2,
                hy,
                text=price_text(self.bars[self.hover].c, digits),
                fill="#ffffff",
                font=("Tahoma", 8),
            )
        shown = self.bars[self.hover] if self.hover is not None else last
        ask = (
            self.ask_bars[self.hover]
            if self.hover is not None and self.hover < len(self.ask_bars)
            else self.ask_bars[-1]
        )
        self.canvas.create_text(
            left + 4,
            4,
            anchor="nw",
            text=f"{self.data.symbol}, {TF_LABEL[self.tf]}",
            fill=TEXT,
            font=("Tahoma", 10, "bold"),
        )
        self.canvas.create_text(
            left + 4,
            19,
            anchor="nw",
            text=(
                f"O {price_text(shown.o, digits)}  H {price_text(shown.h, digits)}  "
                f"L {price_text(shown.lo, digits)}  C {price_text(shown.c, digits)}  V {shown.v}"
            ),
            fill="#b0b0b0",
            font=("Tahoma", 8),
        )
        self.canvas.create_text(
            left + 4,
            32,
            anchor="nw",
            text=(
                f"B {price_text(shown.c, digits)}  A {price_text(ask.c, digits)}  "
                f"S {price_text(ask.c - shown.c, digits)}"
            ),
            fill=ASK,
            font=("Tahoma", 8),
        )

    def open_playground(self) -> None:
        if self.playground is not None and self.playground.winfo_exists():
            self.playground.deiconify()
            self.playground.lift()
            self.playground.focus_set()
            return
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            self.playground = PlaygroundWindow(self, self.data.symbol, self.data.day, self.inputs)
        except (OSError, ValueError) as exc:
            messagebox.showerror("X", f"Cannot open the Playground: {exc}", parent=self)
        finally:
            self.configure(cursor="")

    def open_inputs(self) -> None:
        if not self.inputs:
            messagebox.showinfo(
                "X",
                "No expert inputs loaded.\nStart X with:  x desktop --inputs expert.set",
                parent=self,
            )
            return
        dialog = tk.Toplevel(self)
        dialog.title("Expert Inputs")
        dialog.transient(self)
        dialog.configure(bg="#f0f0f0")
        tk.Label(dialog, text="Input", bg="#f0f0f0", anchor="w").grid(
            row=0, column=0, sticky="w", padx=4, pady=2
        )
        for column, label in enumerate(("Value", "Start", "Step", "Stop"), start=1):
            tk.Label(dialog, text=label, bg="#f0f0f0", anchor="w").grid(
                row=0, column=column, sticky="w", padx=4, pady=2
            )
        variables: list[tuple[ExpertInput, list[tk.StringVar]]] = []
        for row, item in enumerate(self.inputs, start=1):
            tk.Label(dialog, text=item.name, bg="#f0f0f0", anchor="w").grid(
                row=row, column=0, sticky="w", padx=4, pady=2
            )
            values = [
                tk.StringVar(dialog, value=item.value),
                tk.StringVar(dialog, value=item.start or ""),
                tk.StringVar(dialog, value=item.step or ""),
                tk.StringVar(dialog, value=item.stop or ""),
            ]
            variables.append((item, values))
            for column, variable in enumerate(values, start=1):
                tk.Entry(dialog, textvariable=variable, width=12).grid(
                    row=row, column=column, padx=4, pady=2
                )

        def save() -> None:
            path = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".set",
                filetypes=[("MT4 preset", "*.set")],
                initialfile="expert.set",
            )
            if not path:
                return
            updated = tuple(
                ExpertInput(
                    item.name,
                    values[0].get(),
                    values[1].get() or None,
                    values[2].get() or None,
                    values[3].get() or None,
                )
                for item, values in variables
            )
            Path(path).write_text(render_set(updated), encoding="utf-8", newline="\n")
            messagebox.showinfo("X", f"Saved {path}", parent=dialog)

        tk.Button(dialog, text="Save .set", command=save).grid(
            row=len(self.inputs) + 1, column=3, padx=4, pady=8, sticky="e"
        )
        tk.Button(dialog, text="Close", command=dialog.destroy).grid(
            row=len(self.inputs) + 1, column=4, padx=4, pady=8, sticky="e"
        )

    def _about(self) -> None:
        messagebox.showinfo(
            "About X",
            "X — local tick and trade analysis.\nNo browser, no server, no network.",
            parent=self,
        )


def run_desktop(symbol: str, day: date, inputs_path: Path | None = None) -> None:
    data = load_chart_data(symbol, day)
    inputs = read_inputs(inputs_path) if inputs_path is not None else ()
    app = XApp(data, inputs)
    app.mainloop()
