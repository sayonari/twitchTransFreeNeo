#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依存関係なしの独立GUI版 twitchTransFreeNeo
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime

class StandaloneGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("twitchTransFreeNeo v1.0.0 (Standalone)")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        
        # 設定データ
        self.config_file = "config.json"
        self.config = {
            "twitch_channel": "",
            "trans_username": "",
            "trans_oauth": "",
            "translator": "google",
            "lang_trans_to_home": "ja",
            "lang_home_to_other": "en"
        }
        self.load_config()
        
        self._create_widgets()
        self.log_message("twitchTransFreeNeo Standalone版を起動しました")
        self.log_message("注意: この版では実際の翻訳機能は含まれていません")
        
    def _create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # タイトル
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(title_frame, text="twitchTransFreeNeo", font=('Arial', 16, 'bold')).pack(side='left')
        ttk.Label(title_frame, text="(Standalone版)", font=('Arial', 10), foreground='gray').pack(side='left', padx=(10, 0))
        
        # ツールバー
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        self.connect_button = ttk.Button(toolbar, text="設定", command=self.open_settings)
        self.connect_button.pack(side='left', padx=(0, 5))
        
        ttk.Button(toolbar, text="ログクリア", command=self.clear_log).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="設定ファイル保存", command=self.save_config).pack(side='left', padx=(0, 5))
        
        # ステータス
        status_frame = ttk.Frame(toolbar)
        status_frame.pack(side='right')
        
        ttk.Label(status_frame, text="チャンネル:").pack(side='left')
        self.channel_label = ttk.Label(status_frame, text="未設定", foreground="red")
        self.channel_label.pack(side='left', padx=(2, 10))
        
        # コンテンツエリア
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # 左パネル - 模擬チャット表示
        left_frame = ttk.LabelFrame(content_frame, text="チャット表示（模擬）")
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.chat_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
        self.chat_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # サンプルチャットボタン
        sample_frame = ttk.Frame(left_frame)
        sample_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        ttk.Button(sample_frame, text="サンプルメッセージ追加", command=self.add_sample_message).pack(side='left')
        ttk.Button(sample_frame, text="チャットクリア", command=self.clear_chat).pack(side='left', padx=(5, 0))
        
        # 右パネル - 情報
        right_frame = ttk.LabelFrame(content_frame, text="情報・ログ")
        right_frame.pack(side='right', fill='y', padx=(5, 0))
        right_frame.configure(width=300)
        
        # 設定表示
        config_frame = ttk.LabelFrame(right_frame, text="現在の設定")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        self.config_display = tk.Text(config_frame, height=6, width=30, wrap=tk.WORD, state=tk.DISABLED)
        self.config_display.pack(fill='x', padx=5, pady=5)
        
        # ログ
        log_frame = ttk.LabelFrame(right_frame, text="ログ")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=30, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ステータスバー
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill='x', pady=(5, 0))
        
        self.status_label = ttk.Label(status_bar, text="準備完了")
        self.status_label.pack(side='left')
        
        self.time_label = ttk.Label(status_bar, text="")
        self.time_label.pack(side='right')
        
        self.update_displays()
        self.update_time()
    
    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        try:
            self.time_label.configure(text=current_time)
            self.root.after(1000, self.update_time)
        except tk.TclError:
            pass  # ウィンドウが閉じられた場合
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 設定フレーム
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="基本設定", font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Twitchチャンネル
        ttk.Label(main_frame, text="Twitchチャンネル名:").pack(anchor='w')
        self.channel_var = tk.StringVar(value=self.config.get("twitch_channel", ""))
        ttk.Entry(main_frame, textvariable=self.channel_var, width=50).pack(fill='x', pady=(0, 10))
        
        # ユーザー名
        ttk.Label(main_frame, text="翻訳botユーザー名:").pack(anchor='w')
        self.username_var = tk.StringVar(value=self.config.get("trans_username", ""))
        ttk.Entry(main_frame, textvariable=self.username_var, width=50).pack(fill='x', pady=(0, 10))
        
        # OAuth
        ttk.Label(main_frame, text="OAuthトークン:").pack(anchor='w')
        self.oauth_var = tk.StringVar(value=self.config.get("trans_oauth", ""))
        ttk.Entry(main_frame, textvariable=self.oauth_var, width=50, show="*").pack(fill='x', pady=(0, 5))
        
        # OAuth取得ボタン
        oauth_frame = ttk.Frame(main_frame)
        oauth_frame.pack(fill='x', pady=(0, 15))
        
        def open_oauth_page():
            import webbrowser
            webbrowser.open("https://twitchapps.com/tmi/")
            self.log_message("OAuth取得ページを開きました")
        
        ttk.Button(oauth_frame, text="OAuth取得ページを開く", command=open_oauth_page).pack(side='left')
        
        # 翻訳設定
        ttk.Label(main_frame, text="翻訳設定", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 5))
        
        trans_frame = ttk.Frame(main_frame)
        trans_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(trans_frame, text="翻訳エンジン:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.translator_var = tk.StringVar(value=self.config.get("translator", "google"))
        translator_combo = ttk.Combobox(trans_frame, textvariable=self.translator_var, width=15)
        translator_combo['values'] = ['google', 'deepl']
        translator_combo.grid(row=0, column=1, sticky='w')
        
        ttk.Label(trans_frame, text="ホーム言語:").grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        self.home_lang_var = tk.StringVar(value=self.config.get("lang_trans_to_home", "ja"))
        home_lang_combo = ttk.Combobox(trans_frame, textvariable=self.home_lang_var, width=15)
        home_lang_combo['values'] = ['ja', 'en', 'ko', 'zh-CN', 'zh-TW', 'fr', 'de', 'es']
        home_lang_combo.grid(row=1, column=1, sticky='w', pady=(5, 0))
        
        ttk.Label(trans_frame, text="外国語:").grid(row=2, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        self.other_lang_var = tk.StringVar(value=self.config.get("lang_home_to_other", "en"))
        other_lang_combo = ttk.Combobox(trans_frame, textvariable=self.other_lang_var, width=15)
        other_lang_combo['values'] = ['en', 'ja', 'ko', 'zh-CN', 'zh-TW', 'fr', 'de', 'es']
        other_lang_combo.grid(row=2, column=1, sticky='w', pady=(5, 0))
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        def save_settings():
            self.config.update({
                "twitch_channel": self.channel_var.get().strip(),
                "trans_username": self.username_var.get().strip(), 
                "trans_oauth": self.oauth_var.get().strip(),
                "translator": self.translator_var.get(),
                "lang_trans_to_home": self.home_lang_var.get(),
                "lang_home_to_other": self.other_lang_var.get()
            })
            self.save_config()
            self.update_displays()
            self.log_message("設定を保存しました")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=settings_window.destroy).pack(side='right')
    
    def update_displays(self):
        # チャンネル表示更新
        channel = self.config.get("twitch_channel", "")
        if channel:
            self.channel_label.configure(text=channel, foreground="green")
        else:
            self.channel_label.configure(text="未設定", foreground="red")
        
        # 設定表示更新
        config_text = f"""チャンネル: {self.config.get('twitch_channel', '未設定')}
Bot用ユーザー: {self.config.get('trans_username', '未設定')}
OAuth: {'設定済み' if self.config.get('trans_oauth') else '未設定'}
翻訳エンジン: {self.config.get('translator', 'google')}
ホーム言語: {self.config.get('lang_trans_to_home', 'ja')}
外国語: {self.config.get('lang_home_to_other', 'en')}"""
        
        self.config_display.configure(state=tk.NORMAL)
        self.config_display.delete("1.0", tk.END)
        self.config_display.insert("1.0", config_text)
        self.config_display.configure(state=tk.DISABLED)
    
    def add_sample_message(self):
        import random
        sample_messages = [
            "Hello everyone! こんにちは！",
            "This is a test message これはテストメッセージです",
            "Great stream! 素晴らしい配信ですね！",
            "Thanks for the translation ありがとうございます",
            "LOL that was funny! それは面白かった！"
        ]
        
        message = random.choice(sample_messages)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{timestamp}] TestUser: {message}\n")
        self.chat_text.insert(tk.END, f"  → [翻訳例] This would be translated\n\n")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)
        
        self.log_message("サンプルメッセージを追加しました")
    
    def clear_chat(self):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.configure(state=tk.DISABLED)
        self.log_message("チャットをクリアしました")
    
    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        print(log_entry.strip())
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
                    print("設定ファイルを読み込みました")
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log_message(f"設定保存エラー: {e}")
            return False
    
    def run(self):
        self.root.mainloop()

def main():
    print("twitchTransFreeNeo Standalone版を起動中...")
    app = StandaloneGUI()
    app.run()

if __name__ == "__main__":
    main()