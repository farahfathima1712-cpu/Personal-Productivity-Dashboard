"""Personal Productivity Dashboard - Python + Tkinter (no external packages).
Run:  python productivity_dashboard.py
Data is saved to dashboard_data.json next to this file.
"""
import calendar
import json
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox

DATA_FILE = Path(__file__).with_name("dashboard_data.json")

BG = "#F4F6FB"
SIDEBAR = "#1E2235"
SIDEBAR_HOVER = "#2B3050"
ACCENT = "#5B6CFF"
CARD = "#FFFFFF"
TEXT = "#1F2437"
MUTED = "#7A8197"
GREEN = "#2FBF71"
RED = "#E5484D"
AMBER = "#F5A524"

FONT = ("Segoe UI", 11)
FONT_B = ("Segoe UI", 11, "bold")
FONT_H1 = ("Segoe UI", 22, "bold")
FONT_H2 = ("Segoe UI", 14, "bold")
FONT_BIG = ("Segoe UI", 28, "bold")


# ---------------------------------------------------------------- data layer
def today_str(d=None):
    return (d or date.today()).isoformat()


def load_data():
    default = {"tasks": [], "planner": {}, "notes": [], "habits": [], "pomodoro": {}}
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            for k, v in default.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return default


def save_data(data):
    try:
        DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        messagebox.showerror("Save failed", str(e))


# ---------------------------------------------------------------- UI helpers
def lighten(hex_color, amt=18):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, c + amt) for c in (r, g, b))


def button(parent, text, cmd, bg=ACCENT, fg="white", padx=16, pady=7):
    b = tk.Label(parent, text=text, bg=bg, fg=fg, font=FONT_B,
                 padx=padx, pady=pady, cursor="hand2")
    b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>", lambda e: b.config(bg=lighten(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def entry(parent, width=30):
    return tk.Entry(parent, font=FONT, width=width, relief="flat", bg="white",
                    fg=TEXT, insertbackground=TEXT, highlightthickness=1,
                    highlightbackground="#D8DCEA", highlightcolor=ACCENT)


def listbox(parent, **kw):
    return tk.Listbox(parent, font=FONT, relief="flat", bg="white", fg=TEXT,
                      highlightthickness=1, highlightbackground="#D8DCEA",
                      selectbackground=ACCENT, selectforeground="white",
                      activestyle="none", **kw)


def stat_card(parent, title, value, color=ACCENT):
    c = tk.Frame(parent, bg=CARD, padx=18, pady=14,
                 highlightthickness=1, highlightbackground="#E3E6F0")
    tk.Frame(c, bg=color, height=4).pack(fill="x", pady=(0, 10))
    tk.Label(c, text=str(value), font=FONT_BIG, bg=CARD, fg=TEXT).pack(anchor="w")
    tk.Label(c, text=title, font=FONT, bg=CARD, fg=MUTED).pack(anchor="w")
    return c


class Page(tk.Frame):
    title = ""
    subtitle = ""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.data = app.data
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=30, pady=(24, 10))
        tk.Label(head, text=self.title, font=FONT_H1, bg=BG, fg=TEXT).pack(anchor="w")
        if self.subtitle:
            tk.Label(head, text=self.subtitle, font=FONT, bg=BG, fg=MUTED).pack(anchor="w")
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self.build()

    def build(self):
        pass

    def refresh(self):
        pass

    def save(self):
        save_data(self.data)

    def clear_body(self):
        for w in self.body.winfo_children():
            w.destroy()


# ---------------------------------------------------------------- pages
class Dashboard(Page):
    title = "Dashboard"

    def build(self):
        self.subtitle_lbl = None

    def refresh(self):
        self.clear_body()
        d = self.data
        t = today_str()
        done_today = sum(1 for x in d["tasks"] if x.get("done_on") == t)
        pending = sum(1 for x in d["tasks"] if not x["done"])
        focus = d["pomodoro"].get(t, 0)
        habits_done = sum(1 for h in d["habits"] if t in h["log"])
        habits_total = len(d["habits"])

        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x")
        cards = [("Tasks done today", done_today, GREEN), ("Tasks pending", pending, AMBER),
                 ("Focus sessions today", focus, ACCENT),
                 ("Habits today", f"{habits_done}/{habits_total}", "#B05CFF")]
        for i, (title, val, col) in enumerate(cards):
            row.columnconfigure(i, weight=1, uniform="c")
            stat_card(row, title, val, col).grid(row=0, column=i, sticky="nsew",
                                                 padx=(0 if i == 0 else 12, 0))

        lower = tk.Frame(self.body, bg=BG)
        lower.pack(fill="both", expand=True, pady=(20, 0))
        lower.columnconfigure((0, 1), weight=1, uniform="l")
        lower.rowconfigure(0, weight=1)

        left = self._panel(lower, "Upcoming tasks", 0)
        open_tasks = sorted((x for x in d["tasks"] if not x["done"]),
                            key=lambda x: x.get("due") or "9999")
        if not open_tasks:
            tk.Label(left, text="Nothing pending. Nice!", font=FONT, bg=CARD, fg=MUTED).pack(anchor="w")
        for x in open_tasks[:8]:
            due = x.get("due")
            overdue = due and due < t
            txt = x["text"] + (f"   (due {due})" if due else "")
            tk.Label(left, text="• " + txt, font=FONT, bg=CARD,
                     fg=RED if overdue else TEXT, anchor="w").pack(fill="x", pady=2)

        right = self._panel(lower, "Today's plan", 1)
        plan = sorted(d["planner"].get(t, []), key=lambda x: x["time"])
        if not plan:
            tk.Label(right, text="No activities planned.", font=FONT, bg=CARD, fg=MUTED).pack(anchor="w")
        for p in plan[:8]:
            tk.Label(right, text=f"{p['time']}   {p['text']}", font=FONT, bg=CARD,
                     fg=TEXT, anchor="w").pack(fill="x", pady=2)

    def _panel(self, parent, title, col):
        p = tk.Frame(parent, bg=CARD, padx=18, pady=14,
                     highlightthickness=1, highlightbackground="#E3E6F0")
        p.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 12, 0))
        tk.Label(p, text=title, font=FONT_H2, bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 8))
        return p


class TodoPage(Page):
    title = "To-Do List"
    subtitle = "Add tasks, mark them done, delete them."

    def build(self):
        bar = tk.Frame(self.body, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        self.e_task = entry(bar, 36)
        self.e_task.pack(side="left", ipady=6)
        self.e_task.bind("<Return>", lambda e: self.add())
        tk.Label(bar, text="Due (YYYY-MM-DD)", font=FONT, bg=BG, fg=MUTED).pack(side="left", padx=(12, 6))
        self.e_due = entry(bar, 12)
        self.e_due.pack(side="left", ipady=6)
        button(bar, "Add", self.add).pack(side="left", padx=12)

        self.lb = listbox(self.body)
        self.lb.pack(fill="both", expand=True)
        acts = tk.Frame(self.body, bg=BG)
        acts.pack(fill="x", pady=(12, 0))
        button(acts, "Toggle done", self.toggle, GREEN).pack(side="left")
        button(acts, "Delete", self.delete, RED).pack(side="left", padx=10)
        self.view = []

    def add(self):
        text = self.e_task.get().strip()
        due = self.e_due.get().strip()
        if not text:
            return
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid date", "Use the format YYYY-MM-DD.")
                return
        self.data["tasks"].append({"text": text, "done": False, "due": due or None,
                                   "created": today_str(), "done_on": None})
        self.e_task.delete(0, "end")
        self.e_due.delete(0, "end")
        self.save()
        self.refresh()

    def selected(self):
        sel = self.lb.curselection()
        return self.view[sel[0]] if sel else None

    def toggle(self):
        t = self.selected()
        if t is None:
            return
        t["done"] = not t["done"]
        t["done_on"] = today_str() if t["done"] else None
        self.save()
        self.refresh()

    def delete(self):
        t = self.selected()
        if t is None:
            return
        self.data["tasks"].remove(t)
        self.save()
        self.refresh()

    def refresh(self):
        self.lb.delete(0, "end")
        self.view = sorted(self.data["tasks"], key=lambda x: (x["done"], x.get("due") or "9999"))
        for i, t in enumerate(self.view):
            mark = "☑" if t["done"] else "☐"
            due = f"   (due {t['due']})" if t.get("due") else ""
            self.lb.insert("end", f"  {mark}  {t['text']}{due}")
            if t["done"]:
                self.lb.itemconfig(i, fg=MUTED)
            elif t.get("due") and t["due"] < today_str():
                self.lb.itemconfig(i, fg=RED)


class PlannerPage(Page):
    title = "Daily Planner"
    subtitle = "Organise your day by time."

    def build(self):
        self.day = date.today()
        nav = tk.Frame(self.body, bg=BG)
        nav.pack(fill="x", pady=(0, 12))
        button(nav, "◀", lambda: self.shift(-1), CARD, TEXT, 12).pack(side="left")
        self.lbl = tk.Label(nav, font=FONT_H2, bg=BG, fg=TEXT, width=22)
        self.lbl.pack(side="left", padx=8)
        button(nav, "▶", lambda: self.shift(1), CARD, TEXT, 12).pack(side="left")
        button(nav, "Today", self.go_today, ACCENT).pack(side="left", padx=12)

        add = tk.Frame(self.body, bg=BG)
        add.pack(fill="x", pady=(0, 12))
        tk.Label(add, text="Time (HH:MM)", font=FONT, bg=BG, fg=MUTED).pack(side="left", padx=(0, 6))
        self.e_time = entry(add, 8)
        self.e_time.pack(side="left", ipady=6)
        self.e_text = entry(add, 40)
        self.e_text.pack(side="left", ipady=6, padx=10)
        self.e_text.bind("<Return>", lambda e: self.add())
        button(add, "Add", self.add).pack(side="left")

        self.lb = listbox(self.body)
        self.lb.pack(fill="both", expand=True)
        button(self.body, "Delete selected", self.delete, RED).pack(anchor="w", pady=(12, 0))
        self.view = []

    def shift(self, n):
        self.day += timedelta(days=n)
        self.refresh()

    def go_today(self):
        self.day = date.today()
        self.refresh()

    def add(self):
        tm, text = self.e_time.get().strip(), self.e_text.get().strip()
        try:
            tm = datetime.strptime(tm, "%H:%M").strftime("%H:%M")
        except ValueError:
            messagebox.showwarning("Invalid time", "Use 24-hour HH:MM, e.g. 09:30.")
            return
        if not text:
            return
        self.data["planner"].setdefault(today_str(self.day), []).append({"time": tm, "text": text})
        self.e_text.delete(0, "end")
        self.save()
        self.refresh()

    def delete(self):
        sel = self.lb.curselection()
        if not sel:
            return
        self.data["planner"][today_str(self.day)].remove(self.view[sel[0]])
        self.save()
        self.refresh()

    def refresh(self):
        self.lbl.config(text=self.day.strftime("%A, %d %b %Y"))
        self.lb.delete(0, "end")
        self.view = sorted(self.data["planner"].get(today_str(self.day), []), key=lambda x: x["time"])
        for p in self.view:
            self.lb.insert("end", f"  {p['time']}    {p['text']}")


class PomodoroPage(Page):
    title = "Pomodoro Timer"
    subtitle = "25 minutes of focus, 5 minutes of rest."
    WORK, BREAK = 25 * 60, 5 * 60

    def build(self):
        self.mode = "work"
        self.remaining = self.WORK
        self.running = False
        self.job = None

        card = tk.Frame(self.body, bg=CARD, padx=40, pady=30,
                        highlightthickness=1, highlightbackground="#E3E6F0")
        card.pack(pady=20)
        self.mode_lbl = tk.Label(card, font=FONT_H2, bg=CARD, fg=ACCENT)
        self.mode_lbl.pack()
        self.time_lbl = tk.Label(card, font=("Segoe UI", 64, "bold"), bg=CARD, fg=TEXT)
        self.time_lbl.pack(pady=10)
        self.count_lbl = tk.Label(card, font=FONT, bg=CARD, fg=MUTED)
        self.count_lbl.pack(pady=(0, 14))
        row = tk.Frame(card, bg=CARD)
        row.pack()
        self.start_btn = button(row, "Start", self.toggle, GREEN)
        self.start_btn.pack(side="left")
        button(row, "Reset", self.reset, MUTED).pack(side="left", padx=10)
        button(row, "Skip", self.skip, AMBER).pack(side="left")
        self.update_display()

    def update_display(self):
        m, s = divmod(self.remaining, 60)
        self.time_lbl.config(text=f"{m:02d}:{s:02d}")
        self.mode_lbl.config(text="FOCUS" if self.mode == "work" else "BREAK",
                             fg=ACCENT if self.mode == "work" else GREEN)
        self.count_lbl.config(text=f"Sessions completed today: {self.data['pomodoro'].get(today_str(), 0)}")
        self.start_btn.config(text="Pause" if self.running else "Start")

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.tick()
        elif self.job:
            self.after_cancel(self.job)
            self.job = None
        self.update_display()

    def tick(self):
        if not self.running:
            return
        if self.remaining <= 0:
            self.finish()
            return
        self.remaining -= 1
        self.update_display()
        self.job = self.after(1000, self.tick)

    def finish(self):
        self.bell()
        if self.mode == "work":
            t = today_str()
            self.data["pomodoro"][t] = self.data["pomodoro"].get(t, 0) + 1
            self.save()
            self.mode, self.remaining = "break", self.BREAK
        else:
            self.mode, self.remaining = "work", self.WORK
        self.running = False
        self.update_display()

    def skip(self):
        self.mode = "break" if self.mode == "work" else "work"
        self.remaining = self.BREAK if self.mode == "break" else self.WORK
        self.running = False
        if self.job:
            self.after_cancel(self.job)
        self.update_display()

    def reset(self):
        self.running = False
        if self.job:
            self.after_cancel(self.job)
        self.remaining = self.WORK if self.mode == "work" else self.BREAK
        self.update_display()

    def refresh(self):
        self.update_display()


class NotesPage(Page):
    title = "Notes"
    subtitle = "Write and manage personal notes."

    def build(self):
        self.body.columnconfigure(1, weight=1)
        self.body.rowconfigure(0, weight=1)
        left = tk.Frame(self.body, bg=BG)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        self.lb = listbox(left, width=26)
        self.lb.pack(fill="y", expand=True)
        self.lb.bind("<<ListboxSelect>>", self.on_select)
        button(left, "+ New note", self.new).pack(fill="x", pady=(10, 0))

        right = tk.Frame(self.body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        self.e_title = entry(right, 40)
        self.e_title.pack(fill="x", ipady=6)
        self.txt = tk.Text(right, font=FONT, relief="flat", wrap="word", bg="white", fg=TEXT,
                           insertbackground=TEXT, highlightthickness=1,
                           highlightbackground="#D8DCEA", padx=10, pady=10)
        self.txt.pack(fill="both", expand=True, pady=10)
        row = tk.Frame(right, bg=BG)
        row.pack(fill="x")
        button(row, "Save", self.save_note, GREEN).pack(side="left")
        button(row, "Delete", self.delete, RED).pack(side="left", padx=10)
        self.current = None

    def new(self):
        self.current = None
        self.lb.selection_clear(0, "end")
        self.e_title.delete(0, "end")
        self.txt.delete("1.0", "end")
        self.e_title.focus()

    def on_select(self, _):
        sel = self.lb.curselection()
        if not sel:
            return
        self.current = self.data["notes"][sel[0]]
        self.e_title.delete(0, "end")
        self.e_title.insert(0, self.current["title"])
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", self.current["body"])

    def save_note(self):
        title = self.e_title.get().strip() or "Untitled"
        body = self.txt.get("1.0", "end").rstrip()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.current is None:
            self.current = {"title": title, "body": body, "updated": stamp}
            self.data["notes"].insert(0, self.current)
        else:
            self.current.update(title=title, body=body, updated=stamp)
        self.save()
        self.refresh()
        self.lb.selection_set(self.data["notes"].index(self.current))

    def delete(self):
        if self.current is None:
            return
        if messagebox.askyesno("Delete note", "Delete this note?"):
            self.data["notes"].remove(self.current)
            self.save()
            self.new()
            self.refresh()

    def refresh(self):
        self.lb.delete(0, "end")
        for n in self.data["notes"]:
            self.lb.insert("end", "  " + n["title"])


class HabitsPage(Page):
    title = "Habit Tracker"
    subtitle = "Build streaks one day at a time."

    def build(self):
        bar = tk.Frame(self.body, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        self.e = entry(bar, 36)
        self.e.pack(side="left", ipady=6)
        self.e.bind("<Return>", lambda e: self.add())
        button(bar, "Add habit", self.add).pack(side="left", padx=12)
        self.lb = listbox(self.body)
        self.lb.pack(fill="both", expand=True)
        acts = tk.Frame(self.body, bg=BG)
        acts.pack(fill="x", pady=(12, 0))
        button(acts, "Toggle today", self.toggle, GREEN).pack(side="left")
        button(acts, "Delete", self.delete, RED).pack(side="left", padx=10)

    @staticmethod
    def streak(h):
        d = date.today()
        if today_str(d) not in h["log"]:
            d -= timedelta(days=1)
        n = 0
        while today_str(d) in h["log"]:
            n += 1
            d -= timedelta(days=1)
        return n

    def add(self):
        name = self.e.get().strip()
        if name:
            self.data["habits"].append({"name": name, "log": []})
            self.e.delete(0, "end")
            self.save()
            self.refresh()

    def sel(self):
        s = self.lb.curselection()
        return self.data["habits"][s[0]] if s else None

    def toggle(self):
        h = self.sel()
        if h is None:
            return
        t = today_str()
        h["log"].remove(t) if t in h["log"] else h["log"].append(t)
        self.save()
        self.refresh()

    def delete(self):
        h = self.sel()
        if h is not None:
            self.data["habits"].remove(h)
            self.save()
            self.refresh()

    def refresh(self):
        self.lb.delete(0, "end")
        t = today_str()
        for i, h in enumerate(self.data["habits"]):
            done = t in h["log"]
            self.lb.insert("end", f"  {'✔' if done else '○'}  {h['name']}      🔥 {self.streak(h)}-day streak")
            if done:
                self.lb.itemconfig(i, fg=GREEN)


class CalendarPage(Page):
    title = "Calendar"
    subtitle = "Click a day to see its tasks and plans."

    def build(self):
        self.year, self.month = date.today().year, date.today().month
        self.selected = date.today()
        self.body.columnconfigure(0, weight=3)
        self.body.columnconfigure(1, weight=2)
        self.body.rowconfigure(0, weight=1)
        self.left = tk.Frame(self.body, bg=CARD, padx=16, pady=14,
                             highlightthickness=1, highlightbackground="#E3E6F0")
        self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.right = tk.Frame(self.body, bg=CARD, padx=18, pady=14,
                              highlightthickness=1, highlightbackground="#E3E6F0")
        self.right.grid(row=0, column=1, sticky="nsew")

    def shift(self, n):
        m = self.month + n
        self.year += (m - 1) // 12
        self.month = (m - 1) % 12 + 1
        self.refresh()

    def pick(self, d):
        self.selected = d
        self.refresh()

    def refresh(self):
        for w in self.left.winfo_children() + self.right.winfo_children():
            w.destroy()
        head = tk.Frame(self.left, bg=CARD)
        head.pack(fill="x", pady=(0, 8))
        button(head, "◀", lambda: self.shift(-1), BG, TEXT, 10, 4).pack(side="left")
        tk.Label(head, text=date(self.year, self.month, 1).strftime("%B %Y"),
                 font=FONT_H2, bg=CARD, fg=TEXT).pack(side="left", expand=True)
        button(head, "▶", lambda: self.shift(1), BG, TEXT, 10, 4).pack(side="right")

        grid = tk.Frame(self.left, bg=CARD)
        grid.pack(fill="both", expand=True)
        for c in range(7):
            grid.columnconfigure(c, weight=1, uniform="d")
            tk.Label(grid, text=calendar.day_abbr[c], font=FONT_B, bg=CARD,
                     fg=MUTED).grid(row=0, column=c, pady=4)

        due_days = {t["due"] for t in self.data["tasks"] if t.get("due") and not t["done"]}
        plan_days = {k for k, v in self.data["planner"].items() if v}
        today = date.today()
        for r, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                d = date(self.year, self.month, day)
                iso = today_str(d)
                bg, fg = BG, TEXT
                if d == self.selected:
                    bg, fg = ACCENT, "white"
                elif d == today:
                    bg, fg = "#DDE1FF", ACCENT
                dot = " •" if (iso in due_days or iso in plan_days) else ""
                lab = tk.Label(grid, text=f"{day}{dot}", font=FONT, bg=bg, fg=fg,
                               width=5, pady=8, cursor="hand2")
                lab.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                lab.bind("<Button-1>", lambda e, dd=d: self.pick(dd))

        iso = today_str(self.selected)
        tk.Label(self.right, text=self.selected.strftime("%A, %d %b"), font=FONT_H2,
                 bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 8))
        tasks = [t for t in self.data["tasks"] if t.get("due") == iso]
        plans = sorted(self.data["planner"].get(iso, []), key=lambda x: x["time"])
        if not tasks and not plans:
            tk.Label(self.right, text="Nothing scheduled.", font=FONT, bg=CARD, fg=MUTED).pack(anchor="w")
        for t in tasks:
            tk.Label(self.right, text=("☑ " if t["done"] else "☐ ") + t["text"], font=FONT,
                     bg=CARD, fg=MUTED if t["done"] else TEXT, anchor="w",
                     wraplength=240, justify="left").pack(fill="x", pady=2)
        for p in plans:
            tk.Label(self.right, text=f"{p['time']}  {p['text']}", font=FONT, bg=CARD,
                     fg=TEXT, anchor="w", wraplength=240, justify="left").pack(fill="x", pady=2)


class ProgressPage(Page):
    title = "Progress Tracker"
    subtitle = "Completed tasks and productivity over the last 7 days."

    def refresh(self):
        self.clear_body()
        tasks = self.data["tasks"]
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        rate = f"{round(100 * done / total)}%" if total else "—"
        sessions = sum(self.data["pomodoro"].values())

        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x")
        for i, (title, val, col) in enumerate([("Completion rate", rate, GREEN),
                                               ("Tasks completed", done, ACCENT),
                                               ("Focus sessions (all time)", sessions, AMBER)]):
            row.columnconfigure(i, weight=1, uniform="p")
            stat_card(row, title, val, col).grid(row=0, column=i, sticky="nsew",
                                                 padx=(0 if i == 0 else 12, 0))

        panel = tk.Frame(self.body, bg=CARD, padx=18, pady=14,
                         highlightthickness=1, highlightbackground="#E3E6F0")
        panel.pack(fill="both", expand=True, pady=(20, 0))
        tk.Label(panel, text="Tasks completed per day", font=FONT_H2, bg=CARD, fg=TEXT).pack(anchor="w")
        cv = tk.Canvas(panel, bg=CARD, highlightthickness=0, height=240)
        cv.pack(fill="both", expand=True, pady=(8, 0))
        cv.bind("<Configure>", lambda e: self.draw(cv))
        self.draw(cv)

    def draw(self, cv):
        cv.delete("all")
        w, h = cv.winfo_width() or 700, cv.winfo_height() or 240
        days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        counts = [sum(1 for t in self.data["tasks"] if t.get("done_on") == today_str(d)) for d in days]
        peak = max(counts + [1])
        slot = (w - 40) / 7
        base = h - 30
        for i, (d, n) in enumerate(zip(days, counts)):
            x0 = 20 + i * slot + slot * 0.2
            x1 = 20 + (i + 1) * slot - slot * 0.2
            top = base - (base - 30) * n / peak
            cv.create_rectangle(x0, top, x1, base, fill=ACCENT if n else "#E3E6F0", outline="")
            cv.create_text((x0 + x1) / 2, top - 10, text=str(n), font=FONT_B, fill=TEXT)
            cv.create_text((x0 + x1) / 2, base + 14, text=d.strftime("%a"), font=FONT, fill=MUTED)


# ---------------------------------------------------------------- app shell
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Productivity Dashboard")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.data = load_data()

        side = tk.Frame(self, bg=SIDEBAR, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="⚡ Productivity", font=("Segoe UI", 16, "bold"),
                 bg=SIDEBAR, fg="white").pack(anchor="w", padx=22, pady=(28, 24))

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(side="left", fill="both", expand=True)

        pages = [("Dashboard", "🏠", Dashboard), ("To-Do List", "✅", TodoPage),
                 ("Daily Planner", "🗓", PlannerPage), ("Pomodoro", "⏱", PomodoroPage),
                 ("Notes", "📝", NotesPage), ("Habits", "🔥", HabitsPage),
                 ("Calendar", "📅", CalendarPage), ("Progress", "📊", ProgressPage)]
        self.pages, self.nav = {}, {}
        for name, icon, cls in pages:
            page = cls(self.container, self)
            page.place(relwidth=1, relheight=1)
            self.pages[name] = page
            lab = tk.Label(side, text=f"  {icon}   {name}", font=FONT, bg=SIDEBAR, fg="#C9CEE6",
                           anchor="w", padx=14, pady=11, cursor="hand2")
            lab.pack(fill="x", padx=10, pady=1)
            lab.bind("<Button-1>", lambda e, n=name: self.show(n))
            lab.bind("<Enter>", lambda e, n=name: self.hover(n, True))
            lab.bind("<Leave>", lambda e, n=name: self.hover(n, False))
            self.nav[name] = lab
        self.current = None
        self.show("Dashboard")

    def hover(self, name, inside):
        if name != self.current:
            self.nav[name].config(bg=SIDEBAR_HOVER if inside else SIDEBAR)

    def show(self, name):
        self.current = name
        for n, lab in self.nav.items():
            active = n == name
            lab.config(bg=ACCENT if active else SIDEBAR, fg="white" if active else "#C9CEE6")
        page = self.pages[name]
        page.refresh()
        page.tkraise()


if __name__ == "__main__":
    App().mainloop()
