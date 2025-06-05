#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from ..core.chat_monitor import ChatMessage
except ImportError:
    from twitchTransFreeNeo.core.chat_monitor import ChatMessage

class SimpleChatDisplay(ttk.Frame):
    """簡易チャット表示ウィジェット"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        super().__init__(parent)
        self.config = config
        self.messages: List[ChatMessage] = []
        self.max_messages = 1000
        self._create_widgets()
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # コントロールフレーム
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(control_frame, text="チャット表示").pack(side='left')
        ttk.Button(control_frame, text="履歴クリア", command=self.clear_messages).pack(side='right')
        
        # メインチャット表示エリア
        self.chat_text = scrolledtext.ScrolledText(
            self, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            height=20,
            font=("Consolas", self.config.get("font_size", 12))
        )
        self.chat_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ステータス
        status_frame = ttk.Frame(self)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        self.stats_label = ttk.Label(status_frame, text="メッセージ: 0件")
        self.stats_label.pack(side='left')
    
    def add_message(self, message: ChatMessage):
        """メッセージを追加"""
        self.messages.append(message)
        
        # 最大件数チェック
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            self._update_display()
        else:
            self._add_message_to_display(message)
        
        # 統計更新
        self._update_stats()
        
        # 自動スクロール
        self.chat_text.see(tk.END)
    
    def _add_message_to_display(self, message: ChatMessage):
        """表示エリアにメッセージを追加"""
        self.chat_text.configure(state=tk.NORMAL)
        
        # タイムスタンプとユーザー名
        self.chat_text.insert(tk.END, f"[{message.timestamp}] {message.username}: ")
        
        # 原文表示
        self.chat_text.insert(tk.END, f"{message.content}")
        
        # 翻訳文表示
        if message.is_translated:
            self.chat_text.insert(tk.END, f"\n  → {message.translated}")
            if message.lang and message.target_lang:
                self.chat_text.insert(tk.END, f" ({message.lang} → {message.target_lang})")
        
        self.chat_text.insert(tk.END, "\n\n")
        self.chat_text.configure(state=tk.DISABLED)
    
    def _update_display(self):
        """表示を更新"""
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        
        for message in self.messages:
            self._add_message_to_display(message)
        
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    def _update_stats(self):
        """統計情報を更新"""
        total = len(self.messages)
        translated = sum(1 for msg in self.messages if msg.is_translated)
        
        stats_text = f"メッセージ: {total}件 (翻訳済み: {translated}件)"
        self.stats_label.configure(text=stats_text)
    
    def clear_messages(self):
        """メッセージをクリア"""
        if messagebox.askyesno("確認", "チャット履歴をクリアしますか？"):
            self.messages.clear()
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete("1.0", tk.END)
            self.chat_text.configure(state=tk.DISABLED)
            self._update_stats()
    
    def update_config(self, config: Dict[str, Any]):
        """設定更新"""
        self.config.update(config)
        font_size = config.get("font_size", 12)
        self.chat_text.configure(font=("Consolas", font_size))
    
    def get_message_count(self) -> int:
        """メッセージ件数を取得"""
        return len(self.messages)
    
    def get_filtered_messages(self) -> List[ChatMessage]:
        """フィルター済みメッセージを取得"""
        return self.messages


class SimpleStatusBar(ttk.Frame):
    """簡易ステータスバー"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.timer_id = None
        self._create_widgets()
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # 接続状態
        self.connection_label = ttk.Label(self, text="未接続", foreground="red")
        self.connection_label.pack(side='left', padx=5)
        
        # 翻訳エンジン状態
        self.translator_label = ttk.Label(self, text="翻訳エンジン: 停止中")
        self.translator_label.pack(side='left', padx=20)
        
        # メッセージ統計
        self.message_stats_label = ttk.Label(self, text="メッセージ: 0件")
        self.message_stats_label.pack(side='left', padx=20)
        
        # 時刻表示
        self.time_label = ttk.Label(self, text="")
        self.time_label.pack(side='right', padx=5)
        
        # 時刻更新
        self._update_time()
    
    def _update_time(self):
        """時刻更新"""
        try:
            if self.winfo_exists() and hasattr(self, 'time_label') and self.time_label.winfo_exists():
                current_time = datetime.now().strftime("%H:%M:%S")
                self.time_label.configure(text=current_time)
                self.timer_id = self.after(1000, self._update_time)
        except (tk.TclError, AttributeError):
            # ウィジェットが破棄された場合は何もしない
            pass
    
    def destroy(self):
        """ウィジェット破棄時にタイマーも停止"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        super().destroy()
    
    def set_connection_status(self, connected: bool, channel: str = ""):
        """接続状態を設定"""
        if connected:
            self.connection_label.configure(text=f"接続中: {channel}", foreground="green")
        else:
            self.connection_label.configure(text="未接続", foreground="red")
    
    def set_translator_status(self, engine: str, status: str):
        """翻訳エンジン状態を設定"""
        self.translator_label.configure(text=f"翻訳エンジン: {engine} ({status})")
    
    def set_message_stats(self, total: int, translated: int):
        """メッセージ統計を設定"""
        self.message_stats_label.configure(text=f"メッセージ: {total}件 (翻訳済み: {translated}件)")