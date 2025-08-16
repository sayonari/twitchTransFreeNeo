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
    from .settings_window import SimpleSettingsWindow
    from .chat_display import SimpleChatDisplay, SimpleStatusBar
except ImportError:
    # フォールバック: 絶対インポート
    from twitchTransFreeNeo.utils.config_manager import ConfigManager
    from twitchTransFreeNeo.core.chat_monitor import ChatMonitor, ChatMessage
    from twitchTransFreeNeo.gui.settings_window import SimpleSettingsWindow
    from twitchTransFreeNeo.gui.chat_display import SimpleChatDisplay, SimpleStatusBar

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
        self._apply_theme()  # テーマを適用
        self._create_widgets()
        self._load_config()
        
        # 自動接続チェック
        if self.config_manager.get("auto_start", False):
            self.root.after(1000, self._auto_connect)
    
    def _setup_window(self):
        """ウィンドウ設定"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"
        self.root.title(f"twitchTransFreeNeo v{__version__}")
        
        # ウィンドウサイズと位置の設定
        width = self.config_manager.get("window_width", 1200)
        height = self.config_manager.get("window_height", 800)
        x = self.config_manager.get("window_x", None)
        y = self.config_manager.get("window_y", None)
        
        # ウィンドウサイズを設定
        if x is not None and y is not None:
            # 保存された位置がある場合
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            # 初回起動時は画面中央に配置
            self.root.geometry(f"{width}x{height}")
            self.root.update_idletasks()  # ウィンドウサイズを確定
            
            # 画面サイズを取得して中央に配置
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # 最小サイズ設定
        self.root.minsize(1000, 600)
        
        # ウィンドウ状態変更イベントをバインド
        self.root.bind("<Configure>", self._on_window_configure)
        
        # 終了処理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _apply_theme(self):
        """フォントサイズとウィンドウサイズを適用"""
        from tkinter import ttk, font
        
        font_size = self.config_manager.get("font_size", 12)
        
        # フォントの設定
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=font_size)
        
        text_font = font.nametofont("TkTextFont") 
        text_font.configure(size=font_size)
        
        # スタイル設定
        style = ttk.Style()
        style.configure(".", font=('', font_size))
        style.configure("TButton", font=('', font_size))
        style.configure("TEntry", font=('', font_size))
        style.configure("Treeview", font=('', font_size))
        style.configure("Treeview.Heading", font=('', font_size, 'bold'))
        
        # ウィンドウサイズの更新
        width = self.config_manager.get("window_width", 1200)
        height = self.config_manager.get("window_height", 800)
        self.root.geometry(f"{width}x{height}")
    
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
        self.paned_window = ttk.PanedWindow(content_frame, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True)
        
        # 左パネル（チャット表示）
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)
        
        # チャット表示ウィジェット
        self.chat_display = SimpleChatDisplay(left_frame, self.config_manager.get_all())
        self.chat_display.pack(fill='both', expand=True)
        
        # 右パネル（情報パネル）
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)
        
        self._create_simple_info_panel(right_frame)
        
        # ステータスバー
        self.status_bar = SimpleStatusBar(main_frame)
        self.status_bar.pack(fill='x', side='bottom')
        
        # ペイン幅の復元と保存設定
        self.root.after(100, self._restore_pane_position)
        # 複数のイベントにバインドして安定性を向上
        self.paned_window.bind('<ButtonRelease-1>', self._save_pane_position)
        self.paned_window.bind('<Button1-Motion>', self._on_pane_drag)
        self.paned_window.bind('<B1-Motion>', self._on_pane_drag)
    
    def _create_simple_info_panel(self, parent):
        """シンプルな情報パネル作成"""
        # タイトル
        title_label = ttk.Label(parent, text="情報", font=('', 12, 'bold'))
        title_label.pack(pady=10)
        
        # 統計情報
        stats_frame = ttk.LabelFrame(parent, text="統計")
        stats_frame.pack(fill='x', padx=5, pady=5)
        
        self.total_messages_var = tk.StringVar(value="0")
        self.translated_messages_var = tk.StringVar(value="0")
        
        ttk.Label(stats_frame, text="総メッセージ数:").pack(anchor='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_messages_var).pack(anchor='w', padx=15, pady=2)
        
        ttk.Label(stats_frame, text="翻訳済み:").pack(anchor='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.translated_messages_var).pack(anchor='w', padx=15, pady=2)
        
        # 接続情報
        connection_frame = ttk.LabelFrame(parent, text="接続情報")
        connection_frame.pack(fill='x', padx=5, pady=5)
        
        self.connection_status_var = tk.StringVar(value="未接続")
        ttk.Label(connection_frame, text="状態:").pack(anchor='w', padx=5, pady=2)
        self.connection_status_label = ttk.Label(connection_frame, textvariable=self.connection_status_var)
        self.connection_status_label.pack(anchor='w', padx=15, pady=2)
        
        # ログエリア
        log_frame = ttk.LabelFrame(parent, text="ログ")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')
    
    def _create_toolbar(self, parent):
        """ツールバー作成"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        # 接続ボタン
        self.connect_button = ttk.Button(toolbar, text="接続開始", command=self._toggle_connection)
        self.connect_button.pack(side='left', padx=2)
        
        # 設定ボタン
        ttk.Button(toolbar, text="設定", command=self._open_settings).pack(side='left', padx=2)
        
        # 診断ボタン
        ttk.Button(toolbar, text="診断", command=self._open_diagnostics).pack(side='left', padx=2)
        
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
        
        # フォントサイズ更新
        font_size = config.get("font_size", 12)
        self.status_bar.update_font_size(font_size)
        
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
        # ボタンを一時的に無効化（連続クリック防止）
        self.connect_button.configure(state='disabled')
        self.root.update_idletasks()
        
        try:
            if self.is_connected:
                self._disconnect()
            else:
                self._connect()
        finally:
            # 1秒後にボタンを再有効化
            self.root.after(1000, lambda: self.connect_button.configure(state='normal'))
    
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
    
    def _open_diagnostics(self):
        """診断ウィンドウを開く"""
        from ..utils.diagnostics import DiagnosticsWindow
        DiagnosticsWindow(self.root, self.config_manager.get_all())
    
    def _open_settings(self):
        """設定画面を開く"""
        try:
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.window.winfo_exists():
                self.settings_window.window.lift()
                return
        except:
            pass
        
        self.settings_window = SimpleSettingsWindow(
            self.root, 
            self.config_manager.get_all(), 
            self._on_config_changed
        )
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """設定変更時のコールバック"""
        self.config_manager.update(new_config)
        self.config_manager.save_config()
        self._apply_theme()  # テーマを再適用
        self._update_ui_from_config()
        
        # 接続中なら一度切断して再接続（新しい設定を反映させるため）
        if self.chat_monitor and self.is_connected:
            self._log_message("設定変更のため、Twitchとの接続を再起動します...")
            
            # 現在の接続を停止
            self._disconnect()
            
            # 少し待機（接続の確実な終了を待つ）
            self.root.after(1000, self._restart_connection_with_new_config, new_config)
        else:
            self._log_message("設定が更新されました")
    
    def _restart_connection_with_new_config(self, new_config: Dict[str, Any]):
        """新しい設定でTwitch接続を再開"""
        self._log_message("新しい設定でTwitchに再接続します...")
        self._connect()
    
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
        log_entry = f"[{timestamp}] {message}\n"
        
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
    
    def _restore_pane_position(self):
        """ペイン位置を復元"""
        try:
            pane_position = self.config_manager.get("pane_position", None)
            if pane_position is not None and pane_position > 200:  # 最小幅チェック
                self.paned_window.sashpos(0, pane_position)
            else:
                # デフォルト位置を設定（ウィンドウ幅の75%）
                self.root.update_idletasks()
                width = self.paned_window.winfo_width()
                if width > 1:
                    default_pos = int(width * 0.75)
                    self.paned_window.sashpos(0, default_pos)
        except Exception as e:
            print(f"ペイン位置復元エラー: {e}")
    
    def _on_pane_drag(self, event=None):
        """ペインドラッグ中の処理"""
        # ドラッグ中は頻繁に保存しない（パフォーマンス向上）
        pass
    
    def _save_pane_position(self, event=None):
        """ペイン位置を保存"""
        try:
            position = self.paned_window.sashpos(0)
            if position > 200:  # 最小幅チェック
                self.config_manager.set("pane_position", position)
                # 遅延保存でパフォーマンス向上
                if hasattr(self, '_save_timer'):
                    self.root.after_cancel(self._save_timer)
                self._save_timer = self.root.after(500, self._delayed_save)
        except Exception as e:
            print(f"ペイン位置保存エラー: {e}")
    
    def _delayed_save(self):
        """遅延保存"""
        try:
            self.config_manager.save_config()
        except:
            pass
    
    def _on_window_configure(self, event=None):
        """ウィンドウ設定変更時のコールバック"""
        # ウィンドウのリサイズや移動が頻繁に発生するため、
        # 遅延保存を使用してパフォーマンスを向上
        if hasattr(self, '_geometry_save_timer'):
            self.root.after_cancel(self._geometry_save_timer)
        # 500ms後に保存（連続的な変更が終わってから保存）
        self._geometry_save_timer = self.root.after(500, self._save_window_geometry)
    
    def _save_window_geometry(self):
        """ウィンドウの位置とサイズを保存"""
        try:
            # 現在のウィンドウジオメトリを取得
            geometry = self.root.geometry()
            # 例: "1200x800+100+50" の形式をパース
            match = geometry.split('+')
            if len(match) == 3:
                size = match[0].split('x')
                if len(size) == 2:
                    width = int(size[0])
                    height = int(size[1])
                    x = int(match[1])
                    y = int(match[2])
                    
                    # 設定を更新（最小サイズ以上の場合のみ保存）
                    if width >= 1000 and height >= 600:
                        self.config_manager.set("window_width", width)
                        self.config_manager.set("window_height", height)
                        self.config_manager.set("window_x", x)
                        self.config_manager.set("window_y", y)
        except Exception as e:
            print(f"ウィンドウジオメトリ保存エラー: {e}")
    
    def _show_help(self):
        """ヘルプ表示"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"
        
        help_text = f"""twitchTransFreeNeo v{__version__} ヘルプ

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
        # ウィンドウの位置とサイズを保存
        self._save_window_geometry()
        
        # 接続停止
        if self.is_connected:
            self._disconnect()
        
        # 設定保存
        self.config_manager.save_config()
        
        # イベントループ停止
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            # ループスレッドの終了を待つ
            if self.loop_thread and self.loop_thread.is_alive():
                self.loop_thread.join(timeout=2)
        
        # pygameを明示的に終了（macOSのautorelease pool問題対策）
        try:
            import pygame
            if pygame.get_init():
                pygame.quit()
        except:
            pass
        
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