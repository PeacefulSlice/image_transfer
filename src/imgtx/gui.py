# src/imgtx/gui.py
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .live_tests import sender_preflight, receiver_postflight, TestResult

# ВАЖЛИВО: ці імпорти підстав під твої реальні модулі.
# Якщо у тебе інші назви файлів/класів — скажеш, я підправлю.
from .sender import Sender
from .receiver import ReceiverServer
from .config import DEFAULT_HOST, DEFAULT_PORT


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("image_transfer — GUI")
        self.geometry("1000x650")

        self.expected_meta: dict[str, object] | None = None
        self.stop_flag = threading.Event()
        self.recv_thread: threading.Thread | None = None

        # ---- Controls
        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Host").grid(row=0, column=0, sticky="w")
        self.host = tk.Entry(top, width=18)
        self.host.insert(0, DEFAULT_HOST)
        self.host.grid(row=0, column=1, padx=6)

        tk.Label(top, text="Port").grid(row=0, column=2, sticky="w")
        self.port = tk.Entry(top, width=8)
        self.port.insert(0, str(DEFAULT_PORT))
        self.port.grid(row=0, column=3, padx=6)

        tk.Label(top, text="Output dir").grid(row=0, column=4, sticky="w")
        self.outdir = tk.Entry(top, width=28)
        self.outdir.insert(0, "outputs/received")
        self.outdir.grid(row=0, column=5, padx=6)

        self.btn_start = tk.Button(top, text="Start receiver", command=self.start_receiver)
        self.btn_start.grid(row=0, column=6, padx=6)

        self.btn_stop = tk.Button(top, text="Stop receiver", command=self.stop_receiver, state="disabled")
        self.btn_stop.grid(row=0, column=7, padx=6)

        self.btn_send = tk.Button(top, text="Choose & send…", command=self.choose_and_send)
        self.btn_send.grid(row=0, column=8, padx=6)

        # ---- Table of test results
        tk.Label(self, text="Live test results (during transfer):").pack(anchor="w", padx=10)

        self.table = ttk.Treeview(self, columns=("name", "status", "details"), show="headings", height=16)
        self.table.heading("name", text="Test")
        self.table.heading("status", text="OK")
        self.table.heading("details", text="Details")
        self.table.column("name", width=260)
        self.table.column("status", width=60, anchor="center")
        self.table.column("details", width=640)
        self.table.pack(fill="both", expand=False, padx=10, pady=8)

        # ---- Log
        tk.Label(self, text="Log:").pack(anchor="w", padx=10)
        self.log = tk.Text(self, height=10, wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._log("Ready.")

    def _log(self, msg: str):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def _clear_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

    def _add_results(self, results: list[TestResult], prefix: str = ""):
        for r in results:
            name = f"{prefix}{r.name}" if prefix else r.name
            self.table.insert("", "end", values=(name, "✅" if r.ok else "❌", r.details))

    def start_receiver(self):
        if self.recv_thread and self.recv_thread.is_alive():
            messagebox.showinfo("Receiver", "Receiver already running.")
            return

        host = self.host.get().strip()
        port = int(self.port.get().strip())
        outdir = Path(self.outdir.get().strip())
        outdir.mkdir(parents=True, exist_ok=True)

        self.stop_flag.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._log(f"[RECV] starting on {host}:{port}, out={outdir}")

        def loop():
            # Якщо у твоєму ReceiverServer є лише serve_once() — крутимо в циклі.
            while not self.stop_flag.is_set():
                try:
                    srv = ReceiverServer(host=host, port=port, output_dir=str(outdir))
                    res = srv.serve_once()  # має повертати шлях до збереженого файла
                    saved_path = getattr(res, "saved_path", None) or getattr(res, "path", None) or str(res)

                    self._log(f"[RECV] got file: {saved_path}")

                    # ---- POSTFLIGHT tests
                    post = receiver_postflight(saved_path, expected=self.expected_meta or {})
                    self._add_results(post, prefix="POST: ")

                except Exception as e:
                    if self.stop_flag.is_set():
                        break
                    self._log(f"[RECV] ERROR: {e}")

            self._log("[RECV] stopped")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

        self.recv_thread = threading.Thread(target=loop, daemon=True)
        self.recv_thread.start()

    def stop_receiver(self):
        self.stop_flag.set()
        self._log("[RECV] stop requested (may stop after current accept)")

    def choose_and_send(self):
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not path:
            return

        self._clear_table()

        # ---- PREFLIGHT tests
        pre, meta = sender_preflight(path)
        self.expected_meta = meta
        self._add_results(pre, prefix="PRE: ")

        if not all(r.ok for r in pre):
            self._log("[SEND] preflight failed -> not sending")
            return

        host = self.host.get().strip()
        port = int(self.port.get().strip())

        self._log(f"[SEND] sending {path} -> {host}:{port}")

        def run():
            try:
                s = Sender(host=host, port=port)
                s.send_image(path)
                self._log("[SEND] done")
            except Exception as e:
                self._log(f"[SEND] ERROR: {e}")

        threading.Thread(target=run, daemon=True).start()


def main():
    App().mainloop()

if __name__ == "__main__":
    main()
