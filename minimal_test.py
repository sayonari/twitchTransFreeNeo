#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最低限のGUIテスト
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

def main():
    print("最低限GUIテスト開始")
    
    # ルートウィンドウ作成
    root = tk.Tk()
    root.title("Minimal Test")
    root.geometry("600x400")
    
    print("ルートウィンドウ作成完了")
    
    # メインフレーム
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    print("メインフレーム作成完了")
    
    # タイトル
    title = ttk.Label(main_frame, text="twitchTransFreeNeo 最低限テスト", 
                     font=('Arial', 16, 'bold'))
    title.pack(pady=10)
    
    print("タイトル作成完了")
    
    # ボタンフレーム
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    # ボタン
    def on_click():
        print("ボタンがクリックされました")
        result_label.config(text="ボタンが正常に動作しています！")
    
    test_button = ttk.Button(button_frame, text="テストボタン", command=on_click)
    test_button.pack(side='left', padx=5)
    
    quit_button = ttk.Button(button_frame, text="終了", command=root.quit)
    quit_button.pack(side='left', padx=5)
    
    print("ボタン作成完了")
    
    # 結果表示ラベル
    result_label = ttk.Label(main_frame, text="ボタンをクリックしてテストしてください")
    result_label.pack(pady=20)
    
    print("結果ラベル作成完了")
    
    # 情報表示
    info_text = f"""Python: {sys.version}
Tkinter: 利用可能
OS: {os.name}
"""
    
    info_label = ttk.Label(main_frame, text=info_text, justify='left')
    info_label.pack(pady=10)
    
    print("情報ラベル作成完了")
    
    # 強制的に前面表示
    root.lift()
    root.attributes('-topmost', True)
    root.after(2000, lambda: root.attributes('-topmost', False))
    
    print("mainloop開始")
    root.mainloop()
    print("mainloop終了")

if __name__ == "__main__":
    main()