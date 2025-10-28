#!/usr/bin/env python3
"""
Optimized Universal Turing Machine Visualizer (for big examples)
- Handles long tapes smoothly (shows only a window of cells).
- Dark bold text for clear visibility.
- Non-blocking animation using root.after.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ----------------------------
# Simple Turing Machine Model
# ----------------------------
class TuringMachine:
    def __init__(self, tape_str="_", transitions=None, start_state="q0",
                 accept_state="q_accept", reject_state="q_reject", blank="_"):
        self.blank = blank
        self.tape = list(tape_str) if tape_str else [blank]
        self.head = 0
        self.start_state = start_state
        self.state = start_state
        self.accept_state = accept_state
        self.reject_state = reject_state
        self.transitions = transitions or {}

    def ensure_head_in_bounds(self):
        if self.head < 0:
            add = [self.blank] * abs(self.head)
            self.tape = add + self.tape
            self.head += len(add)
        elif self.head >= len(self.tape):
            add = [self.blank] * (self.head - len(self.tape) + 1)
            self.tape.extend(add)

    def step(self):
        if self.state in (self.accept_state, self.reject_state):
            return False
        self.ensure_head_in_bounds()
        symbol = self.tape[self.head]
        key = (self.state, symbol)
        if key not in self.transitions:
            self.state = self.reject_state
            return False
        write, move, new_state = self.transitions[key]
        self.tape[self.head] = write
        if move.upper() == "R":
            self.head += 1
        elif move.upper() == "L":
            self.head -= 1
        self.state = new_state
        return True

    def reset(self, tape_str):
        self.tape = list(tape_str) if tape_str else [self.blank]
        self.head = 0
        self.state = self.start_state


# ----------------------------
# Parser
# ----------------------------
def parse_tm_description(text):
    transitions = {}
    start_state, accept_state, reject_state, tape = "q0", "q_accept", "q_reject", "_"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "->" in line:
            left, right = line.split("->", 1)
            state, symbol = [s.strip() for s in left.split(",", 1)]
            write_symbol, move, new_state = [s.strip() for s in right.split(",", 2)]
            if symbol.lower() == "blank":
                symbol = "_"
            if write_symbol.lower() == "blank":
                write_symbol = "_"
            transitions[(state, symbol)] = (write_symbol, move.upper(), new_state)
        elif ":" in line:
            key, val = [p.strip() for p in line.split(":", 1)]
            key = key.upper()
            if key == "START":
                start_state = val
            elif key == "ACCEPT":
                accept_state = val
            elif key == "REJECT":
                reject_state = val
            elif key == "TAPE":
                tape = val if val else "_"
    return transitions, start_state, accept_state, reject_state, tape


# ----------------------------
# GUI Visualizer
# ----------------------------
class UTMVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal TM Visualizer - Big Example Ready")
        self.geometry("980x560")
        self.resizable(False, False)

        left = ttk.Frame(self, width=360)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=8, pady=8)

        ttk.Label(left, text="Encoded TM description (editable):").pack(anchor="w")
        self.text = scrolledtext.ScrolledText(left, width=44, height=20,
                                              wrap=tk.WORD, font=("Courier", 10))
        self.text.pack(pady=6)

        ex_frame = ttk.Frame(left)
        ex_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(ex_frame, text="Examples:").pack(side=tk.LEFT)
        self.example_var = tk.StringVar()
        exbox = ttk.Combobox(ex_frame, textvariable=self.example_var,
                             state="readonly", width=20)
        exbox['values'] = ("Replace a->b", "Move right until blank",
                           "Unary increment (demo)")
        exbox.current(0)
        exbox.pack(side=tk.LEFT, padx=6)
        ttk.Button(ex_frame, text="Load", command=self.load_example).pack(side=tk.LEFT)

        ctrl = ttk.Frame(left)
        ctrl.pack(fill=tk.X, pady=(4, 6))
        ttk.Button(ctrl, text="Parse & Create TM", command=self.parse_and_create_tm).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="Reset", command=self.reset_tm).pack(side=tk.LEFT, padx=4)

        runf = ttk.Frame(left)
        runf.pack(fill=tk.X, pady=(4, 6))
        ttk.Button(runf, text="Step ▶", command=self.step_once).pack(side=tk.LEFT, padx=4)
        ttk.Button(runf, text="Run ▶▶", command=self.run_auto).pack(side=tk.LEFT, padx=4)
        ttk.Button(runf, text="Stop ■", command=self.stop_run).pack(side=tk.LEFT, padx=4)

        ttk.Label(left, text="Speed (sec/step):").pack(anchor="w")
        self.speed_var = tk.DoubleVar(value=0.25)
        ttk.Scale(left, from_=0.05, to=1.0, orient=tk.HORIZONTAL,
                  variable=self.speed_var).pack(fill=tk.X, pady=(0, 6))

        info = ttk.Frame(left)
        info.pack(fill=tk.X, pady=(6, 0))
        self.state_label = ttk.Label(info, text="State: -")
        self.state_label.pack(anchor="w")
        self.tape_label = ttk.Label(info, text="Tape: -")
        self.tape_label.pack(anchor="w")

        self.canvas = tk.Canvas(right, width=580, height=420, bg="#fbfbff")
        self.canvas.pack(padx=6, pady=6)
        ttk.Label(right, text="Load example → Parse & Create TM → Step/Run",
                  foreground="#555").pack(anchor="e", padx=6)

        self.tm = None
        self.running = False
        self.after_id = None

        self.load_example()

    # ----------------------------
    def load_example(self):
        sel = self.example_var.get()
        if sel == "Replace a->b":
            sample = """
# Replace all 'a' with 'b' then halt
q0,a -> b,R,q0
q0,b -> b,R,q0
q0,_ -> _,S,q_accept
START: q0
ACCEPT: q_accept
REJECT: q_reject
TAPE: aaaaaaaaaaaaaaaaaaaaaaaaabbbb_
""".strip()
        elif sel == "Move right until blank":
            sample = """
# Move right until blank then accept
q0,a -> a,R,q0
q0,b -> b,R,q0
q0,_ -> _,S,q_accept
START: q0
ACCEPT: q_accept
REJECT: q_reject
TAPE: aaaaaaaaaaaaaaaaaaaaabbbbbbbb_
""".strip()
        else:
            sample = """
# Unary increment: add one more 1 then halt
q0,1 -> 1,R,q0
q0,_ -> 1,S,q_accept
START: q0
ACCEPT: q_accept
REJECT: q_reject
TAPE: 111111111111111111_
""".strip()
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, sample)
        try:
            self.parse_and_create_tm()
        except Exception:
            pass

    def parse_and_create_tm(self):
        raw = self.text.get("1.0", tk.END)
        try:
            transitions, start, accept, reject, tape = parse_tm_description(raw)
        except Exception as e:
            messagebox.showerror("Parse Error", f"Could not parse TM description:\n{e}")
            return
        self.tm = TuringMachine(tape_str=tape, transitions=transitions,
                                start_state=start, accept_state=accept,
                                reject_state=reject)
        self.update_display()
        messagebox.showinfo("TM Created", f"TM created: start={start}, accept={accept}, reject={reject}")

    # ----------------------------
    # Optimized display for large tapes
    # ----------------------------
    def update_display(self):
        self.canvas.delete("all")
        if not self.tm:
            return

        tape = self.tm.tape
        head = self.tm.head
        window_size = 25
        half = window_size // 2
        cell_w, cell_h = 45, 50
        y = 160

        left = max(0, head - half)
        right = min(len(tape), head + half + 1)
        visible = tape[left:right]
        start_x = (580 - len(visible) * cell_w) // 2

        for i, sym in enumerate(visible, start=left):
            x = start_x + (i - left) * cell_w
            fill = "#bdf5bd" if i == head else "white"
            self.canvas.create_rectangle(x, y, x + cell_w, y + cell_h,
                                         fill=fill, outline="#333")
            self.canvas.create_text(x + cell_w / 2, y + cell_h / 2,
                                    text=str(sym),
                                    font=("Arial", 20, "bold"),
                                    fill="black")
            if i == head:
                self.canvas.create_polygon(x + cell_w / 2, y - 20,
                                           x + 10, y - 5,
                                           x + cell_w - 10, y - 5,
                                           fill="red", outline="")

        self.state_label.config(text=f"State: {self.tm.state} | Tape length: {len(self.tm.tape)}")

    # ----------------------------
    def step_once(self):
        if not self.tm:
            return
        progressed = self.tm.step()
        self.update_display()
        if not progressed:
            messagebox.showinfo("Halted", f"Machine halted in state: {self.tm.state}")

    def run_auto(self):
        if not self.tm or self.running:
            return
        self.running = True
        self._run_step()

    def _run_step(self):
        if not self.running or not self.tm:
            self.running = False
            return
        progressed = self.tm.step()
        self.update_display()
        if not progressed:
            self.running = False
            messagebox.showinfo("Halted", f"Machine halted in state: {self.tm.state}")
            return
        delay_ms = max(int(self.speed_var.get() * 1000), 40)
        self.after_id = self.after(delay_ms, self._run_step)

    def stop_run(self):
        if not self.running:
            return
        self.running = False
        if self.after_id:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        self.update_display()

    def reset_tm(self):
        if not self.tm:
            return
        raw = self.text.get("1.0", tk.END)
        try:
            transitions, start, accept, reject, tape = parse_tm_description(raw)
        except Exception as e:
            messagebox.showerror("Parse Error", f"Could not reset TM:\n{e}")
            return
        self.tm.transitions = transitions
        self.tm.start_state = start
        self.tm.accept_state = accept
        self.tm.reject_state = reject
        self.tm.reset(tape)
        self.update_display()


# ----------------------------
def main():
    app = UTMVisualizer()
    app.mainloop()

if __name__ == "__main__":
    main()
