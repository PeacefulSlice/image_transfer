# src/imgtx/gui.py
from __future__ import annotations

import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from .sender import Sender
from .receiver import ReceiverServer
from .config import DEFAULT_HOST, DEFAULT_PORT


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Transfer (imgtx) — GUI")
        self.geometry("900x600")

        self._recv_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # ===== Top controls =====
        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        # Receiver settings
        tk.Label(top, text="Receiver host:").grid(row=0, column=0, sticky="w")
        self.recv_host = tk.Entry(top, width=16)
        self.recv_host.insert(0, DEFAULT_HOST)
        self.recv_host.grid(row=0, column=1, padx=6)

        tk.Label(top, text="port:").grid(row=0, column=2, sticky="w")
        self.recv_port = tk.Entry(top, width=8)
        self.recv_port.insert(0, str(DEFAULT_PORT))
        self.recv_port.grid(row=0, column=3, padx=6)

        tk.Label(top, text="out dir:").grid(row=0, column=4, sticky="w")
        self.out_dir = tk.Entry(top, width=28)
        self.out_dir.insert(0, "outputs/received")
        self.out_dir.grid(row=0, column=5, padx=6)

        self.btn_start = tk.Button(top, text="Start receiver", command=self.start_receiver)
        self.btn_start.grid(row=0, column=6, padx=6)

        self.btn_stop = tk.Button(top, text="Stop receiver", command=self.stop_receiver, state="disabled")
        self.btn_stop.grid(row=0, column=7, padx=6)

        # Sender settings
        send = tk.Frame(self)
        send.pack(fill="x", padx=10)

        tk.Label(send, text="Sender -> host:").grid(row=0, column=0, sticky="w")
        self.send_host = tk.Entry(send, width=16)
        self.send_host.insert(0, DEFAULT_HOST)
        self.send_host.grid(row=0, column=1, padx=6)

        tk.Label(send, text="port:").grid(row=0, column=2, sticky="w")
        self.send_port = tk.Entry(send, width=8)
        self.send_port.insert(0, str(DEFAULT_PORT))
        self.send_port.grid(row=0, column=3, padx=6)

        self.btn_pick = tk.Button(send, text="Choose image…", command=self.pick_and_send)
        self.btn_pick.grid(row=0, column=4, padx=6)

        # ===== Log =====
        tk.Label(self, text="Log:").pack(anchor="w", padx=10, pady=(10, 0))
        self.log = tk.Text(self, wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=10)
        self._log("Ready.")

    def _log(self, msg: str):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def _parse_host_port(self, host_entry: tk.Entry, port_entry: tk.Entry) -> tuple[str, int]:
        host = host_entry.get().strip()
        try:
            port = int(port_entry.get().strip())
        except ValueError:
            raise ValueError("Port must be an integer")
        return host, port

    # ===== Receiver =====
    def start_receiver(self):
        if self._recv_thread and self._recv_thread.is_alive():
            messagebox.showinfo("Receiver", "Receiver already running.")
            return

        try:
            host, port = self._parse_host_port(self.recv_host, self.recv_port)
        except ValueError as e:
            messagebox.showerror("Receiver", str(e))
            return

        out_dir = self.out_dir.get().strip()
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        self._stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

        self._log(f"[RECV] starting loop on {host}:{port}, out={out_dir}")

        def loop():
            # ReceiverServer у repo "serve_once" — приймає 1 файл і завершується :contentReference[oaicite:5]{index=5}
            # Тому робимо цикл "serve_once" для GUI.
            while not self._stop_event.is_set():
                try:
                    srv = ReceiverServer(host=host, port=port, output_dir=out_dir)
                    res = srv.serve_once()
                    self._log(f"[RECV] OK saved: {res.saved_path}")
                    self._log(f"       sha256={res.sha256[:16]}…  {res.width}x{res.height}  {res.format}")
                except Exception as e:
                    # якщо стоп — не спамимо
                    if self._stop_event.is_set():
                        break
                    self._log(f"[RECV] ERROR: {e}")
                    time.sleep(0.3)

            self._log("[RECV] stopped.")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

        self._recv_thread = threading.Thread(target=loop, daemon=True)
        self._recv_thread.start()

    def stop_receiver(self):
        self._stop_event.set()
        self._log("[RECV] stopping… (if waiting on accept, stop after next connection or restart)")
        # NOTE: serve_once блокується на accept(), тому “м’яка” зупинка
        # може чекати до нового з’єднання. Це обмеження поточної реалізації serve_once() :contentReference[oaicite:6]{index=6}

    # ===== Sender =====
    def pick_and_send(self):
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            host, port = self._parse_host_port(self.send_host, self.send_port)
        except ValueError as e:
            messagebox.showerror("Sender", str(e))
            return

        self._log(f"[SEND] sending {path} -> {host}:{port}")

        def run():
            try:
                s = Sender(host=host, port=port)
                header = s.send_image(path)
                self._log(f"[SEND] OK filename={header.get('filename')} size={header.get('size_bytes')} sha256={str(header.get('sha256'))[:16]}…")
            except Exception as e:
                self._log(f"[SEND] ERROR: {e}")

        threading.Thread(target=run, daemon=True).start()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
