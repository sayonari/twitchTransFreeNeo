#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flet as ft
from typing import Dict, Any, Callable, Optional
import webbrowser


class SettingsDialog:
    """Fletベースの設定ダイアログ（改善版）"""

    # サポートする言語リスト（Google翻訳対応）
    SUPPORTED_LANGUAGES = [
        # 主要言語（上部に配置）
        ('ja', '日本語'), ('en', '英語'), ('ko', '韓国語'),
        ('zh-CN', '中国語（簡体字）'), ('zh-TW', '中国語（繁体字）'),
        # ヨーロッパ言語
        ('fr', 'フランス語'), ('de', 'ドイツ語'), ('es', 'スペイン語'),
        ('pt', 'ポルトガル語'), ('it', 'イタリア語'), ('ru', 'ロシア語'),
        ('nl', 'オランダ語'), ('pl', 'ポーランド語'), ('uk', 'ウクライナ語'),
        ('cs', 'チェコ語'), ('sv', 'スウェーデン語'), ('da', 'デンマーク語'),
        ('fi', 'フィンランド語'), ('no', 'ノルウェー語'), ('el', 'ギリシャ語'),
        ('hu', 'ハンガリー語'), ('ro', 'ルーマニア語'), ('bg', 'ブルガリア語'),
        ('hr', 'クロアチア語'), ('sk', 'スロバキア語'), ('sl', 'スロベニア語'),
        ('lt', 'リトアニア語'), ('lv', 'ラトビア語'), ('et', 'エストニア語'),
        # アジア言語
        ('th', 'タイ語'), ('vi', 'ベトナム語'), ('id', 'インドネシア語'),
        ('ms', 'マレー語'), ('tl', 'フィリピン語/タガログ語'), ('hi', 'ヒンディー語'),
        ('bn', 'ベンガル語'), ('ta', 'タミル語'), ('te', 'テルグ語'),
        ('mr', 'マラーティー語'), ('gu', 'グジャラート語'), ('kn', 'カンナダ語'),
        ('ml', 'マラヤーラム語'), ('pa', 'パンジャブ語'), ('ur', 'ウルドゥー語'),
        ('my', 'ミャンマー語'), ('km', 'クメール語'), ('lo', 'ラオ語'),
        ('ne', 'ネパール語'), ('si', 'シンハラ語'), ('mn', 'モンゴル語'),
        # 中東・アフリカ言語
        ('ar', 'アラビア語'), ('he', 'ヘブライ語'), ('fa', 'ペルシャ語'),
        ('tr', 'トルコ語'), ('sw', 'スワヒリ語'), ('af', 'アフリカーンス語'),
        ('am', 'アムハラ語'), ('zu', 'ズールー語'),
        # その他
        ('ca', 'カタルーニャ語'), ('eu', 'バスク語'), ('gl', 'ガリシア語'),
        ('is', 'アイスランド語'), ('ga', 'アイルランド語'), ('cy', 'ウェールズ語'),
        ('mt', 'マルタ語'), ('sq', 'アルバニア語'), ('mk', 'マケドニア語'),
        ('sr', 'セルビア語'), ('bs', 'ボスニア語'), ('ka', 'ジョージア語'),
        ('az', 'アゼルバイジャン語'), ('kk', 'カザフ語'), ('uz', 'ウズベク語'),
        ('hy', 'アルメニア語'), ('la', 'ラテン語'), ('eo', 'エスペラント語'),
        # カスタム入力用
        ('custom', '✏️ その他（直接入力）'),
    ]

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
        self.home_lang_custom_field: Optional[ft.TextField] = None
        self.other_lang_custom_field: Optional[ft.TextField] = None
        self.home_lang_custom_container: Optional[ft.Container] = None
        self.other_lang_custom_container: Optional[ft.Container] = None
        self.translator_dropdown: Optional[ft.Dropdown] = None
        self.google_suffix_dropdown: Optional[ft.Dropdown] = None
        self.deepl_key_field: Optional[ft.TextField] = None

        # プラットフォーム設定
        self.platform_dropdown: Optional[ft.Dropdown] = None
        self.youtube_video_id_field: Optional[ft.TextField] = None
        self.youtube_client_id_field: Optional[ft.TextField] = None
        self.youtube_client_secret_field: Optional[ft.TextField] = None
        self.youtube_auth_status_text: Optional[ft.Text] = None
        self.youtube_post_interval_field: Optional[ft.TextField] = None
        self.youtube_daily_limit_field: Optional[ft.TextField] = None
        self.youtube_container: Optional[ft.Container] = None

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
        self.sound_enabled_checkbox: Optional[ft.Checkbox] = None
        self.sound_volume_slider: Optional[ft.Slider] = None
        self.accent_color_dropdown: Optional[ft.Dropdown] = None

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
                    ft.Container(expand=True),  # スペーサー
                    ft.IconButton(
                        icon=ft.Icons.FILE_DOWNLOAD,
                        tooltip="設定をエクスポート（保存）",
                        on_click=self._export_settings,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FILE_UPLOAD,
                        tooltip="設定をインポート（適用）",
                        on_click=self._import_settings,
                    ),
                ], spacing=8),
                content=ft.Container(
                    content=self.tabs,
                    width=720,
                    height=520,
                ),
                actions=[
                    ft.TextButton("キャンセル", on_click=self._cancel),
                    ft.ElevatedButton("適用", on_click=self._apply),
                    ft.ElevatedButton(
                        "OK",
                        on_click=self._ok,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PRIMARY,
                            color=ft.Colors.WHITE,
                        )
                    ),
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

        # プラットフォーム選択（同時配信対応）
        current_platform = self.config.get("platform", "twitch")
        self.platform_dropdown = ft.Dropdown(
            label="配信プラットフォーム",
            value=current_platform,
            options=[
                ft.DropdownOption("twitch", "Twitch のみ"),
                ft.DropdownOption("youtube", "YouTube Live のみ"),
                ft.DropdownOption("both", "同時配信 (Twitch + YouTube)"),
            ],
            width=300,
            on_change=lambda e: self._on_platform_change(),
        )

        platform_card = self._create_settings_card(
            "プラットフォーム選択",
            ft.Icons.CONNECTED_TV,
            ft.Column([
                self.platform_dropdown,
                ft.Text(
                    "※ YouTubeはOAuth認証で翻訳投稿も可能（未認証時は読み取り専用）\n※ 同時配信では両方のチャットを監視・翻訳します",
                    size=11, color=ft.Colors.GREY_600,
                ),
            ], spacing=4),
            helper_text="単独配信または同時配信を選択"
        )

        # === Twitch設定 ===
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

        self.twitch_container = ft.Container(
            content=self._create_settings_card(
                "Twitch接続設定",
                ft.Icons.LINK,
                ft.Column([
                    self.channel_field,
                    self.username_field,
                    self.oauth_field,
                    oauth_button,
                ], spacing=8),
                helper_text="チャンネルに接続するために必要な設定です"
            ),
            visible=(current_platform in ["twitch", "both"]),
        )

        # === YouTube設定 ===
        self.youtube_video_id_field = ft.TextField(
            label="YouTube動画ID / URL",
            value=self.config.get("youtube_video_id", ""),
            hint_text="例: dQw4w9WgXcQ または動画URL",
            prefix_icon=ft.Icons.PLAY_CIRCLE,
            width=400,
        )

        # YouTube OAuth認証設定
        self.youtube_client_id_field = ft.TextField(
            label="YouTube Client ID",
            value=self.config.get("youtube_client_id", ""),
            hint_text="Google Cloud Consoleで取得",
            prefix_icon=ft.Icons.FINGERPRINT,
            width=400,
        )

        self.youtube_client_secret_field = ft.TextField(
            label="YouTube Client Secret",
            value=self.config.get("youtube_client_secret", ""),
            password=True,
            can_reveal_password=True,
            hint_text="Google Cloud Consoleで取得",
            prefix_icon=ft.Icons.KEY,
            width=400,
        )

        # 認証状態の表示
        auth_status = self._check_youtube_auth_status()
        self.youtube_auth_status_text = ft.Text(
            auth_status,
            size=12,
            color=ft.Colors.GREEN_700 if "認証済み" in auth_status else ft.Colors.GREY_600,
        )

        youtube_auth_button = ft.ElevatedButton(
            "YouTube認証を行う",
            icon=ft.Icons.LOGIN,
            on_click=self._start_youtube_auth,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )

        youtube_revoke_button = ft.OutlinedButton(
            "認証を取り消す",
            icon=ft.Icons.LOGOUT,
            on_click=self._revoke_youtube_auth,
        )

        youtube_console_button = ft.ElevatedButton(
            "Google Cloud Console",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: webbrowser.open("https://console.cloud.google.com/apis/credentials"),
            tooltip="OAuth認証情報を作成するページを開く",
        )

        youtube_api_enable_button = ft.OutlinedButton(
            "YouTube API有効化",
            icon=ft.Icons.PLAY_CIRCLE,
            on_click=lambda e: webbrowser.open("https://console.cloud.google.com/apis/library/youtube.googleapis.com"),
            tooltip="YouTube Data API v3を有効にする",
        )

        youtube_help_button = ft.ElevatedButton(
            "設定ガイド",
            icon=ft.Icons.HELP_OUTLINE,
            on_click=lambda e: webbrowser.open("https://www.sayonari.com/trans_asr/oauth/youtube/"),
        )

        self.youtube_container = ft.Container(
            content=self._create_settings_card(
                "YouTube Live設定",
                ft.Icons.SMART_DISPLAY,
                ft.Column([
                    self.youtube_video_id_field,
                    ft.Text(
                        "URLから自動的に動画IDを抽出します\n例: https://www.youtube.com/watch?v=XXXXXXXXXXX",
                        size=11, color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=1),
                    ft.Text("OAuth認証設定（翻訳投稿機能を使う場合）", weight=ft.FontWeight.W_500, size=13),
                    self.youtube_client_id_field,
                    self.youtube_client_secret_field,
                    ft.Row([
                        youtube_auth_button,
                        youtube_revoke_button,
                    ], spacing=8),
                    self.youtube_auth_status_text,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("OAuth認証情報の取得方法:", weight=ft.FontWeight.W_500, size=12),
                            ft.Text(
                                "1. Google Cloud Consoleでプロジェクトを作成\n"
                                "2. YouTube Data API v3を有効化\n"
                                "3. OAuth同意画面を設定（テスト用でOK）\n"
                                "4. OAuth 2.0 クライアントIDを作成（デスクトップアプリ）\n"
                                "5. Client IDとClient Secretをコピー",
                                size=11, color=ft.Colors.GREY_700,
                            ),
                            ft.Row([
                                youtube_console_button,
                                youtube_api_enable_button,
                                youtube_help_button,
                            ], wrap=True, spacing=8),
                        ], spacing=4),
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
                        padding=10,
                        border_radius=4,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO, size=16, color=ft.Colors.GREEN_700),
                            ft.Text(
                                "OAuth未設定の場合は読み取り専用で動作します（APIキー不要）",
                                size=12, color=ft.Colors.GREEN_700,
                            ),
                        ], spacing=4),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                        padding=8,
                        border_radius=4,
                    ),
                    ft.Divider(height=1),
                    ft.Text("投稿レート制限", weight=ft.FontWeight.W_500, size=13),
                    self._create_youtube_rate_limit_fields(),
                ], spacing=8),
                helper_text="ライブ配信の動画IDと認証設定"
            ),
            visible=(current_platform in ["youtube", "both"]),
        )

        # === 共通設定 ===
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
                platform_card,
                self.twitch_container,
                self.youtube_container,
                display_card,
                misc_card,
            ], scroll=ft.ScrollMode.ALWAYS, spacing=12),
            padding=10,
        )

    def _create_youtube_rate_limit_fields(self) -> ft.Container:
        """YouTube投稿レート制限フィールドを作成"""
        self.youtube_post_interval_field = ft.TextField(
            label="最小投稿間隔（秒）",
            value=str(self.config.get("youtube_post_interval", 3.0)),
            hint_text="推奨: 3〜5秒",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )

        self.youtube_daily_limit_field = ft.TextField(
            label="1日の投稿上限",
            value=str(self.config.get("youtube_daily_quota_limit", 180)),
            hint_text="推奨: 100〜200件",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self.youtube_post_interval_field,
                    self.youtube_daily_limit_field,
                ], spacing=12),
                ft.Text(
                    "YouTube Data APIにはクォータ制限があります。\n"
                    "投稿間隔を短くしすぎると制限に達する可能性があります。",
                    size=11, color=ft.Colors.GREY_600,
                ),
            ], spacing=4),
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.AMBER),
            padding=10,
            border_radius=4,
        )

    def _on_platform_change(self):
        """プラットフォーム変更時のハンドラ"""
        platform = self.platform_dropdown.value
        self.twitch_container.visible = platform in ["twitch", "both"]
        self.youtube_container.visible = platform in ["youtube", "both"]
        self.page.update()

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

        # 言語ドロップダウンの初期値を決定
        home_lang_value = self.config.get("lang_trans_to_home", "ja")
        other_lang_value = self.config.get("lang_home_to_other", "en")

        # 保存された言語がリストにない場合は custom を選択
        lang_codes = [code for code, _ in self.SUPPORTED_LANGUAGES]
        if home_lang_value not in lang_codes:
            home_lang_custom_value = home_lang_value
            home_lang_value = "custom"
        else:
            home_lang_custom_value = ""

        if other_lang_value not in lang_codes:
            other_lang_custom_value = other_lang_value
            other_lang_value = "custom"
        else:
            other_lang_custom_value = ""

        # ホーム言語ドロップダウン
        self.home_lang_dropdown = ft.Dropdown(
            label="ホーム言語（配信者の言語）",
            value=home_lang_value,
            options=[ft.DropdownOption(lang, text) for lang, text in self.SUPPORTED_LANGUAGES],
            width=350,
            on_change=lambda e: self._on_lang_dropdown_change("home"),
        )

        # ホーム言語カスタム入力
        self.home_lang_custom_field = ft.TextField(
            label="言語コード（直接入力）",
            value=home_lang_custom_value or self.config.get("lang_trans_to_home_custom", ""),
            hint_text="例: fil, haw, mi",
            width=200,
        )
        self.home_lang_custom_container = ft.Container(
            content=self.home_lang_custom_field,
            visible=(home_lang_value == "custom"),
        )

        # 外国語ドロップダウン
        self.other_lang_dropdown = ft.Dropdown(
            label="外国語（翻訳先）",
            value=other_lang_value,
            options=[ft.DropdownOption(lang, text) for lang, text in self.SUPPORTED_LANGUAGES],
            width=350,
            on_change=lambda e: self._on_lang_dropdown_change("other"),
        )

        # 外国語カスタム入力
        self.other_lang_custom_field = ft.TextField(
            label="言語コード（直接入力）",
            value=other_lang_custom_value or self.config.get("lang_home_to_other_custom", ""),
            hint_text="例: fil, haw, mi",
            width=200,
        )
        self.other_lang_custom_container = ft.Container(
            content=self.other_lang_custom_field,
            visible=(other_lang_value == "custom"),
        )

        lang_card = self._create_settings_card(
            "言語設定",
            ft.Icons.LANGUAGE,
            ft.Column([
                ft.Row([self.home_lang_dropdown, self.home_lang_custom_container], spacing=8, wrap=True),
                ft.Row([self.other_lang_dropdown, self.other_lang_custom_container], spacing=8, wrap=True),
                ft.Text(
                    "ホーム言語のコメント → 外国語に翻訳\n外国語のコメント → ホーム言語に翻訳\n※「その他」を選ぶとGoogle翻訳の任意の言語コードを入力できます",
                    size=11, color=ft.Colors.GREY_600,
                ),
            ], spacing=8),
            helper_text="60以上の言語に対応。リストにない言語も直接入力可能"
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

    def _on_lang_dropdown_change(self, which: str):
        """言語ドロップダウン変更時のハンドラ"""
        if which == "home":
            is_custom = self.home_lang_dropdown.value == "custom"
            self.home_lang_custom_container.visible = is_custom
        else:
            is_custom = self.other_lang_dropdown.value == "custom"
            self.other_lang_custom_container.visible = is_custom
        self.page.update()

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
            self.home_lang_custom_container.visible = False
            self.other_lang_custom_container.visible = False
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
        # フォントサイズを有効範囲(10-24)に制限（旧バージョンとの互換性）
        current_font_size = self.config.get("font_size", 12)
        current_font_size = max(10, min(24, current_font_size))

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

        # サウンド通知設定
        self.sound_enabled_checkbox = ft.Checkbox(
            label="サウンド通知を有効にする",
            value=self.config.get("sound_enabled", False),
        )

        sound_volume_text = ft.Text(f"音量: {int(self.config.get('sound_volume', 0.5) * 100)}%", size=12)

        self.sound_volume_slider = ft.Slider(
            min=0,
            max=1,
            divisions=10,
            value=self.config.get("sound_volume", 0.5),
            label="{value}",
            on_change=lambda e: setattr(sound_volume_text, 'value', f"音量: {int(e.control.value * 100)}%") or self.page.update(),
        )

        sound_card = self._create_settings_card(
            "サウンド通知",
            ft.Icons.NOTIFICATIONS_ACTIVE,
            ft.Column([
                self.sound_enabled_checkbox,
                sound_volume_text,
                self.sound_volume_slider,
                ft.Text("翻訳メッセージ受信時に通知音を再生", size=11, color=ft.Colors.GREY_600),
            ], spacing=4),
        )

        # カスタムテーマ設定
        self.accent_color_dropdown = ft.Dropdown(
            label="アクセントカラー",
            options=[
                ft.DropdownOption("blue", "ブルー"),
                ft.DropdownOption("purple", "パープル"),
                ft.DropdownOption("green", "グリーン"),
                ft.DropdownOption("orange", "オレンジ"),
                ft.DropdownOption("red", "レッド"),
                ft.DropdownOption("teal", "ティール"),
            ],
            value=self.config.get("accent_color", "blue"),
            width=200,
        )

        theme_card = self._create_settings_card(
            "テーマ設定",
            ft.Icons.PALETTE,
            ft.Column([
                self.accent_color_dropdown,
                ft.Text("アクセントカラーを変更します", size=11, color=ft.Colors.GREY_600),
                ft.Text("変更は再起動後に反映されます", size=11, color=ft.Colors.GREY_600),
            ], spacing=4),
        )

        return ft.Container(
            content=ft.Column([
                self._create_scroll_hint(),
                font_card,
                window_card,
                quick_card,
                sound_card,
                theme_card,
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

        # プラットフォーム設定
        updated["platform"] = self.platform_dropdown.value

        # Twitch設定
        updated["twitch_channel"] = self.channel_field.value
        updated["trans_username"] = self.username_field.value
        updated["trans_oauth"] = self.oauth_field.value

        # YouTube設定
        youtube_input = self.youtube_video_id_field.value.strip()
        # URLから動画IDを抽出
        updated["youtube_video_id"] = self._extract_youtube_video_id(youtube_input)
        updated["youtube_client_id"] = self.youtube_client_id_field.value.strip()
        updated["youtube_client_secret"] = self.youtube_client_secret_field.value.strip()

        # YouTube投稿レート制限設定
        try:
            updated["youtube_post_interval"] = float(self.youtube_post_interval_field.value) if self.youtube_post_interval_field.value else 3.0
        except ValueError:
            updated["youtube_post_interval"] = 3.0
        try:
            updated["youtube_daily_quota_limit"] = int(self.youtube_daily_limit_field.value) if self.youtube_daily_limit_field.value else 180
        except ValueError:
            updated["youtube_daily_quota_limit"] = 180

        # 表示設定
        updated["trans_text_color"] = self.color_dropdown.value
        updated["show_by_name"] = self.show_name_checkbox.value
        updated["show_by_lang"] = self.show_lang_checkbox.value
        updated["debug"] = self.debug_checkbox.value
        updated["auto_start"] = self.auto_start_checkbox.value
        updated["view_only_mode"] = self.view_only_checkbox.value

        # 翻訳設定（カスタム言語対応）
        if self.home_lang_dropdown.value == "custom":
            updated["lang_trans_to_home"] = self.home_lang_custom_field.value.strip() or "ja"
        else:
            updated["lang_trans_to_home"] = self.home_lang_dropdown.value

        if self.other_lang_dropdown.value == "custom":
            updated["lang_home_to_other"] = self.other_lang_custom_field.value.strip() or "en"
        else:
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

        # サウンド設定
        updated["sound_enabled"] = self.sound_enabled_checkbox.value if self.sound_enabled_checkbox else False
        updated["sound_volume"] = self.sound_volume_slider.value if self.sound_volume_slider else 0.5

        # テーマ設定
        updated["accent_color"] = self.accent_color_dropdown.value if self.accent_color_dropdown else "blue"

        return updated

    def _extract_youtube_video_id(self, input_str: str) -> str:
        """YouTubeのURLまたは動画IDから動画IDを抽出"""
        import re

        if not input_str:
            return ""

        # すでに動画IDの形式（11文字の英数字と_-）の場合
        if re.match(r'^[\w-]{11}$', input_str):
            return input_str

        # 様々なYouTube URL形式から動画IDを抽出
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/live/)([^\s&?]+)',
            r'[?&]v=([^\s&]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, input_str)
            if match:
                video_id = match.group(1)
                # 動画IDは通常11文字
                if len(video_id) >= 11:
                    return video_id[:11]
                return video_id

        # マッチしない場合は入力をそのまま返す
        return input_str

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

    # === YouTube OAuth関連メソッド ===

    def _check_youtube_auth_status(self) -> str:
        """YouTube認証状態をチェック"""
        try:
            from ..core.youtube_auth import YouTubeAuthManager, GOOGLE_AUTH_AVAILABLE
            if not GOOGLE_AUTH_AVAILABLE:
                return "⚠️ Google認証ライブラリが未インストール"

            auth_manager = YouTubeAuthManager(self.config)
            if auth_manager.is_authenticated():
                # アカウント情報を取得して表示
                account_info = self._get_youtube_account_info(auth_manager)
                if account_info:
                    return f"✅ 認証済み（投稿機能が利用可能）\nアカウント: {account_info}"
                return "✅ 認証済み（投稿機能が利用可能）"
            elif auth_manager.has_credentials():
                return "⚠️ 認証情報は設定済み（認証ボタンを押してください）"
            else:
                return "ℹ️ 未設定（Client IDとSecretを入力してください）"
        except Exception as e:
            return f"⚠️ 認証状態の確認エラー: {e}"

    def _start_youtube_auth(self, e):
        """YouTube OAuth認証を開始"""
        # まず設定を保存（Client IDとSecretを反映）
        client_id = self.youtube_client_id_field.value.strip()
        client_secret = self.youtube_client_secret_field.value.strip()

        if not client_id or not client_secret:
            self._show_auth_error("Client IDとClient Secretを入力してください")
            return

        try:
            from ..core.youtube_auth import YouTubeAuthManager, GOOGLE_AUTH_AVAILABLE

            if not GOOGLE_AUTH_AVAILABLE:
                self._show_auth_error("Google認証ライブラリが利用できません。\npip install google-auth google-auth-oauthlib google-api-python-client")
                return

            # 一時的にconfigを更新
            temp_config = self.config.copy()
            temp_config["youtube_client_id"] = client_id
            temp_config["youtube_client_secret"] = client_secret

            auth_manager = YouTubeAuthManager(temp_config)

            # 認証状態を更新
            self.youtube_auth_status_text.value = "🔄 認証中...ブラウザで認証してください"
            self.youtube_auth_status_text.color = ft.Colors.BLUE_700
            self.page.update()

            # 非同期で認証を実行（ブラウザが開く）
            def auth_callback(success, message):
                if success:
                    # 認証成功時にアカウント情報を取得して表示
                    account_info = self._get_youtube_account_info(auth_manager)
                    if account_info:
                        self.youtube_auth_status_text.value = f"✅ 認証成功！\nアカウント: {account_info}"
                    else:
                        self.youtube_auth_status_text.value = "✅ 認証成功！"
                    self.youtube_auth_status_text.color = ft.Colors.GREEN_700
                else:
                    self.youtube_auth_status_text.value = f"❌ 認証失敗: {message}"
                    self.youtube_auth_status_text.color = ft.Colors.RED_700
                self.page.update()

            auth_manager.authenticate_async(auth_callback)

        except Exception as ex:
            self._show_auth_error(f"認証開始エラー: {ex}")

    def _revoke_youtube_auth(self, e):
        """YouTube認証を取り消す"""
        try:
            from ..core.youtube_auth import YouTubeAuthManager, GOOGLE_AUTH_AVAILABLE

            if not GOOGLE_AUTH_AVAILABLE:
                return

            auth_manager = YouTubeAuthManager(self.config)
            if auth_manager.revoke_credentials():
                self.youtube_auth_status_text.value = "ℹ️ 認証を取り消しました"
                self.youtube_auth_status_text.color = ft.Colors.GREY_600
            else:
                self.youtube_auth_status_text.value = "⚠️ 認証取り消しに失敗しました"
                self.youtube_auth_status_text.color = ft.Colors.AMBER_700
            self.page.update()

        except Exception as ex:
            self._show_auth_error(f"認証取り消しエラー: {ex}")

    def _get_youtube_account_info(self, auth_manager) -> Optional[str]:
        """YouTube認証済みアカウントの情報を取得"""
        try:
            service = auth_manager.get_youtube_service()
            if not service:
                return None

            # チャンネル情報を取得
            response = service.channels().list(
                part='snippet',
                mine=True
            ).execute()

            if response.get('items'):
                channel = response['items'][0]
                snippet = channel.get('snippet', {})
                title = snippet.get('title', '')
                custom_url = snippet.get('customUrl', '')
                if custom_url:
                    return f"{title} (@{custom_url})"
                return title
        except Exception as e:
            print(f"[WARNING] YouTubeアカウント情報取得エラー: {e}")
        return None

    def _show_auth_error(self, message: str):
        """認証エラーを表示"""
        self.youtube_auth_status_text.value = f"❌ {message}"
        self.youtube_auth_status_text.color = ft.Colors.RED_700
        self.page.update()

    # === 設定インポート/エクスポート ===

    def _export_settings(self, e):
        """設定をJSONファイルにエクスポート"""
        import json
        from datetime import datetime

        try:
            # 現在の設定を取得
            current_config = self._get_updated_config()

            # セキュリティ上、機密情報を除外するオプション
            export_config = current_config.copy()

            # エクスポートするかどうか確認ダイアログ
            def do_export(include_secrets: bool):
                if not include_secrets:
                    # 機密情報を除外
                    sensitive_keys = ["trans_oauth", "youtube_client_secret", "deepl_api_key"]
                    for key in sensitive_keys:
                        if key in export_config:
                            export_config[key] = ""

                # ファイル名を生成
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"twitchTransFreeNeo_config_{timestamp}.json"

                # JSONに変換
                json_str = json.dumps(export_config, ensure_ascii=False, indent=2)

                # ファイルピッカーを使用
                def save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        try:
                            with open(e.path, 'w', encoding='utf-8') as f:
                                f.write(json_str)
                            self._show_message("エクスポート完了", f"設定を保存しました:\n{e.path}")
                        except Exception as ex:
                            self._show_message("エクスポートエラー", f"ファイルの保存に失敗しました:\n{ex}")
                    self.page.close(confirm_dialog)

                file_picker = ft.FilePicker(on_result=save_result)
                self.page.overlay.append(file_picker)
                self.page.update()
                file_picker.save_file(
                    dialog_title="設定をエクスポート",
                    file_name=filename,
                    allowed_extensions=["json"],
                )

            def close_and_export_with_secrets(e):
                self.page.close(confirm_dialog)
                self.page.update()
                do_export(True)

            def close_and_export_without_secrets(e):
                self.page.close(confirm_dialog)
                self.page.update()
                do_export(False)

            def close_confirm(e):
                self.page.close(confirm_dialog)
                self.page.update()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("設定のエクスポート"),
                content=ft.Column([
                    ft.Text("設定ファイルをエクスポートします。"),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER),
                            ft.Text(
                                "OAuthトークンやAPIキーなどの機密情報を含めますか？\n"
                                "含める場合、ファイルの取り扱いにご注意ください。",
                                size=13,
                            ),
                        ], spacing=8),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
                        padding=10,
                        border_radius=5,
                    ),
                ], spacing=10, tight=True),
                actions=[
                    ft.TextButton("キャンセル", on_click=close_confirm),
                    ft.OutlinedButton("機密情報を除外", on_click=close_and_export_without_secrets),
                    ft.ElevatedButton("すべて含める", on_click=close_and_export_with_secrets),
                ],
            )
            self.page.open(confirm_dialog)
            self.page.update()

        except Exception as ex:
            self._show_message("エクスポートエラー", f"エクスポート中にエラーが発生しました:\n{ex}")

    def _import_settings(self, e):
        """JSONファイルから設定をインポート"""
        import json

        def on_file_picked(e: ft.FilePickerResultEvent):
            if not e.files or len(e.files) == 0:
                return

            try:
                file_path = e.files[0].path
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)

                # 設定を適用
                self._apply_imported_config(imported_config)
                self._show_message("インポート完了", "設定をインポートしました。\n「適用」または「OK」で保存してください。")

            except json.JSONDecodeError:
                self._show_message("インポートエラー", "無効なJSONファイルです。")
            except Exception as ex:
                self._show_message("インポートエラー", f"インポート中にエラーが発生しました:\n{ex}")

        file_picker = ft.FilePicker(on_result=on_file_picked)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="設定をインポート",
            allowed_extensions=["json"],
            allow_multiple=False,
        )

    def _apply_imported_config(self, imported_config: Dict[str, Any]):
        """インポートした設定をUIに反映"""
        # 基本設定
        if "platform" in imported_config and self.platform_dropdown:
            self.platform_dropdown.value = imported_config.get("platform", "twitch")
        if "twitch_channel" in imported_config and self.channel_field:
            self.channel_field.value = imported_config.get("twitch_channel", "")
        if "trans_username" in imported_config and self.username_field:
            self.username_field.value = imported_config.get("trans_username", "")
        if "trans_oauth" in imported_config and self.oauth_field:
            self.oauth_field.value = imported_config.get("trans_oauth", "")

        # YouTube設定
        if "youtube_video_id" in imported_config and self.youtube_video_id_field:
            self.youtube_video_id_field.value = imported_config.get("youtube_video_id", "")
        if "youtube_client_id" in imported_config and self.youtube_client_id_field:
            self.youtube_client_id_field.value = imported_config.get("youtube_client_id", "")
        if "youtube_client_secret" in imported_config and self.youtube_client_secret_field:
            self.youtube_client_secret_field.value = imported_config.get("youtube_client_secret", "")

        # 翻訳設定
        if "lang_trans_to_home" in imported_config and self.home_lang_dropdown:
            lang = imported_config.get("lang_trans_to_home", "ja")
            lang_codes = [code for code, _ in self.SUPPORTED_LANGUAGES]
            if lang in lang_codes:
                self.home_lang_dropdown.value = lang
                self.home_lang_custom_container.visible = False
            else:
                self.home_lang_dropdown.value = "custom"
                self.home_lang_custom_field.value = lang
                self.home_lang_custom_container.visible = True

        if "lang_home_to_other" in imported_config and self.other_lang_dropdown:
            lang = imported_config.get("lang_home_to_other", "en")
            lang_codes = [code for code, _ in self.SUPPORTED_LANGUAGES]
            if lang in lang_codes:
                self.other_lang_dropdown.value = lang
                self.other_lang_custom_container.visible = False
            else:
                self.other_lang_dropdown.value = "custom"
                self.other_lang_custom_field.value = lang
                self.other_lang_custom_container.visible = True

        # 表示設定
        if "trans_text_color" in imported_config and self.color_dropdown:
            self.color_dropdown.value = imported_config.get("trans_text_color", "GoldenRod")
        if "show_by_name" in imported_config and self.show_name_checkbox:
            self.show_name_checkbox.value = imported_config.get("show_by_name", True)
        if "show_by_lang" in imported_config and self.show_lang_checkbox:
            self.show_lang_checkbox.value = imported_config.get("show_by_lang", True)

        # その他
        if "debug" in imported_config and self.debug_checkbox:
            self.debug_checkbox.value = imported_config.get("debug", False)
        if "auto_start" in imported_config and self.auto_start_checkbox:
            self.auto_start_checkbox.value = imported_config.get("auto_start", False)
        if "view_only_mode" in imported_config and self.view_only_checkbox:
            self.view_only_checkbox.value = imported_config.get("view_only_mode", False)

        # プラットフォーム表示を更新
        self._on_platform_change()
        self.page.update()

    def _show_message(self, title: str, message: str):
        """メッセージダイアログを表示"""
        def close_dialog(e):
            self.page.close(msg_dialog)
            self.page.update()

        msg_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.ElevatedButton("OK", on_click=close_dialog)],
        )
        self.page.open(msg_dialog)
        self.page.update()
