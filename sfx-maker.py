import json
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
try:
    import sounddevice as sd
except ImportError:
    sd = None
from scipy.io import wavfile
from scipy.signal import butter, lfilter


class SFXMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("レトロ効果音メーカー v3")
        self.root.geometry("560x760")
        self.root.minsize(520, 700)

        self.sample_rate = 44100
        self.current_audio = None

        self.source_options = ["ノイズ", "サイン波", "矩形波", "三角波", "ノコギリ波", "パルス波", "ノイズ＋矩形波"]
        self.pitch_curve_options = ["直線", "指数", "急降下", "急上昇", "ランダム階段"]
        self.envelope_options = ["指数減衰", "直線減衰", "ADSR", "ゲート", "逆再生風", "ポンピング"]
        self.filter_options = ["なし", "lowpass", "highpass", "bandpass"]

        self.presets = {
            "壁・天井": {
                "duration": 0.05, "source": "ノイズ", "start_pitch": 3500, "end_pitch": 1800,
                "pitch_curve": "直線", "pulse_width": 50, "noise_mix": 0.0,
                "filter_freq": 4200, "filter_type": "highpass", "envelope": "指数減衰",
                "bit_depth": 10, "sample_reduce": 2, "volume": 85,
            },
            "バー（パドル）": {
                "duration": 0.11, "source": "三角波", "start_pitch": 420, "end_pitch": 180,
                "pitch_curve": "指数", "pulse_width": 50, "noise_mix": 0.15,
                "filter_freq": 1300, "filter_type": "lowpass", "envelope": "指数減衰",
                "bit_depth": 12, "sample_reduce": 2, "volume": 85,
            },
            "ブロック（普通）": {
                "duration": 0.13, "source": "矩形波", "start_pitch": 950, "end_pitch": 520,
                "pitch_curve": "直線", "pulse_width": 50, "noise_mix": 0.30,
                "filter_freq": 2400, "filter_type": "bandpass", "envelope": "指数減衰",
                "bit_depth": 9, "sample_reduce": 3, "volume": 90,
            },
            "硬いブロック（弾く）": {
                "duration": 0.035, "source": "パルス波", "start_pitch": 4200, "end_pitch": 2600,
                "pitch_curve": "直線", "pulse_width": 18, "noise_mix": 0.12,
                "filter_freq": 6200, "filter_type": "highpass", "envelope": "ゲート",
                "bit_depth": 8, "sample_reduce": 2, "volume": 90,
            },
            "硬いブロック（破壊）": {
                "duration": 0.38, "source": "ノイズ＋矩形波", "start_pitch": 900, "end_pitch": 90,
                "pitch_curve": "指数", "pulse_width": 45, "noise_mix": 0.65,
                "filter_freq": 1200, "filter_type": "lowpass", "envelope": "指数減衰",
                "bit_depth": 7, "sample_reduce": 5, "volume": 95,
            },
            "アイテム出現": {
                "duration": 0.28, "source": "サイン波", "start_pitch": 640, "end_pitch": 1500,
                "pitch_curve": "指数", "pulse_width": 50, "noise_mix": 0.02,
                "filter_freq": 5000, "filter_type": "なし", "envelope": "ADSR",
                "bit_depth": 12, "sample_reduce": 1, "volume": 75,
            },
            "アイテム取得": {
                "duration": 0.22, "source": "三角波", "start_pitch": 820, "end_pitch": 2200,
                "pitch_curve": "指数", "pulse_width": 50, "noise_mix": 0.05,
                "filter_freq": 4800, "filter_type": "lowpass", "envelope": "ADSR",
                "bit_depth": 10, "sample_reduce": 2, "volume": 80,
            },
            "ミス": {
                "duration": 0.45, "source": "ノコギリ波", "start_pitch": 360, "end_pitch": 70,
                "pitch_curve": "指数", "pulse_width": 50, "noise_mix": 0.10,
                "filter_freq": 1700, "filter_type": "lowpass", "envelope": "直線減衰",
                "bit_depth": 9, "sample_reduce": 3, "volume": 85,
            },
            "レーザー": {
                "duration": 0.18, "source": "パルス波", "start_pitch": 5000, "end_pitch": 700,
                "pitch_curve": "急降下", "pulse_width": 28, "noise_mix": 0.12,
                "filter_freq": 7000, "filter_type": "bandpass", "envelope": "ゲート",
                "bit_depth": 6, "sample_reduce": 4, "volume": 90,
            },
            "爆発": {
                "duration": 0.65, "source": "ノイズ", "start_pitch": 900, "end_pitch": 80,
                "pitch_curve": "指数", "pulse_width": 50, "noise_mix": 0.0,
                "filter_freq": 900, "filter_type": "lowpass", "envelope": "指数減衰",
                "bit_depth": 6, "sample_reduce": 7, "volume": 100,
            },
            "決定": {
                "duration": 0.11, "source": "矩形波", "start_pitch": 900, "end_pitch": 1350,
                "pitch_curve": "直線", "pulse_width": 50, "noise_mix": 0.03,
                "filter_freq": 5000, "filter_type": "なし", "envelope": "ADSR",
                "bit_depth": 10, "sample_reduce": 2, "volume": 80,
            },
            "キャンセル": {
                "duration": 0.14, "source": "矩形波", "start_pitch": 650, "end_pitch": 260,
                "pitch_curve": "直線", "pulse_width": 50, "noise_mix": 0.06,
                "filter_freq": 2500, "filter_type": "lowpass", "envelope": "指数減衰",
                "bit_depth": 9, "sample_reduce": 3, "volume": 80,
            },
        }

        self._build_ui()
        self.apply_preset()

    # ---------------- UI ----------------
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        preset_frame = ttk.LabelFrame(main, text="プリセット")
        preset_frame.pack(fill=tk.X, pady=(0, 8))

        self.preset_var = tk.StringVar(value="壁・天井")
        self.preset_menu = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=["カスタム"] + list(self.presets.keys()),
            state="readonly",
        )
        self.preset_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=8)
        self.preset_menu.bind("<<ComboboxSelected>>", self.apply_preset)

        ttk.Button(preset_frame, text="🎲 ランダム", command=self.randomize_params).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(preset_frame, text="🎛 ちょい変化", command=self.mutate_params).pack(side=tk.LEFT, padx=(0, 8))

        synth_frame = ttk.LabelFrame(main, text="音源 / ピッチ")
        synth_frame.pack(fill=tk.X, pady=8)

        row = 0
        ttk.Label(synth_frame, text="音源タイプ:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        self.source_var = tk.StringVar(value="ノイズ")
        ttk.Combobox(
            synth_frame,
            textvariable=self.source_var,
            values=self.source_options,
            state="readonly",
            width=16,
        ).grid(row=row, column=1, sticky="ew", padx=8, pady=5)

        ttk.Label(synth_frame, text="ピッチカーブ:").grid(row=row, column=2, sticky="w", padx=8, pady=5)
        self.pitch_curve_var = tk.StringVar(value="直線")
        ttk.Combobox(
            synth_frame,
            textvariable=self.pitch_curve_var,
            values=self.pitch_curve_options,
            state="readonly",
            width=12,
        ).grid(row=row, column=3, sticky="ew", padx=8, pady=5)

        self.duration_var = tk.DoubleVar(value=0.1)
        self.start_pitch_var = tk.DoubleVar(value=800)
        self.end_pitch_var = tk.DoubleVar(value=200)
        self.pulse_width_var = tk.DoubleVar(value=50)
        self.noise_mix_var = tk.DoubleVar(value=0)

        row += 1
        self._add_slider(synth_frame, row, "音の長さ", self.duration_var, 0.01, 1.5, "{:.2f} 秒")
        row += 1
        self._add_slider(synth_frame, row, "開始ピッチ", self.start_pitch_var, 20, 8000, "{:.0f} Hz")
        row += 1
        self._add_slider(synth_frame, row, "終了ピッチ", self.end_pitch_var, 20, 8000, "{:.0f} Hz")
        row += 1
        self._add_slider(synth_frame, row, "パルス幅", self.pulse_width_var, 5, 95, "{:.0f} %")
        row += 1
        self._add_slider(synth_frame, row, "ノイズ混合", self.noise_mix_var, 0, 1, "{:.2f}")

        synth_frame.columnconfigure(1, weight=1)
        synth_frame.columnconfigure(3, weight=1)

        shape_frame = ttk.LabelFrame(main, text="音の形 / 加工")
        shape_frame.pack(fill=tk.X, pady=8)

        row = 0
        ttk.Label(shape_frame, text="エンベロープ:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        self.envelope_var = tk.StringVar(value="指数減衰")
        ttk.Combobox(
            shape_frame,
            textvariable=self.envelope_var,
            values=self.envelope_options,
            state="readonly",
            width=14,
        ).grid(row=row, column=1, sticky="ew", padx=8, pady=5)

        ttk.Label(shape_frame, text="フィルター:").grid(row=row, column=2, sticky="w", padx=8, pady=5)
        self.filter_var = tk.StringVar(value="highpass")
        ttk.Combobox(
            shape_frame,
            textvariable=self.filter_var,
            values=self.filter_options,
            state="readonly",
            width=12,
        ).grid(row=row, column=3, sticky="ew", padx=8, pady=5)

        self.filter_freq_var = tk.DoubleVar(value=3000)
        self.bit_depth_var = tk.DoubleVar(value=12)
        self.sample_reduce_var = tk.DoubleVar(value=1)
        self.volume_var = tk.DoubleVar(value=85)

        row += 1
        self._add_slider(shape_frame, row, "フィルター周波数", self.filter_freq_var, 100, 10000, "{:.0f} Hz")
        row += 1
        self._add_slider(shape_frame, row, "ビット深度", self.bit_depth_var, 2, 16, "{:.0f} bit")
        row += 1
        self._add_slider(shape_frame, row, "サンプル荒らし", self.sample_reduce_var, 1, 20, "x{:.0f}")
        row += 1
        self._add_slider(shape_frame, row, "音量", self.volume_var, 0, 100, "{:.0f} %")

        shape_frame.columnconfigure(1, weight=1)
        shape_frame.columnconfigure(3, weight=1)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=12)
        ttk.Button(btn_frame, text="▶ 再生", command=self.play_sound).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="■ 停止", command=self.stop_sound).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 WAV保存", command=self.save_wav).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⚙ 設定保存", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 設定読込", command=self.load_settings).pack(side=tk.LEFT, padx=5)

        note = (
            "メモ: ノイズ混合・ビット深度・サンプル荒らしを強めると、"
            "PSG/チップチューンっぽい荒い音になります。設定保存/読込はJSON形式です。"
        )
        ttk.Label(main, text=note, wraplength=520, foreground="#555555").pack(anchor="w", pady=(4, 0))

    def _add_slider(self, parent, row, label, var, min_value, max_value, fmt):
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        scale = ttk.Scale(parent, from_=min_value, to=max_value, variable=var, orient=tk.HORIZONTAL)
        scale.grid(row=row, column=1, columnspan=2, sticky="ew", padx=8, pady=4)
        value_label = ttk.Label(parent, width=10, anchor="e")
        value_label.grid(row=row, column=3, sticky="e", padx=8, pady=4)

        def update_label(*_):
            value_label.config(text=fmt.format(var.get()))
            self.current_audio = None

        var.trace_add("write", update_label)
        update_label()
        return scale

    # ---------------- Parameter operations ----------------
    def apply_preset(self, event=None):
        preset = self.presets.get(self.preset_var.get())
        if not preset:
            return
        self.set_params(preset, mark_custom=False)

    def get_params(self):
        return {
            "duration": float(self.duration_var.get()),
            "source": self.source_var.get(),
            "start_pitch": float(self.start_pitch_var.get()),
            "end_pitch": float(self.end_pitch_var.get()),
            "pitch_curve": self.pitch_curve_var.get(),
            "pulse_width": float(self.pulse_width_var.get()),
            "noise_mix": float(self.noise_mix_var.get()),
            "filter_freq": float(self.filter_freq_var.get()),
            "filter_type": self.filter_var.get(),
            "envelope": self.envelope_var.get(),
            "bit_depth": float(self.bit_depth_var.get()),
            "sample_reduce": float(self.sample_reduce_var.get()),
            "volume": float(self.volume_var.get()),
        }

    def set_params(self, params, mark_custom=True):
        def number(name, default, low, high):
            try:
                value = float(params.get(name, default))
            except (TypeError, ValueError):
                value = default
            return max(low, min(high, value))

        def choice(name, default, options):
            value = str(params.get(name, default))
            return value if value in options else default

        self.duration_var.set(number("duration", 0.1, 0.01, 1.5))
        self.source_var.set(choice("source", "ノイズ", self.source_options))
        self.start_pitch_var.set(number("start_pitch", 800, 20, 8000))
        self.end_pitch_var.set(number("end_pitch", 200, 20, 8000))
        self.pitch_curve_var.set(choice("pitch_curve", "直線", self.pitch_curve_options))
        self.pulse_width_var.set(number("pulse_width", 50, 5, 95))
        self.noise_mix_var.set(number("noise_mix", 0, 0, 1))
        self.filter_freq_var.set(number("filter_freq", 3000, 100, 10000))
        self.filter_var.set(choice("filter_type", "なし", self.filter_options))
        self.envelope_var.set(choice("envelope", "指数減衰", self.envelope_options))
        self.bit_depth_var.set(number("bit_depth", 12, 2, 16))
        self.sample_reduce_var.set(number("sample_reduce", 1, 1, 20))
        self.volume_var.set(number("volume", 85, 0, 100))

        if mark_custom:
            self.preset_var.set("カスタム")
        self.current_audio = None

    def save_settings(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("SFX settings", "*.json"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="設定を保存",
        )
        if not filepath:
            return

        data = {
            "app": "retro_sfx_maker",
            "version": 3,
            "sample_rate": self.sample_rate,
            "preset_name": self.preset_var.get(),
            "params": self.get_params(),
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror("保存エラー", f"設定を保存できませんでした。\n{e}")
            return

        messagebox.showinfo("保存完了", f"{filepath}\nに設定を保存しました。")

    def load_settings(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("SFX settings", "*.json"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="設定を読み込み",
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("読み込みエラー", f"設定ファイルを読み込めませんでした。\n{e}")
            return

        params = data.get("params", data)
        if not isinstance(params, dict):
            messagebox.showerror("読み込みエラー", "設定ファイルの形式が正しくありません。")
            return

        self.set_params(params, mark_custom=True)
        messagebox.showinfo("読み込み完了", f"{filepath}\nから設定を読み込みました。")

    def randomize_params(self):
        self.preset_var.set("カスタム")
        source = random.choice(self.source_options)
        self.source_var.set(source)
        self.duration_var.set(random.uniform(0.03, 0.75))
        self.start_pitch_var.set(random.choice([random.uniform(60, 800), random.uniform(800, 3500), random.uniform(3500, 7600)]))
        self.end_pitch_var.set(random.choice([random.uniform(40, 500), random.uniform(500, 2500), random.uniform(2500, 6500)]))
        self.pitch_curve_var.set(random.choice(self.pitch_curve_options))
        self.pulse_width_var.set(random.uniform(10, 90))
        self.noise_mix_var.set(0.0 if source == "ノイズ" else random.uniform(0.0, 0.75))
        self.filter_var.set(random.choice(self.filter_options))
        self.filter_freq_var.set(random.uniform(300, 9000))
        self.envelope_var.set(random.choice(self.envelope_options))
        self.bit_depth_var.set(random.randint(4, 16))
        self.sample_reduce_var.set(random.randint(1, 10))
        self.volume_var.set(random.uniform(70, 100))
        self.current_audio = None
        self.play_sound()

    def mutate_params(self):
        self.preset_var.set("カスタム")

        def clamp(value, low, high):
            return max(low, min(high, value))

        self.duration_var.set(clamp(self.duration_var.get() * random.uniform(0.82, 1.18), 0.01, 1.5))
        self.start_pitch_var.set(clamp(self.start_pitch_var.get() * random.uniform(0.75, 1.25), 20, 8000))
        self.end_pitch_var.set(clamp(self.end_pitch_var.get() * random.uniform(0.75, 1.25), 20, 8000))
        self.pulse_width_var.set(clamp(self.pulse_width_var.get() + random.uniform(-12, 12), 5, 95))
        self.noise_mix_var.set(clamp(self.noise_mix_var.get() + random.uniform(-0.15, 0.15), 0, 1))
        self.filter_freq_var.set(clamp(self.filter_freq_var.get() * random.uniform(0.75, 1.25), 100, 10000))
        self.bit_depth_var.set(clamp(round(self.bit_depth_var.get() + random.choice([-1, 0, 1])), 2, 16))
        self.sample_reduce_var.set(clamp(round(self.sample_reduce_var.get() + random.choice([-1, 0, 1])), 1, 20))
        self.current_audio = None
        self.play_sound()

    # ---------------- Synthesis ----------------
    def generate_audio(self):
        duration = max(0.01, float(self.duration_var.get()))
        n = max(1, int(self.sample_rate * duration))
        t = np.arange(n) / self.sample_rate

        start_pitch = float(self.start_pitch_var.get())
        end_pitch = float(self.end_pitch_var.get())
        curve = self.pitch_curve_var.get()
        freqs = self._make_pitch_curve(start_pitch, end_pitch, curve, n)

        phase = np.cumsum(2.0 * np.pi * freqs / self.sample_rate)
        source = self.source_var.get()
        audio = self._make_source(source, phase)

        audio *= self._make_envelope(self.envelope_var.get(), t, duration)
        audio = self._apply_filter(audio, self.filter_var.get(), float(self.filter_freq_var.get()))
        audio = self._apply_bitcrusher(audio, int(round(self.bit_depth_var.get())), int(round(self.sample_reduce_var.get())))

        # 最終クリック防止用のごく短いフェード。鋭さは残しつつ破綻だけ防ぐ。
        audio = self._safe_edge_fade(audio, fade_ms=1.5)

        peak = np.max(np.abs(audio)) if len(audio) else 0
        if peak > 0:
            audio = audio / peak

        audio *= float(self.volume_var.get()) / 100.0
        audio = np.clip(audio, -1.0, 1.0).astype(np.float32)
        self.current_audio = audio
        return audio

    def _make_pitch_curve(self, start_pitch, end_pitch, curve, n):
        if n <= 1:
            return np.array([start_pitch], dtype=np.float32)
        x = np.linspace(0.0, 1.0, n)

        if curve == "指数":
            start = max(1.0, start_pitch)
            end = max(1.0, end_pitch)
            freqs = start * ((end / start) ** x)
        elif curve == "急降下":
            shaped = x ** 0.28
            freqs = start_pitch + (end_pitch - start_pitch) * shaped
        elif curve == "急上昇":
            shaped = x ** 2.7
            freqs = start_pitch + (end_pitch - start_pitch) * shaped
        elif curve == "ランダム階段":
            steps = max(4, min(32, int(n / (self.sample_rate * 0.02))))
            points = np.linspace(start_pitch, end_pitch, steps)
            jitter = np.random.uniform(0.75, 1.25, steps)
            stepped = np.repeat(points * jitter, int(np.ceil(n / steps)))[:n]
            freqs = stepped
        else:
            freqs = start_pitch + (end_pitch - start_pitch) * x

        return np.clip(freqs, 20.0, self.sample_rate * 0.45).astype(np.float32)

    def _make_source(self, source, phase):
        n = len(phase)
        noise = np.random.uniform(-1.0, 1.0, n)
        noise_mix = float(self.noise_mix_var.get())
        pulse_width = np.clip(float(self.pulse_width_var.get()) / 100.0, 0.05, 0.95)
        cycle = (phase / (2.0 * np.pi)) % 1.0

        if source == "ノイズ":
            return noise.astype(np.float32)
        if source == "サイン波":
            wave = np.sin(phase)
        elif source == "矩形波":
            wave = np.where(np.sin(phase) >= 0, 1.0, -1.0)
        elif source == "三角波":
            wave = (2.0 / np.pi) * np.arcsin(np.sin(phase))
        elif source == "ノコギリ波":
            wave = 2.0 * cycle - 1.0
        elif source == "パルス波":
            wave = np.where(cycle < pulse_width, 1.0, -1.0)
        elif source == "ノイズ＋矩形波":
            wave = np.where(np.sin(phase) >= 0, 1.0, -1.0)
            noise_mix = max(noise_mix, 0.35)
        else:
            wave = noise

        return ((1.0 - noise_mix) * wave + noise_mix * noise).astype(np.float32)

    def _make_envelope(self, kind, t, duration):
        if len(t) == 0:
            return np.array([], dtype=np.float32)
        x = np.clip(t / max(duration, 1e-6), 0.0, 1.0)

        if kind == "直線減衰":
            env = 1.0 - x
        elif kind == "ADSR":
            attack = 0.10
            decay = 0.18
            sustain_level = 0.55
            release_start = 0.62
            env = np.zeros_like(x)
            attack_mask = x < attack
            decay_mask = (x >= attack) & (x < attack + decay)
            sustain_mask = (x >= attack + decay) & (x < release_start)
            release_mask = x >= release_start

            env[attack_mask] = x[attack_mask] / max(attack, 1e-6)
            env[decay_mask] = 1.0 - (1.0 - sustain_level) * ((x[decay_mask] - attack) / decay)
            env[sustain_mask] = sustain_level
            env[release_mask] = sustain_level * (1.0 - (x[release_mask] - release_start) / max(1.0 - release_start, 1e-6))
        elif kind == "ゲート":
            env = np.ones_like(x)
            release = 0.10
            mask = x > (1.0 - release)
            env[mask] = 1.0 - (x[mask] - (1.0 - release)) / release
        elif kind == "逆再生風":
            env = np.sin(x * np.pi * 0.5) ** 1.8
        elif kind == "ポンピング":
            base = np.exp(-3.8 * x)
            pump = 0.62 + 0.38 * (0.5 + 0.5 * np.sin(2.0 * np.pi * 18.0 * t))
            env = base * pump
        else:
            env = np.exp(-5.0 * x)

        return np.clip(env, 0.0, 1.0).astype(np.float32)

    def _apply_filter(self, audio, filter_type, cutoff_freq):
        if filter_type == "なし" or len(audio) < 8:
            return audio

        nyq = 0.5 * self.sample_rate
        normal_cutoff = np.clip(cutoff_freq / nyq, 0.01, 0.99)

        try:
            if filter_type == "bandpass":
                low = max(0.01, normal_cutoff * 0.65)
                high = min(0.99, normal_cutoff * 1.35)
                if low >= high:
                    low = max(0.01, normal_cutoff - 0.05)
                    high = min(0.99, normal_cutoff + 0.05)
                b, a = butter(2, [low, high], btype="bandpass", analog=False)
            else:
                b, a = butter(2, normal_cutoff, btype=filter_type, analog=False)
            return lfilter(b, a, audio).astype(np.float32)
        except ValueError:
            return audio

    def _apply_bitcrusher(self, audio, bit_depth, sample_reduce):
        crushed = audio.astype(np.float32)
        sample_reduce = max(1, int(sample_reduce))
        if sample_reduce > 1 and len(crushed) > sample_reduce:
            crushed = np.repeat(crushed[::sample_reduce], sample_reduce)[: len(crushed)]

        bit_depth = int(np.clip(bit_depth, 2, 16))
        if bit_depth < 16:
            levels = (2 ** bit_depth) - 1
            crushed = np.round((crushed + 1.0) * 0.5 * levels) / levels
            crushed = crushed * 2.0 - 1.0
        return crushed.astype(np.float32)

    def _safe_edge_fade(self, audio, fade_ms=1.5):
        if len(audio) < 4:
            return audio
        fade_len = min(int(self.sample_rate * fade_ms / 1000.0), len(audio) // 4)
        if fade_len <= 1:
            return audio
        out = audio.copy()
        out[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
        out[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
        return out

    # ---------------- Playback / save ----------------
    def play_sound(self):
        if sd is None:
            messagebox.showerror(
                "再生エラー",
                "sounddevice が見つかりません。\n再生するには pip install sounddevice を実行してください。\nWAV保存はこのまま使えます。",
            )
            return
        audio = self.generate_audio()
        sd.stop()
        sd.play(audio, self.sample_rate)

    def stop_sound(self):
        if sd is not None:
            sd.stop()

    def save_wav(self):
        if self.current_audio is None:
            self.generate_audio()

        filepath = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            title="WAVファイルとして保存",
        )
        if not filepath:
            return

        audio_16bit = np.int16(np.clip(self.current_audio, -1.0, 1.0) * 32767)
        wavfile.write(filepath, self.sample_rate, audio_16bit)
        messagebox.showinfo("保存完了", f"{filepath}\nにWAVファイルを保存しました。")


if __name__ == "__main__":
    root = tk.Tk()
    app = SFXMaker(root)
    root.mainloop()
