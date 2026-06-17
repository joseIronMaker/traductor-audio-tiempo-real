"""
app.py — Interfaz gráfica del traductor de audio en tiempo real.

    python app.py

Elige idioma origen (auto) y destino, el dispositivo de salida, y controla
Iniciar / Pausar / Detener. El idioma destino se puede cambiar EN VIVO.
Reconexión automática incluida.

Recuerda enrutar la fuente (navegador/Zoom) a "CABLE Input" para no oír el
audio original; la app captura de "CABLE Output".
"""

import queue
import tkinter as tk
from tkinter import ttk, font as tkfont

import sounddevice as sd

import config
from engine import TranslatorEngine

# Idiomas comunes (BCP-47). El de ORIGEN es informativo: el modelo lo detecta.
IDIOMAS = [
    ("Español", "es"), ("Inglés", "en"), ("Francés", "fr"),
    ("Portugués", "pt"), ("Alemán", "de"), ("Italiano", "it"),
    ("Japonés", "ja"), ("Coreano", "ko"), ("Chino", "zh"),
    ("Ruso", "ru"), ("Árabe", "ar"), ("Hindi", "hi"),
]

# MME primero: evita el error -9999 de WASAPI/WDM-KS con dispositivos USB.
# WDM-KS se excluye (es la API que causa el -9999 y es exclusiva/frágil).
_HOSTAPI_PREF = {"MME": 0, "Windows WASAPI": 1, "Windows DirectSound": 2}

# Paleta
BG = "#f3f4f6"
CARD = "#ffffff"
PRIMARY = "#4f46e5"
PRIMARY_DK = "#4338ca"
INK = "#1f2937"
MUTED = "#6b7280"
GREEN = "#16a34a"
GREEN_DK = "#15803d"
AMBER = "#d97706"
AMBER_DK = "#b45309"
RED = "#dc2626"
RED_DK = "#b91c1c"
ES_COLOR = "#1d4ed8"
EN_COLOR = "#9ca3af"


def listar_dispositivos(kind):
    """
    Lista (etiqueta, índice) de dispositivos, fusionando el mismo equipo entre
    Host APIs. Muestra el nombre completo pero usa el índice de la API preferida
    (MME) para abrir el stream de forma fiable.
    """
    key = "max_output_channels" if kind == "output" else "max_input_channels"
    ha = sd.query_hostapis()
    groups = {}
    for i, d in enumerate(sd.query_devices()):
        if d[key] <= 0:
            continue
        api = ha[d["hostapi"]]["name"]
        if api not in _HOSTAPI_PREF:
            continue
        name = d["name"].strip()
        norm = name[:28].lower()
        groups.setdefault(norm, []).append((_HOSTAPI_PREF[api], i, name))

    items = []
    for norm, lst in groups.items():
        lst.sort()
        rank, idx, _ = lst[0]
        display = max((x[2] for x in lst), key=len)
        items.append((rank, idx, display))
    items.sort(key=lambda x: (x[0], x[2]))
    return [(display, idx) for rank, idx, display in items]


class App:
    def __init__(self, root):
        self.root = root
        root.title("Traductor de audio en vivo — Gemini")
        root.geometry("760x620")
        root.minsize(640, 520)
        root.configure(bg=BG)

        self.ui_queue = queue.Queue()
        self.engine = TranslatorEngine(
            on_status=lambda s: self.ui_queue.put(("status", s)),
            on_transcript=lambda lang, t: self.ui_queue.put(("tr", lang, t)),
        )

        self._init_style()
        self._build_widgets()
        self._poll_queue()

    # ---- Estilo ---------------------------------------------------------- #
    def _init_style(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Card.TFrame", background=CARD)
        st.configure("BG.TFrame", background=BG)
        st.configure("Card.TLabel", background=CARD, foreground=INK,
                     font=("Segoe UI", 10))
        st.configure("Field.TLabel", background=CARD, foreground=MUTED,
                     font=("Segoe UI", 9, "bold"))
        st.configure("Tip.TLabel", background=BG, foreground=MUTED,
                     font=("Segoe UI", 9))
        st.configure("TCombobox", fieldbackground="white", background="white")
        st.configure("TCheckbutton", background=CARD, foreground=INK)

    def _boton(self, parent, texto, color, color_dk, cmd, state="normal"):
        return tk.Button(parent, text=texto, command=cmd, bg=color, fg="white",
                         activebackground=color_dk, activeforeground="white",
                         font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                         padx=16, pady=7, cursor="hand2",
                         disabledforeground="#e5e7eb", state=state)

    # ---- Construcción ---------------------------------------------------- #
    def _build_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=PRIMARY)
        header.pack(fill="x")
        tk.Label(header, text="🎧  Traductor de audio en vivo", bg=PRIMARY,
                 fg="white", font=("Segoe UI", 16, "bold")).pack(
                     anchor="w", padx=18, pady=(12, 0))
        tk.Label(header, text="Gemini 3.5 Live Translate · traduce lo que suena "
                 "en tu PC", bg=PRIMARY, fg="#c7d2fe",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 12))

        # Tarjeta de ajustes
        card = ttk.Frame(self.root, style="Card.TFrame", padding=14)
        card.pack(fill="x", padx=14, pady=(14, 8))
        for c in (1, 3):
            card.columnconfigure(c, weight=1)

        def fila(r, txt):
            ttk.Label(card, text=txt, style="Field.TLabel").grid(
                row=r, column=0, sticky="w", padx=(0, 8), pady=5)

        fila(0, "Idioma origen")
        self.cb_origen = ttk.Combobox(card, state="readonly", width=16,
                                      values=["Auto-detectar"] + [n for n, _ in IDIOMAS])
        self.cb_origen.current(0)
        self.cb_origen.grid(row=0, column=1, sticky="ew", padx=(0, 16))

        ttk.Label(card, text="Idioma destino", style="Field.TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 8))
        self.cb_destino = ttk.Combobox(card, state="readonly", width=16,
                                       values=[n for n, _ in IDIOMAS])
        idx_def = next((i for i, (_, c) in enumerate(IDIOMAS)
                        if c == config.TARGET_LANGUAGE), 0)
        self.cb_destino.current(idx_def)
        self.cb_destino.grid(row=0, column=3, sticky="ew")
        self.cb_destino.bind("<<ComboboxSelected>>", self.on_cambio_destino)

        fila(1, "Salida de audio")
        self.salidas = [("Predeterminado de Windows", None)] + listar_dispositivos("output")
        self.cb_salida = ttk.Combobox(card, state="readonly",
                                      values=[n for n, _ in self.salidas])
        self.cb_salida.current(0)
        self.cb_salida.grid(row=1, column=1, columnspan=3, sticky="ew", pady=5)

        fila(2, "Capturar de")
        self.entradas = listar_dispositivos("input")
        cap_idx = next((i for i, (n, _) in enumerate(self.entradas)
                        if "cable output" in n.lower()), 0)
        self.cb_captura = ttk.Combobox(card, state="readonly",
                                       values=[n for n, _ in self.entradas])
        if self.entradas:
            self.cb_captura.current(cap_idx)
        self.cb_captura.grid(row=2, column=1, columnspan=3, sticky="ew")

        # Controles
        ctr = tk.Frame(self.root, bg=BG)
        ctr.pack(fill="x", padx=14, pady=4)
        self.btn_iniciar = self._boton(ctr, "▶  Iniciar", GREEN, GREEN_DK,
                                       self.on_iniciar)
        self.btn_iniciar.pack(side="left", padx=(0, 6))
        self.btn_pausa = self._boton(ctr, "⏸  Pausar", AMBER, AMBER_DK,
                                     self.on_pausa, state="disabled")
        self.btn_pausa.pack(side="left", padx=6)
        self.btn_detener = self._boton(ctr, "⏹  Detener", RED, RED_DK,
                                       self.on_detener, state="disabled")
        self.btn_detener.pack(side="left", padx=6)

        self.var_en = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctr, text="Mostrar inglés", variable=self.var_en
                        ).pack(side="right", padx=(6, 0))
        tk.Button(ctr, text="🧹 Limpiar", command=self._limpiar, relief="flat",
                  bd=0, bg=BG, fg=MUTED, activebackground=BG, cursor="hand2",
                  font=("Segoe UI", 9)).pack(side="right", padx=6)

        # Estado
        est = tk.Frame(self.root, bg=BG)
        est.pack(fill="x", padx=16, pady=(6, 2))
        self.lbl_estado = tk.Label(est, text="●  Detenido", bg=BG, fg=MUTED,
                                   font=("Segoe UI", 10, "bold"))
        self.lbl_estado.pack(side="left")

        # Transcripción
        wrap = tk.Frame(self.root, bg="#e5e7eb")
        wrap.pack(fill="both", expand=True, padx=14, pady=(4, 6))
        inner = tk.Frame(wrap, bg=CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self.txt = tk.Text(inner, wrap="word", font=("Segoe UI", 13), bd=0,
                           bg=CARD, fg=INK, padx=14, pady=12,
                           insertbackground=INK, spacing1=2, spacing3=4)
        scroll = ttk.Scrollbar(inner, command=self.txt.yview)
        self.txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.txt.pack(side="left", fill="both", expand=True)
        self.txt.tag_config("es", foreground=ES_COLOR)
        self.txt.tag_config("en", foreground=EN_COLOR,
                            font=("Segoe UI", 11, "italic"))
        self.txt.configure(state="disabled")

        # Footer
        ttk.Label(self.root, style="Tip.TLabel",
                  text="Tip: enruta la fuente (navegador/Zoom) a 'CABLE Input'. "
                       "La 'Salida de audio' debe ser tus audífonos, nunca un cable."
                  ).pack(padx=16, pady=(0, 10), anchor="w")

    # ---- Acciones -------------------------------------------------------- #
    def _codigo(self, combo, lista):
        nombre = combo.get()
        for n, c in lista:
            if n == nombre:
                return c
        return None

    def on_iniciar(self):
        destino = self._codigo(self.cb_destino, IDIOMAS)
        salida = dict(self.salidas).get(self.cb_salida.get())
        captura = dict(self.entradas).get(self.cb_captura.get()) if self.entradas else None
        self.engine.start(target_lang=destino, out_device=salida,
                          capture_device=captura)
        self._set_corriendo(True)

    def on_pausa(self):
        self.engine.toggle_pause()
        self.btn_pausa.config(text="▶  Reanudar" if self.engine.paused
                              else "⏸  Pausar")

    def on_detener(self):
        self.engine.stop()
        self._set_corriendo(False)
        self.btn_pausa.config(text="⏸  Pausar")

    def on_cambio_destino(self, event=None):
        code = self._codigo(self.cb_destino, IDIOMAS)
        if self.engine.is_running():
            self.engine.set_language(code)

    def _limpiar(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")

    def _set_corriendo(self, corriendo):
        estado = "disabled" if corriendo else "readonly"
        for cb in (self.cb_origen, self.cb_salida, self.cb_captura):
            cb.config(state=estado)
        self.cb_destino.config(state="readonly")    # siempre editable (en vivo)
        self.btn_iniciar.config(state="disabled" if corriendo else "normal")
        self.btn_pausa.config(state="normal" if corriendo else "disabled")
        self.btn_detener.config(state="normal" if corriendo else "disabled")

    # ---- Puente motor -> GUI -------------------------------------------- #
    def _poll_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg[0] == "status":
                    self._mostrar_estado(msg[1])
                elif msg[0] == "tr":
                    self._mostrar_transcripcion(msg[1], msg[2])
        except queue.Empty:
            pass
        self.root.after(60, self._poll_queue)

    def _mostrar_estado(self, texto):
        color = MUTED
        if texto.startswith("Traduciendo"):
            color = GREEN
        elif texto.startswith("Pausado"):
            color = AMBER
        elif texto.startswith(("Conectando", "Reconectando", "Cambiando")):
            color = AMBER
        elif texto.startswith("Error"):
            color = RED
        self.lbl_estado.config(text=f"●  {texto}", foreground=color)
        if texto.startswith("Error") or texto == "Detenido":
            self._set_corriendo(False)
            self.btn_pausa.config(text="⏸  Pausar")

    def _mostrar_transcripcion(self, lang, texto):
        if lang == "en" and not self.var_en.get():
            return
        self.txt.configure(state="normal")
        if lang == "en":
            self.txt.insert("end", f"\n[EN] {texto.strip()} ", "en")
        else:
            self.txt.insert("end", texto, "es")
        if float(self.txt.index("end-1c").split(".")[0]) > 500:
            self.txt.delete("1.0", "120.0")
        self.txt.see("end")
        self.txt.configure(state="disabled")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
