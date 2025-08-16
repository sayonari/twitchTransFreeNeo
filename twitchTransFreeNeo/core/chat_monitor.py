#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import re
from typing import Dict, Any, Callable, Optional, List

# オプショナルな依存関係
try:
    from twitchio.ext import commands
    TWITCHIO_AVAILABLE = True
except ImportError:
    TWITCHIO_AVAILABLE = False
    print("警告: twitchioが利用できません。Twitch接続機能は無効になります。")

try:
    from emoji import distinct_emoji_list
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    def distinct_emoji_list(text):
        return []

try:
    from .translator import TranslationEngine, LanguageDetector
    from .database import TranslationDatabase
    from .tts import TTSEngine
except ImportError:
    try:
        from twitchTransFreeNeo.core.translator import TranslationEngine, LanguageDetector
        from twitchTransFreeNeo.core.database import TranslationDatabase
        from twitchTransFreeNeo.core.tts import TTSEngine
    except ImportError:
        # フォールバック用のダミークラス
        class TranslationEngine:
            def __init__(self, *args, **kwargs): pass
            async def translate(self, *args, **kwargs): return ""
        
        class LanguageDetector:
            def __init__(self, *args, **kwargs): pass
            def detect(self, *args, **kwargs): return "unknown"
        
        class TranslationDatabase:
            def __init__(self, *args, **kwargs): pass
            async def save_translation(self, *args, **kwargs): return True
            async def get_translation(self, *args, **kwargs): return None
        
        class TTSEngine:
            def __init__(self, *args, **kwargs): pass
            async def speak(self, *args, **kwargs): pass

class ChatMessage:
    """チャットメッセージクラス"""
    
    def __init__(self, user: str, text: str, timestamp, lang: str = "", translation: str = ""):
        from datetime import datetime
        self.user = user
        self.text = text
        self.timestamp = timestamp if hasattr(timestamp, 'strftime') else datetime.now()
        self.lang = lang
        self.translation = translation
        
        # 追加の属性
        self.is_translated = bool(translation)  # 翻訳済みかどうか
        self.cleaned_content = text  # クリーンアップされたコンテンツ（デフォルトは元のテキスト）
        self.target_lang = ""  # ターゲット言語

class MessageProcessor:
    """メッセージ処理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._load_filters()
    
    def _load_filters(self):
        """フィルター設定を読み込み"""
        self.ignore_users = [user.lower() for user in self.config.get("ignore_users", [])]
        self.ignore_lines = self.config.get("ignore_line", [])
        self.ignore_www = self.config.get("ignore_www", [])
        self.delete_words = self.config.get("delete_words", [])
    
    def should_ignore_user(self, username: str) -> bool:
        """ユーザーを無視すべきかチェック"""
        return username.lower() in self.ignore_users
    
    def should_ignore_message(self, message: str) -> bool:
        """メッセージを無視すべきかチェック"""
        # 無視テキストチェック
        for ignore_text in self.ignore_lines:
            if ignore_text in message:
                return True
        
        # 単芝チェック
        if message in self.ignore_www:
            return True
        
        return False
    
    def clean_message(self, message: str, emotes_data: Optional[str] = None) -> str:
        """メッセージをクリーニング"""
        cleaned = message
        
        # エモート除去
        if emotes_data:
            emote_list = self._extract_emotes(message, emotes_data)
            for emote in sorted(emote_list, key=len, reverse=True):
                cleaned = cleaned.replace(emote, '')
        
        # Unicode絵文字除去
        unicode_emojis = distinct_emoji_list(cleaned)
        for emoji in unicode_emojis:
            cleaned = cleaned.replace(emoji, '')
        
        # 削除単語除去
        for word in self.delete_words:
            cleaned = cleaned.replace(word, '')
        
        # @ユーザー名除去
        cleaned = re.sub(r'@\S+', '', cleaned)
        
        # 複数スペースを単一スペースに
        cleaned = " ".join(cleaned.split())
        
        return cleaned.strip()
    
    def _extract_emotes(self, message: str, emotes_data: str) -> List[str]:
        """Twitchエモートを抽出"""
        emote_list = []
        
        if not emotes_data:
            return emote_list
        
        try:
            emotes_s = emotes_data.split('/')
            for emo in emotes_s:
                e_id, e_pos = emo.split(':')
                
                if ',' in e_pos:
                    positions = e_pos.split(',')
                    for pos in positions:
                        start, end = pos.split('-')
                        emote_text = message[int(start):int(end)+1]
                        emote_list.append(emote_text)
                else:
                    start, end = e_pos.split('-')
                    emote_text = message[int(start):int(end)+1]
                    emote_list.append(emote_text)
        except Exception as e:
            print(f"エモート抽出エラー: {e}")
        
        return emote_list

if TWITCHIO_AVAILABLE:
    class TwitchChatBot(commands.Bot):
        """Twitchチャット監視ボット"""
        
        def __init__(self, config: Dict[str, Any], message_callback: Callable[[ChatMessage], None]):
            # print("[DEBUG] TwitchChatBot.__init__ 開始")
            # print(f"[DEBUG] 引数の型: config={type(config)}, message_callback={type(message_callback)}")
            
            self.config = config
            self.message_callback = message_callback
            self.processor = MessageProcessor(config)
            self.translator = TranslationEngine(config)
            self.language_detector = LanguageDetector(config)
            self.database = TranslationDatabase()
            self.tts_engine = TTSEngine(config)
            self.is_running = False
        
            # 表示のみモードの場合はダミートークンを使用
            oauth_token = config.get("trans_oauth", "")
            if config.get("view_only_mode", False) and not oauth_token:
                oauth_token = "oauth:dummy_token_for_view_only_mode"
            
            # OAuthトークンの形式確認
            if oauth_token and not oauth_token.startswith("oauth:"):
                print(f"[WARNING] OAuthトークンの形式が正しくありません。'oauth:'で始まる必要があります。")
                oauth_token = f"oauth:{oauth_token}"
            
            # print(f"[DEBUG] OAuth token (先頭10文字): {oauth_token[:10] if oauth_token else 'None'}")
            
            # initial_channelsが空文字列の場合は空のリストに変換
            channels = []
            channel = config.get("twitch_channel", "").strip()
            if channel and channel != "":
                channels = [channel]
            
            # print(f"[DEBUG] channels: {channels}")
            # print("[DEBUG] super().__init__を呼び出します...")
            
            try:
                super().__init__(
                    token=oauth_token,
                    prefix="!",
                    initial_channels=channels
                )
                # print("[DEBUG] super().__init__が成功しました")
            except Exception as e:
                print(f"TwitchChatBot初期化エラー: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
    
        async def event_ready(self):
            """ボット起動時"""
            print(f"[INFO] チャットボット '{self.nick}' が起動しました")
            print(f"[INFO] ユーザーID: {self.user_id}")
            print(f"[INFO] 接続チャンネル: {list(self.connected_channels)}")
            self.is_running = True
            # TTSエンジンを開始
            self.tts_engine.start()
    
        async def event_channel_joined(self, channel):
            """チャンネル参加時"""
            print(f"チャンネル '{channel.name}' に参加しました")
            # 表示のみモードでない場合のみチャットに投稿
            if not self.config.get("view_only_mode", False):
                try:
                    color = self.config.get("trans_text_color", "GoldenRod")
                    await channel.send(f"/color {color}")
                    from .. import __version__
                    startup_message = f"twitchTFNeo v{__version__} by saatan / sayonari"
                    await channel.send(f"/me {startup_message}")
                except Exception as e:
                    print(f"チャンネル参加時メッセージ送信エラー: {e}")
            else:
                print(f"表示のみモードでチャンネル '{channel.name}' に参加しました")
    
        async def event_message(self, msg):
            """メッセージ受信時"""
            # msg.authorがNoneの場合をチェック
            if not msg.author:
                return
            
            # ボットが停止中の場合は処理しない
            if not self.is_running:
                return
                
            # Echo無視
            if msg.echo:
                return
            
            # コマンド処理
            await self.handle_commands(msg)
            
            # コマンドメッセージは翻訳処理しない
            if msg.content.startswith('!'):
                return
            
            await self._process_message(msg)
    
        async def _process_message(self, msg):
            """メッセージ処理"""
            # 再度停止状態を確認
            if not self.is_running:
                return
                
            username = msg.author.name
            original_content = msg.content
            timestamp = msg.timestamp.strftime("%H:%M:%S") if msg.timestamp else ""
            
            # ユーザーフィルター
            if self.processor.should_ignore_user(username):
                return
            
            # メッセージフィルター
            if self.processor.should_ignore_message(original_content):
                return
            
            # メッセージクリーニング
            emotes_data = msg.tags.get('emotes') if msg.tags else None
            cleaned_content = self.processor.clean_message(original_content, emotes_data)
            
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
            
            # チャットに投稿（表示のみモードでない場合）
            if not self.config.get("view_only_mode", False):
                await self._post_translation(msg.channel, chat_message)
    
        async def _post_translation(self, channel, chat_message: ChatMessage):
            """翻訳結果をチャットに投稿"""
            if not chat_message.translation:
                return
            
            output_text = chat_message.translation
            
            # 名前表示
            if self.config.get("show_by_name", True):
                output_text = f"{output_text} [by {chat_message.user}]"
            
            # 言語表示
            if self.config.get("show_by_lang", True):
                output_text = f"{output_text} ({chat_message.lang} > {chat_message.target_lang})"
            
            try:
                await channel.send(f"/me {output_text}")
            except Exception as e:
                print(f"チャット投稿エラー: {e}")
    
        def _add_tts_messages(self, chat_message: ChatMessage):
            """TTS読み上げメッセージを追加"""
            # TTSが無効の場合は何もしない
            if not self.config.get("tts_enabled", False):
                if self.config.get("debug", False):
                    print("TTS: Disabled in config")
                return
            
            if self.config.get("debug", False):
                print(f"TTS: Processing message from {chat_message.user}")
                print(f"TTS: tts_in={self.config.get('tts_in', False)}, tts_out={self.config.get('tts_out', False)}")
            
            # 言語制限チェック
            read_only_langs = self.config.get("read_only_these_lang", [])
            if read_only_langs and chat_message.lang not in read_only_langs:
                if self.config.get("debug", False):
                    print(f"TTS: Language {chat_message.lang} not in allowed list: {read_only_langs}")
                return
            
            # 入力TTS（絵文字除去済みのメッセージ）
            if self.config.get("tts_in", False) and chat_message.cleaned_content:
                tts_text = self._build_tts_text(chat_message, chat_message.cleaned_content, chat_message.lang, is_input=True)
                if tts_text:
                    if self.config.get("debug", False):
                        print(f"TTS: Adding input text to queue: {tts_text[:50]}...")
                    self.tts_engine.put(tts_text, chat_message.lang)
                elif self.config.get("debug", False):
                    print("TTS: No input text generated")
            
            # 出力TTS（翻訳されたメッセージ）
            if self.config.get("tts_out", False) and chat_message.translation:
                # 翻訳後のテキストからも絵文字を除去
                cleaned_translated = self._clean_text_for_tts(chat_message.translation)
                tts_text = self._build_tts_text(chat_message, cleaned_translated, chat_message.target_lang, is_input=False)
                if tts_text:
                    if self.config.get("debug", False):
                        print(f"TTS: Adding output text to queue: {tts_text[:50]}...")
                    self.tts_engine.put(tts_text, chat_message.target_lang)
                elif self.config.get("debug", False):
                    print("TTS: No output text generated")
    
        def _build_tts_text(self, chat_message: ChatMessage, content: str, lang: str, is_input: bool = True) -> str:
            """TTS用のテキストを構築"""
            parts = []
            
            # ユーザー名を読み上げ（入力/翻訳で分ける）
            if is_input:
                # 入力言語の場合
                if self.config.get("tts_read_username_input", self.config.get("tts_read_username", True)):
                    parts.append(chat_message.user)
            else:
                # 翻訳言語の場合
                if self.config.get("tts_read_username_output", self.config.get("tts_read_username", True)):
                    parts.append(chat_message.user)
            
            # 言語情報を読み上げ
            if self.config.get("tts_read_lang", False):
                parts.append(f"[{lang}]")
            
            # 内容を読み上げ
            if self.config.get("tts_read_content", True):
                # 最大文字数チェック
                max_length = self.config.get("tts_text_max_length", 30)
                if max_length > 0 and len(content) > max_length:
                    content = content[:max_length] + self.config.get("tts_message_for_omitting", "以下略")
                parts.append(content)
            
            return ", ".join(parts) if parts else ""
    
        def _clean_text_for_tts(self, text: str) -> str:
            """TTS用にテキストをクリーニング（絵文字除去など）"""
            cleaned = text
            
            # Unicode絵文字除去
            unicode_emojis = distinct_emoji_list(cleaned)
            for emoji in unicode_emojis:
                cleaned = cleaned.replace(emoji, '')
            
            # 削除単語除去
            for word in self.processor.delete_words:
                cleaned = cleaned.replace(word, '')
            
            # 複数スペースを単一スペースに
            cleaned = " ".join(cleaned.split())
            
            return cleaned.strip()
    
        @commands.command(name='ver')
        async def version_command(self, ctx):
            """バージョン表示コマンド"""
            from .. import __version__
            await ctx.send(f'twitchTFNeo v{__version__} by saatan/sayonari')
    
        def stop_bot(self):
            """ボット停止"""
            print(f"ボット停止開始: is_running={self.is_running}")
            self.is_running = False
            
            # TTSエンジンを停止
            if hasattr(self, 'tts_engine'):
                self.tts_engine.stop()
                print("TTS停止完了")
            
            # WebSocket接続を適切に閉じる
            try:
                print("WebSocket接続の停止を試行中...")
                
                # 現在のイベントループを取得
                try:
                    loop = asyncio.get_running_loop()
                    is_running = True
                except RuntimeError:
                    loop = None
                    is_running = False
                    print("イベントループが実行されていません")
                
                # TwitchIOの内部状態をチェック
                if hasattr(self, '_ws') and self._ws:
                    print("WebSocket接続が見つかりました、停止中...")
                    try:
                        if is_running:
                            asyncio.create_task(self._ws.close())
                        else:
                            # イベントループが実行されていない場合は直接クローズを試みる
                            if asyncio.iscoroutinefunction(self._ws.close):
                                pass  # コルーチンは実行できないのでスキップ
                    except:
                        pass
                
                if hasattr(self, '_connection') and self._connection:
                    print("内部接続オブジェクトが見つかりました、停止中...")
                    try:
                        if hasattr(self._connection, 'close'):
                            if is_running:
                                asyncio.create_task(self._connection.close())
                        elif hasattr(self._connection, '_websocket') and self._connection._websocket:
                            if is_running:
                                asyncio.create_task(self._connection._websocket.close())
                    except:
                        pass
                        
                # ボット自体を停止
                if hasattr(self, 'close'):
                    print("ボットクローズメソッド実行中...")
                    if is_running:
                        asyncio.create_task(self.close())
                
                # 強制的にイベントループから切り離し
                if hasattr(self, '_loop') and self._loop:
                    print("イベントループ停止中...")
                    try:
                        self._loop.call_soon_threadsafe(lambda: print("ループ停止シグナル送信"))
                    except:
                        pass
                        
            except Exception as e:
                print(f"ボット停止時のエラー: {e}")
            
            print(f"ボット停止完了: is_running={self.is_running}")
            
            # 完全に停止させるため、すべての内部状態をクリア
            try:
                self._ws = None
                self._connection = None
                if hasattr(self, 'user'):
                    self.user = None
            except:
                pass

class ChatMonitor:
    """チャット監視統合クラス"""
    
    def __init__(self, config: Dict[str, Any], message_callback: Callable[[ChatMessage], None]):
        self.config = config
        self.message_callback = message_callback
        self.bot: Optional[TwitchChatBot] = None
        self.is_running = False
    
    async def start(self) -> bool:
        """監視開始"""
        try:
            # print("[DEBUG] ChatMonitor.start() 開始")
            # print(f"[DEBUG] TWITCHIO_AVAILABLE: {TWITCHIO_AVAILABLE}")
            
            if not TWITCHIO_AVAILABLE:
                print("TwitchIOが利用できません。Twitch接続機能は無効です。")
                return False
            
            # チャンネル名を表示
            print(f"Twitchチャンネル: {self.config.get('twitch_channel')}")
            print(f"表示のみモード: {self.config.get('view_only_mode')}")
            
            self.bot = TwitchChatBot(self.config, self.message_callback)
            
            # 設定検証
            if not self.config.get("twitch_channel"):
                return False
            
            # 表示のみモードでない場合はOAuthトークンも必要
            if not self.config.get("view_only_mode", False) and not self.config.get("trans_oauth"):
                return False
            
            # 非同期でボット起動
            asyncio.create_task(self.bot.start())
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"チャット監視開始エラー: {e}")
            return False
    
    def stop(self):
        """監視停止"""
        try:
            print("チャット監視停止処理を開始...")
            self.is_running = False
            if self.bot:
                print("ボット停止中...")
                self.bot.stop_bot()
                # 確実にボットを停止させるため少し待機
                import time
                time.sleep(0.8)
                self.bot = None
                print("ボット停止完了")
        except Exception as e:
            print(f"監視停止エラー: {e}")
            # エラーが発生してもボットオブジェクトはクリア
            self.bot = None
        finally:
            self.is_running = False
            print("チャット監視停止処理完了")
    
    def update_config(self, new_config: Dict[str, Any]):
        """設定更新"""
        self.config.update(new_config)
        if self.bot:
            self.bot.config.update(new_config)
            self.bot.processor = MessageProcessor(new_config)
            self.bot.translator = TranslationEngine(new_config)
            self.bot.language_detector = LanguageDetector(new_config)
            # TTS設定も更新
            if hasattr(self.bot, 'tts_engine'):
                self.bot.tts_engine.update_config(new_config)