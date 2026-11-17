"""TOM'un küçük penceresi: durum küresi, sohbet akışı, mikrofon/uyku/sustur düğmeleri, yazarak soru.

    PYTHONPATH=. .venv/bin/python -m tom.gui --deepspeed        (masaüstü simgesi bunu açar)

Asistan arka thread'de, terminaldeki TOM ile aynı döngüde çalışır (tom.__main__.run_live). Pencere
yalnız olayları gösterir ve komutları kuyruğa koyar; asistanın kendisine tek thread dokunur.
"""

from __future__ import annotations

import math
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

BG, PANEL, LINE = "#0b0f17", "#131a26", "#222c3d"
TEXT, MUTED, ACCENT = "#e7ecf3", "#8a96a8", "#60a5fa"
STATE = {  # durum → (renk, etiket, nabız)
    "loading": ("#5b6b85", "Yükleniyor…", False),
    "idle": ("#2fa37a", "Dinliyorum · Hey TOM", False),
    "hearing": ("#34d399", "Duyuyorum…", True),
    "thinking": ("#f59e0b", "Düşünüyorum…", True),
    "speaking": ("#60a5fa", "Konuşuyor", True),
    "sleeping": ("#7c6fd6", "Uyuyor · Hey TOM ile uyandır", False),
    "researching": ("#8b5cf6", "Araştırıyor…", True),
    "muted": ("#5b6b85", "Mikrofon kapalı", False),
    "error": ("#f87171", "Hata", False),
}


class Tee:
    """print çıktısını hem terminale hem pencereye (yükleme durumu için) verir."""

    def __init__(self, stream, q: queue.Queue):
        self.stream, self.q = stream, q

    def write(self, s):
        self.stream.write(s)
        for line in s.splitlines():
            if line.strip():
                self.q.put(("log", {"text": line.strip()}))

    def flush(self):
        self.stream.flush()


class TomWindow:
    def __init__(self, root: tk.Tk, args):
        from tom.__main__ import Control

        self.root, self.args = root, args
        self.events: queue.Queue = queue.Queue()
        self.control = Control()
        self.state = "loading"
        self.phase = 0.0
        self.bot = None
        self.deep = False          # "Derin" düğmesi: yazılan soru derin araştırmaya gider
        self.researching = False
        self._build()
        sys.stdout = Tee(sys.__stdout__, self.events)
        threading.Thread(target=self._worker, daemon=True, name="tom-asistan").start()
        self.root.after(40, self._tick)

    # ---------------- asistan thread'i ----------------
    def _worker(self):
        from tom.__main__ import build, run_live

        try:
            bot, tts, persona = build(self.args)
            self.bot = bot
            bot.on_event = lambda kind, data: self.events.put((kind, data))
            run_live(bot, tts, persona, self.args, control=self.control, module="tom.gui")
        except Exception as e:  # noqa: BLE001 — pencerede göster
            self.events.put(("error", {"text": f"{type(e).__name__}: {e}"}))
        finally:
            self.events.put(("closed", {}))

    # ---------------- arayüz ----------------
    def _build(self):
        r = self.root
        r.title("TOM")
        r.configure(bg=BG)
        r.geometry("420x660")
        r.minsize(340, 480)
        try:
            from tom.voice.settings import ROOT
            r.iconphoto(True, tk.PhotoImage(file=str(ROOT / "assets" / "tom.png")))
        except Exception:  # noqa: BLE001
            pass
        base = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.f_title = tkfont.Font(family=base, size=13, weight="bold")
        self.f_text = tkfont.Font(family=base, size=11)
        self.f_small = tkfont.Font(family=base, size=9)
        self.f_status = tkfont.Font(family=base, size=10)

        top = tk.Frame(r, bg=BG)
        top.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(top, text="TOM", font=self.f_title, fg=TEXT, bg=BG).pack(side="left")
        # Tk renkli emoji çizemiyor: düğmeler kısa yazılı
        self.btn_pin = self._button(top, "Üstte", self._toggle_pin)
        self.btn_pin.pack(side="right", padx=(4, 0))
        self.btn_stop = self._button(top, "Sus", lambda: self.control.actions.put("stop_speaking"))
        self.btn_stop.pack(side="right", padx=(4, 0))
        self.btn_sleep = self._button(top, "Uyut", self._toggle_sleep)
        self.btn_sleep.pack(side="right", padx=(4, 0))
        self.btn_mic = self._button(top, "Mikrofon", self._toggle_mic)
        self.btn_mic.pack(side="right", padx=(4, 0))

        self.canvas = tk.Canvas(r, height=150, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="x", pady=(4, 0))
        self.status = tk.Label(r, text="", font=self.f_status, fg=MUTED, bg=BG)
        self.status.pack()

        bottom = tk.Frame(r, bg=BG)
        bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 12))
        box = tk.Frame(r, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        box.pack(fill="both", expand=True, padx=12, pady=8)
        self.chat = tk.Text(box, bg=PANEL, fg=TEXT, font=self.f_text, wrap="word", bd=0, padx=10, pady=8,
                            highlightthickness=0, cursor="arrow", spacing1=2, spacing3=6)
        sb = tk.Scrollbar(box, command=self.chat.yview, bg=PANEL, troughcolor=PANEL, bd=0, highlightthickness=0)
        self.chat.configure(yscrollcommand=sb.set, state="disabled")
        sb.pack(side="right", fill="y")
        self.chat.pack(side="left", fill="both", expand=True)
        self.chat.tag_configure("user", justify="right", foreground="#bcd7ff", lmargin1=60, lmargin2=60)
        self.chat.tag_configure("tom", justify="left", foreground=TEXT, rmargin=40)
        self.chat.tag_configure("meta_user", justify="right", foreground=MUTED, font=self.f_small)
        self.chat.tag_configure("meta", justify="left", foreground=MUTED, font=self.f_small)
        self.chat.tag_configure("sys", justify="center", foreground=MUTED, font=self.f_small)
        self.chat.tag_configure("err", justify="center", foreground="#f87171", font=self.f_small)
        self.f_head = tkfont.Font(family=self.f_text.actual()["family"], size=12, weight="bold")
        self.f_bold = tkfont.Font(family=self.f_text.actual()["family"], size=11, weight="bold")
        self.chat.tag_configure("step", justify="left", foreground="#a78bfa", font=self.f_small)
        self.chat.tag_configure("report", justify="left", foreground=TEXT, rmargin=10)
        self.chat.tag_configure("r_head", justify="left", foreground=ACCENT, font=self.f_head, spacing1=8)
        self.chat.tag_configure("r_sum", justify="left", foreground=TEXT, font=self.f_bold, spacing3=8)
        self.chat.tag_configure("r_item", justify="left", foreground=TEXT, lmargin1=8, lmargin2=22)
        self.chat.tag_configure("r_src", justify="left", foreground=MUTED, font=self.f_small, lmargin1=8, lmargin2=22)
        self.chat.tag_configure("link", justify="left", foreground=ACCENT, underline=True, font=self.f_small)
        self.chat.tag_bind("link", "<Enter>", lambda e: self.chat.configure(cursor="hand2"))
        self.chat.tag_bind("link", "<Leave>", lambda e: self.chat.configure(cursor="arrow"))

        self.entry = tk.Entry(bottom, bg=PANEL, fg=TEXT, insertbackground=TEXT, font=self.f_text, bd=0,
                              highlightthickness=1, highlightbackground=LINE, highlightcolor=ACCENT)
        self.entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.entry.bind("<Return>", lambda e: self._send())
        self.btn_deep = self._button(bottom, "Derin", self._toggle_deep)
        self.btn_deep.pack(side="left", padx=(8, 0))
        self._button(bottom, "Gönder", self._send).pack(side="left", padx=(6, 0))
        self._placeholder()
        r.protocol("WM_DELETE_WINDOW", self._close)

    def _button(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg=PANEL, fg=TEXT, activebackground=LINE,
                         activeforeground=TEXT, bd=0, highlightthickness=1, highlightbackground=LINE,
                         font=self.f_small, padx=8, pady=4, cursor="hand2")

    def _placeholder(self):
        self._ph = "Yaz ya da konuş…"

        def on_in(_):
            if self.entry.get() == self._ph:
                self.entry.delete(0, "end")
                self.entry.configure(fg=TEXT)

        def on_out(_):
            if not self.entry.get():
                self.entry.insert(0, self._ph)
                self.entry.configure(fg=MUTED)

        self.entry.bind("<FocusIn>", on_in)
        self.entry.bind("<FocusOut>", on_out)
        on_out(None)

    # ---------------- sohbet ----------------
    def _append(self, text: str, tag: str, meta: str | None = None):
        c = self.chat
        c.configure(state="normal")
        if meta:
            c.insert("end", meta + "\n", "meta_user" if tag == "user" else "meta")
        c.insert("end", text + "\n", tag)
        c.configure(state="disabled")
        c.see("end")

    def _sys(self, text: str, tag: str = "sys"):
        self._append(text, tag)

    # ---------------- olaylar ----------------
    def _tick(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                self._on_event(kind, data)
        except queue.Empty:
            pass
        self.phase = (self.phase + 0.04) % 1.0
        self._draw()
        self.root.after(40, self._tick)

    def _on_event(self, kind: str, data: dict):
        if kind == "state":
            self.state = data["state"]
        elif kind == "user":
            self._append(data["text"], "user")
        elif kind == "tom":
            meta = None
            if data.get("skill"):
                meta = f"⚡ {data['skill']}"
            elif data.get("tools"):
                meta = "🔧 " + ", ".join(data["tools"])
            elif data.get("notice"):
                meta = "🔔 bildirim"
            self._append(data["text"], "tom", meta)
        elif kind == "log" and self.state == "loading":
            line = data["text"]
            if any(k in line for k in ("yükleniyor", "ısınıyor", "Hazır cümle", "Ses:")):
                self.status.configure(text=line[:60])
        elif kind == "research_step":
            self._append(data["text"], "step")
        elif kind == "research_start":
            self.chat.configure(state="normal")
            self.chat.mark_set("rep_start", "end-1c")
            self.chat.mark_gravity("rep_start", "left")
            self.chat.configure(state="disabled")
        elif kind == "research_text":
            self.chat.configure(state="normal")
            self.chat.insert("end", data["piece"], "report")
            self.chat.configure(state="disabled")
            self.chat.see("end")
        elif kind == "research_done":
            self._render_report(data["report"])
        elif kind == "error":
            self.state = "error"
            self._sys(data["text"], "err")
        elif kind == "closed" and self.state != "error":
            self._sys("TOM kapandı.")

    def _visual_state(self) -> str:
        if self.state in ("loading", "error", "sleeping"):
            return self.state
        p = self.control.player
        if p is not None and p.busy:
            return "speaking"
        if self.researching and self.state == "idle":
            return "researching"
        if self.control.mic_muted and self.state == "idle":
            return "muted"
        return self.state

    def _draw(self):
        st = self._visual_state()
        color, label, pulse = STATE.get(st, STATE["idle"])
        if self.status.cget("text") != label and not (st == "loading" and self.status.cget("text")):
            self.status.configure(text=label)
        c = self.canvas
        c.delete("all")
        w = c.winfo_width() or 420
        cx, cy, base = w / 2, 75, 44
        if pulse:
            for k in (0, 0.5):
                p = (self.phase + k) % 1
                r = base * (0.95 + p * 0.6)
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=_mix(color, BG, p), width=2)
        breathe = 1 + (0.04 * math.sin(self.phase * 2 * math.pi) if st in ("idle", "sleeping") else 0)
        r = base * breathe
        for i in range(8, 0, -1):  # yumuşak parıltı
            rr = r + i * 2.2
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="", fill=_mix(color, BG, 0.55 + i * 0.055))
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="", fill=color)
        hr = r * 0.55
        c.create_oval(cx - hr - r * 0.18, cy - hr - r * 0.22, cx + hr - r * 0.18, cy + hr - r * 0.22, outline="",
                      fill=_mix(color, "#ffffff", 0.35))
        self.btn_sleep.configure(text="Uyandır" if st == "sleeping" else "Uyut")
        self.btn_mic.configure(bg="#34d399" if not self.control.mic_muted else PANEL,
                               fg="#052e1c" if not self.control.mic_muted else TEXT)

    # ---------------- düğmeler ----------------
    def _send(self):
        t = self.entry.get().strip()
        if not t or t == self._ph or self.bot is None:
            return
        self.entry.delete(0, "end")
        if self.deep:
            self._start_research(t)
        else:
            self.control.texts.put(t)

    # ---------------- derin araştırma ----------------
    def _toggle_deep(self):
        self.deep = not self.deep
        self.btn_deep.configure(bg="#8b5cf6" if self.deep else PANEL, fg="#ffffff" if self.deep else TEXT)
        self._ph_text = "Derin araştırma: sorunu yaz…" if self.deep else "Yaz ya da konuş…"
        if self.entry.get() in ("Yaz ya da konuş…", "Derin araştırma: sorunu yaz…"):
            self.entry.delete(0, "end")
            self.entry.insert(0, self._ph_text)
            self.entry.configure(fg=MUTED)
        self._ph = self._ph_text

    def _start_research(self, question: str):
        if self.researching:
            self._sys("Bir araştırma zaten sürüyor; bitince yenisini başlatabilirsin.")
            return
        self.researching = True
        self._append(question, "user", "🔬 derin araştırma")
        bot = self.bot

        def work():
            from tom.research import default_research

            q = self.events
            try:
                dr = default_research(bot.llm_model, bot.llm_options)
                started = [False]

                def on_text(piece):
                    if not started[0]:
                        started[0] = True
                        q.put(("research_start", {}))
                    q.put(("research_text", {"piece": piece}))

                rep = dr.run(question, progress=lambda t: q.put(("research_step", {"text": t})), on_text=on_text)
                q.put(("research_done", {"report": rep}))
                if rep.summary:
                    bot.notify(f"Araştırma bitti. {rep.summary}")  # boşta olduğu ilk anda sesli söylenir
            except Exception as e:  # noqa: BLE001
                q.put(("error", {"text": f"Araştırma hatası: {type(e).__name__}: {e}"}))
            finally:
                self.researching = False

        threading.Thread(target=work, daemon=True, name="tom-arastirma").start()

    def _render_report(self, rep):
        """Akan ham metni biçimli rapora çevir: başlıklar, maddeler, kaynaklar, 'Raporu aç' bağlantısı."""
        c = self.chat
        c.configure(state="normal")
        try:
            c.delete("rep_start", "end-1c")
        except tk.TclError:
            pass
        c.insert("end", "\n")
        for line in rep.text.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.startswith("#"):
                c.insert("end", l.lstrip("#").strip() + "\n", "r_head")
            elif re.match(r"^\**Özet\**\s*:", l, re.I):
                c.insert("end", re.sub(r"\*", "", l) + "\n", "r_sum")
            elif re.match(r"^[-*•]\s+", l):
                c.insert("end", "• " + re.sub(r"\*\*", "", re.sub(r"^[-*•]\s+", "", l)) + "\n", "r_item")
            else:
                c.insert("end", re.sub(r"\*\*", "", l) + "\n", "report")
        if rep.sources:
            c.insert("end", "Kaynaklar\n", "r_head")
            for src in rep.sources:
                c.insert("end", f"{src.n}. {src.title} — {src.url}\n", "r_src")
        if rep.path:
            tag = f"link{id(rep)}"
            c.insert("end", "📄 Raporu aç\n", ("link", tag))
            c.tag_bind(tag, "<Button-1>", lambda e, p=str(rep.path): __import__("subprocess").Popen(["xdg-open", p]))
        c.configure(state="disabled")
        c.see("end")

    def _toggle_mic(self):
        self.control.mic_muted = not self.control.mic_muted

    def _toggle_sleep(self):
        self.control.actions.put("wake" if self.state == "sleeping" else "sleep")

    def _toggle_pin(self):
        on = not bool(self.root.attributes("-topmost"))
        self.root.attributes("-topmost", on)
        self.btn_pin.configure(bg=ACCENT if on else PANEL)

    def _close(self):
        self.control.stopped = True
        self.root.after(300, lambda: (self.root.destroy(), os._exit(0)))


def _mix(a: str, b: str, t: float) -> str:
    """a'dan b'ye t oranında renk (0: a, 1: b)."""
    t = max(0.0, min(1.0, t))
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def main():
    from tom.__main__ import make_parser

    args = make_parser("tom.gui").parse_args()
    root = tk.Tk(className="tom")
    win = TomWindow(root, args)
    import signal

    # scripts/tom-kapat.sh SIGINT/SIGTERM gönderir; Tk bunu kendisi işlemez: pencereyi düzgün kapat
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: root.after(0, win._close))
    root.mainloop()


if __name__ == "__main__":
    main()
