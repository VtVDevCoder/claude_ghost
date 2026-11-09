import queue as _q
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from . import logger
from .queue_manager import load_queue, save_queue, load_state, save_state
from .runner import Runner, MODE_CLASSIC, MODE_QUEUE

BG, FG, PANEL, ACCENT = "#1e1f22", "#e6e6e6", "#2b2d31", "#d97757"
TAGS = {"INFO": "#56b6c2", "OK": "#7ec699", "AVISO": "#e5c07b", "ERRO": "#e06c75",
        "ALERTA": "#e06c75", "ESPERA": "#e5c07b", "ENERGIA": "#c678dd",
        "FILA": "#56b6c2", "AÇÃO": "#7ec699", "LIMPEZA": "#56b6c2", "SUCESSO": "#7ec699"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Claude Ghost")
        self.geometry("980x640")
        self.minsize(820, 520)
        self.configure(bg=BG)
        self.runner = None
        self.events = _q.Queue()
        logger.set_handler(lambda lvl, msg: self.events.put(("log", lvl, msg)))

        self.mode = tk.StringVar(value=MODE_QUEUE)
        self.screen_off = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Parado")
        self.countdown = tk.StringVar(value="")

        self._style()
        self._build()
        self._refresh_queue()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(100, self._poll)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL)
        s.configure("TFrame", background=BG)
        s.configure("TLabelframe", background=BG, foreground=FG)
        s.configure("TLabelframe.Label", background=BG, foreground=ACCENT)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("TRadiobutton", background=BG, foreground=FG)
        s.configure("TCheckbutton", background=BG, foreground=FG)
        s.configure("TButton", background=PANEL, foreground=FG, padding=6)
        s.map("TButton", background=[("active", "#3a3d44"), ("disabled", BG)])
        s.configure("Accent.TButton", background=ACCENT, foreground="#fff")
        s.map("Accent.TButton", background=[("active", "#e8896b"), ("disabled", "#5a4036")])

    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Radiobutton(top, text="Modo Clássico (só 'continue')", variable=self.mode,
                        value=MODE_CLASSIC).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(top, text="Modo Fila de Prompts", variable=self.mode,
                        value=MODE_QUEUE).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(top, text="Desligar tela em esperas longas",
                        variable=self.screen_off).pack(side="left")
        self.btn_stop = ttk.Button(top, text="■ Parar", command=self.stop, state="disabled")
        self.btn_stop.pack(side="right")
        self.btn_start = ttk.Button(top, text="▶ Iniciar", style="Accent.TButton", command=self.start)
        self.btn_start.pack(side="right", padx=6)

        bar = ttk.Frame(self, padding=(10, 0))
        bar.pack(fill="x")
        ttk.Label(bar, text="Status:").pack(side="left")
        ttk.Label(bar, textvariable=self.status, foreground=ACCENT).pack(side="left", padx=6)
        ttk.Label(bar, textvariable=self.countdown).pack(side="right")

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1, uniform="c")
        body.columnconfigure(1, weight=2, uniform="c")
        body.rowconfigure(0, weight=1)

        # Fila
        qf = ttk.LabelFrame(body, text="Fila de prompts", padding=8)
        qf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        qf.rowconfigure(0, weight=1)
        qf.columnconfigure(0, weight=1)
        self.listbox = tk.Listbox(qf, bg=PANEL, fg=FG, selectbackground=ACCENT,
                                  highlightthickness=0, relief="flat", activestyle="none")
        self.listbox.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(qf, command=self.listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=sb.set)

        self.entry = tk.Text(qf, height=4, bg=PANEL, fg=FG, insertbackground=FG,
                             relief="flat", wrap="word")
        self.entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        btns = ttk.Frame(qf)
        btns.grid(row=2, column=0, columnspan=2, sticky="ew")
        for txt, cmd in [("Adicionar", self.add), ("Remover", self.remove),
                         ("↑", lambda: self.move(-1)), ("↓", lambda: self.move(1)),
                         ("Limpar", self.clear)]:
            ttk.Button(btns, text=txt, command=cmd, width=9 if len(txt) > 1 else 3).pack(side="left", padx=2)

        # Log
        lf = ttk.LabelFrame(body, text="Log", padding=8)
        lf.grid(row=0, column=1, sticky="nsew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)
        self.log = ScrolledText(lf, bg=PANEL, fg=FG, relief="flat", state="disabled",
                                font=("monospace", 10), wrap="word")
        self.log.grid(row=0, column=0, sticky="nsew")
        for k, v in TAGS.items():
            self.log.tag_config(k, foreground=v)
        ttk.Button(lf, text="Limpar log", command=self._clear_log).grid(row=1, column=0, sticky="e", pady=(6, 0))

    # --- fila ---
    def _refresh_queue(self):
        self.listbox.delete(0, "end")
        for i, p in enumerate(load_queue(), 1):
            one = p.replace("\n", " ")
            self.listbox.insert("end", f"{i}. {one[:70]}{'...' if len(one) > 70 else ''}")

    def add(self):
        text = self.entry.get("1.0", "end").strip()
        if not text:
            return
        q = load_queue()
        q.append(text)
        save_queue(q)
        self.entry.delete("1.0", "end")
        self._refresh_queue()

    def _sel(self):
        s = self.listbox.curselection()
        return s[0] if s else None

    def remove(self):
        i = self._sel()
        if i is None:
            return
        q = load_queue()
        if i < len(q):
            q.pop(i)
            save_queue(q)
        self._refresh_queue()

    def move(self, d):
        i = self._sel()
        q = load_queue()
        if i is None or not 0 <= i + d < len(q):
            return
        q[i], q[i + d] = q[i + d], q[i]
        save_queue(q)
        self._refresh_queue()
        self.listbox.selection_set(i + d)

    def clear(self):
        if load_queue() and messagebox.askyesno("Limpar fila", "Remover todos os prompts da fila?"):
            save_queue([])
            self._refresh_queue()

    # --- execução ---
    def start(self):
        if self.runner and self.runner.is_alive():
            return
        self.runner = Runner(
            self.mode.get(), self.screen_off.get(),
            on_status=lambda s: self.events.put(("status", s)),
            on_countdown=lambda s: self.events.put(("count", s)),
        )
        self.runner.start()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

    def stop(self):
        if self.runner:
            self.runner.stop()
        self.btn_stop.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "log":
                    self.log.config(state="normal")
                    self.log.insert("end", f"[{ev[1]}] ", ev[1])
                    self.log.insert("end", ev[2] + "\n")
                    self.log.see("end")
                    self.log.config(state="disabled")
                    self._refresh_queue()
                elif ev[0] == "status":
                    self.status.set(ev[1])
                elif ev[0] == "count":
                    s = ev[1]
                    self.countdown.set(f"Retorno em {s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s else "")
        except _q.Empty:
            pass
        if self.runner and not self.runner.is_alive() and str(self.btn_start["state"]) == "disabled":
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
        self.after(100, self._poll)

    def _close(self):
        if self.runner and self.runner.is_alive():
            self.runner.stop()
        try:
            subprocess.run(["xset", "dpms", "force", "on"], check=False)
        except Exception:
            pass
        self.destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
