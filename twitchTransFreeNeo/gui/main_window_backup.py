#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from typing import Dict, Any, Optional
from ..utils.config_manager import ConfigManager
from ..core.chat_monitor import ChatMonitor, ChatMessage
from .settings_window import SettingsWindow
from .chat_display import ChatDisplayWidget, StatusBar

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
        
        # アイコン設定（オプション）
        try:
            # アイコンファイルがある場合
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass
    
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
        self.chat_display = ChatDisplayWidget(left_frame, self.config_manager.get_all())
        self.chat_display.pack(fill='both', expand=True)
        
        # 右パネル（情報パネル）
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        self._create_info_panel(right_frame)
        
        # ステータスバー
        self.status_bar = StatusBar(main_frame)
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
        self._create_config_tab(config_frame)\n    \n    def _create_stats_tab(self, parent):\n        \"\"\"統計タブ作成\"\"\"\n        # 統計情報表示\n        stats_label_frame = ttk.LabelFrame(parent, text=\"メッセージ統計\")\n        stats_label_frame.pack(fill='x', padx=5, pady=5)\n        \n        self.total_messages_var = tk.StringVar(value=\"0\")\n        self.translated_messages_var = tk.StringVar(value=\"0\")\n        self.translation_rate_var = tk.StringVar(value=\"0%\")\n        \n        ttk.Label(stats_label_frame, text=\"総メッセージ数:\").grid(row=0, column=0, sticky='w', padx=5, pady=2)\n        ttk.Label(stats_label_frame, textvariable=self.total_messages_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)\n        \n        ttk.Label(stats_label_frame, text=\"翻訳済み:\").grid(row=1, column=0, sticky='w', padx=5, pady=2)\n        ttk.Label(stats_label_frame, textvariable=self.translated_messages_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)\n        \n        ttk.Label(stats_label_frame, text=\"翻訳率:\").grid(row=2, column=0, sticky='w', padx=5, pady=2)\n        ttk.Label(stats_label_frame, textvariable=self.translation_rate_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)\n        \n        # 言語統計\n        lang_label_frame = ttk.LabelFrame(parent, text=\"言語統計\")\n        lang_label_frame.pack(fill='both', expand=True, padx=5, pady=5)\n        \n        # 言語統計用TreeView\n        self.lang_tree = ttk.Treeview(lang_label_frame, columns=('count',), show='tree headings', height=8)\n        self.lang_tree.heading('#0', text='言語')\n        self.lang_tree.heading('count', text='件数')\n        self.lang_tree.column('#0', width=100)\n        self.lang_tree.column('count', width=80)\n        \n        lang_scroll = ttk.Scrollbar(lang_label_frame, orient='vertical', command=self.lang_tree.yview)\n        self.lang_tree.configure(yscrollcommand=lang_scroll.set)\n        \n        self.lang_tree.pack(side='left', fill='both', expand=True)\n        lang_scroll.pack(side='right', fill='y')\n        \n        # 統計更新ボタン\n        ttk.Button(parent, text=\"統計更新\", command=self._update_statistics).pack(pady=5)\n    \n    def _create_log_tab(self, parent):\n        \"\"\"ログタブ作成\"\"\"\n        log_frame = ttk.Frame(parent)\n        log_frame.pack(fill='both', expand=True, padx=5, pady=5)\n        \n        # ログ表示エリア\n        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)\n        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)\n        self.log_text.configure(yscrollcommand=log_scroll.set)\n        \n        self.log_text.pack(side='left', fill='both', expand=True)\n        log_scroll.pack(side='right', fill='y')\n        \n        # ログクリアボタン\n        ttk.Button(parent, text=\"ログクリア\", command=self._clear_log).pack(pady=5)\n    \n    def _create_config_tab(self, parent):\n        \"\"\"設定確認タブ作成\"\"\"\n        config_frame = ttk.Frame(parent)\n        config_frame.pack(fill='both', expand=True, padx=5, pady=5)\n        \n        # 設定表示エリア\n        self.config_tree = ttk.Treeview(config_frame, columns=('value',), show='tree headings')\n        self.config_tree.heading('#0', text='設定項目')\n        self.config_tree.heading('value', text='値')\n        self.config_tree.column('#0', width=150)\n        self.config_tree.column('value', width=200)\n        \n        config_scroll = ttk.Scrollbar(config_frame, orient='vertical', command=self.config_tree.yview)\n        self.config_tree.configure(yscrollcommand=config_scroll.set)\n        \n        self.config_tree.pack(side='left', fill='both', expand=True)\n        config_scroll.pack(side='right', fill='y')\n        \n        # 設定更新ボタン\n        ttk.Button(parent, text=\"設定表示更新\", command=self._update_config_display).pack(pady=5)\n    \n    def _load_config(self):\n        \"\"\"設定を読み込み\"\"\"\n        self.config_manager.load_config()\n        self._update_ui_from_config()\n    \n    def _update_ui_from_config(self):\n        \"\"\"設定からUIを更新\"\"\"\n        config = self.config_manager.get_all()\n        \n        # チャンネル・botユーザー表示更新\n        channel = config.get(\"twitch_channel\", \"\")\n        bot_user = config.get(\"trans_username\", \"\")\n        \n        if channel:\n            self.channel_label.configure(text=channel, foreground=\"green\")\n        else:\n            self.channel_label.configure(text=\"未設定\", foreground=\"red\")\n        \n        if bot_user:\n            self.bot_label.configure(text=bot_user, foreground=\"green\")\n        else:\n            self.bot_label.configure(text=\"未設定\", foreground=\"red\")\n        \n        # チャット表示設定更新\n        self.chat_display.update_config(config)\n        \n        # 設定表示更新\n        self._update_config_display()\n        \n        # 翻訳エンジン状態更新\n        engine = config.get(\"translator\", \"google\")\n        self.status_bar.set_translator_status(engine, \"設定済み\")\n    \n    def _auto_connect(self):\n        \"\"\"自動接続\"\"\"\n        if not self.is_connected:\n            valid, errors = self.config_manager.is_valid_config()\n            if valid:\n                self._toggle_connection()\n            else:\n                self._log_message(\"自動接続失敗: 設定が不完全です\")\n    \n    def _toggle_connection(self):\n        \"\"\"接続切り替え\"\"\"\n        if self.is_connected:\n            self._disconnect()\n        else:\n            self._connect()\n    \n    def _connect(self):\n        \"\"\"接続開始\"\"\"\n        # 設定確認\n        valid, errors = self.config_manager.is_valid_config()\n        if not valid:\n            messagebox.showerror(\"設定エラー\", \"\\n\".join(errors))\n            return\n        \n        try:\n            # 非同期イベントループ開始\n            if not self.loop_thread or not self.loop_thread.is_alive():\n                self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)\n                self.loop_thread.start()\n            \n            # チャット監視開始\n            config = self.config_manager.get_all()\n            self.chat_monitor = ChatMonitor(config, self._on_message_received)\n            \n            # 非同期で接続開始\n            asyncio.run_coroutine_threadsafe(self._async_connect(), self.loop)\n            \n        except Exception as e:\n            messagebox.showerror(\"接続エラー\", f\"接続に失敗しました: {e}\")\n            self._log_message(f\"接続エラー: {e}\")\n    \n    async def _async_connect(self):\n        \"\"\"非同期接続処理\"\"\"\n        try:\n            success = await self.chat_monitor.start()\n            if success:\n                self.is_connected = True\n                channel = self.config_manager.get(\"twitch_channel\")\n                \n                # UI更新（メインスレッドで実行）\n                self.root.after(0, lambda: self._on_connected(channel))\n            else:\n                self.root.after(0, lambda: self._on_connect_failed())\n                \n        except Exception as e:\n            self.root.after(0, lambda: self._on_connect_error(str(e)))\n    \n    def _on_connected(self, channel: str):\n        \"\"\"接続成功時\"\"\"\n        self.connect_button.configure(text=\"接続停止\")\n        self.status_bar.set_connection_status(True, channel)\n        self._log_message(f\"チャンネル '{channel}' に接続しました\")\n    \n    def _on_connect_failed(self):\n        \"\"\"接続失敗時\"\"\"\n        messagebox.showerror(\"接続エラー\", \"Twitchチャンネルへの接続に失敗しました\")\n        self._log_message(\"接続に失敗しました\")\n    \n    def _on_connect_error(self, error: str):\n        \"\"\"接続エラー時\"\"\"\n        messagebox.showerror(\"接続エラー\", f\"接続中にエラーが発生しました: {error}\")\n        self._log_message(f\"接続エラー: {error}\")\n    \n    def _disconnect(self):\n        \"\"\"接続停止\"\"\"\n        try:\n            if self.chat_monitor:\n                self.chat_monitor.stop()\n            \n            self.is_connected = False\n            self.connect_button.configure(text=\"接続開始\")\n            self.status_bar.set_connection_status(False)\n            self._log_message(\"接続を停止しました\")\n            \n        except Exception as e:\n            self._log_message(f\"切断エラー: {e}\")\n    \n    def _run_event_loop(self):\n        \"\"\"イベントループ実行\"\"\"\n        asyncio.set_event_loop(self.loop)\n        self.loop.run_forever()\n    \n    def _on_message_received(self, message: ChatMessage):\n        \"\"\"メッセージ受信時のコールバック\"\"\"\n        # UIスレッドでチャット表示更新\n        self.root.after(0, lambda: self.chat_display.add_message(message))\n        self.root.after(0, self._update_message_stats)\n    \n    def _update_message_stats(self):\n        \"\"\"メッセージ統計更新\"\"\"\n        total = self.chat_display.get_message_count()\n        filtered = len(self.chat_display.get_filtered_messages())\n        translated = sum(1 for msg in self.chat_display.messages if msg.is_translated)\n        \n        self.total_messages_var.set(str(total))\n        self.translated_messages_var.set(str(translated))\n        \n        if total > 0:\n            rate = (translated / total) * 100\n            self.translation_rate_var.set(f\"{rate:.1f}%\")\n        else:\n            self.translation_rate_var.set(\"0%\")\n        \n        self.status_bar.set_message_stats(total, translated)\n    \n    def _open_settings(self):\n        \"\"\"設定画面を開く\"\"\"\n        if self.settings_window is None or not self.settings_window.window.winfo_exists():\n            self.settings_window = SettingsWindow(\n                self.root, \n                self.config_manager.get_all(), \n                self._on_config_changed\n            )\n    \n    def _on_config_changed(self, new_config: Dict[str, Any]):\n        \"\"\"設定変更時のコールバック\"\"\"\n        self.config_manager.update(new_config)\n        self.config_manager.save_config()\n        self._update_ui_from_config()\n        \n        # 接続中なら監視設定も更新\n        if self.chat_monitor and self.is_connected:\n            self.chat_monitor.update_config(new_config)\n        \n        self._log_message(\"設定が更新されました\")\n    \n    def _clear_chat(self):\n        \"\"\"チャットクリア\"\"\"\n        self.chat_display.clear_messages()\n        self._update_message_stats()\n    \n    def _clear_log(self):\n        \"\"\"ログクリア\"\"\"\n        self.log_text.configure(state=tk.NORMAL)\n        self.log_text.delete(\"1.0\", tk.END)\n        self.log_text.configure(state=tk.DISABLED)\n    \n    def _log_message(self, message: str):\n        \"\"\"ログメッセージ追加\"\"\"\n        from datetime import datetime\n        timestamp = datetime.now().strftime(\"%H:%M:%S\")\n        log_entry = f\"[{timestamp}] {message}\\n\"\n        \n        self.log_text.configure(state=tk.NORMAL)\n        self.log_text.insert(tk.END, log_entry)\n        self.log_text.see(tk.END)\n        self.log_text.configure(state=tk.DISABLED)\n    \n    def _update_statistics(self):\n        \"\"\"統計情報更新\"\"\"\n        self._update_message_stats()\n        \n        # 言語統計更新\n        lang_stats = {}\n        for message in self.chat_display.messages:\n            if message.lang:\n                lang_stats[message.lang] = lang_stats.get(message.lang, 0) + 1\n        \n        # TreeView更新\n        for item in self.lang_tree.get_children():\n            self.lang_tree.delete(item)\n        \n        for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):\n            self.lang_tree.insert('', 'end', text=lang, values=(count,))\n    \n    def _update_config_display(self):\n        \"\"\"設定表示更新\"\"\"\n        # TreeView更新\n        for item in self.config_tree.get_children():\n            self.config_tree.delete(item)\n        \n        config = self.config_manager.get_all()\n        \n        # 主要設定のみ表示\n        important_configs = {\n            \"twitch_channel\": \"Twitchチャンネル\",\n            \"trans_username\": \"翻訳botユーザー\",\n            \"translator\": \"翻訳エンジン\",\n            \"lang_trans_to_home\": \"ホーム言語\",\n            \"lang_home_to_other\": \"外国語\",\n            \"tts_in\": \"入力TTS\",\n            \"tts_out\": \"出力TTS\",\n            \"show_by_name\": \"ユーザー名表示\",\n            \"show_by_lang\": \"言語表示\"\n        }\n        \n        for key, label in important_configs.items():\n            value = config.get(key, \"未設定\")\n            if isinstance(value, bool):\n                value = \"有効\" if value else \"無効\"\n            self.config_tree.insert('', 'end', text=label, values=(str(value),))\n    \n    def _show_help(self):\n        \"\"\"ヘルプ表示\"\"\"\n        help_text = \"\"\"\ntwitchTransFreeNeo v1.0.0 ヘルプ\n\n【基本的な使い方】\n1. 「設定」ボタンから必要な設定を行ってください\n2. 「接続開始」ボタンでTwitchチャンネルに接続します\n3. チャットメッセージが自動的に翻訳されて表示されます\n\n【必須設定】\n- Twitchチャンネル名\n- 翻訳bot用ユーザー名\n- OAuthトークン（https://twitchapps.com/tmi/ で取得）\n\n【機能】\n- リアルタイム翻訳\n- 翻訳履歴表示\n- フィルタリング機能\n- 検索機能\n- 統計情報表示\n\n【サポート】\n問題がある場合は、設定を確認してください。\nデバッグモードを有効にすると詳細なログが表示されます。\"\"\"\n        \n        messagebox.showinfo(\"ヘルプ\", help_text)\n    \n    def _on_closing(self):\n        \"\"\"ウィンドウ終了時\"\"\"\n        # 接続停止\n        if self.is_connected:\n            self._disconnect()\n        \n        # 設定保存\n        self.config_manager.save_config()\n        \n        # イベントループ停止\n        if self.loop and self.loop.is_running():\n            self.loop.call_soon_threadsafe(self.loop.stop)\n        \n        # ウィンドウ終了\n        self.root.destroy()\n    \n    def run(self):\n        \"\"\"アプリケーション実行\"\"\"\n        self.root.mainloop()


def main():\n    \"\"\"メイン関数\"\"\"\n    app = MainWindow()\n    app.run()\n\n\nif __name__ == \"__main__\":\n    main()