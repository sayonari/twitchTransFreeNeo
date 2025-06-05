#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小限のテスト用GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class TestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("twitchTransFreeNeo Test GUI")
        self.root.geometry("800x600")
        
        self._create_widgets()
    
    def _create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # タイトル
        ttk.Label(main_frame, text="twitchTransFreeNeo Test GUI", 
                 font=('Arial', 18, 'bold')).pack(pady=10)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # テストボタン
        ttk.Button(button_frame, text="設定テスト", 
                  command=self.test_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="メッセージボックステスト", 
                  command=self.test_messagebox).pack(side='left', padx=5)
        ttk.Button(button_frame, text="終了", 
                  command=self.root.quit).pack(side='left', padx=5)
        
        # ステータス表示
        self.status_var = tk.StringVar(value="テスト用GUIが正常に動作しています")
        ttk.Label(main_frame, textvariable=self.status_var).pack(pady=20)
        
        # テキストエリア
        text_frame = ttk.LabelFrame(main_frame, text="ログ")
        text_frame.pack(fill='both', expand=True, pady=10)
        
        self.text_area = tk.Text(text_frame, height=15)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        self.text_area.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 初期メッセージ
        self.log_message("テスト用GUI起動完了")
        self.log_message("設定テストボタンで簡易設定画面を開けます")
    
    def log_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.text_area.insert(tk.END, log_entry)
        self.text_area.see(tk.END)
    
    def test_settings(self):
        try:
            # 設定ウィンドウテスト
            settings_window = tk.Toplevel(self.root)
            settings_window.title("設定テスト")
            settings_window.geometry("400x300")
            
            # 簡易設定フォーム
            ttk.Label(settings_window, text="テスト設定", font=('Arial', 14, 'bold')).pack(pady=10)
            
            # チャンネル名
            ttk.Label(settings_window, text="Twitchチャンネル名:").pack(anchor='w', padx=20)
            channel_var = tk.StringVar()
            ttk.Entry(settings_window, textvariable=channel_var, width=40).pack(padx=20, pady=5)
            
            # ユーザー名
            ttk.Label(settings_window, text="Bot用ユーザー名:").pack(anchor='w', padx=20)
            user_var = tk.StringVar()
            ttk.Entry(settings_window, textvariable=user_var, width=40).pack(padx=20, pady=5)
            
            # OAuth
            ttk.Label(settings_window, text="OAuthトークン:").pack(anchor='w', padx=20)
            oauth_var = tk.StringVar()
            ttk.Entry(settings_window, textvariable=oauth_var, width=40, show="*").pack(padx=20, pady=5)
            
            # ボタン
            button_frame = ttk.Frame(settings_window)
            button_frame.pack(pady=20)
            
            def save_test():
                self.log_message("設定保存テスト実行")
                self.log_message(f"チャンネル: {channel_var.get()}")
                self.log_message(f"ユーザー: {user_var.get()}")
                self.log_message(f"OAuth: {'設定済み' if oauth_var.get() else '未設定'}")
                settings_window.destroy()
            
            ttk.Button(button_frame, text="保存", command=save_test).pack(side='left', padx=5)
            ttk.Button(button_frame, text="キャンセル", command=settings_window.destroy).pack(side='left', padx=5)
            
            self.log_message("設定テストウィンドウを開きました")
            
        except Exception as e:
            self.log_message(f"設定テストエラー: {e}")
    
    def test_messagebox(self):
        result = messagebox.showinfo("テスト", "メッセージボックスのテストです")
        self.log_message("メッセージボックステスト完了")
    
    def run(self):
        self.log_message("アプリケーション開始")
        self.root.mainloop()

if __name__ == "__main__":
    app = TestGUI()
    app.run()