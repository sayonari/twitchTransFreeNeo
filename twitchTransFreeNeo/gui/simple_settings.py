#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Dict, Any, Callable

class SimpleSettingsWindow:
    """簡略化された設定画面"""
    
    def __init__(self, parent, config: Dict[str, Any], on_config_change: Callable[[Dict[str, Any]], None]):
        self.parent = parent
        self.config = config.copy()
        self.on_config_change = on_config_change
        self.window = None
        self.language_map = self._init_language_map()
        self._create_window()
    
    def _init_language_map(self) -> Dict[str, list]:
        """地域別言語マップを初期化"""
        return {
            '東アジア': [
                ('ja', '日本語'),
                ('ko', '韓国語'),
                ('zh-CN', '中国語(簡体)'),
                ('zh-TW', '中国語(繁体)'),
                ('mn', 'モンゴル語')
            ],
            '東南アジア': [
                ('th', 'タイ語'),
                ('vi', 'ベトナム語'),
                ('id', 'インドネシア語'),
                ('ms', 'マレー語'),
                ('tl', 'フィリピン語'),
                ('my', 'ミャンマー語'),
                ('km', 'クメール語'),
                ('lo', 'ラオ語')
            ],
            'ヨーロッパ': [
                ('en', '英語'),
                ('fr', 'フランス語'),
                ('de', 'ドイツ語'),
                ('es', 'スペイン語'),
                ('it', 'イタリア語'),
                ('pt', 'ポルトガル語'),
                ('ru', 'ロシア語'),
                ('pl', 'ポーランド語'),
                ('nl', 'オランダ語'),
                ('sv', 'スウェーデン語'),
                ('da', 'デンマーク語'),
                ('no', 'ノルウェー語'),
                ('fi', 'フィンランド語'),
                ('cs', 'チェコ語'),
                ('hu', 'ハンガリー語'),
                ('ro', 'ルーマニア語'),
                ('bg', 'ブルガリア語'),
                ('hr', 'クロアチア語'),
                ('sk', 'スロバキア語'),
                ('sl', 'スロベニア語'),
                ('et', 'エストニア語'),
                ('lv', 'ラトビア語'),
                ('lt', 'リトアニア語'),
                ('el', 'ギリシャ語'),
                ('tr', 'トルコ語')
            ],
            '北米': [
                ('en', '英語'),
                ('es', 'スペイン語'),
                ('fr', 'フランス語')
            ],
            '南米': [
                ('es', 'スペイン語'),
                ('pt', 'ポルトガル語')
            ],
            'アフリカ': [
                ('ar', 'アラビア語'),
                ('sw', 'スワヒリ語'),
                ('am', 'アムハラ語'),
                ('zu', 'ズールー語'),
                ('af', 'アフリカーンス語')
            ],
            'オセアニア': [
                ('en', '英語'),
                ('mi', 'マオリ語')
            ],
            'その他': [
                ('hi', 'ヒンディー語'),
                ('bn', 'ベンガル語'),
                ('ur', 'ウルドゥー語'),
                ('fa', 'ペルシャ語'),
                ('he', 'ヘブライ語'),
                ('ta', 'タミル語'),
                ('te', 'テルグ語'),
                ('ml', 'マラヤーラム語'),
                ('kn', 'カンナダ語'),
                ('gu', 'グジャラート語'),
                ('pa', 'パンジャブ語'),
                ('ne', 'ネパール語'),
                ('si', 'シンハラ語'),
                ('is', 'アイスランド語'),
                ('mt', 'マルタ語'),
                ('cy', 'ウェールズ語'),
                ('ga', 'アイルランド語'),
                ('eu', 'バスク語'),
                ('ca', 'カタルーニャ語'),
                ('gl', 'ガリシア語'),
                ('sq', 'アルバニア語'),
                ('mk', 'マケドニア語'),
                ('be', 'ベラルーシ語'),
                ('uk', 'ウクライナ語'),
                ('ka', 'ジョージア語'),
                ('hy', 'アルメニア語'),
                ('az', 'アゼルバイジャン語'),
                ('kk', 'カザフ語'),
                ('ky', 'キルギス語'),
                ('tg', 'タジク語'),
                ('tk', 'トルクメン語'),
                ('uz', 'ウズベク語')
            ]
        }
    
    def _create_window(self):
        """設定ウィンドウを作成"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("設定 - twitchTransFreeNeo")
        
        # 前回のウィンドウ設定を復元
        self._restore_window_geometry()
        
        self.window.resizable(True, True)
        self.window.minsize(650, 800)
        
        # モーダルにする
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # ウィンドウ終了時の処理
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # タブ付きノートブック
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(10, 5))
        
        # タブ切り替えイベントをバインド
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # 基本設定タブ
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="基本設定")
        self._create_basic_tab(basic_tab)
        
        # 翻訳設定タブ
        translation_tab = ttk.Frame(self.notebook)
        self.notebook.add(translation_tab, text="翻訳設定")
        self._create_translation_tab(translation_tab)
        
        # フィルター設定タブ
        filter_tab = ttk.Frame(self.notebook)
        self.notebook.add(filter_tab, text="フィルター設定")
        self._create_filter_tab(filter_tab)
        
        # TTS設定タブ
        tts_tab = ttk.Frame(self.notebook)
        self.notebook.add(tts_tab, text="TTS・表示設定")
        self._create_tts_tab(tts_tab)
        
        # ボタンフレーム（固定位置）
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', side='bottom', padx=10, pady=10)
        self._create_buttons(button_frame)
        
        # 初期描画を強制実行
        self.window.update_idletasks()
        self.window.update()
    
    def _restore_window_geometry(self):
        """前回のウィンドウ位置・サイズを復元"""
        window_config = self.config.get("window_settings", {})
        
        # デフォルト値
        default_width = 700
        default_height = 950
        default_x = 150
        default_y = 30
        
        # 設定から復元
        width = window_config.get("settings_width", default_width)
        height = window_config.get("settings_height", default_height)
        x = window_config.get("settings_x", default_x)
        y = window_config.get("settings_y", default_y)
        
        # 画面範囲チェック
        try:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # 画面外にならないように調整
            if x < 0 or x > screen_width - 200:
                x = default_x
            if y < 0 or y > screen_height - 200:
                y = default_y
            if width < 650:
                width = default_width
            if height < 800:
                height = default_height
                
            self.window.geometry(f"{width}x{height}+{x}+{y}")
        except:
            # エラー時はデフォルト値を使用
            self.window.geometry(f"{default_width}x{default_height}+{default_x}+{default_y}")
    
    def _save_window_geometry(self):
        """現在のウィンドウ位置・サイズを保存"""
        try:
            # 現在の状態を取得
            self.window.update_idletasks()
            
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            x = self.window.winfo_x()
            y = self.window.winfo_y()
            
            # 設定に保存
            if "window_settings" not in self.config:
                self.config["window_settings"] = {}
            
            self.config["window_settings"].update({
                "settings_width": width,
                "settings_height": height,
                "settings_x": x,
                "settings_y": y
            })
            
        except Exception as e:
            print(f"設定ウィンドウジオメトリ保存エラー: {e}")
    
    def _on_tab_changed(self, event):
        """タブ切り替え時のイベントハンドラ"""
        # 即座に一度更新
        self.window.update_idletasks()
        
        # フォーカスを変更して描画を促進
        try:
            current_tab_id = self.notebook.select()
            if current_tab_id:
                current_tab_widget = self.notebook.nametowidget(current_tab_id)
                current_tab_widget.focus_set()
        except:
            pass
        
        # tkinterのNotebookバグ回避: マウスイベントをシミュレート
        self.window.after(1, self._force_redraw_workaround)
        self.window.after(20, self._force_redraw_workaround)
        self.window.after(50, self._force_redraw_workaround)
        
        # 少し遅延させて再度更新（複数回実行で確実に描画）
        self.window.after(1, self._delayed_update)
        self.window.after(10, self._delayed_update)
        self.window.after(50, self._delayed_update)
        self.window.after(100, self._delayed_update)
        
        # 現在のタブを取得
        try:
            current_tab = self.notebook.index(self.notebook.select())
            if hasattr(self, '_debug_tab_change'):
                print(f"Tab changed to index: {current_tab}")
        except:
            pass
    
    def _delayed_update(self):
        """遅延更新処理"""
        try:
            # 現在のタブを取得して直接更新
            current_tab_id = self.notebook.select()
            if current_tab_id:
                current_tab_widget = self.notebook.nametowidget(current_tab_id)
                current_tab_widget.update_idletasks()
                current_tab_widget.update()
            
            # ウィンドウ全体も更新
            self.window.update_idletasks()
            self.window.update()
            
            # ノートブック自体も更新
            self.notebook.update_idletasks()
            self.notebook.update()
        except:
            pass
    
    def _force_redraw_workaround(self):
        """tkinter Notebookの描画バグ回避処理"""
        try:
            # Method 1: 実際のマウスカーソル移動（最も効果的）
            try:
                import pyautogui
                pyautogui.FAILSAFE = False
                current_x, current_y = pyautogui.position()
                # 1ピクセル移動してすぐ戻す
                pyautogui.moveTo(current_x + 1, current_y, duration=0)
                pyautogui.moveTo(current_x, current_y, duration=0)
            except ImportError:
                # pyautoguiが利用できない場合は他の方法を使用
                pass
            
            # Method 2: 仮想的なマウス移動イベントを生成
            self.window.event_generate('<Motion>', x=0, y=0)
            
            # Method 3: Notebookの強制再描画
            self.notebook.event_generate('<Enter>')
            self.notebook.event_generate('<Leave>')
            self.notebook.event_generate('<Enter>')
            
            # Method 4: ウィンドウサイズ変更は無効化（横幅増加の原因）
            # ※ 他の手法で十分効果的なため、この方法はコメントアウト
            # current_geometry = self.window.geometry()
            # if 'x' in current_geometry:
            #     width, height_and_pos = current_geometry.split('x', 1)
            #     height, pos = height_and_pos.split('+', 1) if '+' in height_and_pos else (height_and_pos.split('-', 1) if '-' in height_and_pos else (height_and_pos, ''))
            #     new_width = int(width) + 1
            #     temp_geometry = f"{new_width}x{height}+{pos}" if pos else f"{new_width}x{height}"
            #     self.window.geometry(temp_geometry)
            #     self.window.after(1, lambda: self.window.geometry(current_geometry))
            
            # Method 5: タブコンテンツエリアに直接フォーカス
            current_tab_id = self.notebook.select()
            if current_tab_id:
                current_tab_widget = self.notebook.nametowidget(current_tab_id)
                # コンテンツエリアの最初の子ウィジェットを探す
                children = current_tab_widget.winfo_children()
                if children:
                    for child in children:
                        child.event_generate('<Enter>')
                        child.event_generate('<Motion>', x=1, y=1)
                        break
            
            # Method 6: ウィンドウ全体に対するマウスイベント
            window_x = self.window.winfo_rootx()
            window_y = self.window.winfo_rooty()
            self.window.event_generate('<Motion>', x=window_x + 10, y=window_y + 10)
            
        except Exception as e:
            if hasattr(self, '_debug_redraw'):
                print(f"Redraw workaround error: {e}")
            pass
    
    def _create_basic_tab(self, parent):
        """基本設定タブ"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._create_basic_section(scrollable_frame)
        
        # 強制描画更新
        parent.update_idletasks()
    
    def _create_basic_section(self, parent):
        """基本設定セクション"""
        basic_frame = ttk.LabelFrame(parent, text="基本設定")
        basic_frame.pack(fill='x', pady=5)
        
        # 必須設定
        ttk.Label(basic_frame, text="Twitchチャンネル名:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.channel_var = tk.StringVar(value=self.config.get("twitch_channel", ""))
        ttk.Entry(basic_frame, textvariable=self.channel_var, width=30).grid(row=0, column=1, sticky='ew', padx=5, pady=3)
        
        ttk.Label(basic_frame, text="翻訳botユーザー名:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.username_var = tk.StringVar(value=self.config.get("trans_username", ""))
        ttk.Entry(basic_frame, textvariable=self.username_var, width=30).grid(row=1, column=1, sticky='ew', padx=5, pady=3)
        
        ttk.Label(basic_frame, text="OAuthトークン:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.oauth_var = tk.StringVar(value=self.config.get("trans_oauth", ""))
        ttk.Entry(basic_frame, textvariable=self.oauth_var, width=30, show="*").grid(row=2, column=1, sticky='ew', padx=5, pady=3)
        
        # OAuth取得ボタン
        ttk.Button(basic_frame, text="OAuthトークン取得ページ", 
                  command=lambda: webbrowser.open("https://www.sayonari.com/trans_asr/ttfn_oauth.html")).grid(row=3, column=1, sticky='w', padx=5, pady=3)
        
        basic_frame.grid_columnconfigure(1, weight=1)
    
    def _create_translation_tab(self, parent):
        """翻訳設定タブ"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._create_translation_section(scrollable_frame)
        
        # 強制描画更新
        parent.update_idletasks()
    
    def _create_translation_section(self, parent):
        """翻訳設定セクション"""
        trans_frame = ttk.LabelFrame(parent, text="翻訳設定")
        trans_frame.pack(fill='x', pady=5)
        
        # ホーム言語設定
        ttk.Label(trans_frame, text="ホーム言語地域:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.home_region_var = tk.StringVar(value=self.config.get("home_region", "東アジア"))
        home_region_combo = ttk.Combobox(trans_frame, textvariable=self.home_region_var, width=15, state="readonly")
        home_region_combo['values'] = ['東アジア', '東南アジア', 'ヨーロッパ', '北米', '南米', 'アフリカ', 'オセアニア', 'その他']
        home_region_combo.grid(row=0, column=1, sticky='w', padx=5, pady=3)
        home_region_combo.bind('<<ComboboxSelected>>', self._on_home_region_change)
        
        ttk.Label(trans_frame, text="ホーム言語:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.home_lang_var = tk.StringVar(value=self.config.get("lang_trans_to_home", "ja"))
        self.home_combo = ttk.Combobox(trans_frame, textvariable=self.home_lang_var, width=20, state="readonly")
        self.home_combo.grid(row=0, column=3, sticky='ew', padx=5, pady=3)
        
        # 外国語設定
        ttk.Label(trans_frame, text="外国語地域:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.foreign_region_var = tk.StringVar(value=self.config.get("foreign_region", "ヨーロッパ"))
        foreign_region_combo = ttk.Combobox(trans_frame, textvariable=self.foreign_region_var, width=15, state="readonly")
        foreign_region_combo['values'] = ['東アジア', '東南アジア', 'ヨーロッパ', '北米', '南米', 'アフリカ', 'オセアニア', 'その他']
        foreign_region_combo.grid(row=1, column=1, sticky='w', padx=5, pady=3)
        foreign_region_combo.bind('<<ComboboxSelected>>', self._on_foreign_region_change)
        
        ttk.Label(trans_frame, text="外国語:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.other_lang_var = tk.StringVar(value=self.config.get("lang_home_to_other", "en"))
        self.other_combo = ttk.Combobox(trans_frame, textvariable=self.other_lang_var, width=20, state="readonly")
        self.other_combo.grid(row=1, column=3, sticky='ew', padx=5, pady=3)
        
        # 翻訳エンジン
        ttk.Label(trans_frame, text="翻訳エンジン:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.translator_var = tk.StringVar(value=self.config.get("translator", "google"))
        translator_combo = ttk.Combobox(trans_frame, textvariable=self.translator_var, width=27, state="readonly")
        translator_combo['values'] = ['google', 'deepl']
        translator_combo.grid(row=2, column=1, columnspan=3, sticky='w', padx=5, pady=3)
        
        # 初期化
        self._update_home_language_options()
        self._update_foreign_language_options()
        
        trans_frame.grid_columnconfigure(3, weight=1)
    
    def _create_filter_tab(self, parent):
        """フィルター設定タブ"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._create_filter_section(scrollable_frame)
        
        # 強制描画更新
        parent.update_idletasks()
    
    def _create_tts_tab(self, parent):
        """TTS・表示設定タブ"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # TTS設定
        tts_frame = ttk.LabelFrame(scrollable_frame, text="TTS（音声合成）設定")
        tts_frame.pack(fill='x', pady=5)
        
        self.tts_enabled_var = tk.BooleanVar(value=self.config.get("tts_enabled", False))
        ttk.Checkbutton(tts_frame, text="TTS (音声読み上げ) を有効", variable=self.tts_enabled_var).grid(row=0, column=0, sticky='w', padx=5, pady=3)
        
        # TTS詳細設定
        tts_detail_frame = ttk.LabelFrame(tts_frame, text="TTS詳細設定")
        tts_detail_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        self.tts_in_var = tk.BooleanVar(value=self.config.get("tts_in", False))
        ttk.Checkbutton(tts_detail_frame, text="入力メッセージを読み上げ", variable=self.tts_in_var).grid(row=0, column=0, sticky='w', padx=5, pady=3)
        
        self.tts_out_var = tk.BooleanVar(value=self.config.get("tts_out", False))
        ttk.Checkbutton(tts_detail_frame, text="翻訳メッセージを読み上げ", variable=self.tts_out_var).grid(row=0, column=1, sticky='w', padx=5, pady=3)
        
        ttk.Label(tts_detail_frame, text="最大文字数:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.tts_max_length_var = tk.StringVar(value=str(self.config.get("tts_text_max_length", 40)))
        ttk.Entry(tts_detail_frame, textvariable=self.tts_max_length_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=3)
        
        ttk.Label(tts_detail_frame, text="省略時メッセージ:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.tts_omit_message_var = tk.StringVar(value=self.config.get("tts_message_for_omitting", "..."))
        ttk.Entry(tts_detail_frame, textvariable=self.tts_omit_message_var, width=20).grid(row=2, column=1, sticky='w', padx=5, pady=3)
        
        # 表示オプション
        options_frame = ttk.LabelFrame(scrollable_frame, text="表示オプション")
        options_frame.pack(fill='x', pady=5)
        
        self.show_name_var = tk.BooleanVar(value=self.config.get("show_by_name", True))
        ttk.Checkbutton(options_frame, text="ユーザー名を表示", variable=self.show_name_var).grid(row=0, column=0, sticky='w', padx=5, pady=3)
        
        self.show_lang_var = tk.BooleanVar(value=self.config.get("show_by_lang", True))
        ttk.Checkbutton(options_frame, text="言語情報を表示", variable=self.show_lang_var).grid(row=0, column=1, sticky='w', padx=5, pady=3)
        
        self.view_only_var = tk.BooleanVar(value=self.config.get("view_only_mode", False))
        ttk.Checkbutton(options_frame, text="表示のみモード (翻訳をチャットに投稿しない)", variable=self.view_only_var).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        self.debug_var = tk.BooleanVar(value=self.config.get("debug", False))
        ttk.Checkbutton(options_frame, text="デバッグモード", variable=self.debug_var).grid(row=2, column=0, sticky='w', padx=5, pady=3)
        
        # 強制描画更新
        parent.update_idletasks()
    
    def _on_home_region_change(self, event=None):
        """ホーム言語地域変更時の処理"""
        self._update_home_language_options()
    
    def _on_foreign_region_change(self, event=None):
        """外国語地域変更時の処理"""
        self._update_foreign_language_options()
    
    def _update_home_language_options(self):
        """ホーム言語地域に基づいて言語選択肢を更新"""
        region = self.home_region_var.get()
        if region in self.language_map:
            languages = self.language_map[region]
            # 表示用のリスト (言語コード + 言語名)
            display_values = [f"{code} ({name})" for code, name in languages]
            
            # コンボボックスを更新
            self.home_combo['values'] = display_values
            
            # 現在の値が新しい選択肢にない場合、デフォルトを設定
            current_home = self.home_lang_var.get()
            
            # 現在の値を表示形式に変換
            home_display = self._lang_code_to_display(current_home, languages)
            
            if home_display:
                self.home_lang_var.set(home_display)
            elif display_values:
                self.home_lang_var.set(display_values[0])
    
    def _update_foreign_language_options(self):
        """外国語地域に基づいて言語選択肢を更新"""
        region = self.foreign_region_var.get()
        if region in self.language_map:
            languages = self.language_map[region]
            # 表示用のリスト (言語コード + 言語名)
            display_values = [f"{code} ({name})" for code, name in languages]
            
            # コンボボックスを更新
            self.other_combo['values'] = display_values
            
            # 現在の値が新しい選択肢にない場合、デフォルトを設定
            current_other = self.other_lang_var.get()
            
            # 現在の値を表示形式に変換
            other_display = self._lang_code_to_display(current_other, languages)
            
            if other_display:
                self.other_lang_var.set(other_display)
            elif display_values:
                self.other_lang_var.set(display_values[0])
    
    def _lang_code_to_display(self, code: str, languages: list) -> str:
        """言語コードを表示形式に変換"""
        for lang_code, lang_name in languages:
            if lang_code == code:
                return f"{lang_code} ({lang_name})"
        return ""
    
    def _display_to_lang_code(self, display: str) -> str:
        """表示形式から言語コードを抽出"""
        if '(' in display:
            return display.split(' (')[0]
        return display
    
    def _create_filter_section(self, parent):
        """フィルター設定セクション"""
        filter_frame = ttk.LabelFrame(parent, text="フィルター設定")
        filter_frame.pack(fill='x', pady=5)
        
        ttk.Label(filter_frame, text="無視するユーザー (カンマ区切り):").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.ignore_users_var = tk.StringVar(value=','.join(self.config.get("ignore_users", [])))
        ttk.Entry(filter_frame, textvariable=self.ignore_users_var, width=40).grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=3)
        
        ttk.Label(filter_frame, text="無視する言語 (カンマ区切り):").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.ignore_langs_var = tk.StringVar(value=','.join(self.config.get("ignore_languages", [])))
        ttk.Entry(filter_frame, textvariable=self.ignore_langs_var, width=40).grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=3)
        
        ttk.Label(filter_frame, text="無視するテキストパターン (カンマ区切り):").grid(row=4, column=0, sticky='w', padx=5, pady=3)
        self.ignore_patterns_var = tk.StringVar(value=','.join(self.config.get("ignore_text_patterns", [])))
        ttk.Entry(filter_frame, textvariable=self.ignore_patterns_var, width=40).grid(row=5, column=0, columnspan=2, sticky='ew', padx=5, pady=3)
        
        ttk.Label(filter_frame, text="削除する単語 (カンマ区切り):").grid(row=6, column=0, sticky='w', padx=5, pady=3)
        self.delete_words_var = tk.StringVar(value=','.join(self.config.get("delete_words", [])))
        ttk.Entry(filter_frame, textvariable=self.delete_words_var, width=40).grid(row=7, column=0, columnspan=2, sticky='ew', padx=5, pady=3)
        
        self.www_ignore_var = tk.BooleanVar(value=self.config.get("www_ignore", False))
        ttk.Checkbutton(filter_frame, text="WWWを含むメッセージを無視", variable=self.www_ignore_var).grid(row=8, column=0, sticky='w', padx=5, pady=3)
        
        filter_frame.grid_columnconfigure(0, weight=1)
    
    def _create_buttons(self, parent):
        """ボタン作成"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="キャンセル", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(button_frame, text="適用", command=self.apply).pack(side='right', padx=5)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side='right', padx=5)
    
    def _collect_config(self) -> Dict[str, Any]:
        """設定を収集"""
        new_config = {
            "twitch_channel": self.channel_var.get().strip(),
            "trans_username": self.username_var.get().strip(),
            "trans_oauth": self.oauth_var.get().strip(),
            "home_region": self.home_region_var.get(),
            "foreign_region": self.foreign_region_var.get(),
            "lang_trans_to_home": self._display_to_lang_code(self.home_lang_var.get()),
            "lang_home_to_other": self._display_to_lang_code(self.other_lang_var.get()),
            "translator": self.translator_var.get(),
            "ignore_users": [user.strip() for user in self.ignore_users_var.get().split(',') if user.strip()],
            "ignore_languages": [lang.strip() for lang in self.ignore_langs_var.get().split(',') if lang.strip()],
            "ignore_text_patterns": [pattern.strip() for pattern in self.ignore_patterns_var.get().split(',') if pattern.strip()],
            "delete_words": [word.strip() for word in self.delete_words_var.get().split(',') if word.strip()],
            "www_ignore": self.www_ignore_var.get(),
            "tts_enabled": self.tts_enabled_var.get(),
            "tts_in": self.tts_in_var.get(),
            "tts_out": self.tts_out_var.get(),
            "tts_text_max_length": int(self.tts_max_length_var.get()) if self.tts_max_length_var.get().isdigit() else 40,
            "tts_message_for_omitting": self.tts_omit_message_var.get(),
            "view_only_mode": self.view_only_var.get(),
            "show_by_name": self.show_name_var.get(),
            "show_by_lang": self.show_lang_var.get(),
            "debug": self.debug_var.get()
        }
        
        # 既存設定をマージ
        result = self.config.copy()
        result.update(new_config)
        return result
    
    def _validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """設定の妥当性をチェック"""
        errors = []
        
        if not config.get("twitch_channel"):
            errors.append("Twitchチャンネル名は必須です")
        
        if not config.get("trans_username"):
            errors.append("翻訳botユーザー名は必須です")
        
        if not config.get("trans_oauth"):
            errors.append("OAuthトークンは必須です")
        
        return len(errors) == 0, errors
    
    def apply(self):
        """設定を適用"""
        new_config = self._collect_config()
        is_valid, errors = self._validate_config(new_config)
        
        if not is_valid:
            messagebox.showerror("設定エラー", "\n".join(errors))
            return
        
        # ウィンドウジオメトリも保存
        self._save_window_geometry()
        
        self.config = new_config
        self.on_config_change(new_config)
        messagebox.showinfo("設定", "設定を適用しました")
    
    def ok(self):
        """OK ボタン"""
        self.apply()
        self._save_window_geometry()
        self.window.destroy()
    
    def cancel(self):
        """キャンセル"""
        self._save_window_geometry()
        self.window.destroy()