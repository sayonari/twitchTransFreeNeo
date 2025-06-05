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

class SimpleMainWindow:
    """簡易メインウィンドウクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config_manager = ConfigManager()
        self.chat_monitor: Optional[ChatMonitor] = None
        self.is_connected = False
        self.settings_window = None
        
        # 非同期イベントループ
        self.loop = asyncio.new_event_loop()
        self.loop_thread = None
        
        try:
            self._setup_window()
            print("ウィンドウ設定完了")
            self._create_widgets()
            print("ウィジェット作成完了")
            self._load_config()
            print("設定読み込み完了")
        except Exception as e:
            print(f"初期化エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_window(self):
        """ウィンドウ設定"""
        from .. import __version__
        self.root.title(f"twitchTransFreeNeo v{__version__}")
        
        # 前回のウィンドウ設定を復元
        self._restore_window_geometry()
        
        self.root.minsize(600, 400)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _restore_window_geometry(self):
        """前回のウィンドウ位置・サイズを復元"""
        config = self.config_manager.get_all()
        window_config = config.get("window_settings", {})
        
        # デフォルト値
        default_width = 900
        default_height = 600
        default_x = 100
        default_y = 100
        
        # 設定から復元
        width = window_config.get("main_width", default_width)
        height = window_config.get("main_height", default_height)
        x = window_config.get("main_x", default_x)
        y = window_config.get("main_y", default_y)
        
        # ジオメトリ設定（画面範囲チェック付き）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 画面外にならないように調整
        if x < 0 or x > screen_width - 200:
            x = default_x
        if y < 0 or y > screen_height - 200:
            y = default_y
        if width < 600:
            width = default_width
        if height < 400:
            height = default_height
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _save_window_geometry(self):
        """現在のウィンドウ位置・サイズを保存"""
        try:
            # 現在の状態を取得
            self.root.update_idletasks()  # ジオメトリ情報を最新にする
            
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # 設定に保存
            config = self.config_manager.get_all()
            if "window_settings" not in config:
                config["window_settings"] = {}
            
            config["window_settings"].update({
                "main_width": width,
                "main_height": height,
                "main_x": x,
                "main_y": y
            })
            
            self.config_manager.update(config)
            
        except Exception as e:
            print(f"ウィンドウジオメトリ保存エラー: {e}")
    
    def _create_widgets(self):
        """ウィジェット作成"""
        try:
            # メインフレーム
            print("メインフレーム作成中...")
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill='both', expand=True, padx=3, pady=3)
            
            # 統合ヘッダー（タイトル+ボタン+情報+アイコン）
            print("統合ヘッダー作成中...")
            self._create_compact_header(main_frame)
            
            # コンテンツエリア（水平分割）
            print("コンテンツエリア作成中...")
            content_frame = ttk.Frame(main_frame)
            content_frame.pack(fill='both', expand=True, pady=(2, 0))
            
            # 左パネル（チャット表示）
            print("左パネル作成中...")
            left_frame = ttk.LabelFrame(content_frame, text="チャット")
            left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
            
            # チャット表示ウィジェット
            print("チャット表示ウィジェット作成中...")
            self.chat_display = SimpleChatDisplay(left_frame, self.config_manager.get_all())
            self.chat_display.pack(fill='both', expand=True, padx=3, pady=3)
            
            # 右パネル（情報パネル）
            print("右パネル作成中...")
            right_frame = ttk.LabelFrame(content_frame, text="情報")
            right_frame.pack(side='right', fill='y', padx=(5, 0))
            right_frame.configure(width=400)
            
            print("情報パネル作成中...")
            self._create_info_panel(right_frame)
            
            # ステータスバー
            print("ステータスバー作成中...")
            self.status_bar = SimpleStatusBar(main_frame)
            self.status_bar.pack(fill='x', pady=(2, 0))
            print("全ウィジェット作成完了")
            
            # デバッグ: ウィジェットの存在確認
            print(f"main_frame exists: {main_frame.winfo_exists()}")
            print(f"title_frame exists: {title_frame.winfo_exists()}")
            print(f"toolbar_frame will be checked...")
            
        except Exception as e:
            print(f"ウィジェット作成エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_compact_header(self, parent):
        """コンパクトヘッダー作成（タイトル+ボタン+情報+アイコンを1行に）"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 2))
        
        # 左側エリア（タイトル+ボタン）
        left_area = ttk.Frame(header_frame)
        left_area.pack(side='left', fill='y')
        
        # タイトル（左側上段）
        title_label = ttk.Label(left_area, text="twitchTransFreeNeo", font=('Arial', 16, 'bold'))
        title_label.pack(anchor='w')
        
        # ボタン群（左側下段）
        buttons_frame = ttk.Frame(left_area)
        buttons_frame.pack(anchor='w', pady=(2, 0))
        
        # 接続ボタン
        self.connect_button = ttk.Button(buttons_frame, text="接続開始", command=self._toggle_connection)
        self.connect_button.pack(side='left', padx=(0, 5))
        
        # 設定ボタン
        settings_button = ttk.Button(buttons_frame, text="設定", command=self._open_settings)
        settings_button.pack(side='left', padx=(0, 5))
        
        # 履歴クリアボタン
        clear_button = ttk.Button(buttons_frame, text="履歴クリア", command=self._clear_chat)
        clear_button.pack(side='left', padx=(0, 5))
        
        # 右側エリア（チャンネル・Bot情報）
        right_area = ttk.Frame(header_frame)
        right_area.pack(side='right', fill='y')
        
        # 情報表示（2行レイアウト）
        info_frame = ttk.Frame(right_area)
        info_frame.pack()
        
        # 1行目：チャンネル
        channel_frame = ttk.Frame(info_frame)
        channel_frame.pack(anchor='w')
        ttk.Label(channel_frame, text="チャンネル:").pack(side='left')
        self.channel_label = ttk.Label(channel_frame, text="未設定", foreground="red")
        self.channel_label.pack(side='left', padx=(2, 0))
        
        # 2行目：Bot
        bot_frame = ttk.Frame(info_frame)
        bot_frame.pack(anchor='w')
        ttk.Label(bot_frame, text="Bot:").pack(side='left')
        self.bot_label = ttk.Label(bot_frame, text="未設定", foreground="red")
        self.bot_label.pack(side='left', padx=(2, 0))
    
    def _create_info_panel(self, parent):
        """情報パネル作成"""
        # 統計情報
        stats_frame = ttk.LabelFrame(parent, text="統計")
        stats_frame.pack(fill='x', padx=3, pady=3)
        
        self.total_messages_var = tk.StringVar(value="0")
        self.translated_messages_var = tk.StringVar(value="0")
        
        ttk.Label(stats_frame, text="総メッセージ:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_messages_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(stats_frame, text="翻訳済み:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.translated_messages_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # 設定確認
        config_frame = ttk.LabelFrame(parent, text="現在の設定")
        config_frame.pack(fill='x', padx=3, pady=3)
        
        self.config_info = tk.Text(config_frame, height=8, width=40, wrap=tk.WORD, state=tk.DISABLED)
        self.config_info.pack(fill='both', expand=True, padx=3, pady=3)
        
        # ログ表示
        log_frame = ttk.LabelFrame(parent, text="ログ")
        log_frame.pack(fill='both', expand=True, padx=3, pady=3)
        
        self.log_text = tk.Text(log_frame, height=8, width=40, wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side='left', fill='both', expand=True, padx=(3, 0), pady=3)
        log_scroll.pack(side='right', fill='y', pady=3)
        
        # ログクリアボタン
        ttk.Button(parent, text="ログクリア", command=self._clear_log).pack(pady=3)
    
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
        
        # 翻訳エンジン状態更新
        engine = config.get("translator", "google")
        self.status_bar.set_translator_status(engine, "設定済み")
        
        # 設定情報表示更新
        self._update_config_display()
    
    def _update_config_display(self):
        """設定情報表示を更新"""
        config = self.config_manager.get_all()
        
        info_text = f"""チャンネル: {config.get('twitch_channel', '未設定')}
Bot: {config.get('trans_username', '未設定')}
翻訳エンジン: {config.get('translator', 'google')}
ホーム言語: {config.get('lang_trans_to_home', 'ja')}
外国語: {config.get('lang_home_to_other', 'en')}
TTS入力: {'有効' if config.get('tts_in', False) else '無効'}
TTS出力: {'有効' if config.get('tts_out', False) else '無効'}
"""
        
        self.config_info.configure(state=tk.NORMAL)
        self.config_info.delete("1.0", tk.END)
        self.config_info.insert("1.0", info_text)
        self.config_info.configure(state=tk.DISABLED)
    
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
            messagebox.showerror("設定エラー", "\n".join(errors))
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
            self._log_message("接続停止処理を開始します...")
            
            if self.chat_monitor:
                self.chat_monitor.stop()
                # 確実にクリア
                self.chat_monitor = None
            
            self.is_connected = False
            self.connect_button.configure(text="接続開始")
            self.status_bar.set_connection_status(False)
            self._log_message("接続を停止しました")
            
        except Exception as e:
            self._log_message(f"切断エラー: {e}")
            # エラーが発生してもUIと状態はリセット
            self.is_connected = False
            self.connect_button.configure(text="接続開始")
            self.status_bar.set_connection_status(False)
            self.chat_monitor = None
    
    def _force_disconnect_all(self):
        """完全切断（表示のみモード変更時など）"""
        try:
            self._log_message("完全切断処理を開始します...")
            
            # 既存の接続を強制停止
            if self.chat_monitor:
                self.chat_monitor.stop()
                self.chat_monitor = None
            
            # イベントループを停止・再作成
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
                # 少し待ってからループをクリア
                import time
                time.sleep(0.5)
            
            # 新しいイベントループを作成
            self.loop = asyncio.new_event_loop()
            self.loop_thread = None
            
            # 状態をリセット
            self.is_connected = False
            self.connect_button.configure(text="接続開始")
            self.status_bar.set_connection_status(False)
            
            self._log_message("完全切断処理が完了しました")
            
        except Exception as e:
            self._log_message(f"完全切断エラー: {e}")
            # エラーが発生してもUIは更新
            self.is_connected = False
            self.connect_button.configure(text="接続開始")
            self.status_bar.set_connection_status(False)
    
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
        try:
            if self.settings_window is None or not self.settings_window.window.winfo_exists():
                self.settings_window = SimpleSettingsWindow(
                    self.root, 
                    self.config_manager.get_all(), 
                    self._on_config_changed
                )
        except Exception as e:
            messagebox.showerror("設定エラー", f"設定画面を開けませんでした: {e}")
            self._log_message(f"設定画面エラー: {e}")
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """設定変更時のコールバック"""
        # 現在の設定と新しい設定を比較
        old_config = self.config_manager.get_all()
        old_view_only = old_config.get("view_only_mode", False)
        new_view_only = new_config.get("view_only_mode", False)
        
        # 表示のみモードが変更された場合
        if old_view_only != new_view_only:
            if self.is_connected:
                self._force_disconnect_all()
                self._log_message(f"表示のみモードが変更されたため接続を完全停止しました (表示のみ: {new_view_only})")
        
        self.config_manager.update(new_config)
        self.config_manager.save_config()
        self._update_ui_from_config()
        
        # 接続中なら監視設定も更新（表示のみモード変更以外の場合）
        if self.chat_monitor and self.is_connected and old_view_only == new_view_only:
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
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        print(log_entry.strip())  # コンソールにも出力
    
    def _on_closing(self):
        """ウィンドウ終了時"""
        # 接続停止
        if self.is_connected:
            self._disconnect()
        
        # ウィンドウ位置・サイズ保存
        self._save_window_geometry()
        
        # 設定保存
        self.config_manager.save_config()
        
        # イベントループ停止
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # ウィンドウ終了
        self.root.destroy()
    
    def run(self):
        """アプリケーション実行"""
        print("mainloop開始前")
        # ウィンドウを前面に表示
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        
        print("mainloop開始")
        self.root.mainloop()
        print("mainloop終了")


def main():
    """メイン関数"""
    app = SimpleMainWindow()
    app.run()


if __name__ == "__main__":
    main()