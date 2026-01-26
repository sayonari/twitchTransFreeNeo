#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTubeチャットモニター
pytchatライブラリを使用してYouTube Liveのチャットを監視・翻訳
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from collections import deque

# pytchatのインポート
try:
    import pytchat
    PYTCHAT_AVAILABLE = True
except ImportError:
    PYTCHAT_AVAILABLE = False
    print("警告: pytchatが利用できません。YouTube接続機能は無効になります。")

try:
    from emoji import distinct_emoji_list
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    def distinct_emoji_list(text):
        return []

try:
    from .chat_monitor import ChatMessage, MessageProcessor
    from .translator import TranslationEngine, LanguageDetector
    from .database import TranslationDatabase
    from .tts import TTSEngine
    from .youtube_auth import YouTubeAuthManager, GOOGLE_AUTH_AVAILABLE
except ImportError:
    from twitchTransFreeNeo.core.chat_monitor import ChatMessage, MessageProcessor
    from twitchTransFreeNeo.core.translator import TranslationEngine, LanguageDetector
    from twitchTransFreeNeo.core.database import TranslationDatabase
    from twitchTransFreeNeo.core.tts import TTSEngine
    from twitchTransFreeNeo.core.youtube_auth import YouTubeAuthManager, GOOGLE_AUTH_AVAILABLE


class YouTubeChatMonitor:
    """YouTube Liveチャット監視クラス（読み取り＋書き込み対応）"""

    def __init__(self, config: Dict[str, Any], message_callback: Callable[[ChatMessage], None]):
        self.config = config
        self.message_callback = message_callback
        self.processor = MessageProcessor(config)
        self.translator = TranslationEngine(config)
        self.language_detector = LanguageDetector(config)
        self.database = TranslationDatabase()
        self.tts_engine = TTSEngine(config)

        self.is_running = False
        self.chat = None
        self._loop = None
        self._monitor_thread = None

        self.video_id = config.get("youtube_video_id", "")

        # YouTube認証マネージャー（投稿用）
        self.auth_manager: Optional[YouTubeAuthManager] = None
        self.live_chat_id: Optional[str] = None
        self.can_post = False  # 投稿可能かどうか

        # 表示のみモードかチェック
        self.view_only_mode = config.get("view_only_mode", False)

        # 投稿レート制限設定
        self.post_interval = config.get("youtube_post_interval", 3.0)  # 最小投稿間隔（秒）
        self.last_post_time = 0.0
        self.post_queue: deque = deque(maxlen=100)  # 投稿キュー
        self.daily_post_count = 0  # 1日の投稿数カウント
        self.daily_quota_limit = config.get("youtube_daily_quota_limit", 180)  # 1日の投稿上限（約9000ユニット分）
        self._rate_limit_warned = False

        # 認証情報があれば初期化
        if not self.view_only_mode and GOOGLE_AUTH_AVAILABLE:
            self._init_auth_manager()

    def _init_auth_manager(self):
        """認証マネージャーを初期化"""
        try:
            self.auth_manager = YouTubeAuthManager(self.config)
            if self.auth_manager.is_authenticated():
                print("[INFO] YouTube認証済み: 投稿機能が利用可能です")
            else:
                print("[INFO] YouTube未認証: 読み取り専用モードで動作します")
        except Exception as e:
            print(f"[WARNING] YouTube認証マネージャー初期化エラー: {e}")
            self.auth_manager = None

    def start(self):
        """チャット監視を開始"""
        if not PYTCHAT_AVAILABLE:
            print("[ERROR] pytchatが利用できないため、YouTube監視を開始できません")
            return False

        if not self.video_id:
            print("[ERROR] YouTube動画IDが設定されていません")
            return False

        try:
            print(f"[INFO] YouTube Live チャット監視を開始: video_id={self.video_id}")
            self.chat = pytchat.create(video_id=self.video_id)
            self.is_running = True

            # TTSエンジンを開始
            self.tts_engine.start()

            # 投稿機能の初期化（認証済みの場合）
            self._init_posting()

            # 非同期ループを取得または作成
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            # 別スレッドで監視を開始
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

            mode = "投稿可能" if self.can_post else "読み取り専用"
            print(f"[INFO] YouTube Live チャット監視を開始しました ({mode})")
            return True

        except Exception as e:
            print(f"[ERROR] YouTube監視開始エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _init_posting(self):
        """投稿機能を初期化"""
        if self.view_only_mode:
            print("[INFO] 表示のみモード: 投稿機能は無効です")
            self.can_post = False
            return

        if not self.auth_manager:
            print("[INFO] 認証なし: 投稿機能は無効です")
            self.can_post = False
            return

        if not self.auth_manager.is_authenticated():
            print("[INFO] 未認証: 投稿機能は無効です")
            self.can_post = False
            return

        # ライブチャットIDを取得
        live_chat_id, error = self.auth_manager.get_live_chat_id(self.video_id)
        if live_chat_id:
            self.live_chat_id = live_chat_id
            self.can_post = True
            print(f"[INFO] ライブチャットID取得成功: {live_chat_id[:20]}...")
        else:
            print(f"[WARNING] ライブチャットID取得失敗: {error}")
            self.can_post = False

    def _monitor_loop(self):
        """チャット監視ループ（別スレッド）"""
        # このスレッド用の新しいイベントループを作成
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.is_running and self.chat and self.chat.is_alive():
                try:
                    for c in self.chat.get().sync_items():
                        if not self.is_running:
                            break
                        # 非同期処理をループで実行
                        loop.run_until_complete(self._process_message(c))
                except Exception as e:
                    if self.is_running:
                        print(f"[ERROR] YouTube チャットメッセージ処理エラー: {e}")
        except Exception as e:
            print(f"[ERROR] YouTube監視ループエラー: {e}")
        finally:
            loop.close()
            print("[INFO] YouTube監視ループが終了しました")

    async def _process_message(self, chat_item):
        """メッセージ処理"""
        if not self.is_running:
            return

        username = chat_item.author.name
        original_content = chat_item.message
        timestamp = chat_item.datetime

        # ユーザーフィルター
        if self.processor.should_ignore_user(username):
            return

        # メッセージフィルター
        if self.processor.should_ignore_message(original_content):
            return

        # メッセージクリーニング（YouTubeエモートは不要）
        cleaned_content = self._clean_message(original_content)

        if not cleaned_content:
            return

        # 言語指定確認
        target_lang_override, text_to_translate = self.language_detector.extract_target_language_from_text(cleaned_content)

        # 言語検出
        detected_lang = await self.translator.detect_language(text_to_translate or cleaned_content)

        if not detected_lang:
            return

        # 無視言語チェック
        if self.language_detector.should_ignore_language(detected_lang):
            return

        # 翻訳先言語決定
        if target_lang_override:
            target_lang = target_lang_override
            final_text = text_to_translate
        else:
            target_lang = self.language_detector.determine_target_language(detected_lang, cleaned_content)
            final_text = cleaned_content

        # 同じ言語なら翻訳不要
        if detected_lang == target_lang:
            return

        # データベースから既訳語チェック
        cached_translation = await self.database.get_translation(final_text, target_lang)

        if cached_translation:
            translated_text = cached_translation
        else:
            # 翻訳実行
            translated_text = await self.translator.translate_text(final_text, target_lang, detected_lang)

            if translated_text:
                # データベースに保存
                await self.database.save_translation(final_text, translated_text, target_lang)

        if not translated_text:
            return

        # 翻訳後も削除単語除去
        for word in self.processor.delete_words:
            translated_text = translated_text.replace(word, '')

        # ChatMessageオブジェクト作成
        chat_message = ChatMessage(
            user=username,
            text=original_content,
            timestamp=timestamp,
            lang=detected_lang,
            translation=translated_text
        )

        # cleaned_contentとtarget_langを設定
        chat_message.cleaned_content = cleaned_content
        chat_message.target_lang = target_lang

        # GUI更新用コールバック
        if self.message_callback:
            self.message_callback(chat_message)

        # TTS読み上げ（TTS設定が有効な場合）
        self._add_tts_messages(chat_message)

        # チャットに投稿（投稿可能な場合）
        if self.can_post and not self.view_only_mode:
            self._post_translation(chat_message)

    def _post_translation(self, chat_message: ChatMessage):
        """翻訳結果をYouTubeチャットに投稿（レート制限付き）"""
        if not self.can_post or not self.auth_manager or not self.live_chat_id:
            return

        # 1日のクォータ制限チェック
        if self.daily_post_count >= self.daily_quota_limit:
            if not self._rate_limit_warned:
                print(f"[WARNING] YouTube投稿: 1日のクォータ上限({self.daily_quota_limit}件)に達しました")
                self._rate_limit_warned = True
            return

        # 投稿間隔チェック
        current_time = time.time()
        elapsed = current_time - self.last_post_time
        if elapsed < self.post_interval:
            # 間隔が短すぎる場合はスキップ（キューに入れない）
            if self.config.get("debug", False):
                print(f"[DEBUG] YouTube投稿スキップ: 間隔が短すぎます ({elapsed:.1f}s < {self.post_interval}s)")
            return

        try:
            # 投稿フォーマットを作成
            post_format = self.config.get("post_format", "[{lang}] {text}")
            message_text = post_format.format(
                user=chat_message.user,
                lang=chat_message.target_lang,
                text=chat_message.translation
            )

            # メッセージ長制限（YouTube Live チャットは200文字制限）
            max_length = 200
            if len(message_text) > max_length:
                message_text = message_text[:max_length - 3] + "..."

            # YouTube チャットに投稿
            success, error = self.auth_manager.send_message(self.live_chat_id, message_text)

            if success:
                self.last_post_time = current_time
                self.daily_post_count += 1
                if self.config.get("debug", False):
                    print(f"[DEBUG] YouTube投稿成功 ({self.daily_post_count}/{self.daily_quota_limit})")
            else:
                print(f"[WARNING] YouTube投稿失敗: {error}")
                # クォータ超過エラーの場合は制限フラグを立てる
                if "quotaExceeded" in str(error):
                    self._rate_limit_warned = True

        except Exception as e:
            print(f"[ERROR] YouTube投稿エラー: {e}")

    def _clean_message(self, message: str) -> str:
        """メッセージをクリーニング"""
        import re

        cleaned = message

        # Unicode絵文字除去
        unicode_emojis = distinct_emoji_list(cleaned)
        for emoji in unicode_emojis:
            cleaned = cleaned.replace(emoji, '')

        # 削除単語除去
        for word in self.processor.delete_words:
            cleaned = cleaned.replace(word, '')

        # @ユーザー名除去
        cleaned = re.sub(r'@\S+', '', cleaned)

        # 複数スペースを単一スペースに
        cleaned = " ".join(cleaned.split())

        return cleaned.strip()

    def _add_tts_messages(self, chat_message: ChatMessage):
        """TTS読み上げメッセージを追加"""
        # TTSが無効の場合は何もしない
        if not self.config.get("tts_enabled", False):
            return

        # 読み上げ言語制限チェック
        read_only_langs = self.config.get("read_only_these_lang", [])
        if read_only_langs:
            if chat_message.lang not in read_only_langs and chat_message.target_lang not in read_only_langs:
                return

        # 入力テキスト読み上げ
        if self.config.get("tts_in", False):
            tts_text = self._format_tts_text(chat_message, is_input=True)
            if tts_text:
                self.tts_engine.add_message(tts_text, chat_message.lang)

        # 出力テキスト読み上げ
        if self.config.get("tts_out", False):
            tts_text = self._format_tts_text(chat_message, is_input=False)
            if tts_text:
                self.tts_engine.add_message(tts_text, chat_message.target_lang)

    def _format_tts_text(self, chat_message: ChatMessage, is_input: bool = True) -> str:
        """TTS用のテキストをフォーマット"""
        parts = []

        # ユーザー名
        if is_input and self.config.get("tts_read_username_input", True):
            parts.append(chat_message.user)
        elif not is_input and self.config.get("tts_read_username_output", True):
            parts.append(chat_message.user)

        # 言語情報
        if self.config.get("tts_read_lang", False):
            if is_input:
                parts.append(f"({chat_message.lang})")
            else:
                parts.append(f"({chat_message.target_lang})")

        # 発言内容
        if self.config.get("tts_read_content", True):
            content = chat_message.text if is_input else chat_message.translation
            max_length = self.config.get("tts_text_max_length", 50)
            if max_length > 0 and len(content) > max_length:
                content = content[:max_length]
                omit_msg = self.config.get("tts_message_for_omitting", "")
                if omit_msg:
                    content += omit_msg
            parts.append(content)

        return " ".join(parts) if parts else ""

    def stop(self):
        """チャット監視を停止"""
        print("[INFO] YouTube Live チャット監視を停止中...")
        self.is_running = False

        if hasattr(self, 'tts_engine'):
            self.tts_engine.stop()

        if self.chat:
            try:
                self.chat.terminate()
            except Exception as e:
                print(f"[WARNING] pytchat終了時エラー: {e}")
            self.chat = None

        print("[INFO] YouTube Live チャット監視を停止しました")

    def update_config(self, config: Dict[str, Any]):
        """設定を更新"""
        self.config = config
        self.processor = MessageProcessor(config)
        self.translator = TranslationEngine(config)
        self.language_detector = LanguageDetector(config)
        self.video_id = config.get("youtube_video_id", "")
