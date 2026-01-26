#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from ..utils.config_manager import ConfigManager
    from ..core.chat_monitor import ChatMonitor, ChatMessage
    from ..core.youtube_chat_monitor import YouTubeChatMonitor, PYTCHAT_AVAILABLE
    from .settings_dialog import SettingsDialog
except ImportError:
    from twitchTransFreeNeo.utils.config_manager import ConfigManager
    from twitchTransFreeNeo.core.chat_monitor import ChatMonitor, ChatMessage
    from twitchTransFreeNeo.core.youtube_chat_monitor import YouTubeChatMonitor, PYTCHAT_AVAILABLE
    from twitchTransFreeNeo.gui.settings_dialog import SettingsDialog

class MainWindow:
    """Fletベースのメインウィンドウクラス"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.chat_monitor: Optional[ChatMonitor] = None
        self.youtube_monitor: Optional[YouTubeChatMonitor] = None
        self.is_connected = False
        self.page: Optional[ft.Page] = None

        # UI要素の参照
        self.connect_button: Optional[ft.ElevatedButton] = None
        self.platform_indicator: Optional[ft.Container] = None
        self.channel_text: Optional[ft.Text] = None
        self.bot_text: Optional[ft.Text] = None
        self.chat_list: Optional[ft.ListView] = None
        self.search_field: Optional[ft.TextField] = None
        self.lang_filter: Optional[ft.Dropdown] = None
        self.status_text: Optional[ft.Text] = None
        self.status_icon: Optional[ft.Icon] = None
        self.total_messages_text: Optional[ft.Text] = None
        self.translated_messages_text: Optional[ft.Text] = None
        self.log_text: Optional[ft.Text] = None

        # データ
        self.messages: List[ChatMessage] = []
        self.filtered_messages: List[ChatMessage] = []

    def main(self, page: ft.Page):
        """メインエントリーポイント"""
        self.page = page
        self._setup_window()
        self._load_config()
        self._create_ui()

        # 自動接続チェック
        if self.config_manager.get("auto_start", False):
            self.page.run_task(self._auto_connect)

        # UIを更新
        self.page.update()

    def _setup_window(self):
        """ウィンドウ設定"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"

        self.page.title = f"twitchTransFreeNeo v{__version__}"

        # ウィンドウサイズ
        width = self.config_manager.get("window_width", 1200)
        height = self.config_manager.get("window_height", 800)
        self.page.window.width = width
        self.page.window.height = height
        self.page.window.min_width = 1000
        self.page.window.min_height = 600

        # テーマ設定
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 0

        # 終了時の処理
        self.page.on_close = self._on_closing

    def _load_config(self):
        """設定を読み込み"""
        self.config_manager.load_config()

    def _create_ui(self):
        """UI作成"""
        # メインレイアウト
        self.page.add(
            ft.Column([
                self._create_toolbar(),
                ft.Divider(height=1),
                ft.Row([
                    self._create_chat_area(),
                    ft.VerticalDivider(width=1),
                    self._create_info_panel(),
                ], expand=True),
                ft.Divider(height=1),
                self._create_status_bar(),
            ], spacing=0, expand=True)
        )

    def _create_toolbar(self) -> ft.Container:
        """ツールバー作成"""
        config = self.config_manager.get_all()
        channel = config.get("twitch_channel", "")
        bot_user = config.get("trans_username", "")
        platform = config.get("platform", "twitch")

        self.connect_button = ft.ElevatedButton(
            "接続開始",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._toggle_connection,
        )

        # プラットフォームインジケーター
        self.platform_indicator = self._create_platform_indicator(platform)

        self.channel_text = ft.Text(
            channel if channel else "未設定",
            color=ft.Colors.GREEN if channel else ft.Colors.RED,
        )

        self.bot_text = ft.Text(
            bot_user if bot_user else "未設定",
            color=ft.Colors.GREEN if bot_user else ft.Colors.RED,
        )

        return ft.Container(
            content=ft.Row([
                self.platform_indicator,
                self.connect_button,
                ft.ElevatedButton("設定", icon=ft.Icons.SETTINGS, on_click=self._open_settings),
                ft.ElevatedButton("診断", icon=ft.Icons.TROUBLESHOOT, on_click=self._open_diagnostics),
                ft.VerticalDivider(),
                ft.Text("チャンネル:"),
                self.channel_text,
                ft.Text("翻訳bot:"),
                self.bot_text,
                ft.Container(expand=True),  # スペーサー
                ft.ElevatedButton("履歴クリア", icon=ft.Icons.CLEAR_ALL, on_click=self._clear_chat),
                ft.ElevatedButton("ヘルプ", icon=ft.Icons.HELP, on_click=self._show_help),
            ], spacing=10),
            padding=10,
        )

    def _create_platform_indicator(self, platform: str) -> ft.Container:
        """プラットフォームインジケーターを作成"""
        if platform == "youtube":
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SMART_DISPLAY, color=ft.Colors.WHITE, size=16),
                    ft.Text("YouTube", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=ft.Colors.RED_700,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
            )
        elif platform == "both":
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIVE_TV, color=ft.Colors.WHITE, size=14),
                    ft.Text("+", color=ft.Colors.WHITE, size=12),
                    ft.Icon(ft.Icons.SMART_DISPLAY, color=ft.Colors.WHITE, size=14),
                    ft.Text("同時配信", color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
                ], spacing=2),
                bgcolor=ft.Colors.PURPLE_700,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
            )
        else:  # twitch
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIVE_TV, color=ft.Colors.WHITE, size=16),
                    ft.Text("Twitch", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=ft.Colors.PURPLE_500,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
            )

    def _create_chat_area(self) -> ft.Container:
        """チャット表示エリア作成"""
        # 検索とフィルタ
        self.search_field = ft.TextField(
            label="検索",
            width=200,
            on_change=self._apply_filters,
        )

        self.lang_filter = ft.Dropdown(
            label="言語フィルタ",
            width=150,
            options=[
                ft.DropdownOption("all", "すべて"),
                ft.DropdownOption("ja", "日本語"),
                ft.DropdownOption("en", "英語"),
                ft.DropdownOption("ko", "韓国語"),
                ft.DropdownOption("zh", "中国語"),
                ft.DropdownOption("other", "その他"),
            ],
            value="all",
            on_change=self._apply_filters,
        )

        # チャットリスト
        self.chat_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=True,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self.search_field,
                    self.lang_filter,
                ], spacing=10),
                ft.Divider(),
                self.chat_list,
            ], expand=True),
            expand=3,
            padding=10,
        )

    def _create_info_panel(self) -> ft.Container:
        """情報パネル作成"""
        self.total_messages_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)
        self.translated_messages_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)
        self.log_text = ft.Text("", selectable=True)

        return ft.Container(
            content=ft.Column([
                ft.Text("統計情報", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Text("総メッセージ数:"),
                    self.total_messages_text,
                ]),
                ft.Row([
                    ft.Text("翻訳済み:"),
                    self.translated_messages_text,
                ]),
                ft.Divider(),
                ft.Text("ログ", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        self.log_text,
                    ], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=5,
                    padding=10,
                ),
                ft.ElevatedButton("ログクリア", on_click=self._clear_log),
            ], spacing=10, expand=True),
            width=300,
            padding=10,
        )

    def _create_status_bar(self) -> ft.Container:
        """ステータスバー作成"""
        self.status_text = ft.Text("未接続", size=12)

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=12, color=ft.Colors.RED),
                self.status_text,
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.GREY_200,
        )

    async def _auto_connect(self):
        """自動接続"""
        await asyncio.sleep(1)
        if not self.is_connected:
            valid, errors = self.config_manager.is_valid_config()
            if valid:
                await self._connect()
            else:
                self._log_message("自動接続失敗: 設定が不完全です")

    def _toggle_connection(self, e):
        """接続切り替え"""
        self._log_message("接続ボタンが押されました")
        print("DEBUG: _toggle_connection called")
        if self.is_connected:
            self.page.run_task(self._disconnect)
        else:
            self.page.run_task(self._connect)

    async def _connect(self):
        """接続開始"""
        config = self.config_manager.get_all()
        platform = config.get("platform", "twitch")

        # プラットフォームに応じた設定確認
        valid, errors = self._validate_config_for_platform(platform)
        if not valid:
            await self._show_error_dialog("設定エラー", "\n".join(errors))
            return

        try:
            twitch_success = True
            youtube_success = True
            status_parts = []

            # Twitch接続（twitch または both の場合）
            if platform in ["twitch", "both"]:
                self.chat_monitor = ChatMonitor(config, self._on_message_received)
                success, error_msg = await self.chat_monitor.start()
                if success:
                    channel = config.get("twitch_channel", "")
                    status_parts.append(f"Twitch: {channel}")
                    self._log_message(f"Twitchチャンネル '{channel}' に接続しました")
                else:
                    twitch_success = False
                    self._log_message(f"Twitch接続エラー: {error_msg}")
                    if platform == "twitch":
                        await self._show_error_dialog("接続エラー", error_msg or "Twitchへの接続に失敗しました")
                        return

            # YouTube接続（youtube または both の場合）
            if platform in ["youtube", "both"]:
                if not PYTCHAT_AVAILABLE:
                    youtube_success = False
                    self._log_message("YouTube接続エラー: pytchatが利用できません")
                    if platform == "youtube":
                        await self._show_error_dialog("接続エラー", "pytchatライブラリが利用できません")
                        return
                else:
                    self.youtube_monitor = YouTubeChatMonitor(config, self._on_message_received)
                    if self.youtube_monitor.start():
                        video_id = config.get("youtube_video_id", "")
                        status_parts.append(f"YouTube: {video_id}")
                        self._log_message(f"YouTube Live '{video_id}' に接続しました")
                    else:
                        youtube_success = False
                        self._log_message("YouTube接続エラー: 接続に失敗しました")
                        if platform == "youtube":
                            await self._show_error_dialog("接続エラー", "YouTube Liveへの接続に失敗しました")
                            return

            # 少なくとも1つ成功していれば接続状態とする
            if twitch_success or youtube_success:
                self.is_connected = True
                self.connect_button.text = "接続停止"
                self.connect_button.icon = ft.Icons.STOP
                self.status_text.value = f"接続中: {', '.join(status_parts)}"
                self.status_text.color = ft.Colors.GREEN
                self.page.update()
            else:
                await self._show_error_dialog("接続エラー", "すべてのプラットフォームへの接続に失敗しました")

        except Exception as e:
            await self._show_error_dialog("接続エラー", f"接続中にエラーが発生しました: {e}")

    def _validate_config_for_platform(self, platform: str) -> tuple:
        """プラットフォームに応じた設定確認"""
        errors = []
        config = self.config_manager.get_all()

        if platform in ["twitch", "both"]:
            if not config.get("twitch_channel"):
                errors.append("Twitchチャンネル名が設定されていません")
            if not config.get("trans_oauth") and not config.get("view_only_mode", False):
                errors.append("OAuthトークンが設定されていません（表示のみモードでない場合）")

        if platform in ["youtube", "both"]:
            if not config.get("youtube_video_id"):
                errors.append("YouTube動画IDが設定されていません")

        return (len(errors) == 0, errors)

    async def _disconnect(self):
        """接続停止"""
        try:
            # Twitchモニターを停止
            if self.chat_monitor:
                self.chat_monitor.stop()
                self.chat_monitor = None

            # YouTubeモニターを停止
            if self.youtube_monitor:
                self.youtube_monitor.stop()
                self.youtube_monitor = None

            self.is_connected = False
            self.connect_button.text = "接続開始"
            self.connect_button.icon = ft.Icons.PLAY_ARROW
            self.status_text.value = "未接続"
            self.status_text.color = ft.Colors.RED
            self._log_message("接続を停止しました")
            self.page.update()

        except Exception as e:
            self._log_message(f"切断エラー: {e}")

    def _on_message_received(self, message: ChatMessage):
        """メッセージ受信時のコールバック"""
        self.messages.append(message)

        # 最大メッセージ数を超えたら古いものを削除
        if len(self.messages) > 1000:
            self.messages.pop(0)

        # フィルタ適用
        self._apply_filters(None)

        # 統計更新
        self._update_message_stats()

    def _apply_filters(self, e):
        """フィルタ適用"""
        search_text = self.search_field.value.lower() if self.search_field.value else ""
        lang_filter = self.lang_filter.value if self.lang_filter.value else "all"

        # フィルタリング
        self.filtered_messages = []
        for msg in self.messages:
            # 言語フィルタ
            if lang_filter != "all":
                if lang_filter == "other":
                    if msg.lang in ["ja", "en", "ko", "zh"]:
                        continue
                elif msg.lang != lang_filter:
                    continue

            # 検索フィルタ
            if search_text:
                if search_text not in msg.user.lower() and \
                   search_text not in msg.text.lower() and \
                   (not msg.translation or search_text not in msg.translation.lower()):
                    continue

            self.filtered_messages.append(msg)

        # 表示更新
        self._update_chat_display()

    def _update_chat_display(self):
        """チャット表示更新"""
        self.chat_list.controls.clear()

        for msg in self.filtered_messages[-100:]:  # 最新100件のみ表示
            self.chat_list.controls.append(self._create_message_widget(msg))

        self.page.update()

    def _create_message_widget(self, message: ChatMessage) -> ft.Container:
        """メッセージウィジェット作成"""
        # メッセージカード
        content = ft.Column([
            ft.Row([
                ft.Text(
                    message.timestamp.strftime("%H:%M:%S"),
                    size=10,
                    color=ft.Colors.GREY,
                ),
                ft.Text(
                    f"{message.user}:",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"[{message.lang}]" if message.lang else "",
                    size=10,
                    color=ft.Colors.GREY,
                ),
            ], spacing=5),
            ft.Text(message.text),
        ], spacing=2)

        # 翻訳がある場合
        if message.translation:
            content.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.TRANSLATE, size=16, color=ft.Colors.BLUE),
                    ft.Text(message.translation, color=ft.Colors.BLUE_700),
                ], spacing=5)
            )

        return ft.Container(
            content=content,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )

    def _update_message_stats(self):
        """メッセージ統計更新"""
        total = len(self.messages)
        translated = sum(1 for msg in self.messages if msg.translation)

        self.total_messages_text.value = str(total)
        self.translated_messages_text.value = str(translated)
        self.page.update()

    def _clear_chat(self, e):
        """チャットクリア"""
        self._log_message("履歴クリアボタンが押されました")
        print("DEBUG: _clear_chat called")
        self.messages.clear()
        self.filtered_messages.clear()
        self.chat_list.controls.clear()
        self._update_message_stats()
        self.page.update()

    def _clear_log(self, e):
        """ログクリア"""
        self.log_text.value = ""
        self.page.update()

    def _log_message(self, message: str):
        """ログメッセージ追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.value += log_entry
        self.page.update()

    def _open_settings(self, e):
        """設定画面を開く"""
        self._log_message("設定ボタンが押されました")
        print("DEBUG: _open_settings called")
        try:
            config = self.config_manager.get_all()
            print(f"DEBUG: config loaded: {len(config)} items")
            settings_dialog = SettingsDialog(self.page, config, self._on_config_changed)
            print("DEBUG: SettingsDialog created")
            settings_dialog.show()
            print("DEBUG: SettingsDialog.show() called")
        except Exception as ex:
            print(f"ERROR in _open_settings: {ex}")
            import traceback
            traceback.print_exc()
            self._log_message(f"設定ダイアログエラー: {ex}")

    def _on_config_changed(self, new_config: Dict[str, Any]):
        """設定変更時のコールバック"""
        try:
            # 設定を保存
            self.config_manager.update(new_config)
            self.config_manager.save_config()

            # UIを更新
            self._update_ui_from_config()

            self._log_message("設定が更新されました")

            # 接続中なら一度切断して再接続（新しい設定を反映させるため）
            if self.is_connected:
                self._log_message("設定変更のため、Twitchとの接続を再起動します...")
                self.page.run_task(self._restart_connection)

        except Exception as e:
            self._log_message(f"設定変更エラー: {e}")

    async def _restart_connection(self):
        """接続を再起動"""
        await self._disconnect()
        await asyncio.sleep(0.5)
        await self._connect()

    def _update_ui_from_config(self):
        """設定からUIを更新"""
        config = self.config_manager.get_all()

        channel = config.get("twitch_channel", "")
        bot_user = config.get("trans_username", "")
        platform = config.get("platform", "twitch")

        if self.channel_text:
            self.channel_text.value = channel if channel else "未設定"
            self.channel_text.color = ft.Colors.GREEN if channel else ft.Colors.RED

        if self.bot_text:
            self.bot_text.value = bot_user if bot_user else "未設定"
            self.bot_text.color = ft.Colors.GREEN if bot_user else ft.Colors.RED

        # プラットフォームインジケーターを更新
        if self.platform_indicator and self.platform_indicator.parent:
            parent = self.platform_indicator.parent
            new_indicator = self._create_platform_indicator(platform)
            idx = parent.controls.index(self.platform_indicator)
            parent.controls[idx] = new_indicator
            self.platform_indicator = new_indicator

        self.page.update()

    def _open_diagnostics(self, e):
        """診断画面を開く"""
        self._log_message("診断ボタンが押されました")
        print("DEBUG: _open_diagnostics called")
        try:
            from .diagnostics_dialog import DiagnosticsDialog
            config = self.config_manager.get_all()
            print(f"DEBUG: config loaded: {len(config)} items")
            diag_dialog = DiagnosticsDialog(self.page, config)
            print("DEBUG: DiagnosticsDialog created")
            diag_dialog.show()
            print("DEBUG: DiagnosticsDialog.show() called")
        except Exception as ex:
            print(f"ERROR in _open_diagnostics: {ex}")
            import traceback
            traceback.print_exc()
            self._log_message(f"診断ダイアログエラー: {ex}")

    def _show_help(self, e):
        """ヘルプ表示"""
        self._log_message("ヘルプボタンが押されました")
        print("DEBUG: _show_help called")
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"

        help_text = f"""twitchTransFreeNeo v{__version__}

【基本的な使い方】
1. 「設定」ボタンから必要な設定を行ってください
2. 「接続開始」ボタンでチャンネルに接続します
3. チャットメッセージが自動的に翻訳されて表示されます

【対応プラットフォーム】
- Twitch: チャンネル名とOAuthトークンが必要
- YouTube Live: 動画IDが必要（OAuth認証で投稿も可能）
- 同時配信: TwitchとYouTube両方を監視

【Twitch設定】
- Twitchチャンネル名
- 翻訳bot用ユーザー名
- OAuthトークン

【YouTube Live設定】
- YouTube動画ID（URLでも可）
- Client ID / Client Secret（投稿する場合）

【機能】
- リアルタイム翻訳（60以上の言語対応）
- 翻訳結果のチャット投稿
- フィルタリング・検索機能
- TTS（音声読み上げ）
"""

        def close_help_dialog(e):
            self.page.close(dialog)
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ヘルプ"),
            content=ft.Text(help_text),
            actions=[ft.TextButton("閉じる", on_click=close_help_dialog)],
        )
        self.page.open(dialog)
        self.page.update()

    async def _show_error_dialog(self, title: str, message: str):
        """エラーダイアログ表示"""
        def close_dialog(e):
            self.page.close(dialog)
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=close_dialog)],
        )
        self.page.open(dialog)
        self.page.update()

    def _on_closing(self, e):
        """ウィンドウ終了時"""
        # 接続停止
        if self.is_connected:
            self.page.run_task(self._disconnect)

        # 設定保存
        self.config_manager.save_config()

    def run(self):
        """アプリケーション実行"""
        ft.app(target=self.main)


def main():
    """メイン関数"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
