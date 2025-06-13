#!/usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import sys
import os
import json
import asyncio
import socket
import threading
from datetime import datetime
from typing import Dict, Any, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# オプショナルな依存関係
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("警告: aiohttpが利用できません。ネットワークテスト機能は制限されます。")

class DiagnosticsTool:
    """診断ツールクラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {}
        
    async def run_all_diagnostics(self) -> Dict[str, Any]:
        """全ての診断を実行"""
        self.results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self._get_system_info(),
            "config_check": self._check_config(),
            "network_check": await self._check_network(),
            "twitch_check": await self._check_twitch_connection(),
            "translator_check": await self._check_translator(),
            "summary": {}
        }
        
        # サマリー作成
        self._create_summary()
        
        return self.results
    
    def _get_system_info(self) -> Dict[str, str]:
        """システム情報を取得"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"
            
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version,
            "app_version": __version__,
            "platform": platform.platform(),
            "machine": platform.machine()
        }
    
    def _check_config(self) -> Dict[str, Any]:
        """設定チェック"""
        required_fields = ["twitch_channel", "trans_username", "trans_oauth"]
        missing = []
        
        for field in required_fields:
            if not self.config.get(field):
                missing.append(field)
        
        result = {
            "complete": len(missing) == 0,
            "missing_fields": missing
        }
        
        # OAuthトークンの形式チェック
        oauth = self.config.get("trans_oauth", "")
        if oauth and not oauth.startswith("oauth:"):
            result["oauth_format_error"] = "OAuthトークンは 'oauth:' で始まる必要があります"
        
        return result
    
    async def _check_network(self) -> Dict[str, Any]:
        """ネットワーク接続チェック"""
        results = {}
        
        # インターネット接続確認
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            results["internet"] = {"status": "OK", "message": "インターネット接続: 正常"}
        except:
            results["internet"] = {"status": "ERROR", "message": "インターネット接続: 失敗"}
        
        # DNS解決確認
        try:
            socket.gethostbyname("www.twitch.tv")
            results["dns"] = {"status": "OK", "message": "DNS解決: 正常"}
        except:
            results["dns"] = {"status": "ERROR", "message": "DNS解決: 失敗"}
        
        return results
    
    async def _check_twitch_connection(self) -> Dict[str, Any]:
        """Twitch接続チェック"""
        if not self.config.get("twitch_channel"):
            return {"status": "SKIP", "message": "チャンネル名が設定されていません"}
        
        if not AIOHTTP_AVAILABLE:
            return {"status": "WARNING", "message": "aiohttpが利用できないため、Twitch接続テストをスキップしました"}
        
        try:
            # Twitch APIエンドポイントへの接続テスト
            async with aiohttp.ClientSession() as session:
                url = f"https://api.twitch.tv/helix/users?login={self.config['twitch_channel']}"
                headers = {
                    "Client-ID": "gp762nuuoqcoxypju8c569th9wz7q5",  # 公開クライアントID
                }
                
                async with session.get(url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        return {"status": "OK", "message": "Twitch API接続: 正常"}
                    else:
                        return {"status": "ERROR", "message": f"Twitch API接続: エラー (Status: {response.status})"}
        except asyncio.TimeoutError:
            return {"status": "ERROR", "message": "Twitch API接続: タイムアウト"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Twitch API接続: エラー ({str(e)})"}
    
    async def _check_translator(self) -> Dict[str, Any]:
        """翻訳エンジン接続チェック"""
        translator = self.config.get("translator", "google")
        
        if translator == "google":
            return await self._check_google_translate()
        elif translator == "deepl":
            return await self._check_deepl()
        else:
            return {"status": "ERROR", "message": "不明な翻訳エンジン"}
    
    async def _check_google_translate(self) -> Dict[str, Any]:
        """Google翻訳接続チェック"""
        if not AIOHTTP_AVAILABLE:
            return {"status": "WARNING", "message": "aiohttpが利用できないため、Google翻訳テストをスキップしました"}
        
        try:
            suffix = self.config.get("google_translate_suffix", "com")
            url = f"https://translate.google.{suffix}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        return {"status": "OK", "message": "Google翻訳接続: 正常"}
                    else:
                        return {"status": "ERROR", "message": f"Google翻訳接続: エラー (Status: {response.status})"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Google翻訳接続: エラー ({str(e)})"}
    
    async def _check_deepl(self) -> Dict[str, Any]:
        """DeepL接続チェック"""
        api_key = self.config.get("deepl_api_key", "")
        
        if not api_key:
            return {"status": "ERROR", "message": "DeepL APIキーが設定されていません"}
        
        if not AIOHTTP_AVAILABLE:
            return {"status": "WARNING", "message": "aiohttpが利用できないため、DeepLテストをスキップしました"}
        
        try:
            url = "https://api-free.deepl.com/v2/usage"
            headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        return {"status": "OK", "message": "DeepL API接続: 正常"}
                    elif response.status == 403:
                        return {"status": "ERROR", "message": "DeepL API接続: 認証エラー (APIキーを確認してください)"}
                    else:
                        return {"status": "ERROR", "message": f"DeepL API接続: エラー (Status: {response.status})"}
        except Exception as e:
            return {"status": "ERROR", "message": f"DeepL API接続: エラー ({str(e)})"}
    
    def _create_summary(self):
        """診断結果のサマリーを作成"""
        issues = []
        warnings = []
        
        # 設定チェック
        if not self.results["config_check"]["complete"]:
            issues.append("必須設定が不足しています: " + ", ".join(self.results["config_check"]["missing_fields"]))
        
        if "oauth_format_error" in self.results["config_check"]:
            issues.append(self.results["config_check"]["oauth_format_error"])
        
        # ネットワークチェック
        for key, value in self.results["network_check"].items():
            if value["status"] == "ERROR":
                issues.append(value["message"])
        
        # Twitchチェック
        if self.results["twitch_check"]["status"] == "ERROR":
            issues.append(self.results["twitch_check"]["message"])
        
        # 翻訳エンジンチェック
        if self.results["translator_check"]["status"] == "ERROR":
            warnings.append(self.results["translator_check"]["message"])
        
        self.results["summary"] = {
            "status": "ERROR" if issues else ("WARNING" if warnings else "OK"),
            "issues": issues,
            "warnings": warnings,
            "message": self._generate_summary_message(issues, warnings)
        }
    
    def _generate_summary_message(self, issues: List[str], warnings: List[str]) -> str:
        """サマリーメッセージを生成"""
        if not issues and not warnings:
            return "すべての診断項目が正常です！"
        
        message = ""
        if issues:
            message += "【エラー】\n" + "\n".join(f"• {issue}" for issue in issues)
        
        if warnings:
            if message:
                message += "\n\n"
            message += "【警告】\n" + "\n".join(f"• {warning}" for warning in warnings)
        
        return message
    
    def collect_logs(self) -> List[str]:
        """最近のログを収集"""
        logs = []
        
        # ログファイルが存在する場合は読み込む
        log_file = "twitchTransFreeNeo.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 最新の100行を取得
                    logs = lines[-100:] if len(lines) > 100 else lines
            except:
                logs = ["ログファイルの読み込みに失敗しました"]
        
        return logs
    
    def generate_report(self) -> str:
        """診断レポートを生成"""
        report = []
        report.append("="*60)
        report.append("twitchTransFreeNeo 診断レポート")
        report.append("="*60)
        report.append(f"実行日時: {self.results['timestamp']}")
        report.append("")
        
        # システム情報
        report.append("[システム情報]")
        for key, value in self.results["system_info"].items():
            if key == "python_version":
                value = value.split()[0]  # バージョン番号のみ
            report.append(f"  {key}: {value}")
        report.append("")
        
        # 設定チェック
        report.append("[設定チェック]")
        config_check = self.results["config_check"]
        if config_check["complete"]:
            report.append("  ✓ 必須設定: すべて入力済み")
        else:
            report.append("  ✗ 必須設定: 未入力項目あり")
            for field in config_check["missing_fields"]:
                report.append(f"    - {field}")
        
        if "oauth_format_error" in config_check:
            report.append(f"  ✗ {config_check['oauth_format_error']}")
        report.append("")
        
        # ネットワークチェック
        report.append("[ネットワークチェック]")
        for key, value in self.results["network_check"].items():
            status = "✓" if value["status"] == "OK" else "✗"
            report.append(f"  {status} {value['message']}")
        report.append("")
        
        # Twitch接続チェック
        report.append("[Twitch接続チェック]")
        twitch = self.results["twitch_check"]
        status = "✓" if twitch["status"] == "OK" else ("○" if twitch["status"] == "SKIP" else "✗")
        report.append(f"  {status} {twitch['message']}")
        report.append("")
        
        # 翻訳エンジンチェック
        report.append("[翻訳エンジンチェック]")
        translator = self.results["translator_check"]
        status = "✓" if translator["status"] == "OK" else "✗"
        report.append(f"  {status} {translator['message']}")
        report.append("")
        
        # サマリー
        report.append("[診断結果サマリー]")
        summary = self.results["summary"]
        report.append(summary["message"])
        report.append("")
        
        # ログ情報（エラーがある場合のみ）
        if summary["status"] != "OK":
            logs = self.collect_logs()
            if logs:
                report.append("[最近のログ（最新100行）]")
                report.append("..." + "."*56)
                for log in logs[-20:]:  # 最新20行のみレポートに含める
                    report.append(log.rstrip())
                report.append("..." + "."*56)
                report.append("")
        
        report.append("="*60)
        
        return "\n".join(report)


class DiagnosticsWindow:
    """診断ウィンドウ"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        self.window = tk.Toplevel(parent)
        self.window.title("システム診断")
        self.window.geometry("700x600")
        self.window.resizable(True, True)
        
        self.config = config
        self.diagnostics_tool = DiagnosticsTool(config)
        
        self._create_widgets()
        
        # ウィンドウを中央に配置
        self.window.transient(parent)
        self.window.grab_set()
        
        # 自動で診断開始
        self.window.after(100, self._run_diagnostics)
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # ヘッダー
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(header_frame, text="システム診断", font=('', 14, 'bold')).pack(side='left')
        
        # プログレスバー
        self.progress = ttk.Progressbar(self.window, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=(0, 10))
        
        # 結果表示エリア
        result_frame = ttk.Frame(self.window)
        result_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10)
        )
        self.result_text.pack(fill='both', expand=True)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="再診断", command=self._run_diagnostics)
        self.run_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="レポートをコピー", command=self._copy_report).pack(side='left', padx=5)
        ttk.Button(button_frame, text="レポートを保存", command=self._save_report).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="閉じる", command=self.window.destroy).pack(side='right', padx=5)
    
    def _run_diagnostics(self):
        """診断を実行"""
        self.run_button.configure(state='disabled')
        self.progress.start(10)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "診断を実行中...\n")
        
        # 非同期で診断実行
        thread = threading.Thread(target=self._run_diagnostics_thread)
        thread.daemon = True
        thread.start()
    
    def _run_diagnostics_thread(self):
        """診断を別スレッドで実行"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(self.diagnostics_tool.run_all_diagnostics())
            report = self.diagnostics_tool.generate_report()
            
            # UIスレッドで結果表示
            self.window.after(0, self._show_results, report)
        except Exception as e:
            error_msg = f"診断中にエラーが発生しました:\n{str(e)}"
            self.window.after(0, self._show_results, error_msg)
        finally:
            loop.close()
    
    def _show_results(self, report: str):
        """診断結果を表示"""
        self.progress.stop()
        self.run_button.configure(state='normal')
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, report)
        
        # エラーがある場合は色を変える
        if "✗" in report:
            self.result_text.tag_add("error", "1.0", tk.END)
            self.result_text.tag_config("error", foreground="red")
    
    def _copy_report(self):
        """レポートをクリップボードにコピー"""
        report = self.result_text.get(1.0, tk.END).strip()
        self.window.clipboard_clear()
        self.window.clipboard_append(report)
        messagebox.showinfo("コピー完了", "診断レポートをクリップボードにコピーしました")
    
    def _save_report(self):
        """レポートをファイルに保存"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            initialfile=f"診断レポート_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.get(1.0, tk.END).strip())
                messagebox.showinfo("保存完了", f"診断レポートを保存しました:\n{filename}")
            except Exception as e:
                messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{str(e)}")