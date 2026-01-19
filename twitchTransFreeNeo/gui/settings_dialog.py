#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
from typing import Dict, Any, Callable, Optional
import webbrowser


class SettingsDialog:
    """Fletベースの設定ダイアログ（改善版）"""

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

    def _create_settings_card(self, title: str, icon: str, content: ft.Control,
                              helper_text: str = None) -> ft.Card:
        """設定グループをカード形式で作成"""
        card_content = [
            ft.Row([
                ft.Icon(icon, size=20, color=ft.Colors.PRIMARY),
                ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
            ], spacing=8),
        ]

        if helper_text:
            card_content.append(
                ft.Text(helper_text, size=11, color=ft.Colors.GREY_600, italic=True)
            )

        card_content.append(ft.Container(content=content, padding=ft.padding.only(top=8)))

        return ft.Card(
            content=ft.Container(
                content=ft.Column(card_content, spacing=4),
                padding=12,
            ),
            elevation=1,
        )

    def _create_scroll_hint(self) -> ft.Container:
        """スクロールヒントを作成"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=14, color=ft.Colors.GREY_500),
                ft.Text("↓ 下にスクロールで続きます", size=11, color=ft.Colors.GREY_500),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.only(top=4, bottom=4),
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
            border_radius=4,
        )

    def show(self):
        """設定ダイアログを表示"""
        print("DEBUG: SettingsDialog.show() - Creating tabs...")
        try:
            self.tabs = ft.Tabs(
                selected_index=0,
                animation_duration=200,
                tabs=[
                    ft.Tab(
                        text="基本設定",
                        icon=ft.Icons.SETTINGS,
                        content=self._create_basic_tab()
                    ),
                    ft.Tab(
                        text="翻訳",
                        icon=ft.Icons.TRANSLATE,
                        content=self._create_translation_tab()
                    ),
                    ft.Tab(
                        text="フィルタ",
                        icon=ft.Icons.FILTER_ALT,
                        content=self._create_filter_tab()
                    ),
                    ft.Tab(
                        text="TTS",
                        icon=ft.Icons.RECORD_VOICE_OVER,
                        content=self._create_tts_tab()
                    ),
                    ft.Tab(
                        text="表示",
                        icon=ft.Icons.DISPLAY_SETTINGS,
                        content=self._create_gui_tab()
                    ),
                ],
                expand=1,
            )
            print("DEBUG: Tabs created successfully")

            self.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.TUNE, color=ft.Colors.PRIMARY),
                    ft.Text("設定", weight=ft.FontWeight.BOLD),
                ], spacing=8),
                content=ft.Container(
                    content=self.tabs,
                    width=720,
                    height=520,
                ),
                actions=[
                    ft.TextButton("キャンセル", on_click=self._cancel),
                    ft.ElevatedButton("適用", on_click=self._apply),
                    ft.ElevatedButton("OK", on_click=self._ok,
                                     style=ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY)),
                ],
            )
            print("DEBUG: AlertDialog created")

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
            hint_text="例: sayonari",
            prefix_icon=ft.Icons.LIVE_TV,
            width=400,
        )

        self.username_field = ft.TextField(
            label="翻訳bot用ユーザー名",
            value=self.config.get("trans_username", ""),
            hint_text="翻訳投稿用のTwitchアカウント名",
            prefix_icon=ft.Icons.PERSON,
            width=400,
        )

        self.oauth_field = ft.TextField(
            label="OAuthトークン",
            value=self.config.get("trans_oauth", ""),
            password=True,
            can_reveal_password=True,
            hint_text="oauth:で始まるトークン",
            prefix_icon=ft.Icons.KEY,
            width=400,
        )

        oauth_button = ft.ElevatedButton(
            "OAuthトークンを取得",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: webbrowser.open("https://www.sayonari.com/trans_asr/ttfn_oauth.html"),
        )

        # 接続設定カード
        connection_card = self._create_settings_card(
            "Twitch接続設定",
            ft.Icons.LINK,
            ft.Column([
                self.channel_field,
                self.username_field,
                self.oauth_field,
                oauth_button,
            ], spacing=8),
            helper_text="チャンネルに接続するために必要な設定です"
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
            width=300,
        )

        self.show_name_checkbox = ft.Checkbox(
            label="ユーザー名を表示",
            value=self.config.get("show_by_name", True),
        )

        self.show_lang_checkbox = ft.Checkbox(
            label="言語情報を表示（例: [ja→en]）",
            value=self.config.get("show_by_lang", True),
        )

        # 表示設定カード
        display_card = self._create_settings_card(
            "チャット表示設定",
            ft.Icons.CHAT_BUBBLE_OUTLINE,
            ft.Column([
                self.color_dropdown,
                self.show_name_checkbox,
                self.show_lang_checkbox,
            ], spacing=4),
            helper_text="翻訳されたチャットの表示形式"
        )

        self.debug_checkbox = ft.Checkbox(
            label="デバッグモード（詳細ログを表示）",
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

        # その他設定カード
        misc_card = self._create_settings_card(
            "その他のオプション",
            ft.Icons.MORE_HORIZ,
            ft.Column([
                self.auto_start_checkbox,
                self.view_only_checkbox,
                self.debug_checkbox,
            ], spacing=4),
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                connection_card,
                display_card,
                misc_card,
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _create_translation_tab(self) -> ft.Container:
        """翻訳設定タブ"""

        # かんたん設定プリセット
        preset_buttons = ft.Row([
            ft.OutlinedButton(
                "日本語配信者",
                icon=ft.Icons.FLAG,
                tooltip="ホーム言語:日本語、外国語:英語",
                on_click=lambda e: self._apply_preset("ja_streamer"),
            ),
            ft.OutlinedButton(
                "English Streamer",
                icon=ft.Icons.FLAG,
                tooltip="Home: English, Other: Japanese",
                on_click=lambda e: self._apply_preset("en_streamer"),
            ),
            ft.OutlinedButton(
                "한국어 스트리머",
                icon=ft.Icons.FLAG,
                tooltip="홈: 한국어, 외국어: 영어",
                on_click=lambda e: self._apply_preset("ko_streamer"),
            ),
        ], wrap=True, spacing=8)

        preset_card = self._create_settings_card(
            "かんたん設定",
            ft.Icons.FLASH_ON,
            preset_buttons,
            helper_text="ワンクリックで言語設定をプリセットに変更"
        )

        self.home_lang_dropdown = ft.Dropdown(
            label="ホーム言語（配信者の言語）",
            value=self.config.get("lang_trans_to_home", "ja"),
            options=[
                ft.DropdownOption(lang, text) for lang, text in [
                    ('ja', '日本語'), ('en', '英語'), ('ko', '韓国語'),
                    ('zh-CN', '中国語（簡体字）'), ('zh-TW', '中国語（繁体字）'),
                    ('fr', 'フランス語'), ('de', 'ドイツ語'), ('es', 'スペイン語'),
                    ('pt', 'ポルトガル語'), ('it', 'イタリア語'), ('ru', 'ロシア語'),
                    ('th', 'タイ語'), ('vi', 'ベトナム語'), ('id', 'インドネシア語'),
                ]
            ],
            width=350,
        )

        self.other_lang_dropdown = ft.Dropdown(
            label="外国語（翻訳先）",
            value=self.config.get("lang_home_to_other", "en"),
            options=[
                ft.DropdownOption(lang, text) for lang, text in [
                    ('en', '英語'), ('ja', '日本語'), ('ko', '韓国語'),
                    ('zh-CN', '中国語（簡体字）'), ('zh-TW', '中国語（繁体字）'),
                    ('fr', 'フランス語'), ('de', 'ドイツ語'), ('es', 'スペイン語'),
                    ('pt', 'ポルトガル語'), ('it', 'イタリア語'), ('ru', 'ロシア語'),
                    ('th', 'タイ語'), ('vi', 'ベトナム語'), ('id', 'インドネシア語'),
                ]
            ],
            width=350,
        )

        lang_card = self._create_settings_card(
            "言語設定",
            ft.Icons.LANGUAGE,
            ft.Column([
                self.home_lang_dropdown,
                self.other_lang_dropdown,
                ft.Text(
                    "ホーム言語のコメント → 外国語に翻訳\n外国語のコメント → ホーム言語に翻訳",
                    size=11, color=ft.Colors.GREY_600,
                ),
            ], spacing=8),
            helper_text="どの言語間で翻訳するかを設定"
        )

        self.translator_dropdown = ft.Dropdown(
            label="翻訳エンジン",
            value=self.config.get("translator", "google"),
            options=[
                ft.DropdownOption("google", "Google翻訳（無料・高速）"),
                ft.DropdownOption("deepl", "DeepL（高品質・APIキー必要）"),
            ],
            width=350,
        )

        self.google_suffix_dropdown = ft.Dropdown(
            label="Google翻訳サーバー",
            value=self.config.get("google_translate_suffix", "co.jp"),
            options=[
                ft.DropdownOption(suffix) for suffix in ['co.jp', 'com', 'co.uk', 'fr', 'de']
            ],
            width=250,
        )

        self.deepl_key_field = ft.TextField(
            label="DeepL APIキー",
            value=self.config.get("deepl_api_key", ""),
            password=True,
            can_reveal_password=True,
            hint_text="DeepLを使う場合のみ必要",
            width=350,
        )

        engine_card = self._create_settings_card(
            "翻訳エンジン設定",
            ft.Icons.TRANSLATE,
            ft.Column([
                self.translator_dropdown,
                self.google_suffix_dropdown,
                self.deepl_key_field,
            ], spacing=8),
            helper_text="通常はGoogle翻訳で十分です"
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                preset_card,
                lang_card,
                engine_card,
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _apply_preset(self, preset_name: str):
        """言語プリセットを適用"""
        presets = {
            "ja_streamer": ("ja", "en"),
            "en_streamer": ("en", "ja"),
            "ko_streamer": ("ko", "en"),
        }
        if preset_name in presets:
            home, other = presets[preset_name]
            self.home_lang_dropdown.value = home
            self.other_lang_dropdown.value = other
            self.page.update()

    def _create_filter_tab(self) -> ft.Container:
        """フィルタ設定タブ"""
        self.ignore_lang_field = ft.TextField(
            label="無視する言語コード",
            value=','.join(self.config.get("ignore_lang", [])),
            hint_text="例: zh-CN,th（翻訳しない言語）",
            width=450,
        )

        self.ignore_user_field = ft.TextField(
            label="無視するユーザー",
            value=','.join(self.config.get("ignore_users", [])),
            hint_text="例: Nightbot,StreamElements",
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=450,
        )

        filter_basic_card = self._create_settings_card(
            "基本フィルター",
            ft.Icons.BLOCK,
            ft.Column([
                self.ignore_lang_field,
                self.ignore_user_field,
            ], spacing=8),
            helper_text="特定の言語やユーザーを翻訳対象外にする"
        )

        self.ignore_line_field = ft.TextField(
            label="無視するテキスト（部分一致）",
            value=','.join(self.config.get("ignore_line", [])),
            hint_text="例: !command,http://",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=450,
        )

        self.delete_words_field = ft.TextField(
            label="削除する単語",
            value=','.join(self.config.get("delete_words", [])),
            hint_text="翻訳前にテキストから削除される",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=450,
        )

        self.ignore_www_field = ft.TextField(
            label="単芝フィルター（笑い表現）",
            value=','.join(self.config.get("ignore_www", ["w", "ｗ", "W", "Ｗ", "ww", "ｗｗ", "WW", "ＷＷ", "www", "ｗｗｗ", "WWW", "ＷＷＷ", "草"])),
            hint_text="翻訳しない短い表現",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=450,
        )

        filter_advanced_card = self._create_settings_card(
            "詳細フィルター",
            ft.Icons.TUNE,
            ft.Column([
                self.ignore_line_field,
                self.delete_words_field,
                self.ignore_www_field,
            ], spacing=8),
            helper_text="翻訳を改善するための細かい設定"
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                filter_basic_card,
                filter_advanced_card,
                ft.Container(
                    content=ft.Text(
                        "💡 ヒント: フィルターはカンマ（,）で区切って複数指定できます",
                        size=12, color=ft.Colors.GREY_600,
                    ),
                    padding=8,
                ),
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _create_tts_tab(self) -> ft.Container:
        """TTS設定タブ"""
        self.tts_enabled_checkbox = ft.Checkbox(
            label="TTSを有効にする（音声読み上げ）",
            value=self.config.get("tts_enabled", False),
        )

        tts_main_card = self._create_settings_card(
            "TTS 有効/無効",
            ft.Icons.VOLUME_UP,
            self.tts_enabled_checkbox,
            helper_text="チャットを音声で読み上げます"
        )

        self.tts_in_checkbox = ft.Checkbox(
            label="元のテキストを読み上げ",
            value=self.config.get("tts_in", False),
        )

        self.tts_out_checkbox = ft.Checkbox(
            label="翻訳後のテキストを読み上げ",
            value=self.config.get("tts_out", False),
        )

        # 読み上げ内容の詳細設定
        old_username_setting = self.config.get("tts_read_username", True)

        self.tts_read_username_input_checkbox = ft.Checkbox(
            label="ユーザー名（元の言語）",
            value=self.config.get("tts_read_username_input", old_username_setting),
        )

        self.tts_read_username_output_checkbox = ft.Checkbox(
            label="ユーザー名（翻訳言語）",
            value=self.config.get("tts_read_username_output", old_username_setting),
        )

        self.tts_read_content_checkbox = ft.Checkbox(
            label="発言内容",
            value=self.config.get("tts_read_content", True),
        )

        self.tts_read_lang_checkbox = ft.Checkbox(
            label="言語情報",
            value=self.config.get("tts_read_lang", False),
        )

        tts_what_card = self._create_settings_card(
            "読み上げ対象",
            ft.Icons.SPEAKER_NOTES,
            ft.Column([
                ft.Row([self.tts_in_checkbox, self.tts_out_checkbox], wrap=True),
                ft.Divider(height=1),
                ft.Text("読み上げ内容:", size=12, weight=ft.FontWeight.W_500),
                ft.Row([
                    self.tts_read_username_input_checkbox,
                    self.tts_read_username_output_checkbox,
                ], wrap=True),
                ft.Row([
                    self.tts_read_content_checkbox,
                    self.tts_read_lang_checkbox,
                ], wrap=True),
            ], spacing=6),
        )

        self.tts_kind_dropdown = ft.Dropdown(
            label="TTS種類",
            value=self.config.get("tts_kind", "gTTS"),
            options=[
                ft.DropdownOption("gTTS", "gTTS（Google TTS・推奨）"),
                ft.DropdownOption("CeVIO", "CeVIO（Windows専用）"),
            ],
            width=300,
        )

        self.cevio_cast_field = ft.TextField(
            label="CeVIOキャスト名",
            value=self.config.get("cevio_cast", "さとうささら"),
            hint_text="CeVIO使用時のみ",
            width=250,
        )

        self.tts_max_length_field = ft.TextField(
            label="最大文字数（0=無制限）",
            value=str(self.config.get("tts_text_max_length", 50)),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )

        self.tts_omit_message_field = ft.TextField(
            label="省略時のメッセージ",
            value=self.config.get("tts_message_for_omitting", ""),
            hint_text="例: 以下省略",
            width=200,
        )

        tts_engine_card = self._create_settings_card(
            "TTS詳細設定",
            ft.Icons.SETTINGS_VOICE,
            ft.Column([
                ft.Row([self.tts_kind_dropdown, self.cevio_cast_field], wrap=True, spacing=12),
                ft.Row([self.tts_max_length_field, self.tts_omit_message_field], wrap=True, spacing=12),
            ], spacing=8),
        )

        self.read_only_lang_field = ft.TextField(
            label="読み上げ言語制限",
            value=','.join(self.config.get("read_only_these_lang", [])),
            hint_text="空白=全言語、例: ja,en",
            width=300,
        )

        tts_lang_card = self._create_settings_card(
            "読み上げ言語制限",
            ft.Icons.LANGUAGE,
            self.read_only_lang_field,
            helper_text="指定した言語のみ読み上げ（空白で全言語）"
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                tts_main_card,
                tts_what_card,
                tts_engine_card,
                tts_lang_card,
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _create_gui_tab(self) -> ft.Container:
        """GUI設定タブ"""
        current_font_size = self.config.get("font_size", 12)

        font_size_text = ft.Text(f"フォントサイズ: {current_font_size}pt", size=14)

        self.font_size_slider = ft.Slider(
            min=10,
            max=24,
            divisions=14,
            value=current_font_size,
            label="{value}pt",
            on_change=lambda e: setattr(font_size_text, 'value', f"フォントサイズ: {int(e.control.value)}pt") or self.page.update(),
        )

        font_card = self._create_settings_card(
            "フォント設定",
            ft.Icons.TEXT_FIELDS,
            ft.Column([
                font_size_text,
                self.font_size_slider,
                ft.Text("変更は再起動後に完全に反映されます", size=11, color=ft.Colors.GREY_600),
            ], spacing=4),
        )

        self.window_width_field = ft.TextField(
            label="ウィンドウ幅",
            value=str(self.config.get("window_width", 1200)),
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="px",
            width=150,
        )

        self.window_height_field = ft.TextField(
            label="ウィンドウ高さ",
            value=str(self.config.get("window_height", 800)),
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="px",
            width=150,
        )

        window_card = self._create_settings_card(
            "ウィンドウサイズ",
            ft.Icons.ASPECT_RATIO,
            ft.Column([
                ft.Row([self.window_width_field, self.window_height_field], spacing=12),
                ft.Text("推奨: 幅 800-1920、高さ 600-1080", size=11, color=ft.Colors.GREY_600),
                ft.Text("変更は再起動後に反映されます", size=11, color=ft.Colors.GREY_600),
            ], spacing=4),
        )

        # クイック設定
        quick_size_buttons = ft.Row([
            ft.OutlinedButton(
                "小 (800x600)",
                on_click=lambda e: self._set_window_size(800, 600),
            ),
            ft.OutlinedButton(
                "中 (1200x800)",
                on_click=lambda e: self._set_window_size(1200, 800),
            ),
            ft.OutlinedButton(
                "大 (1600x1000)",
                on_click=lambda e: self._set_window_size(1600, 1000),
            ),
        ], wrap=True, spacing=8)

        quick_card = self._create_settings_card(
            "クイックサイズ設定",
            ft.Icons.PHOTO_SIZE_SELECT_SMALL,
            quick_size_buttons,
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                font_card,
                window_card,
                quick_card,
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _set_window_size(self, width: int, height: int):
        """ウィンドウサイズを設定"""
        self.window_width_field.value = str(width)
        self.window_height_field.value = str(height)
        self.page.update()

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
