#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
from typing import Dict, Any, Callable, Optional
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
        self.ignore_line_field: Optional[ft.TextField] = None
        self.delete_words_field: Optional[ft.TextField] = None
        self.ignore_www_field: Optional[ft.TextField] = None

        # TTS設定
        self.tts_enabled_checkbox: Optional[ft.Checkbox] = None
        self.tts_in_checkbox: Optional[ft.Checkbox] = None
        self.tts_out_checkbox: Optional[ft.Checkbox] = None
        self.tts_read_username_input_checkbox: Optional[ft.Checkbox] = None
        self.tts_read_username_output_checkbox: Optional[ft.Checkbox] = None
        self.tts_read_content_checkbox: Optional[ft.Checkbox] = None
        self.tts_read_lang_checkbox: Optional[ft.Checkbox] = None
        self.tts_kind_dropdown: Optional[ft.Dropdown] = None
        self.cevio_cast_field: Optional[ft.TextField] = None
        self.tts_max_length_field: Optional[ft.TextField] = None
        self.tts_omit_message_field: Optional[ft.TextField] = None
        self.read_only_lang_field: Optional[ft.TextField] = None

        # GUI設定
        self.font_size_slider: Optional[ft.Slider] = None
        self.window_width_field: Optional[ft.TextField] = None
        self.window_height_field: Optional[ft.TextField] = None

    def show(self):
        """設定ダイアログを表示"""
        print("DEBUG: SettingsDialog.show() - Creating tabs...")
        try:
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
            print("DEBUG: Tabs created successfully")

            self.dialog = ft.AlertDialog(
                modal=True,
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
            print("DEBUG: AlertDialog created")

            # 推奨される方法: page.open()を使用
            self.page.open(self.dialog)
            print("DEBUG: page.open(dialog) called")
        except Exception as ex:
            print(f"ERROR in SettingsDialog.show(): {ex}")
            import traceback
            traceback.print_exc()

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
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: webbrowser.open("https://www.sayonari.com/trans_asr/ttfn_oauth.html"),
        )

        self.color_dropdown = ft.Dropdown(
            label="翻訳テキストの色",
            value=self.config.get("trans_text_color", "GoldenRod"),
            options=[
                ft.DropdownOption(color) for color in [
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
                ft.DropdownOption(lang, text) for lang, text in [
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
                ft.DropdownOption(lang, text) for lang, text in [
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
                ft.DropdownOption("google", "Google翻訳"),
                ft.DropdownOption("deepl", "DeepL"),
            ],
            width=400,
        )

        self.google_suffix_dropdown = ft.Dropdown(
            label="Google翻訳サーバー",
            value=self.config.get("google_translate_suffix", "co.jp"),
            options=[
                ft.DropdownOption(suffix) for suffix in ['co.jp', 'com', 'co.uk', 'fr', 'de']
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
            width=500,
        )

        self.ignore_user_field = ft.TextField(
            label="無視するユーザー (カンマ区切り)",
            value=','.join(self.config.get("ignore_users", [])),
            multiline=True,
            width=500,
        )

        self.ignore_line_field = ft.TextField(
            label="無視するテキスト (カンマ区切り)",
            value=','.join(self.config.get("ignore_line", [])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=500,
        )

        self.delete_words_field = ft.TextField(
            label="削除する単語 (カンマ区切り)",
            value=','.join(self.config.get("delete_words", [])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=500,
        )

        self.ignore_www_field = ft.TextField(
            label="単芝フィルター (カンマ区切り)",
            value=','.join(self.config.get("ignore_www", ["w", "ｗ", "W", "Ｗ", "ww", "ｗｗ", "WW", "ＷＷ", "www", "ｗｗｗ", "WWW", "ＷＷＷ", "草"])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=500,
            hint_text="w, ww, www, 草 など",
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("フィルター設定", weight=ft.FontWeight.BOLD, size=14),
                self.ignore_lang_field,
                self.ignore_user_field,
                self.ignore_line_field,
                self.delete_words_field,
                self.ignore_www_field,
                ft.Text(
                    "※ 空白のまま保存すると、フィルターは適用されません",
                    size=12,
                    color=ft.Colors.GREY,
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=10,
        )

    def _create_tts_tab(self) -> ft.Container:
        """TTS設定タブ"""
        self.tts_enabled_checkbox = ft.Checkbox(
            label="TTSを有効にする",
            value=self.config.get("tts_enabled", False),
        )

        self.tts_in_checkbox = ft.Checkbox(
            label="入力テキストを読み上げ",
            value=self.config.get("tts_in", False),
        )

        self.tts_out_checkbox = ft.Checkbox(
            label="翻訳テキストを読み上げ",
            value=self.config.get("tts_out", False),
        )

        # 読み上げ内容の詳細設定
        old_username_setting = self.config.get("tts_read_username", True)

        self.tts_read_username_input_checkbox = ft.Checkbox(
            label="ユーザー名（入力言語）を読み上げ",
            value=self.config.get("tts_read_username_input", old_username_setting),
        )

        self.tts_read_username_output_checkbox = ft.Checkbox(
            label="ユーザー名（翻訳言語）を読み上げ",
            value=self.config.get("tts_read_username_output", old_username_setting),
        )

        self.tts_read_content_checkbox = ft.Checkbox(
            label="発言内容を読み上げ",
            value=self.config.get("tts_read_content", True),
        )

        self.tts_read_lang_checkbox = ft.Checkbox(
            label="言語情報を読み上げ",
            value=self.config.get("tts_read_lang", False),
        )

        # TTS詳細設定
        self.tts_kind_dropdown = ft.Dropdown(
            label="TTS種類",
            value=self.config.get("tts_kind", "gTTS"),
            options=[
                ft.DropdownOption("gTTS", "gTTS (Google Text-to-Speech)"),
                ft.DropdownOption("CeVIO", "CeVIO (Windows専用)"),
            ],
            width=400,
        )

        self.cevio_cast_field = ft.TextField(
            label="CeVIOキャスト名",
            value=self.config.get("cevio_cast", "さとうささら"),
            width=400,
        )

        self.tts_max_length_field = ft.TextField(
            label="最大読み上げ文字数 (0で無制限)",
            value=str(self.config.get("tts_text_max_length", 50)),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )

        self.tts_omit_message_field = ft.TextField(
            label="省略時のメッセージ",
            value=self.config.get("tts_message_for_omitting", ""),
            width=400,
        )

        self.read_only_lang_field = ft.TextField(
            label="読み上げ言語制限 (カンマ区切り、空白で全言語)",
            value=','.join(self.config.get("read_only_these_lang", [])),
            multiline=True,
            width=400,
            hint_text="例: ja,en,ko",
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("TTS（音声合成）設定", weight=ft.FontWeight.BOLD, size=14),
                self.tts_enabled_checkbox,
                ft.Divider(),

                ft.Text("TTS設定", weight=ft.FontWeight.BOLD),
                self.tts_in_checkbox,
                self.tts_out_checkbox,
                ft.Divider(),

                ft.Text("読み上げ内容", weight=ft.FontWeight.BOLD),
                self.tts_read_username_input_checkbox,
                self.tts_read_username_output_checkbox,
                self.tts_read_content_checkbox,
                self.tts_read_lang_checkbox,
                ft.Divider(),

                ft.Text("TTS詳細設定", weight=ft.FontWeight.BOLD),
                self.tts_kind_dropdown,
                self.cevio_cast_field,
                self.tts_max_length_field,
                self.tts_omit_message_field,
                ft.Divider(),

                ft.Text("読み上げ言語制限", weight=ft.FontWeight.BOLD),
                self.read_only_lang_field,

                ft.Text(
                    "※ TTS機能はgTTSまたはCeVIO（Windows専用）を使用します",
                    size=12,
                    color=ft.Colors.GREY,
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

        self.window_width_field = ft.TextField(
            label="ウィンドウ幅 (800-1920)",
            value=str(self.config.get("window_width", 1200)),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )

        self.window_height_field = ft.TextField(
            label="ウィンドウ高さ (600-1080)",
            value=str(self.config.get("window_height", 800)),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("外観設定", weight=ft.FontWeight.BOLD, size=14),

                ft.Text("フォント設定", weight=ft.FontWeight.BOLD),
                font_size_text,
                self.font_size_slider,
                ft.Text(
                    "※ フォントサイズの変更は再起動後に完全に反映されます",
                    size=12,
                    color=ft.Colors.GREY,
                ),

                ft.Divider(),

                ft.Text("ウィンドウサイズ", weight=ft.FontWeight.BOLD),
                self.window_width_field,
                self.window_height_field,
                ft.Text(
                    "※ ウィンドウサイズの変更は再起動後に反映されます",
                    size=12,
                    color=ft.Colors.GREY,
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
        updated["ignore_users"] = [user.strip() for user in self.ignore_user_field.value.split(',') if user.strip()]
        updated["ignore_line"] = [line.strip() for line in self.ignore_line_field.value.split(',') if line.strip()]
        updated["delete_words"] = [word.strip() for word in self.delete_words_field.value.split(',') if word.strip()]
        updated["ignore_www"] = [word.strip() for word in self.ignore_www_field.value.split(',') if word.strip()]

        # TTS設定
        updated["tts_enabled"] = self.tts_enabled_checkbox.value
        updated["tts_in"] = self.tts_in_checkbox.value
        updated["tts_out"] = self.tts_out_checkbox.value
        updated["tts_read_username_input"] = self.tts_read_username_input_checkbox.value
        updated["tts_read_username_output"] = self.tts_read_username_output_checkbox.value
        updated["tts_read_content"] = self.tts_read_content_checkbox.value
        updated["tts_read_lang"] = self.tts_read_lang_checkbox.value
        updated["tts_kind"] = self.tts_kind_dropdown.value
        updated["cevio_cast"] = self.cevio_cast_field.value
        updated["tts_text_max_length"] = int(self.tts_max_length_field.value) if self.tts_max_length_field.value.isdigit() else 50
        updated["tts_message_for_omitting"] = self.tts_omit_message_field.value
        updated["read_only_these_lang"] = [lang.strip() for lang in self.read_only_lang_field.value.split(',') if lang.strip()]

        # GUI設定
        updated["font_size"] = int(self.font_size_slider.value)
        updated["window_width"] = int(self.window_width_field.value) if self.window_width_field.value.isdigit() else 1200
        updated["window_height"] = int(self.window_height_field.value) if self.window_height_field.value.isdigit() else 800

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
            self.page.close(self.dialog)
