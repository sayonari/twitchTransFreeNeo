#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

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
        self.lang_stats_column: Optional[ft.Column] = None
        self.connection_time_text: Optional[ft.Text] = None
        self.auto_scroll_switch: Optional[ft.Switch] = None
        self.status_icon: Optional[ft.Icon] = None
        self.twitch_status_icon: Optional[ft.Icon] = None
        self.youtube_status_icon: Optional[ft.Icon] = None

        # データ
        self.messages: List[ChatMessage] = []
        self.filtered_messages: List[ChatMessage] = []

        # 統計データ
        self.lang_stats: Dict[str, int] = {}  # 言語別カウント
        self.connection_start_time: Optional[datetime] = None
        self.auto_scroll_enabled = True
        self._connection_timer_running = False

        # メッセージレート計測用
        self.message_timestamps: List[datetime] = []
        self.message_rate_text: Optional[ft.Text] = None

        # ファイル保存用
        self.file_picker: Optional[ft.FilePicker] = None

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

        # キーボードショートカット設定
        self.page.on_keyboard_event = self._on_keyboard_event

    def _load_config(self):
        """設定を読み込み"""
        self.config_manager.load_config()

    def _create_ui(self):
        """UI作成"""
        # ファイルピッカーを設定
        self.file_picker = ft.FilePicker(on_result=self._on_file_picker_result)
        self.page.overlay.append(self.file_picker)

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
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE,
                    tooltip="テーマ切り替え",
                    on_click=self._toggle_theme,
                ),
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
        self.total_messages_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY)
        self.translated_messages_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.connection_time_text = ft.Text("--:--:--", size=14, color=ft.Colors.GREY_600)
        self.message_rate_text = ft.Text("0/分", size=12, color=ft.Colors.ORANGE)
        self.lang_stats_column = ft.Column([], spacing=2)
        self.log_text = ft.Text("", selectable=True, size=11)

        # 自動スクロール切り替え
        self.auto_scroll_switch = ft.Switch(
            value=True,
            label="自動スクロール",
            on_change=self._toggle_auto_scroll,
        )

        # 統計カード
        stats_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ANALYTICS, size=18, color=ft.Colors.PRIMARY),
                    ft.Text("統計情報", size=14, weight=ft.FontWeight.BOLD),
                ], spacing=5),
                ft.Row([
                    ft.Column([
                        ft.Text("メッセージ", size=11, color=ft.Colors.GREY_600),
                        self.total_messages_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    ft.Column([
                        ft.Text("翻訳済み", size=11, color=ft.Colors.GREY_600),
                        self.translated_messages_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Divider(height=1),
                ft.Row([
                    ft.Column([
                        ft.Text("接続時間", size=11, color=ft.Colors.GREY_600),
                        self.connection_time_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    ft.Column([
                        ft.Text("受信速度", size=11, color=ft.Colors.GREY_600),
                        self.message_rate_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], spacing=8),
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
            border_radius=8,
        )

        # 言語統計カード
        lang_stats_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LANGUAGE, size=18, color=ft.Colors.BLUE),
                    ft.Text("言語別統計", size=14, weight=ft.FontWeight.BOLD),
                ], spacing=5),
                self.lang_stats_column,
            ], spacing=8),
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
            border_radius=8,
        )

        # ログカード
        log_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TERMINAL, size=18, color=ft.Colors.GREY_600),
                    ft.Text("ログ", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=16,
                        tooltip="ログクリア",
                        on_click=self._clear_log,
                    ),
                ], spacing=5),
                ft.Container(
                    content=ft.Column([
                        self.log_text,
                    ], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    padding=8,
                    bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
                ),
            ], spacing=8, expand=True),
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.GREY),
            border_radius=8,
            expand=True,
        )

        # アクションボタン
        action_buttons = ft.Row([
            ft.OutlinedButton(
                "ログ出力",
                icon=ft.Icons.DOWNLOAD,
                on_click=self._export_log,
                tooltip="翻訳ログをファイルに保存",
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                stats_card,
                lang_stats_card,
                self.auto_scroll_switch,
                log_card,
                action_buttons,
            ], spacing=10, expand=True),
            width=320,
            padding=10,
        )

    def _toggle_auto_scroll(self, e):
        """自動スクロール切り替え"""
        self.auto_scroll_enabled = self.auto_scroll_switch.value
        if self.chat_list:
            self.chat_list.auto_scroll = self.auto_scroll_enabled
        self._log_message(f"自動スクロール: {'オン' if self.auto_scroll_enabled else 'オフ'}")

    def _create_status_bar(self) -> ft.Container:
        """ステータスバー作成"""
        self.status_icon = ft.Icon(ft.Icons.CIRCLE, size=12, color=ft.Colors.RED)
        self.status_text = ft.Text("未接続", size=12)
        self.twitch_status_icon = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LIVE_TV, size=14, color=ft.Colors.GREY_500),
                ft.Text("Twitch", size=10, color=ft.Colors.GREY_500),
            ], spacing=2),
            visible=False,
        )
        self.youtube_status_icon = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SMART_DISPLAY, size=14, color=ft.Colors.GREY_500),
                ft.Text("YouTube", size=10, color=ft.Colors.GREY_500),
            ], spacing=2),
            visible=False,
        )

        return ft.Container(
            content=ft.Row([
                self.status_icon,
                self.status_text,
                ft.Container(width=20),
                self.twitch_status_icon,
                self.youtube_status_icon,
                ft.Container(expand=True),
                ft.Text("Ctrl+R: 接続 | Ctrl+,: 設定 | Ctrl+E: 出力 | F1: ヘルプ", size=10, color=ft.Colors.GREY_500),
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
            await self._show_error_dialog(
                "設定エラー",
                "\n".join(errors),
                hint="「設定を開く」ボタンから必要な設定を入力してください。"
            )
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
                        hint = self._get_twitch_error_hint(error_msg)
                        await self._show_error_dialog("Twitch接続エラー", error_msg or "Twitchへの接続に失敗しました", hint=hint)
                        return

            # YouTube接続（youtube または both の場合）
            if platform in ["youtube", "both"]:
                if not PYTCHAT_AVAILABLE:
                    youtube_success = False
                    self._log_message("YouTube接続エラー: pytchatが利用できません")
                    if platform == "youtube":
                        await self._show_error_dialog(
                            "YouTube接続エラー",
                            "pytchatライブラリが利用できません",
                            hint="アプリケーションの再インストールをお試しください。"
                        )
                        return
                else:
                    self.youtube_monitor = YouTubeChatMonitor(config, self._on_message_received)
                    if self.youtube_monitor.start():
                        video_id = config.get("youtube_video_id", "")
                        mode = "投稿可能" if self.youtube_monitor.can_post else "読み取り専用"
                        status_parts.append(f"YouTube: {video_id} ({mode})")
                        self._log_message(f"YouTube Live '{video_id}' に接続しました ({mode})")
                    else:
                        youtube_success = False
                        self._log_message("YouTube接続エラー: 接続に失敗しました")
                        if platform == "youtube":
                            await self._show_error_dialog(
                                "YouTube接続エラー",
                                "YouTube Liveへの接続に失敗しました",
                                hint="動画IDが正しいか、配信がライブ中か確認してください。\n動画IDは11文字の英数字です（例: dQw4w9WgXcQ）"
                            )
                            return

            # 少なくとも1つ成功していれば接続状態とする
            if twitch_success or youtube_success:
                self.is_connected = True
                self.connect_button.text = "接続停止"
                self.connect_button.icon = ft.Icons.STOP
                self.status_text.value = f"接続中: {', '.join(status_parts)}"
                self.status_text.color = ft.Colors.GREEN
                self.status_icon.color = ft.Colors.GREEN

                # 接続時間計測開始
                self.connection_start_time = datetime.now()
                self._start_connection_timer()

                # プラットフォームステータス更新
                if platform in ["twitch", "both"] and twitch_success:
                    self.twitch_status_icon.visible = True
                    self.twitch_status_icon.content.controls[0].color = ft.Colors.PURPLE_500
                    self.twitch_status_icon.content.controls[1].color = ft.Colors.PURPLE_500

                if platform in ["youtube", "both"] and youtube_success:
                    self.youtube_status_icon.visible = True
                    self.youtube_status_icon.content.controls[0].color = ft.Colors.RED_700
                    self.youtube_status_icon.content.controls[1].color = ft.Colors.RED_700

                self.page.update()
            else:
                await self._show_error_dialog(
                    "接続エラー",
                    "すべてのプラットフォームへの接続に失敗しました",
                    hint="ネットワーク接続を確認し、設定を見直してください。"
                )

        except Exception as e:
            error_str = str(e)
            hint = None
            if "network" in error_str.lower() or "connection" in error_str.lower():
                hint = "インターネット接続を確認してください。"
            elif "timeout" in error_str.lower():
                hint = "接続がタイムアウトしました。しばらく待ってから再試行してください。"
            await self._show_error_dialog("接続エラー", f"接続中にエラーが発生しました:\n{e}", hint=hint)

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

    def _get_twitch_error_hint(self, error_msg: str) -> str:
        """Twitchエラーに応じたヒントを返す"""
        if not error_msg:
            return "チャンネル名とOAuthトークンを確認してください。"

        error_lower = error_msg.lower()

        if "oauth" in error_lower or "token" in error_lower or "auth" in error_lower:
            return "OAuthトークンが無効または期限切れの可能性があります。\n「設定」→「OAuthトークンを取得」で新しいトークンを取得してください。"
        elif "channel" in error_lower or "not found" in error_lower:
            return "チャンネル名が正しいか確認してください。\nチャンネル名は大文字小文字を区別しません。"
        elif "network" in error_lower or "connection" in error_lower:
            return "インターネット接続を確認してください。"
        elif "timeout" in error_lower:
            return "接続がタイムアウトしました。Twitchサーバーが混雑している可能性があります。"
        elif "ban" in error_lower or "suspend" in error_lower:
            return "アカウントがBANまたは停止されている可能性があります。"
        else:
            return "チャンネル名とOAuthトークンが正しく設定されているか確認してください。"

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
            self.status_icon.color = ft.Colors.RED

            # 接続時間タイマー停止
            self._connection_timer_running = False
            self.connection_start_time = None
            if self.connection_time_text:
                self.connection_time_text.value = "--:--:--"

            # プラットフォームステータスをリセット
            if self.twitch_status_icon:
                self.twitch_status_icon.visible = False
            if self.youtube_status_icon:
                self.youtube_status_icon.visible = False

            # メッセージレートをリセット
            self.message_timestamps.clear()
            if self.message_rate_text:
                self.message_rate_text.value = "0/分"

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

        # メッセージレート計測用のタイムスタンプを追加
        now = datetime.now()
        self.message_timestamps.append(now)
        # 1分以上前のタイムスタンプを削除
        cutoff = now - timedelta(minutes=1)
        self.message_timestamps = [ts for ts in self.message_timestamps if ts > cutoff]

        # 言語統計を更新
        if message.lang:
            self.lang_stats[message.lang] = self.lang_stats.get(message.lang, 0) + 1

        # フィルタ適用
        self._apply_filters(None)

        # 統計更新
        self._update_message_stats()
        self._update_lang_stats()

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

        def copy_message(e):
            """メッセージをクリップボードにコピー"""
            copy_text = f"{message.user}: {message.text}"
            if message.translation:
                copy_text += f"\n翻訳: {message.translation}"
            self.page.set_clipboard(copy_text)
            self._log_message(f"コピーしました: {message.user}")

        def copy_translation_only(e):
            """翻訳のみコピー"""
            if message.translation:
                self.page.set_clipboard(message.translation)
                self._log_message(f"翻訳をコピーしました")

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
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    icon_size=14,
                    tooltip="メッセージをコピー",
                    on_click=copy_message,
                ),
            ], spacing=5),
            ft.Text(message.text, selectable=True),
        ], spacing=2)

        # 翻訳がある場合
        if message.translation:
            content.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.TRANSLATE, size=16, color=ft.Colors.BLUE),
                    ft.Text(message.translation, color=ft.Colors.BLUE_700, selectable=True, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.COPY_ALL,
                        icon_size=14,
                        tooltip="翻訳をコピー",
                        on_click=copy_translation_only,
                    ),
                ], spacing=5)
            )

        return ft.Container(
            content=content,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            on_hover=lambda e: self._on_message_hover(e),
        )

    def _on_message_hover(self, e):
        """メッセージホバー時のハイライト"""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY)
        else:
            e.control.bgcolor = None
        e.control.update()

    def _update_message_stats(self):
        """メッセージ統計更新"""
        total = len(self.messages)
        translated = sum(1 for msg in self.messages if msg.translation)

        self.total_messages_text.value = str(total)
        self.translated_messages_text.value = str(translated)

        # メッセージレート更新（1分あたりのメッセージ数）
        message_rate = len(self.message_timestamps)
        if self.message_rate_text:
            self.message_rate_text.value = f"{message_rate}/分"

        self.page.update()

    def _update_lang_stats(self):
        """言語統計を更新"""
        if not self.lang_stats_column:
            return

        # 上位5言語を表示
        sorted_langs = sorted(self.lang_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        total = sum(self.lang_stats.values())

        self.lang_stats_column.controls.clear()

        if not sorted_langs:
            self.lang_stats_column.controls.append(
                ft.Text("データなし", size=12, color=ft.Colors.GREY_500)
            )
        else:
            for lang, count in sorted_langs:
                percentage = (count / total * 100) if total > 0 else 0
                self.lang_stats_column.controls.append(
                    ft.Row([
                        ft.Text(lang.upper(), size=11, weight=ft.FontWeight.BOLD, width=35),
                        ft.ProgressBar(
                            value=percentage / 100,
                            width=100,
                            color=ft.Colors.BLUE_400,
                            bgcolor=ft.Colors.GREY_300,
                        ),
                        ft.Text(f"{count} ({percentage:.1f}%)", size=10, color=ft.Colors.GREY_600),
                    ], spacing=5)
                )

        self.page.update()

    def _start_connection_timer(self):
        """接続時間タイマーを開始"""
        if self._connection_timer_running:
            return

        self._connection_timer_running = True
        self.page.run_task(self._update_connection_time)

    async def _update_connection_time(self):
        """接続時間を定期的に更新"""
        while self._connection_timer_running and self.connection_start_time:
            try:
                elapsed = datetime.now() - self.connection_start_time
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                if self.connection_time_text:
                    self.connection_time_text.value = time_str
                    self.page.update()

                await asyncio.sleep(1)
            except Exception:
                break

    def _export_log(self, e):
        """翻訳ログをファイルに出力"""
        if not self.messages:
            self._log_message("エクスポートするメッセージがありません")
            return

        # ファイル保存ダイアログを開く
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"translation_log_{timestamp}.txt"

        self.file_picker.save_file(
            dialog_title="翻訳ログの保存",
            file_name=default_filename,
            allowed_extensions=["txt", "csv"],
        )

    def _on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """ファイルピッカー結果コールバック"""
        if not e.path:
            return

        try:
            file_path = e.path

            # 拡張子に応じて出力形式を変更
            if file_path.endswith(".csv"):
                self._export_as_csv(file_path)
            else:
                self._export_as_txt(file_path)

            self._log_message(f"ログを保存しました: {os.path.basename(file_path)}")

        except Exception as ex:
            self._log_message(f"ログ保存エラー: {ex}")

    def _export_as_txt(self, file_path: str):
        """テキスト形式でエクスポート"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("twitchTransFreeNeo 翻訳ログ\n")
            f.write(f"出力日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"メッセージ数: {len(self.messages)}\n")
            f.write("=" * 60 + "\n\n")

            for msg in self.messages:
                f.write(f"[{msg.timestamp.strftime('%H:%M:%S')}] {msg.user} ({msg.lang})\n")
                f.write(f"  原文: {msg.text}\n")
                if msg.translation:
                    f.write(f"  翻訳: {msg.translation}\n")
                f.write("\n")

    def _export_as_csv(self, file_path: str):
        """CSV形式でエクスポート"""
        import csv

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["時刻", "ユーザー", "言語", "原文", "翻訳"])

            for msg in self.messages:
                writer.writerow([
                    msg.timestamp.strftime("%H:%M:%S"),
                    msg.user,
                    msg.lang or "",
                    msg.text,
                    msg.translation or "",
                ])

    def _clear_chat(self, e):
        """チャットクリア"""
        self._log_message("履歴クリアボタンが押されました")
        print("DEBUG: _clear_chat called")
        self.messages.clear()
        self.filtered_messages.clear()
        self.chat_list.controls.clear()
        self.lang_stats.clear()  # 言語統計もクリア
        self.message_timestamps.clear()  # メッセージレートもクリア
        self._update_message_stats()
        self._update_lang_stats()
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

【キーボードショートカット】
- Ctrl+R: 接続/切断
- Ctrl+,: 設定を開く
- Ctrl+E: ログをエクスポート
- Ctrl+L: ログをクリア
- Ctrl+D: 診断を開く
- Ctrl+T: テーマ切り替え
- Ctrl+Delete: チャット履歴をクリア
- F1: ヘルプを表示

【機能】
- リアルタイム翻訳（60以上の言語対応）
- 翻訳結果のチャット投稿
- フィルタリング・検索機能
- TTS（音声読み上げ）
- メッセージコピー機能
- 言語別統計表示
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

    async def _show_error_dialog(self, title: str, message: str, hint: str = None):
        """エラーダイアログ表示（ヒント付き）"""
        def close_dialog(e):
            self.page.close(dialog)
            self.page.update()

        def open_settings(e):
            self.page.close(dialog)
            self.page.update()
            self._open_settings(None)

        content_controls = [
            ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=40),
                ft.Text(message, expand=True),
            ], spacing=15),
        ]

        if hint:
            content_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=ft.Colors.AMBER, size=20),
                        ft.Text(hint, color=ft.Colors.GREY_700, size=13, expand=True),
                    ], spacing=8),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
                    padding=10,
                    border_radius=5,
                    margin=ft.margin.only(top=15),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED),
                ft.Text(title, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                content=ft.Column(content_controls, spacing=0),
                width=450,
            ),
            actions=[
                ft.TextButton("設定を開く", on_click=open_settings),
                ft.ElevatedButton("OK", on_click=close_dialog),
            ],
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

    def _toggle_theme(self, e):
        """テーマ（ダーク/ライト）を切り替え"""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self._log_message("ダークモードに切り替えました")
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self._log_message("ライトモードに切り替えました")
        self.page.update()

    def _on_keyboard_event(self, e: ft.KeyboardEvent):
        """キーボードショートカット処理"""
        # Ctrlキーが押されている場合
        if e.ctrl:
            if e.key == "Q" or e.key == "q":
                # Ctrl+Q: 終了
                self.page.window.close()
            elif e.key == "," or e.key == "Comma":
                # Ctrl+,: 設定を開く
                self._open_settings(None)
            elif e.key == "R" or e.key == "r":
                # Ctrl+R: 接続/切断トグル
                self._toggle_connection(None)
            elif e.key == "L" or e.key == "l":
                # Ctrl+L: ログクリア
                self._clear_log(None)
            elif e.key == "D" or e.key == "d":
                # Ctrl+D: 診断を開く
                self._open_diagnostics(None)
            elif e.key == "E" or e.key == "e":
                # Ctrl+E: ログエクスポート
                self._export_log(None)
            elif e.key == "Delete":
                # Ctrl+Delete: チャット履歴クリア
                self._clear_chat(None)
            elif e.key == "T" or e.key == "t":
                # Ctrl+T: テーマ切り替え
                self._toggle_theme(None)

        # F1キー: ヘルプ
        elif e.key == "F1":
            self._show_help(None)

    def run(self):
        """アプリケーション実行"""
        ft.app(target=self.main)


def main():
    """メイン関数"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
