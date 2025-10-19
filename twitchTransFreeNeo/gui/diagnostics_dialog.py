#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
from typing import Dict, Any
import socket
import time
import platform
import sys
from datetime import datetime

# オプショナルな依存関係
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class DiagnosticsDialog:
    """診断ダイアログ"""

    def __init__(self, page: ft.Page, config: Dict[str, Any]):
        self.page = page
        self.config = config
        self.dialog = None
        self.result_text = None
        self.progress_ring = None

        # 診断結果
        self.results = {}

    def show(self):
        """診断ダイアログを表示"""
        # プログレスリング
        self.progress_ring = ft.ProgressRing()

        # 結果表示用テキスト
        self.result_text = ft.Text(
            "診断を実行中...",
            size=12,
            font_family="Courier New",
            selectable=True,
        )

        # ダイアログ作成
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("システム診断", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.progress_ring,
                        ft.Container(
                            content=self.result_text,
                            padding=10,
                            border=ft.border.all(1, ft.Colors.GREY_400),
                            border_radius=5,
                        ),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("再診断", on_click=self._rerun),
                ft.TextButton("レポートをコピー", on_click=self._copy_report),
                ft.TextButton("閉じる", on_click=self._close),
            ],
        )

        # ダイアログを表示
        self.page.open(self.dialog)
        self.page.update()

        # 診断を実行
        self.page.run_task(self._run_diagnostics)

    def _get_system_info(self) -> Dict[str, str]:
        """システム情報を取得"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"

        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
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
        except Exception as ex:
            results["internet"] = {"status": "ERROR", "message": f"インターネット接続: 失敗 ({str(ex)})"}

        # DNS解決確認
        try:
            socket.gethostbyname("www.twitch.tv")
            results["dns"] = {"status": "OK", "message": "DNS解決: 正常"}
        except Exception as ex:
            results["dns"] = {"status": "ERROR", "message": f"DNS解決: 失敗 ({str(ex)})"}

        return results

    async def _check_twitch_connection(self) -> Dict[str, Any]:
        """Twitch接続チェック"""
        if not self.config.get("twitch_channel"):
            return {"status": "SKIP", "message": "チャンネル名が設定されていません"}

        if not AIOHTTP_AVAILABLE:
            # aiohttpがない場合はIRC接続のみテスト
            try:
                socket.create_connection(("irc.chat.twitch.tv", 6667), timeout=3)
                return {"status": "OK", "message": "Twitch IRC接続: 正常"}
            except Exception as ex:
                return {"status": "ERROR", "message": f"Twitch IRC接続: 失敗 ({str(ex)})"}

        try:
            # Twitch IRC接続テスト
            socket.create_connection(("irc.chat.twitch.tv", 6667), timeout=3)
            return {"status": "OK", "message": "Twitch IRC接続: 正常"}
        except Exception as ex:
            return {"status": "ERROR", "message": f"Twitch IRC接続: 失敗 ({str(ex)})"}

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
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
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
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
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
            issues.append(self.results["translator_check"]["message"])
        elif self.results["translator_check"]["status"] == "WARNING":
            warnings.append(self.results["translator_check"]["message"])

        self.results["summary"] = {
            "status": "ERROR" if issues else ("WARNING" if warnings else "OK"),
            "issues": issues,
            "warnings": warnings,
        }

    def _generate_report(self) -> str:
        """診断レポートを生成"""
        report = []
        report.append("=" * 60)
        report.append("twitchTransFreeNeo 診断レポート")
        report.append("=" * 60)
        report.append(f"実行日時: {self.results['timestamp']}")
        report.append("")

        # システム情報
        report.append("[システム情報]")
        for key, value in self.results["system_info"].items():
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
        status = "✓" if translator["status"] == "OK" else ("⚠" if translator["status"] == "WARNING" else "✗")
        report.append(f"  {status} {translator['message']}")
        report.append("")

        # サマリー
        report.append("[診断結果サマリー]")
        summary = self.results["summary"]

        if summary["issues"]:
            report.append("【エラー】")
            for issue in summary["issues"]:
                report.append(f"• {issue}")

        if summary["warnings"]:
            if summary["issues"]:
                report.append("")
            report.append("【警告】")
            for warning in summary["warnings"]:
                report.append(f"• {warning}")

        if not summary["issues"] and not summary["warnings"]:
            report.append("すべての診断項目が正常です！")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    async def _run_diagnostics(self):
        """診断を実行"""
        try:
            # プログレスリングを表示
            self.progress_ring.visible = True
            self.result_text.value = "診断を実行中..."
            self.page.update()

            # 診断実行
            self.results = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_info": self._get_system_info(),
                "config_check": self._check_config(),
                "network_check": await self._check_network(),
                "twitch_check": await self._check_twitch_connection(),
                "translator_check": await self._check_translator(),
            }

            # サマリー作成
            self._create_summary()

            # レポート生成
            report = self._generate_report()

            # 結果表示
            self.progress_ring.visible = False
            self.result_text.value = report
            self.page.update()

        except Exception as ex:
            self.progress_ring.visible = False
            self.result_text.value = f"診断中にエラーが発生しました:\n{str(ex)}"
            self.page.update()

    def _rerun(self, e):
        """再診断を実行"""
        self.page.run_task(self._run_diagnostics)

    def _copy_report(self, e):
        """レポートをクリップボードにコピー"""
        if self.result_text and self.result_text.value:
            self.page.set_clipboard(self.result_text.value)
            # 簡易的な通知（ログに表示）
            print("診断レポートをクリップボードにコピーしました")

    def _close(self, e):
        """ダイアログを閉じる"""
        if self.dialog:
            self.page.close(self.dialog)
