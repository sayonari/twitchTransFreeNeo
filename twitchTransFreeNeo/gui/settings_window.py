#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Dict, Any, Callable


class SettingsWindow:
    """設定画面クラス"""
    
    def __init__(self, parent, config: Dict[str, Any], on_config_change: Callable[[Dict[str, Any]], None]):
        self.parent = parent
        self.config = config.copy()
        self.on_config_change = on_config_change
        self.window = None
        self._create_window()
    
    def _create_window(self):
        """設定ウィンドウを作成"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("設定 - twitchTransFreeNeo")
        self.window.geometry("700x700")
        self.window.resizable(True, True)
        
        # モーダルにする
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # ノートブック（タブ）作成
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ノートブックの参照を保持（イベントバインディング前に設定）
        self.notebook = notebook
        
        # 各タブを作成
        self._create_basic_tab(notebook)
        self._create_translation_tab(notebook)
        self._create_filter_tab(notebook)
        self._create_tts_tab(notebook)
        self._create_gui_tab(notebook)
        
        # タブ切り替え時の即座の更新を有効にする
        notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # 各タブを強制的に一度表示して初期化
        for i in range(notebook.index('end')):
            notebook.select(i)
            self.window.update_idletasks()
            # 現在のタブを更新
            current_tab = notebook.nametowidget(notebook.select())
            if current_tab:
                current_tab.update()
                # Canvas要素を探して更新
                for child in current_tab.winfo_children():
                    if isinstance(child, tk.Canvas):
                        child.update_idletasks()
                        child.configure(scrollregion=child.bbox("all"))
        
        notebook.select(0)  # 最初のタブに戻る
        self.window.update_idletasks()
        
        # ボタンフレーム
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # ボタン
        ttk.Button(button_frame, text="キャンセル", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(button_frame, text="適用", command=self.apply).pack(side='right', padx=5)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side='right', padx=5)
    
    def _create_basic_tab(self, notebook):
        """基本設定タブ"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="基本設定")
        frame.update_idletasks()  # 即座に更新
        
        # スクロール可能にする
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 必須設定
        ttk.Label(scrollable_frame, text="必須設定", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=10)
        
        ttk.Label(scrollable_frame, text="Twitchチャンネル名:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.channel_var = tk.StringVar(value=self.config.get("twitch_channel", ""))
        ttk.Entry(scrollable_frame, textvariable=self.channel_var, width=30).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(scrollable_frame, text="翻訳bot用ユーザー名:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.username_var = tk.StringVar(value=self.config.get("trans_username", ""))
        ttk.Entry(scrollable_frame, textvariable=self.username_var, width=30).grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(scrollable_frame, text="OAuthトークン:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.oauth_var = tk.StringVar(value=self.config.get("trans_oauth", ""))
        oauth_entry = ttk.Entry(scrollable_frame, textvariable=self.oauth_var, width=30, show="*")
        oauth_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        # OAuthトークン取得ボタン
        ttk.Button(scrollable_frame, text="OAuthトークン取得", 
                  command=lambda: webbrowser.open("https://www.sayonari.com/trans_asr/ttfn_oauth.html")).grid(row=4, column=1, sticky='w', padx=5, pady=2)
        
        # 表示設定
        ttk.Label(scrollable_frame, text="表示設定", font=('', 12, 'bold')).grid(row=5, column=0, columnspan=2, sticky='w', pady=(20, 10))
        
        ttk.Label(scrollable_frame, text="翻訳テキストの色:").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        self.color_var = tk.StringVar(value=self.config.get("trans_text_color", "GoldenRod"))
        color_combo = ttk.Combobox(scrollable_frame, textvariable=self.color_var, width=27)
        color_combo['values'] = ['Blue', 'Coral', 'DodgerBlue', 'SpringGreen', 'YellowGreen', 'Green', 
                                'OrangeRed', 'Red', 'GoldenRod', 'HotPink', 'CadetBlue', 'SeaGreen', 
                                'Chocolate', 'BlueViolet', 'Firebrick']
        color_combo.grid(row=6, column=1, sticky='ew', padx=5, pady=2)
        
        self.show_name_var = tk.BooleanVar(value=self.config.get("show_by_name", True))
        ttk.Checkbutton(scrollable_frame, text="ユーザー名を表示", variable=self.show_name_var).grid(row=7, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        self.show_lang_var = tk.BooleanVar(value=self.config.get("show_by_lang", True))
        ttk.Checkbutton(scrollable_frame, text="言語情報を表示", variable=self.show_lang_var).grid(row=8, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # その他
        ttk.Label(scrollable_frame, text="その他", font=('', 12, 'bold')).grid(row=9, column=0, columnspan=2, sticky='w', pady=(20, 10))
        
        self.debug_var = tk.BooleanVar(value=self.config.get("debug", False))
        ttk.Checkbutton(scrollable_frame, text="デバッグモード", variable=self.debug_var).grid(row=10, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        self.auto_start_var = tk.BooleanVar(value=self.config.get("auto_start", False))
        ttk.Checkbutton(scrollable_frame, text="起動時に自動接続", variable=self.auto_start_var).grid(row=11, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        self.view_only_mode_var = tk.BooleanVar(value=self.config.get("view_only_mode", False))
        ttk.Checkbutton(scrollable_frame, text="表示のみモード（チャットに投稿しない）", variable=self.view_only_mode_var).grid(row=12, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # Grid設定
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Canvasの初期更新
        frame.update_idletasks()
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _create_translation_tab(self, notebook):
        """翻訳設定タブ"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="翻訳設定")
        frame.update_idletasks()  # 即座に更新
        
        # 言語設定
        ttk.Label(frame, text="言語設定", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=10)
        
        ttk.Label(frame, text="ホーム言語:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.home_lang_var = tk.StringVar(value=self.config.get("lang_trans_to_home", "ja"))
        home_lang_combo = ttk.Combobox(frame, textvariable=self.home_lang_var, width=27)
        home_lang_combo['values'] = ['ja', 'en', 'ko', 'zh-CN', 'zh-TW', 'fr', 'de', 'es', 'pt', 'it']
        home_lang_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame, text="外国語:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.other_lang_var = tk.StringVar(value=self.config.get("lang_home_to_other", "en"))
        other_lang_combo = ttk.Combobox(frame, textvariable=self.other_lang_var, width=27)
        other_lang_combo['values'] = ['en', 'ja', 'ko', 'zh-CN', 'zh-TW', 'fr', 'de', 'es', 'pt', 'it']
        other_lang_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        # 翻訳エンジン設定
        ttk.Label(frame, text="翻訳エンジン設定", font=('', 12, 'bold')).grid(row=3, column=0, columnspan=2, sticky='w', pady=(20, 10))
        
        ttk.Label(frame, text="翻訳エンジン:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.translator_var = tk.StringVar(value=self.config.get("translator", "google"))
        translator_combo = ttk.Combobox(frame, textvariable=self.translator_var, width=27)
        translator_combo['values'] = ['google', 'deepl']
        translator_combo.grid(row=4, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame, text="Google翻訳サーバー:").grid(row=5, column=0, sticky='w', padx=5, pady=2)
        self.google_suffix_var = tk.StringVar(value=self.config.get("google_translate_suffix", "co.jp"))
        suffix_combo = ttk.Combobox(frame, textvariable=self.google_suffix_var, width=27)
        suffix_combo['values'] = ['co.jp', 'com', 'co.uk', 'fr', 'de']
        suffix_combo.grid(row=5, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame, text="DeepL APIキー (オプション):").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        self.deepl_key_var = tk.StringVar(value=self.config.get("deepl_api_key", ""))
        deepl_entry = ttk.Entry(frame, textvariable=self.deepl_key_var, width=30, show="*")
        deepl_entry.grid(row=6, column=1, sticky='ew', padx=5, pady=2)
        
        frame.grid_columnconfigure(1, weight=1)
    
    def _create_filter_tab(self, notebook):
        """フィルタ設定タブ"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="フィルタ設定")
        frame.update_idletasks()  # 即座に更新
        
        # 無視する言語
        ttk.Label(frame, text="無視する言語 (カンマ区切り):", font=('', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        self.ignore_lang_var = tk.StringVar(value=','.join(self.config.get("ignore_lang", [])))
        ttk.Entry(frame, textvariable=self.ignore_lang_var, width=50).grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        
        # 無視するユーザー
        ttk.Label(frame, text="無視するユーザー (カンマ区切り):", font=('', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=(10, 5))
        self.ignore_users_var = tk.StringVar(value=','.join(self.config.get("ignore_users", [])))
        ttk.Entry(frame, textvariable=self.ignore_users_var, width=50).grid(row=3, column=0, sticky='ew', padx=5, pady=2)
        
        # 無視するテキスト
        ttk.Label(frame, text="無視するテキスト (カンマ区切り):", font=('', 10, 'bold')).grid(row=4, column=0, sticky='w', pady=(10, 5))
        ignore_text = tk.Text(frame, height=3, width=50)
        ignore_text.grid(row=5, column=0, sticky='ew', padx=5, pady=2)
        ignore_text.insert('1.0', ','.join(self.config.get("ignore_line", [])))
        self.ignore_line_text = ignore_text
        
        # 削除する単語
        ttk.Label(frame, text="削除する単語 (カンマ区切り):", font=('', 10, 'bold')).grid(row=6, column=0, sticky='w', pady=(10, 5))
        delete_text = tk.Text(frame, height=3, width=50)
        delete_text.grid(row=7, column=0, sticky='ew', padx=5, pady=2)
        delete_text.insert('1.0', ','.join(self.config.get("delete_words", [])))
        self.delete_words_text = delete_text
        
        frame.grid_columnconfigure(0, weight=1)
    
    def _create_tts_tab(self, notebook):
        """TTS設定タブ"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="TTS設定")
        frame.update_idletasks()  # 即座に更新
        
        # スクロール可能にする
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # TTS有効化
        self.tts_enabled_var = tk.BooleanVar(value=self.config.get("tts_enabled", False))
        ttk.Checkbutton(scrollable_frame, text="TTSを有効にする", variable=self.tts_enabled_var).pack(anchor='w', pady=10)
        
        # 2列レイアウトのためのフレーム
        two_column_frame = ttk.Frame(scrollable_frame)
        two_column_frame.pack(fill='both', expand=True, padx=10)
        
        # 左列: TTS設定
        left_frame = ttk.LabelFrame(two_column_frame, text="TTS設定", padding=10)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.tts_in_var = tk.BooleanVar(value=self.config.get("tts_in", False))
        ttk.Checkbutton(left_frame, text="入力テキストを読み上げ", variable=self.tts_in_var).pack(anchor='w', pady=2)
        
        self.tts_out_var = tk.BooleanVar(value=self.config.get("tts_out", False))
        ttk.Checkbutton(left_frame, text="翻訳テキストを読み上げ", variable=self.tts_out_var).pack(anchor='w', pady=2)
        
        # 右列: 読み上げ内容
        right_frame = ttk.LabelFrame(two_column_frame, text="読み上げ内容", padding=10)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        # 既存のtts_read_usernameとの互換性を保つ
        old_username_setting = self.config.get("tts_read_username", True)
        
        self.tts_read_username_input_var = tk.BooleanVar(value=self.config.get("tts_read_username_input", old_username_setting))
        ttk.Checkbutton(right_frame, text="ユーザー名（入力言語）を読み上げ", variable=self.tts_read_username_input_var).pack(anchor='w', pady=2)
        
        self.tts_read_username_output_var = tk.BooleanVar(value=self.config.get("tts_read_username_output", old_username_setting))
        ttk.Checkbutton(right_frame, text="ユーザー名（翻訳言語）を読み上げ", variable=self.tts_read_username_output_var).pack(anchor='w', pady=2)
        
        self.tts_read_content_var = tk.BooleanVar(value=self.config.get("tts_read_content", True))
        ttk.Checkbutton(right_frame, text="発言内容を読み上げ", variable=self.tts_read_content_var).pack(anchor='w', pady=2)
        
        self.tts_read_lang_var = tk.BooleanVar(value=self.config.get("tts_read_lang", False))
        ttk.Checkbutton(right_frame, text="言語情報を読み上げ", variable=self.tts_read_lang_var).pack(anchor='w', pady=2)
        
        # 列の重みを設定
        two_column_frame.grid_columnconfigure(0, weight=1)
        two_column_frame.grid_columnconfigure(1, weight=1)
        
        # TTS詳細設定
        detail_frame = ttk.LabelFrame(scrollable_frame, text="TTS詳細設定", padding=10)
        detail_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # 詳細設定のグリッド
        ttk.Label(detail_frame, text="TTS種類:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.tts_kind_var = tk.StringVar(value=self.config.get("tts_kind", "gTTS"))
        tts_combo = ttk.Combobox(detail_frame, textvariable=self.tts_kind_var, width=20)
        tts_combo['values'] = ['gTTS', 'CeVIO']
        tts_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(detail_frame, text="CeVIOキャスト名:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.cevio_cast_var = tk.StringVar(value=self.config.get("cevio_cast", "さとうささら"))
        ttk.Entry(detail_frame, textvariable=self.cevio_cast_var, width=30).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(detail_frame, text="最大読み上げ文字数:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.tts_max_length_var = tk.IntVar(value=self.config.get("tts_text_max_length", 30))
        ttk.Spinbox(detail_frame, from_=0, to=200, textvariable=self.tts_max_length_var, width=30).grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(detail_frame, text="省略時のメッセージ:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.tts_omit_var = tk.StringVar(value=self.config.get("tts_message_for_omitting", "以下略"))
        ttk.Entry(detail_frame, textvariable=self.tts_omit_var, width=30).grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        detail_frame.grid_columnconfigure(1, weight=1)
        
        # 読み上げ言語制限
        lang_frame = ttk.LabelFrame(scrollable_frame, text="読み上げ言語制限", padding=10)
        lang_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(lang_frame, text="カンマ区切りで言語コードを入力（空白で全言語）:").pack(anchor='w')
        self.read_only_lang_var = tk.StringVar(value=','.join(self.config.get("read_only_these_lang", [])))
        ttk.Entry(lang_frame, textvariable=self.read_only_lang_var, width=50).pack(fill='x', pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Canvasの初期更新
        frame.update_idletasks()
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _create_gui_tab(self, notebook):
        """GUI設定タブ"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="GUI設定")
        frame.update_idletasks()  # 即座に更新
        
        # 外観設定
        ttk.Label(frame, text="外観設定", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=10)
        
        ttk.Label(frame, text="フォントサイズ:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.font_size_var = tk.IntVar(value=self.config.get("font_size", 12))
        ttk.Spinbox(frame, from_=8, to=24, textvariable=self.font_size_var, width=28).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # ウィンドウサイズ
        ttk.Label(frame, text="ウィンドウサイズ", font=('', 12, 'bold')).grid(row=2, column=0, columnspan=2, sticky='w', pady=(20, 10))
        
        ttk.Label(frame, text="幅:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.window_width_var = tk.IntVar(value=self.config.get("window_width", 1200))
        ttk.Spinbox(frame, from_=800, to=1920, textvariable=self.window_width_var, width=28).grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame, text="高さ:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.window_height_var = tk.IntVar(value=self.config.get("window_height", 800))
        ttk.Spinbox(frame, from_=600, to=1080, textvariable=self.window_height_var, width=28).grid(row=4, column=1, sticky='ew', padx=5, pady=2)
        
        frame.grid_columnconfigure(1, weight=1)
    
    def _collect_config(self) -> Dict[str, Any]:
        """GUI から設定を収集"""
        new_config = {
            "twitch_channel": self.channel_var.get().strip(),
            "trans_username": self.username_var.get().strip(),
            "trans_oauth": self.oauth_var.get().strip(),
            "trans_text_color": self.color_var.get(),
            "show_by_name": self.show_name_var.get(),
            "show_by_lang": self.show_lang_var.get(),
            "debug": self.debug_var.get(),
            "auto_start": self.auto_start_var.get(),
            "view_only_mode": self.view_only_mode_var.get(),
            
            "lang_trans_to_home": self.home_lang_var.get(),
            "lang_home_to_other": self.other_lang_var.get(),
            "translator": self.translator_var.get(),
            "google_translate_suffix": self.google_suffix_var.get(),
            "deepl_api_key": self.deepl_key_var.get().strip(),
            
            "ignore_lang": [lang.strip() for lang in self.ignore_lang_var.get().split(',') if lang.strip()],
            "ignore_users": [user.strip() for user in self.ignore_users_var.get().split(',') if user.strip()],
            "ignore_line": [line.strip() for line in self.ignore_line_text.get('1.0', 'end-1c').split(',') if line.strip()],
            "delete_words": [word.strip() for word in self.delete_words_text.get('1.0', 'end-1c').split(',') if word.strip()],
            
            "tts_enabled": self.tts_enabled_var.get(),
            "tts_in": self.tts_in_var.get(),
            "tts_out": self.tts_out_var.get(),
            "tts_read_username_input": self.tts_read_username_input_var.get(),
            "tts_read_username_output": self.tts_read_username_output_var.get(),
            "tts_read_content": self.tts_read_content_var.get(),
            "tts_read_lang": self.tts_read_lang_var.get(),
            "tts_kind": self.tts_kind_var.get(),
            "cevio_cast": self.cevio_cast_var.get(),
            "tts_text_max_length": self.tts_max_length_var.get(),
            "tts_message_for_omitting": self.tts_omit_var.get(),
            "read_only_these_lang": [lang.strip() for lang in self.read_only_lang_var.get().split(',') if lang.strip()],
            
            "font_size": self.font_size_var.get(),
            "window_width": self.window_width_var.get(),
            "window_height": self.window_height_var.get()
        }
        
        # 既存設定をマージ
        result = self.config.copy()
        result.update(new_config)
        return result
    
    def _validate_config(self, config: Dict[str, Any]) -> tuple:
        """設定の妥当性をチェック"""
        errors = []
        
        if not config.get("twitch_channel"):
            errors.append("Twitchチャンネル名は必須です")
        
        if not config.get("trans_username"):
            errors.append("翻訳bot用ユーザー名は必須です")
        
        if not config.get("trans_oauth"):
            errors.append("OAuthトークンは必須です")
        
        if config.get("translator") not in ["google", "deepl"]:
            errors.append("翻訳エンジンは 'google' または 'deepl' を選択してください")
        
        return len(errors) == 0, errors
    
    def apply(self):
        """設定を適用"""
        new_config = self._collect_config()
        is_valid, errors = self._validate_config(new_config)
        
        if not is_valid:
            messagebox.showerror("設定エラー", "\n".join(errors))
            return
        
        self.config = new_config
        self.on_config_change(new_config)
        messagebox.showinfo("設定", "設定を適用しました。\n\nTwitchに接続中の場合は、新しい設定を反映するため自動的に再接続されます。")
    
    def ok(self):
        """OK ボタン"""
        new_config = self._collect_config()
        is_valid, errors = self._validate_config(new_config)
        
        if not is_valid:
            messagebox.showerror("設定エラー", "\n".join(errors))
            return
        
        self.config = new_config
        self.on_config_change(new_config)
        self.window.destroy()
    
    def cancel(self):
        """キャンセル"""
        self.window.destroy()
    
    def _on_tab_changed(self, event):
        """タブ変更時のコールバック"""
        # notebookが設定されていない場合は何もしない
        if not hasattr(self, 'notebook') or not self.notebook:
            return
        
        # 現在のタブを取得
        current_tab = event.widget.select()
        
        # 強制的に更新
        self.window.update_idletasks()
        
        # タブ内のウィジェットを再描画
        if current_tab:
            try:
                tab_widget = self.notebook.nametowidget(current_tab)
                if tab_widget:
                    tab_widget.update()
                    # Canvasを含むタブの場合、Canvasも更新
                    for child in tab_widget.winfo_children():
                        if isinstance(child, tk.Canvas):
                            child.update_idletasks()
                            # スクロール領域を再計算
                            child.configure(scrollregion=child.bbox("all"))
                        child.update()
            except tk.TclError:
                # ウィジェットが存在しない場合のエラーを無視
                pass


# SimpleSettingsWindowのエイリアスを作成（互換性のため）
SimpleSettingsWindow = SettingsWindow