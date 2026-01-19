#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gtts import gTTS
from datetime import datetime
import time
import os
import queue
import threading
import platform
import subprocess
import sys
from typing import Dict, Any, Optional

# プラットフォーム検出
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# PyInstallerバイナリ実行時の検出
IS_FROZEN = getattr(sys, 'frozen', False)

# pygame利用可能チェック
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class TTSEngine:
    """
    TTS(Text To Speech)を取り扱うクラス
    putされた文面をスレッドで処理し、
    必要な加工を施した上で適切なタイミングで読み上げる
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.synth_queue = queue.Queue()
        self.is_running = False
        self.thread_voice: Optional[threading.Thread] = None
        self.tmp_dir = self._setup_tmp_dir()

    def _setup_tmp_dir(self) -> str:
        """一時ディレクトリを設定"""
        if IS_FROZEN:
            # ビルドされた実行ファイルの場合はユーザーホームディレクトリを使用
            # （macOSのApp Translocation対策）
            home_dir = os.path.expanduser("~")
            tmp_dir = os.path.join(home_dir, ".twitchTransFreeNeo", "tmp")
        else:
            # 開発環境ではプロジェクトディレクトリのtmpを使用
            tmp_dir = os.path.join(os.getcwd(), "tmp")

        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    def put(self, text: str, lang: str):
        """TTS読み上げキューに追加"""
        if self.is_enabled():
            self.synth_queue.put([text, lang])

    def is_enabled(self) -> bool:
        """TTSが有効かどうかをチェック"""
        return self.config.get("tts_enabled", False)

    def start(self):
        """TTSスレッドを開始"""
        if self.is_enabled() and not self.is_running:
            self.is_running = True
            self.thread_voice = threading.Thread(target=self.voice_synth, daemon=True)
            self.thread_voice.start()

    def stop(self):
        """TTSスレッドを停止"""
        if self.is_running:
            self.is_running = False
            self.synth_queue.put(None)  # 停止シグナル

    def shorten_tts_comment(self, comment: str) -> str:
        """TTS向けのコメントをコンフィグに応じて短縮する"""
        maxlen = self.config.get("tts_text_max_length", 40)
        if maxlen == 0 or len(comment) <= maxlen:
            return comment
        omit_message = self.config.get("tts_message_for_omitting", "...")
        return f"{comment[:maxlen]} {omit_message}"

    def cevio_play(self, cast: str):
        """CeVIOを呼び出すための関数を生成（Windows専用）"""
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            cevio = win32com.client.Dispatch("CeVIO.Talk.RemoteService2.ServiceControl2")
            cevio.StartHost(False)
            talker = win32com.client.Dispatch("CeVIO.Talk.RemoteService2.Talker2V40")
            talker.Cast = cast

            def play(text, _):
                try:
                    state = talker.Speak(text)
                    state.Wait()
                except Exception as e:
                    print(f'CeVIO error: {e}')
            return play
        except ImportError:
            print("CeVIO is not available on this platform")
            return self.gtts_play

    def gtts_play(self, text: str, lang: str):
        """gTTSを利用して音声合成・再生・削除を行う"""
        tts_file = None
        try:
            # 音声合成
            tts_file = self._synthesize_audio(text, lang)
            if not tts_file:
                return

            # 音声再生
            self._play_audio(tts_file)

        except Exception as e:
            print(f'TTS synthesis error: {e}')
        finally:
            self._cleanup_file(tts_file)

    def _synthesize_audio(self, text: str, lang: str) -> Optional[str]:
        """gTTSで音声ファイルを生成"""
        tts = gTTS(text, lang=lang)
        tts_file = os.path.join(self.tmp_dir, f'tts_{datetime.now().microsecond}.mp3')
        tts.save(tts_file)

        if not os.path.exists(tts_file) or os.path.getsize(tts_file) == 0:
            print(f"TTS error: Failed to create audio file")
            return None
        return tts_file

    def _play_audio(self, tts_file: str) -> bool:
        """プラットフォーム別に音声を再生"""
        # macOS: afplayを優先
        if IS_MACOS:
            if self._play_with_afplay(tts_file):
                return True

        # pygame（クロスプラットフォーム）
        if PYGAME_AVAILABLE:
            if self._play_with_pygame(tts_file):
                return True

        # Windows: winsound
        if IS_WINDOWS:
            if self._play_on_windows(tts_file):
                return True

        # Linux: aplay/paplay
        if IS_LINUX:
            if self._play_on_linux(tts_file):
                return True

        print('TTS error: All playback methods failed')
        return False

    def _play_with_afplay(self, tts_file: str) -> bool:
        """macOSのafplayで再生"""
        try:
            abs_path = os.path.abspath(tts_file)
            result = subprocess.run(
                ['afplay', abs_path],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def _play_with_pygame(self, tts_file: str) -> bool:
        """pygameで再生"""
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(tts_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.quit()
            return True
        except Exception:
            try:
                pygame.mixer.quit()
            except:
                pass
            return False

    def _play_on_windows(self, tts_file: str) -> bool:
        """Windowsのwinsoundで再生"""
        try:
            import winsound
            winsound.PlaySound(tts_file, winsound.SND_FILENAME)
            return True
        except Exception:
            return False

    def _play_on_linux(self, tts_file: str) -> bool:
        """Linuxのaplay/paplayで再生"""
        try:
            result = os.system(f"aplay '{tts_file}' 2>/dev/null")
            if result != 0:
                result = os.system(f"paplay '{tts_file}' 2>/dev/null")
            return result == 0
        except Exception:
            return False

    def _cleanup_file(self, tts_file: Optional[str]):
        """一時ファイルを削除"""
        if tts_file and os.path.exists(tts_file):
            try:
                os.remove(tts_file)
            except Exception:
                pass

    def determine_tts(self):
        """どのTextToSpeechを利用するかをconfigから選択して再生用の関数を返す"""
        kind = self.config.get("tts_kind", "gTTS").strip().upper()
        if kind == "CEVIO" and IS_WINDOWS:
            cast = self.config.get("cevio_cast", "さとうささら")
            return self.cevio_play(cast)
        return self.gtts_play

    def voice_synth(self):
        """音声合成(TTS)の待ち受けスレッド"""
        tts_func = self.determine_tts()

        while self.is_running:
            try:
                q = self.synth_queue.get(timeout=1)
                if q is None:  # 停止シグナル
                    break

                text, lang = q[0], q[1]

                # 読み上げ対象言語のフィルタリング
                read_only_langs = self.config.get("read_only_these_lang", [])
                if read_only_langs and lang not in read_only_langs:
                    continue

                # テキストを短縮して音声合成実行
                text = self.shorten_tts_comment(text)
                tts_func(text, lang)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS thread error: {e}")

    def update_config(self, new_config: Dict[str, Any]):
        """設定を更新"""
        self.config.update(new_config)

        if self.is_enabled() and not self.is_running:
            self.start()
        elif not self.is_enabled() and self.is_running:
            self.stop()
