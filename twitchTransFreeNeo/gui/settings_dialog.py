#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
from typing import Dict, Any, Callable
import webbrowser


class SettingsDialog:
    """Fletベースの設定ダイアログ"""

    def __init__(self, page: ft.Page, config: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        self.page = page
        self.config = config.copy()
        self.on_save = on_save

        # UI要素の参照
        self.dialog: Optional[ft.AlertDialog] = None
        self.tabs: Optional[ft.Tabs] = None

        # 基本設定
        self.channel_field: Optional[ft.TextField] = None
        self.username_field: Optional[ft.TextField] = None
        self.oauth_field: Optional[ft.TextField] = None
        self.color_dropdown: Optional[ft.Dropdown] = None
        self.show_name_checkbox: Optional[ft.Checkbox] = None
        self.show_lang_checkbox: Optional[ft.Checkbox] = None
        self.debug_checkbox: Optional[ft.Checkbox] = None
        self.auto_start_checkbox: Optional[ft.Checkbox] = None
        self.view_only_checkbox: Optional[ft.Checkbox] = None

        # 翻訳設定
        self.home_lang_dropdown: Optional[ft.Dropdown] = None
        self.other_lang_dropdown: Optional[ft.Dropdown] = None
        self.translator_dropdown: Optional[ft.Dropdown] = None
        self.google_suffix_dropdown: Optional[ft.Dropdown] = None
        self.deepl_key_field: Optional[ft.TextField] = None

        # フィルタ設定
        self.ignore_lang_field: Optional[ft.TextField] = None
        self.ignore_user_field: Optional[ft.TextField] = None

        # TTS設定
        self.tts_in_checkbox: Optional[ft.Checkbox] = None
        self.tts_out_checkbox: Optional[ft.Checkbox] = None

        # GUI設定
        self.font_size_slider: Optional[ft.Slider] = None

    def show(self):
        """設定ダイアログを表示"""
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(text="基本設定", content=self._create_basic_tab()),
                ft.Tab(text="翻訳設定", content=self._create_translation_tab()),
                ft.Tab(text="フィルタ設定", content=self._create_filter_tab()),
                ft.Tab(text="TTS設定", content=self._create_tts_tab()),
                ft.Tab(text="GUI設定", content=self._create_gui_tab()),
            ],
            expand=1,
        )

        self.dialog = ft.AlertDialog(
            title=ft.Text("設定"),
            content=ft.Container(
                content=self.tabs,
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=self._cancel),
                ft.TextButton("適用", on_click=self._apply),
                ft.TextButton("OK", on_click=self._ok),
            ],
        )

        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def _create_basic_tab(self) -> ft.Container:
        """基本設定タブ"""
        self.channel_field = ft.TextField(
            label="Twitchチャンネル名",
            value=self.config.get("twitch_channel", ""),
            width=400,
        )

        self.username_field = ft.TextField(
            label="翻訳bot用ユーザー名",
            value=self.config.get("trans_username", ""),
            width=400,
        )

        self.oauth_field = ft.TextField(
            label="OAuthトークン",
            value=self.config.get("trans_oauth", ""),
            password=True,
            can_reveal_password=True,
            width=400,
        )

        oauth_button = ft.ElevatedButton(
            "OAuthトークン取得",
            icon=ft.icons.OPEN_IN_NEW,
            on_click=lambda e: webbrowser.open("https://www.sayonari.com/trans_asr/ttfn_oauth.html"),
        )

        self.color_dropdown = ft.Dropdown(
            label="翻訳テキストの色",
            value=self.config.get("trans_text_color", "GoldenRod"),
            options=[
                ft.dropdown.Option(color) for color in [
                    'Blue', 'Coral', 'DodgerBlue', 'SpringGreen', 'YellowGreen', 'Green',
                    'OrangeRed', 'Red', 'GoldenRod', 'HotPink', 'CadetBlue', 'SeaGreen',
                    'Chocolate', 'BlueViolet', 'Firebrick'
                ]
            ],
            width=400,
        )

        self.show_name_checkbox = ft.Checkbox(
            label="ユーザー名を表示",
            value=self.config.get("show_by_name", True),
        )

        self.show_lang_checkbox = ft.Checkbox(
            label="言語情報を表示",
            value=self.config.get("show_by_lang", True),
        )

        self.debug_checkbox = ft.Checkbox(
            label="デバッグモード",
            value=self.config.get("debug", False),
        )

        self.auto_start_checkbox = ft.Checkbox(
            label="起動時に自動接続",
            value=self.config.get("auto_start", False),
        )

        self.view_only_checkbox = ft.Checkbox(
            label="表示のみモード（チャットに投稿しない）",
            value=self.config.get("view_only_mode", False),
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("必須設定", weight=ft.FontWeight.BOLD),
                self.channel_field,
                self.username_field,
                self.oauth_field,
                oauth_button,
                ft.Divider(),
                ft.Text("表示設定", weight=ft.FontWeight.BOLD),
                self.color_dropdown,
                self.show_name_checkbox,
                self.show_lang_checkbox,
                ft.Divider(),
                ft.Text("その他", weight=ft.FontWeight.BOLD),
                self.debug_checkbox,
                self.auto_start_checkbox,
                self.view_only_checkbox,
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _create_translation_tab(self) -> ft.Container:
        """翻訳設定タブ"""
        self.home_lang_dropdown = ft.Dropdown(
            label="ホーム言語",
            value=self.config.get("lang_trans_to_home", "ja"),
            options=[
                ft.dropdown.Option(lang, text) for lang, text in [
                    ('ja', '日本語'), ('en', '英語'), ('ko', '韓国語'),
                    ('zh-CN', '中国語（簡体字）'), ('zh-TW', '中国語（繁体字）'),
                    ('fr', 'フランス語'), ('de', 'ドイツ語'), ('es', 'スペイン語'),
                    ('pt', 'ポルトガル語'), ('it', 'イタリア語'),
                ]
            ],
            width=400,
        )

        self.other_lang_dropdown = ft.Dropdown(
            label="外国語",
            value=self.config.get("lang_home_to_other", "en"),
            options=[
                ft.dropdown.Option(lang, text) for lang, text in [
                    ('en', '英語'), ('ja', '日本語'), ('ko', '韓国語'),
                    ('zh-CN', '中国語（簡体字）'), ('zh-TW', '中国語（繁体字）'),
                    ('fr', 'フランス語'), ('de', 'ドイツ語'), ('es', 'スペイン語'),
                    ('pt', 'ポルトガル語'), ('it', 'イタリア語'),
                ]
            ],
            width=400,
        )

        self.translator_dropdown = ft.Dropdown(
            label="翻訳エンジン",
            value=self.config.get("translator", "google"),
            options=[
                ft.dropdown.Option("google", "Google翻訳"),
                ft.dropdown.Option("deepl", "DeepL"),
            ],
            width=400,
        )

        self.google_suffix_dropdown = ft.Dropdown(
            label="Google翻訳サーバー",
            value=self.config.get("google_translate_suffix", "co.jp"),
            options=[
                ft.dropdown.Option(suffix) for suffix in ['co.jp', 'com', 'co.uk', 'fr', 'de']
            ],
            width=400,
        )

        self.deepl_key_field = ft.TextField(
            label="DeepL APIキー (オプション)",
            value=self.config.get("deepl_api_key", ""),
            password=True,
            can_reveal_password=True,
            width=400,
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("言語設定", weight=ft.FontWeight.BOLD),
                self.home_lang_dropdown,
                self.other_lang_dropdown,
                ft.Divider(),
                ft.Text("翻訳エンジン設定", weight=ft.FontWeight.BOLD),
                self.translator_dropdown,
                self.google_suffix_dropdown,
                self.deepl_key_field,
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _create_filter_tab(self) -> ft.Container:
        """フィルタ設定タブ"""
        self.ignore_lang_field = ft.TextField(
            label="無視する言語 (カンマ区切り)",
            value=','.join(self.config.get("ignore_lang", [])),
            multiline=True,
            width=400,
        )

        self.ignore_user_field = ft.TextField(
            label="無視するユーザー (カンマ区切り)",
            value=','.join(self.config.get("ignore_user", [])),
            multiline=True,
            width=400,
        )

        return ft.Container(
            content=ft.Column([
                self.ignore_lang_field,
                self.ignore_user_field,
                ft.Text(
                    "※ 空白のまま保存すると、すべての言語・ユーザーを対象とします",
                    size=12,
                    color=ft.colors.GREY,
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _create_tts_tab(self) -> ft.Container:
        """TTS設定タブ"""
        self.tts_in_checkbox = ft.Checkbox(
            label="入力メッセージの読み上げを有効にする",
            value=self.config.get("tts_in", False),
        )

        self.tts_out_checkbox = ft.Checkbox(
            label="翻訳メッセージの読み上げを有効にする",
            value=self.config.get("tts_out", False),
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("TTS（音声合成）設定", weight=ft.FontWeight.BOLD),
                self.tts_in_checkbox,
                self.tts_out_checkbox,
                ft.Text(
                    "※ TTS機能はpygameライブラリを使用します",
                    size=12,
                    color=ft.colors.GREY,
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _create_gui_tab(self) -> ft.Container:
        """GUI設定タブ"""
        current_font_size = self.config.get("font_size", 12)

        font_size_text = ft.Text(f"フォントサイズ: {current_font_size}", size=14)

        self.font_size_slider = ft.Slider(
            min=10,
            max=24,
            divisions=14,
            value=current_font_size,
            label="{value}",
            on_change=lambda e: setattr(font_size_text, 'value', f"フォントサイズ: {int(e.control.value)}") or self.page.update(),
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("フォント設定", weight=ft.FontWeight.BOLD),
                font_size_text,
                self.font_size_slider,
                ft.Text(
                    "※ フォントサイズの変更は再起動後に完全に反映されます",
                    size=12,
                    color=ft.colors.GREY,
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _get_updated_config(self) -> Dict[str, Any]:
        """更新された設定を取得"""
        updated = self.config.copy()

        # 基本設定
        updated["twitch_channel"] = self.channel_field.value
        updated["trans_username"] = self.username_field.value
        updated["trans_oauth"] = self.oauth_field.value
        updated["trans_text_color"] = self.color_dropdown.value
        updated["show_by_name"] = self.show_name_checkbox.value
        updated["show_by_lang"] = self.show_lang_checkbox.value
        updated["debug"] = self.debug_checkbox.value
        updated["auto_start"] = self.auto_start_checkbox.value
        updated["view_only_mode"] = self.view_only_checkbox.value

        # 翻訳設定
        updated["lang_trans_to_home"] = self.home_lang_dropdown.value
        updated["lang_home_to_other"] = self.other_lang_dropdown.value
        updated["translator"] = self.translator_dropdown.value
        updated["google_translate_suffix"] = self.google_suffix_dropdown.value
        updated["deepl_api_key"] = self.deepl_key_field.value

        # フィルタ設定
        updated["ignore_lang"] = [lang.strip() for lang in self.ignore_lang_field.value.split(',') if lang.strip()]
        updated["ignore_user"] = [user.strip() for user in self.ignore_user_field.value.split(',') if user.strip()]

        # TTS設定
        updated["tts_in"] = self.tts_in_checkbox.value
        updated["tts_out"] = self.tts_out_checkbox.value

        # GUI設定
        updated["font_size"] = int(self.font_size_slider.value)

        return updated

    def _apply(self, e):
        """適用ボタン"""
        updated_config = self._get_updated_config()
        self.on_save(updated_config)

    def _ok(self, e):
        """OKボタン"""
        updated_config = self._get_updated_config()
        self.on_save(updated_config)
        self._close()

    def _cancel(self, e):
        """キャンセルボタン"""
        self._close()

    def _close(self):
        """ダイアログを閉じる"""
        if self.dialog:
            self.dialog.open = False
            self.page.update()
