#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from typing import Dict, Any, Optional
try:
    from ..utils.config_manager import ConfigManager
    from ..core.chat_monitor import ChatMonitor, ChatMessage
    from .simple_settings import SimpleSettingsWindow
    from .simple_chat_display import SimpleChatDisplay, SimpleStatusBar
except ImportError:
    # フォールバック: 絶対インポート
    from twitchTransFreeNeo.utils.config_manager import ConfigManager
    from twitchTransFreeNeo.core.chat_monitor import ChatMonitor, ChatMessage
    from twitchTransFreeNeo.gui.simple_settings import SimpleSettingsWindow
    from twitchTransFreeNeo.gui.simple_chat_display import SimpleChatDisplay, SimpleStatusBar

class MainWindow:
    """メインウィンドウクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config_manager = ConfigManager()
        self.chat_monitor: Optional[ChatMonitor] = None
        self.is_connected = False
        self.settings_window = None
        
        # 非同期イベントループ
        self.loop = asyncio.new_event_loop()
        self.loop_thread = None
        
        self._setup_window()
        self._create_widgets()
        self._load_config()
        
        # 自動接続チェック
        if self.config_manager.get("auto_start", False):
            self.root.after(1000, self._auto_connect)
    
    def _setup_window(self):
        """ウィンドウ設定"""
        self.root.title("twitchTransFreeNeo v1.0.0")
        
        # ウィンドウサイズ設定
        width = self.config_manager.get("window_width", 800)
        height = self.config_manager.get("window_height", 600)
        self.root.geometry(f"{width}x{height}")
        
        # 最小サイズ設定
        self.root.minsize(600, 400)
        
        # 終了処理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)
        
        # ツールバー
        self._create_toolbar(main_frame)
        
        # コンテンツエリア
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # パネル分割
        paned_window = ttk.PanedWindow(content_frame, orient='horizontal')
        paned_window.pack(fill='both', expand=True)
        
        # 左パネル（チャット表示）
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)
        
        # チャット表示ウィジェット
        self.chat_display = SimpleChatDisplay(left_frame, self.config_manager.get_all())
        self.chat_display.pack(fill='both', expand=True)
        
        # 右パネル（情報パネル）
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        self._create_simple_info_panel(right_frame)
        
        # ステータスバー
        self.status_bar = SimpleStatusBar(main_frame)
        self.status_bar.pack(fill='x', side='bottom')
    
    def _create_toolbar(self, parent):
        """ツールバー作成"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        # 接続ボタン
        self.connect_button = ttk.Button(toolbar, text="接続開始", command=self._toggle_connection)
        self.connect_button.pack(side='left', padx=2)
        
        # 設定ボタン
        ttk.Button(toolbar, text="設定", command=self._open_settings).pack(side='left', padx=2)
        
        # セパレータ
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        
        # 接続情報表示
        info_frame = ttk.Frame(toolbar)
        info_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(info_frame, text="チャンネル:").pack(side='left', padx=2)
        self.channel_label = ttk.Label(info_frame, text="未設定", foreground="red")
        self.channel_label.pack(side='left', padx=2)
        
        ttk.Label(info_frame, text="翻訳bot:").pack(side='left', padx=(10, 2))
        self.bot_label = ttk.Label(info_frame, text="未設定", foreground="red")
        self.bot_label.pack(side='left', padx=2)
        
        # 右側メニュー
        right_menu = ttk.Frame(toolbar)
        right_menu.pack(side='right')
        
        ttk.Button(right_menu, text="履歴クリア", command=self._clear_chat).pack(side='right', padx=2)
        ttk.Button(right_menu, text="ヘルプ", command=self._show_help).pack(side='right', padx=2)
    
    def _create_simple_info_panel(self, parent):
        """簡易情報パネル作成"""
        # 統計情報
        stats_frame = ttk.LabelFrame(parent, text="統計")
        stats_frame.pack(fill='x', padx=5, pady=5)
        
        self.total_messages_var = tk.StringVar(value="0")
        self.translated_messages_var = tk.StringVar(value="0")
        
        ttk.Label(stats_frame, text="総メッセージ数:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_messages_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(stats_frame, text="翻訳済み:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.translated_messages_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # ログ表示
        log_frame = ttk.LabelFrame(parent, text="ログ")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')
        
        ttk.Button(parent, text="ログクリア", command=self._clear_log).pack(pady=5)
    
    def _create_info_panel(self, parent):
        """情報パネル作成"""
        # ノートブック（タブ）
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # 統計タブ
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="統計")
        self._create_stats_tab(stats_frame)
        
        # ログタブ
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="ログ")
        self._create_log_tab(log_frame)
        
        # 設定確認タブ
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="設定確認")
        self._create_config_tab(config_frame)
    
    def _create_stats_tab(self, parent):
        """統計タブ作成"""
        # 統計情報表示
        stats_label_frame = ttk.LabelFrame(parent, text="メッセージ統計")
        stats_label_frame.pack(fill='x', padx=5, pady=5)
        
        self.total_messages_var = tk.StringVar(value="0")
        self.translated_messages_var = tk.StringVar(value="0")
        self.translation_rate_var = tk.StringVar(value="0%")
        
        ttk.Label(stats_label_frame, text="総メッセージ数:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_label_frame, textvariable=self.total_messages_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(stats_label_frame, text="翻訳済み:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_label_frame, textvariable=self.translated_messages_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(stats_label_frame, text="翻訳率:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_label_frame, textvariable=self.translation_rate_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        # 言語統計
        lang_label_frame = ttk.LabelFrame(parent, text="言語統計")
        lang_label_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 言語統計用TreeView
        self.lang_tree = ttk.Treeview(lang_label_frame, columns=('count',), show='tree headings', height=8)
        self.lang_tree.heading('#0', text='言語')
        self.lang_tree.heading('count', text='件数')
        self.lang_tree.column('#0', width=100)
        self.lang_tree.column('count', width=80)
        
        lang_scroll = ttk.Scrollbar(lang_label_frame, orient='vertical', command=self.lang_tree.yview)
        self.lang_tree.configure(yscrollcommand=lang_scroll.set)
        
        self.lang_tree.pack(side='left', fill='both', expand=True)
        lang_scroll.pack(side='right', fill='y')
        
        # 統計更新ボタン
        ttk.Button(parent, text="統計更新", command=self._update_statistics).pack(pady=5)
    
    def _create_log_tab(self, parent):
        """ログタブ作成"""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ログ表示エリア
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')
        
        # ログクリアボタン
        ttk.Button(parent, text="ログクリア", command=self._clear_log).pack(pady=5)
    
    def _create_config_tab(self, parent):
        """設定確認タブ作成"""
        config_frame = ttk.Frame(parent)
        config_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 設定表示エリア
        self.config_tree = ttk.Treeview(config_frame, columns=('value',), show='tree headings')
        self.config_tree.heading('#0', text='設定項目')
        self.config_tree.heading('value', text='値')
        self.config_tree.column('#0', width=150)
        self.config_tree.column('value', width=200)
        
        config_scroll = ttk.Scrollbar(config_frame, orient='vertical', command=self.config_tree.yview)
        self.config_tree.configure(yscrollcommand=config_scroll.set)
        
        self.config_tree.pack(side='left', fill='both', expand=True)
        config_scroll.pack(side='right', fill='y')
        
        # 設定更新ボタン
        ttk.Button(parent, text="設定表示更新", command=self._update_config_display).pack(pady=5)
    
    def _load_config(self):
        """設定を読み込み"""
        self.config_manager.load_config()
        self._update_ui_from_config()
    
    def _update_ui_from_config(self):
        """設定からUIを更新"""
        config = self.config_manager.get_all()
        
        # チャンネル・botユーザー表示更新
        channel = config.get("twitch_channel", "")
        bot_user = config.get("trans_username", "")
        
        if channel:
            self.channel_label.configure(text=channel, foreground="green")
        else:
            self.channel_label.configure(text="未設定", foreground="red")
        
        if bot_user:
            self.bot_label.configure(text=bot_user, foreground="green")
        else:
            self.bot_label.configure(text="未設定", foreground="red")
        
        # チャット表示設定更新
        self.chat_display.update_config(config)
        
        # 設定表示更新（簡易版では省略）
        
        # 翻訳エンジン状態更新
        engine = config.get("translator", "google")
        self.status_bar.set_translator_status(engine, "設定済み")
    
    def _auto_connect(self):
        """自動接続"""
        if not self.is_connected:
            valid, errors = self.config_manager.is_valid_config()
            if valid:
                self._toggle_connection()
            else:
                self._log_message("自動接続失敗: 設定が不完全です")
    
    def _toggle_connection(self):
        """接続切り替え"""
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """接続開始"""
        # 設定確認
        valid, errors = self.config_manager.is_valid_config()
        if not valid:
            messagebox.showerror("設定エラー", "\\n".join(errors))
            return
        
        try:
            # 非同期イベントループ開始
            if not self.loop_thread or not self.loop_thread.is_alive():
                self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self.loop_thread.start()
            
            # チャット監視開始
            config = self.config_manager.get_all()
            self.chat_monitor = ChatMonitor(config, self._on_message_received)
            
            # 非同期で接続開始
            asyncio.run_coroutine_threadsafe(self._async_connect(), self.loop)
            
        except Exception as e:
            messagebox.showerror("接続エラー", f"接続に失敗しました: {e}")
            self._log_message(f"接続エラー: {e}")
    
    async def _async_connect(self):
        """非同期接続処理"""
        try:
            success = await self.chat_monitor.start()
            if success:
                self.is_connected = True
                channel = self.config_manager.get("twitch_channel")
                
                # UI更新（メインスレッドで実行）
                self.root.after(0, lambda: self._on_connected(channel))
            else:
                self.root.after(0, lambda: self._on_connect_failed())
                
        except Exception as e:
            self.root.after(0, lambda: self._on_connect_error(str(e)))
    
    def _on_connected(self, channel: str):
        """接続成功時"""
        self.connect_button.configure(text="接続停止")
        self.status_bar.set_connection_status(True, channel)
        self._log_message(f"チャンネル '{channel}' に接続しました")
    
    def _on_connect_failed(self):
        """接続失敗時"""
        messagebox.showerror("接続エラー", "Twitchチャンネルへの接続に失敗しました")
        self._log_message("接続に失敗しました")
    
    def _on_connect_error(self, error: str):
        """接続エラー時"""
        messagebox.showerror("接続エラー", f"接続中にエラーが発生しました: {error}")
        self._log_message(f"接続エラー: {error}")
    
    def _disconnect(self):
        """接続停止"""
        try:
            if self.chat_monitor:
                self.chat_monitor.stop()
            
            self.is_connected = False
            self.connect_button.configure(text="接続開始")
            self.status_bar.set_connection_status(False)
            self._log_message("接続を停止しました")
            
        except Exception as e:
            self._log_message(f"切断エラー: {e}")
    
    def _run_event_loop(self):
        """イベントループ実行"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def _on_message_received(self, message: ChatMessage):
        """メッセージ受信時のコールバック"""
        # UIスレッドでチャット表示更新
        self.root.after(0, lambda: self.chat_display.add_message(message))
        self.root.after(0, self._update_message_stats)
    
    def _update_message_stats(self):
        """メッセージ統計更新"""
        total = self.chat_display.get_message_count()
        translated = sum(1 for msg in self.chat_display.messages if msg.is_translated)
        
        self.total_messages_var.set(str(total))
        self.translated_messages_var.set(str(translated))
        
        self.status_bar.set_message_stats(total, translated)
    
    def _open_settings(self):
        """設定画面を開く"""
        if self.settings_window is None or not self.settings_window.window.winfo_exists():
            self.settings_window = SimpleSettingsWindow(
                self.root, 
                self.config_manager.get_all(), 
                self._on_config_changed
            )
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """設定変更時のコールバック"""
        self.config_manager.update(new_config)
        self.config_manager.save_config()
        self._update_ui_from_config()
        
        # 接続中なら監視設定も更新
        if self.chat_monitor and self.is_connected:
            self.chat_monitor.update_config(new_config)
        
        self._log_message("設定が更新されました")
    
    def _clear_chat(self):
        """チャットクリア"""
        self.chat_display.clear_messages()
        self._update_message_stats()
    
    def _clear_log(self):
        """ログクリア"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _log_message(self, message: str):
        """ログメッセージ追加"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _update_statistics(self):
        """統計情報更新"""
        self._update_message_stats()
        
        # 言語統計更新
        lang_stats = {}
        for message in self.chat_display.messages:
            if message.lang:
                lang_stats[message.lang] = lang_stats.get(message.lang, 0) + 1
        
        # TreeView更新
        for item in self.lang_tree.get_children():
            self.lang_tree.delete(item)
        
        for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
            self.lang_tree.insert('', 'end', text=lang, values=(count,))
    
    def _update_config_display(self):
        """設定表示更新"""
        # TreeView更新
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)
        
        config = self.config_manager.get_all()
        
        # 主要設定のみ表示
        important_configs = {
            "twitch_channel": "Twitchチャンネル",
            "trans_username": "翻訳botユーザー",
            "translator": "翻訳エンジン",
            "lang_trans_to_home": "ホーム言語",
            "lang_home_to_other": "外国語",
            "tts_in": "入力TTS",
            "tts_out": "出力TTS",
            "show_by_name": "ユーザー名表示",
            "show_by_lang": "言語表示"
        }
        
        for key, label in important_configs.items():
            value = config.get(key, "未設定")
            if isinstance(value, bool):
                value = "有効" if value else "無効"
            self.config_tree.insert('', 'end', text=label, values=(str(value),))
    
    def _show_help(self):
        """ヘルプ表示"""
        help_text = """twitchTransFreeNeo v1.0.0 ヘルプ

【基本的な使い方】
1. 「設定」ボタンから必要な設定を行ってください
2. 「接続開始」ボタンでTwitchチャンネルに接続します
3. チャットメッセージが自動的に翻訳されて表示されます

【必須設定】
- Twitchチャンネル名
- 翻訳bot用ユーザー名
- OAuthトークン（https://twitchapps.com/tmi/ で取得）

【機能】
- リアルタイム翻訳
- 翻訳履歴表示
- フィルタリング機能
- 検索機能
- 統計情報表示

【サポート】
問題がある場合は、設定を確認してください。
デバッグモードを有効にすると詳細なログが表示されます。"""
        
        messagebox.showinfo("ヘルプ", help_text)
    
    def _on_closing(self):
        """ウィンドウ終了時"""
        # 接続停止
        if self.is_connected:
            self._disconnect()
        
        # 設定保存
        self.config_manager.save_config()
        
        # イベントループ停止
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # ウィンドウ終了
        self.root.destroy()
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()


def main():
    """メイン関数"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()