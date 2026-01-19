#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTubeチャットモニター
pytchatライブラリを使用してYouTube Liveのチャットを監視・翻訳
"""

import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Callable, Optional

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
except ImportError:
    from twitchTransFreeNeo.core.chat_monitor import ChatMessage, MessageProcessor
    from twitchTransFreeNeo.core.translator import TranslationEngine, LanguageDetector
    from twitchTransFreeNeo.core.database import TranslationDatabase
    from twitchTransFreeNeo.core.tts import TTSEngine


class YouTubeChatMonitor:
    """YouTube Liveチャット監視クラス"""

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

            # 非同期ループを取得または作成
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            # 別スレッドで監視を開始
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

            print(f"[INFO] YouTube Live チャット監視を開始しました")
            return True

        except Exception as e:
            print(f"[ERROR] YouTube監視開始エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

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

        # YouTubeはチャット投稿機能なし（読み取り専用）

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
