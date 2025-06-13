#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..core.chat_monitor import ChatMessage


class SimpleChatDisplay(ttk.Frame):
    """シンプルなチャット表示ウィジェット"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        super().__init__(parent)
        self.config = config
        self.messages: List[ChatMessage] = []
        self.filtered_messages: List[ChatMessage] = []
        self.max_messages = 1000
        
        # フィルタリング設定
        self.search_text = ""
        self.lang_filter = "all"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # フィルタバー
        self._create_filter_bar()
        
        # チャット表示エリア
        self._create_chat_area()
    
    def _create_filter_bar(self):
        """フィルタバー作成"""
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        # 検索ボックス
        ttk.Label(filter_frame, text="検索:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._apply_filters())
        
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=(0, 10))
        
        # 言語フィルタ
        ttk.Label(filter_frame, text="言語:").pack(side='left', padx=(0, 5))
        self.lang_var = tk.StringVar(value="all")
        self.lang_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.lang_var,
            values=["all", "ja", "en", "ko", "zh", "es", "fr", "de", "other"],
            state='readonly',
            width=10
        )
        self.lang_combo.pack(side='left', padx=(0, 10))
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())
        
        # クリアボタン
        ttk.Button(filter_frame, text="クリア", command=self.clear_messages).pack(side='right', padx=5)
    
    def _create_chat_area(self):
        """チャット表示エリア作成"""
        # スクロール可能なフレーム
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill='both', expand=True)
        
        # Canvas とスクロールバー
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 配置
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # メッセージ表示用フレーム
        self.messages_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(0, 0, anchor='nw', window=self.messages_frame)
        
        # イベントバインド
        self.messages_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _on_frame_configure(self, event=None):
        """フレームサイズ変更時の処理"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _on_canvas_configure(self, event=None):
        """キャンバスサイズ変更時の処理"""
        canvas_width = event.width if event else self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def add_message(self, message: ChatMessage):
        """メッセージ追加"""
        self.messages.append(message)
        
        # 最大メッセージ数を超えたら古いものを削除
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        # フィルタ適用
        self._apply_filters()
        
        # 自動スクロール
        self.canvas.after_idle(lambda: self.canvas.yview_moveto(1.0))
    
    def _apply_filters(self):
        """フィルタ適用"""
        search_text = self.search_var.get().lower()
        lang_filter = self.lang_var.get()
        
        # フィルタリング
        self.filtered_messages = []
        for msg in self.messages:
            # 言語フィルタ
            if lang_filter != "all" and msg.lang != lang_filter:
                continue
            
            # 検索フィルタ
            if search_text:
                if search_text not in msg.user.lower() and \
                   search_text not in msg.text.lower() and \
                   (not msg.translation or search_text not in msg.translation.lower()):
                    continue
            
            self.filtered_messages.append(msg)
        
        # 表示更新
        self._update_display()
    
    def _update_display(self):
        """表示更新"""
        # 既存のウィジェットをクリア
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        # フィルタリングされたメッセージを表示
        for msg in self.filtered_messages:
            self._create_message_widget(msg)
    
    def _create_message_widget(self, message: ChatMessage):
        """メッセージウィジェット作成"""
        # メッセージフレーム
        msg_frame = ttk.Frame(self.messages_frame, relief='flat', borderwidth=1)
        msg_frame.pack(fill='x', padx=5, pady=2)
        
        # 時刻
        time_label = ttk.Label(
            msg_frame,
            text=message.timestamp.strftime("%H:%M:%S"),
            foreground='gray'
        )
        time_label.pack(side='left', padx=(5, 10))
        
        # ユーザー名
        user_label = ttk.Label(
            msg_frame,
            text=f"{message.user}:",
            font=('', 10, 'bold')
        )
        user_label.pack(side='left', padx=(0, 5))
        
        # 言語表示
        if self.config.get("show_by_lang", True) and message.lang:
            lang_label = ttk.Label(
                msg_frame,
                text=f"[{message.lang}]",
                foreground='gray'
            )
            lang_label.pack(side='left', padx=(0, 5))
        
        # メッセージテキスト
        text_label = ttk.Label(msg_frame, text=message.text, wraplength=400)
        text_label.pack(side='left', fill='x', expand=True)
        
        # 翻訳表示
        if message.translation:
            trans_frame = ttk.Frame(self.messages_frame)
            trans_frame.pack(fill='x', padx=5, pady=(0, 5))
            
            # 翻訳アイコン
            ttk.Label(trans_frame, text="→", foreground='green').pack(side='left', padx=(50, 10))
            
            # 翻訳言語表示
            if self.config.get("show_by_lang", True) and message.target_lang:
                lang_label = ttk.Label(
                    trans_frame,
                    text=f"[{message.target_lang}]",
                    foreground='gray'
                )
                lang_label.pack(side='left', padx=(0, 5))
            
            # 翻訳テキスト
            trans_label = ttk.Label(
                trans_frame,
                text=message.translation,
                foreground=self.config.get("trans_text_color", "goldenrod"),
                wraplength=400
            )
            trans_label.pack(side='left', fill='x', expand=True)
    
    def clear_messages(self):
        """メッセージクリア"""
        self.messages.clear()
        self.filtered_messages.clear()
        self._update_display()
    
    def get_message_count(self) -> int:
        """メッセージ数取得"""
        return len(self.messages)
    
    def get_translated_count(self) -> int:
        """翻訳済みメッセージ数取得"""
        return sum(1 for msg in self.messages if msg.translation)
    
    def update_config(self, config: Dict[str, Any]):
        """設定を更新"""
        self.config = config
        # 表示を更新
        self._update_display()


class SimpleStatusBar(ttk.Frame):
    """ステータスバー"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # 左側：接続状態
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(side='left', padx=10)
        
        # 接続状態アイコンとラベル
        self.connection_indicator = ttk.Label(self.status_frame, text="●", foreground="red", font=('', 12))
        self.connection_indicator.pack(side='left', padx=(0, 5))
        
        self.status_label = ttk.Label(self.status_frame, text="未接続")
        self.status_label.pack(side='left')
        
        # セパレータ
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # 中央：コンポーネント状態
        self.component_frame = ttk.Frame(self)
        self.component_frame.pack(side='left', padx=10)
        
        # Twitch状態
        self.twitch_indicator = ttk.Label(self.component_frame, text="Twitch:", font=('', 9))
        self.twitch_indicator.pack(side='left', padx=(0, 2))
        self.twitch_status = ttk.Label(self.component_frame, text="●", foreground="gray", font=('', 12))
        self.twitch_status.pack(side='left', padx=(0, 10))
        
        # 翻訳エンジン状態
        self.translator_indicator = ttk.Label(self.component_frame, text="翻訳:", font=('', 9))
        self.translator_indicator.pack(side='left', padx=(0, 2))
        self.translator_status = ttk.Label(self.component_frame, text="●", foreground="gray", font=('', 12))
        self.translator_status.pack(side='left', padx=(0, 10))
        
        # DB状態
        self.db_indicator = ttk.Label(self.component_frame, text="DB:", font=('', 9))
        self.db_indicator.pack(side='left', padx=(0, 2))
        self.db_status = ttk.Label(self.component_frame, text="●", foreground="gray", font=('', 12))
        self.db_status.pack(side='left')
        
        # セパレータ
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # 右側：統計情報
        self.stats_label = ttk.Label(self, text="メッセージ: 0 / 翻訳済み: 0")
        self.stats_label.pack(side='left')
    
    def set_status(self, status: str, color: str = "black"):
        """ステータス設定"""
        self.status_label.configure(text=status)
        if status == "接続中":
            self.connection_indicator.configure(foreground="green")
        elif status == "接続中...":
            self.connection_indicator.configure(foreground="orange")
        else:
            self.connection_indicator.configure(foreground="red")
    
    def set_component_status(self, component: str, status: str):
        """コンポーネント状態設定"""
        color = "green" if status == "OK" else ("orange" if status == "WARN" else "red")
        
        if component == "twitch":
            self.twitch_status.configure(foreground=color)
        elif component == "translator":
            self.translator_status.configure(foreground=color)
        elif component == "database":
            self.db_status.configure(foreground=color)
    
    def set_message_stats(self, total: int, translated: int):
        """メッセージ統計設定"""
        self.stats_label.configure(text=f"メッセージ: {total} / 翻訳済み: {translated}")
    
    def set_translator_status(self, engine: str, status: str):
        """翻訳エンジン状態設定"""
        color = "green" if status == "設定済み" else "red"
        self.translator_status.configure(foreground=color)
    
    def set_connection_status(self, connected: bool, channel: str = ""):
        """接続状態設定"""
        if connected:
            self.set_status("接続中")
            self.set_component_status("twitch", "OK")
        else:
            self.set_status("未接続")
            self.set_component_status("twitch", "ERROR")