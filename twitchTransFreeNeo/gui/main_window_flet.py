#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from ..utils.config_manager import ConfigManager
    from ..core.chat_monitor import ChatMonitor, ChatMessage
    from .settings_dialog import SettingsDialog
except ImportError:
    from twitchTransFreeNeo.utils.config_manager import ConfigManager
    from twitchTransFreeNeo.core.chat_monitor import ChatMonitor, ChatMessage
    from twitchTransFreeNeo.gui.settings_dialog import SettingsDialog

class MainWindow:
    """Fletベースのメインウィンドウクラス"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.chat_monitor: Optional[ChatMonitor] = None
        self.is_connected = False
        self.page: Optional[ft.Page] = None

        # UI要素の参照
        self.connect_button: Optional[ft.ElevatedButton] = None
        self.channel_text: Optional[ft.Text] = None
        self.bot_text: Optional[ft.Text] = None
        self.chat_list: Optional[ft.ListView] = None
        self.search_field: Optional[ft.TextField] = None
        self.lang_filter: Optional[ft.Dropdown] = None
        self.status_text: Optional[ft.Text] = None
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
            asyncio.create_task(self._auto_connect())

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

        self.connect_button = ft.ElevatedButton(
            "接続開始",
            icon=ft.icons.PLAY_ARROW,
            on_click=self._toggle_connection,
        )

        self.channel_text = ft.Text(
            channel if channel else "未設定",
            color=ft.colors.GREEN if channel else ft.colors.RED,
        )

        self.bot_text = ft.Text(
            bot_user if bot_user else "未設定",
            color=ft.colors.GREEN if bot_user else ft.colors.RED,
        )

        return ft.Container(
            content=ft.Row([
                self.connect_button,
                ft.ElevatedButton("設定", icon=ft.icons.SETTINGS, on_click=self._open_settings),
                ft.ElevatedButton("診断", icon=ft.icons.TROUBLESHOOT, on_click=self._open_diagnostics),
                ft.VerticalDivider(),
                ft.Text("チャンネル:"),
                self.channel_text,
                ft.Text("翻訳bot:"),
                self.bot_text,
                ft.Container(expand=True),  # スペーサー
                ft.ElevatedButton("履歴クリア", icon=ft.icons.CLEAR_ALL, on_click=self._clear_chat),
                ft.ElevatedButton("ヘルプ", icon=ft.icons.HELP, on_click=self._show_help),
            ], spacing=10),
            padding=10,
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
                ft.dropdown.Option("all", "すべて"),
                ft.dropdown.Option("ja", "日本語"),
                ft.dropdown.Option("en", "英語"),
                ft.dropdown.Option("ko", "韓国語"),
                ft.dropdown.Option("zh", "中国語"),
                ft.dropdown.Option("other", "その他"),
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
                    border=ft.border.all(1, ft.colors.OUTLINE),
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
                ft.Icon(ft.icons.CIRCLE, size=12, color=ft.colors.RED),
                self.status_text,
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.colors.SURFACE_VARIANT,
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
        if self.is_connected:
            asyncio.create_task(self._disconnect())
        else:
            asyncio.create_task(self._connect())

    async def _connect(self):
        """接続開始"""
        # 設定確認
        valid, errors = self.config_manager.is_valid_config()
        if not valid:
            await self._show_error_dialog("設定エラー", "\n".join(errors))
            return

        try:
            # チャット監視開始
            config = self.config_manager.get_all()
            self.chat_monitor = ChatMonitor(config, self._on_message_received)

            success = await self.chat_monitor.start()
            if success:
                self.is_connected = True
                channel = self.config_manager.get("twitch_channel")

                # UI更新
                self.connect_button.text = "接続停止"
                self.connect_button.icon = ft.icons.STOP
                self.status_text.value = f"接続中: {channel}"
                self.status_text.color = ft.colors.GREEN
                self._log_message(f"チャンネル '{channel}' に接続しました")
                self.page.update()
            else:
                await self._show_error_dialog("接続エラー", "Twitchチャンネルへの接続に失敗しました")

        except Exception as e:
            await self._show_error_dialog("接続エラー", f"接続中にエラーが発生しました: {e}")

    async def _disconnect(self):
        """接続停止"""
        try:
            if self.chat_monitor:
                self.chat_monitor.stop()

            self.is_connected = False
            self.connect_button.text = "接続開始"
            self.connect_button.icon = ft.icons.PLAY_ARROW
            self.status_text.value = "未接続"
            self.status_text.color = ft.colors.RED
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
                    color=ft.colors.GREY,
                ),
                ft.Text(
                    f"{message.user}:",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"[{message.lang}]" if message.lang else "",
                    size=10,
                    color=ft.colors.GREY,
                ),
            ], spacing=5),
            ft.Text(message.text),
        ], spacing=2)

        # 翻訳がある場合
        if message.translation:
            content.controls.append(
                ft.Row([
                    ft.Icon(ft.icons.TRANSLATE, size=16, color=ft.colors.BLUE),
                    ft.Text(message.translation, color=ft.colors.BLUE_700),
                ], spacing=5)
            )

        return ft.Container(
            content=content,
            padding=10,
            border=ft.border.all(1, ft.colors.OUTLINE),
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
        config = self.config_manager.get_all()
        settings_dialog = SettingsDialog(self.page, config, self._on_config_changed)
        settings_dialog.show()

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
                asyncio.create_task(self._restart_connection())

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

        if self.channel_text:
            self.channel_text.value = channel if channel else "未設定"
            self.channel_text.color = ft.colors.GREEN if channel else ft.colors.RED

        if self.bot_text:
            self.bot_text.value = bot_user if bot_user else "未設定"
            self.bot_text.color = ft.colors.GREEN if bot_user else ft.colors.RED

        self.page.update()

    def _open_diagnostics(self, e):
        """診断画面を開く"""
        # TODO: 診断機能を実装
        self._log_message("診断機能は実装中です")

    def _show_help(self, e):
        """ヘルプ表示"""
        try:
            from .. import __version__
        except:
            __version__ = "Unknown"

        help_text = f"""twitchTransFreeNeo v{__version__}

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
"""

        dialog = ft.AlertDialog(
            title=ft.Text("ヘルプ"),
            content=ft.Text(help_text),
            actions=[ft.TextButton("閉じる", on_click=lambda e: self._close_dialog())],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def _show_error_dialog(self, title: str, message: str):
        """エラーダイアログ表示"""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog())],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _close_dialog(self):
        """ダイアログを閉じる"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def _on_closing(self, e):
        """ウィンドウ終了時"""
        # 接続停止
        if self.is_connected:
            asyncio.create_task(self._disconnect())

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
