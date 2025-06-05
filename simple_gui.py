#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo 簡易版GUI
基本機能のテスト用簡易バージョン
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class SimpleConfigManager:
    """簡易設定管理"""
    
    def __init__(self):
        self.config_file = "simple_config.json"
        self.config = {
            "twitch_channel": "",
            "trans_username": "",
            "trans_oauth": "",
            "translator": "google",
            "lang_trans_to_home": "ja",
            "lang_home_to_other": "en"
        }
        self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False

class SimpleGUI:
    """簡易GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config_manager = SimpleConfigManager()
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        self.root.title("twitchTransFreeNeo 簡易版 v1.0.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
    
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="twitchTransFreeNeo", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 設定フレーム
        config_frame = ttk.LabelFrame(main_frame, text="基本設定")
        config_frame.pack(fill='x', pady=10)
        
        # 設定項目
        ttk.Label(config_frame, text="Twitchチャンネル名:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.channel_var = tk.StringVar(value=self.config_manager.config.get("twitch_channel", ""))
        ttk.Entry(config_frame, textvariable=self.channel_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="翻訳botユーザー名:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.username_var = tk.StringVar(value=self.config_manager.config.get("trans_username", ""))
        ttk.Entry(config_frame, textvariable=self.username_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="OAuthトークン:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.oauth_var = tk.StringVar(value=self.config_manager.config.get("trans_oauth", ""))
        ttk.Entry(config_frame, textvariable=self.oauth_var, width=30, show="*").grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="翻訳エンジン:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.translator_var = tk.StringVar(value=self.config_manager.config.get("translator", "google"))
        translator_combo = ttk.Combobox(config_frame, textvariable=self.translator_var, width=27)
        translator_combo['values'] = ['google', 'deepl']
        translator_combo.grid(row=3, column=1, padx=5, pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="設定保存", command=self.save_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="設定読み込み", command=self.load_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="OAuth取得ページ", command=self.open_oauth_page).pack(side='left', padx=5)
        
        # ステータスフレーム
        status_frame = ttk.LabelFrame(main_frame, text="ステータス")
        status_frame.pack(fill='x', pady=10)
        
        self.status_var = tk.StringVar(value="設定を入力してください")
        ttk.Label(status_frame, textvariable=self.status_var).pack(pady=10)
        
        # 接続ボタン
        connect_frame = ttk.Frame(main_frame)
        connect_frame.pack(fill='x', pady=10)
        
        self.connect_button = ttk.Button(connect_frame, text="接続テスト", command=self.test_connection)
        self.connect_button.pack(pady=10)
        
        # 情報フレーム
        info_frame = ttk.LabelFrame(main_frame, text="情報")
        info_frame.pack(fill='both', expand=True, pady=10)
        
        info_text = tk.Text(info_frame, height=8, wrap=tk.WORD)
        info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        info_text.insert('1.0', """
twitchTransFreeNeo 簡易版

これは基本機能をテストするための簡易版です。

【設定手順】
1. https://twitchapps.com/tmi/ でOAuthトークンを取得
2. Twitchチャンネル名、翻訳botユーザー名、OAuthトークンを入力
3. 「設定保存」をクリック
4. 「接続テスト」で設定を確認

【次のステップ】
- 依存関係のインストール: pip install -r requirements.txt
- フル機能版の起動: python run.py

このGUIが正常に動作すれば、フル機能版も動作するはずです。
        """)
        info_text.configure(state=tk.DISABLED)
    
    def save_config(self):
        """設定保存"""
        self.config_manager.config.update({
            "twitch_channel": self.channel_var.get().strip(),
            "trans_username": self.username_var.get().strip(),
            "trans_oauth": self.oauth_var.get().strip(),
            "translator": self.translator_var.get()
        })
        
        if self.config_manager.save_config():
            self.status_var.set("設定を保存しました")
            messagebox.showinfo("成功", "設定を保存しました")
        else:
            self.status_var.set("設定保存に失敗しました")
            messagebox.showerror("エラー", "設定保存に失敗しました")
    
    def load_config(self):
        """設定読み込み"""
        self.config_manager.load_config()
        
        self.channel_var.set(self.config_manager.config.get("twitch_channel", ""))
        self.username_var.set(self.config_manager.config.get("trans_username", ""))
        self.oauth_var.set(self.config_manager.config.get("trans_oauth", ""))
        self.translator_var.set(self.config_manager.config.get("translator", "google"))
        
        self.status_var.set("設定を読み込みました")
        messagebox.showinfo("成功", "設定を読み込みました")
    
    def open_oauth_page(self):
        """OAuth取得ページを開く"""
        import webbrowser
        webbrowser.open("https://twitchapps.com/tmi/")
        self.status_var.set("OAuth取得ページを開きました")
    
    def test_connection(self):
        """接続テスト"""
        channel = self.channel_var.get().strip()
        username = self.username_var.get().strip()
        oauth = self.oauth_var.get().strip()
        
        if not channel or not username or not oauth:
            self.status_var.set("必須項目が未入力です")
            messagebox.showerror("エラー", "すべての必須項目を入力してください")
            return
        
        self.status_var.set("設定は正常です（実際の接続テストは未実装）")
        messagebox.showinfo("テスト結果", f"""
設定確認結果:
✓ チャンネル: {channel}
✓ ユーザー名: {username}  
✓ OAuth: 設定済み
✓ 翻訳エンジン: {self.translator_var.get()}

設定は正常です。
フル機能版を起動するには依存関係をインストールしてください:
pip install -r requirements.txt
        """)
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

def main():
    """メイン関数"""
    print("twitchTransFreeNeo 簡易版GUI を起動中...")
    
    try:
        app = SimpleGUI()
        app.run()
    except Exception as e:
        print(f"エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())