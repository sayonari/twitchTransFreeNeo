#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gtts import gTTS
from datetime import datetime
import time
import os
import queue
import threading
import platform
import sys
from typing import Dict, Any, Optional

# Check if we're on macOS
is_macos = platform.system() == 'Darwin'

# Import playsound with appropriate handling for macOS
try:
    from playsound import playsound
    playsound_available = True
except ImportError as e:
    playsound_available = False
    import_error = e

# Try to import pygame as alternative
try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False

# For macOS, try to import AppKit if needed
if is_macos:
    try:
        import AppKit
    except ImportError:
        # If we're in a PyInstaller bundle on macOS
        if getattr(sys, 'frozen', False):
            # Try to use afplay command line tool instead
            def playsound(sound_file, block=True):
                if not os.path.exists(sound_file):
                    print(f"Sound file not found: {sound_file}")
                    return
                
                cmd = f"afplay {sound_file}"
                if block:
                    os.system(cmd)
                else:
                    threading.Thread(target=os.system, args=(cmd,)).start()
            
            playsound_available = True

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
        
        # tmpディレクトリを作成（run.pyと同じ階層）
        # 実行ファイルがある場所から相対パスでtmpディレクトリを指定
        import sys
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた実行ファイルの場合
            base_dir = os.path.dirname(sys.executable)
        else:
            # 通常のPythonスクリプトの場合
            base_dir = os.getcwd()
        
        self.tmp_dir = os.path.join(base_dir, "tmp")
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        
        if self.config.get("debug", False):
            print(f"TTS tmp directory: {self.tmp_dir}")

    def put(self, text: str, lang: str):
        """TTS読み上げキューに追加"""
        if self.is_enabled():
            if self.config.get("debug", False):
                print(f"TTS Engine: Adding to queue - text='{text[:30]}...', lang={lang}")
                print(f"TTS Engine: Queue size before: {self.synth_queue.qsize()}")
            self.synth_queue.put([text, lang])
            if self.config.get("debug", False):
                print(f"TTS Engine: Queue size after: {self.synth_queue.qsize()}")
        else:
            if self.config.get("debug", False):
                print("TTS Engine: TTS is disabled, not adding to queue")

    def is_enabled(self) -> bool:
        """TTSが有効かどうかをチェック"""
        return self.config.get("tts_enabled", False)

    def start(self):
        """TTSスレッドを開始"""
        if self.is_enabled() and not self.is_running:
            print("TTS音声合成スレッドを開始します...")
            self.is_running = True
            self.thread_voice = threading.Thread(target=self.voice_synth, daemon=True)
            self.thread_voice.start()

    def stop(self):
        """TTSスレッドを停止"""
        if self.is_running:
            print("TTS音声合成スレッドを停止します...")
            self.is_running = False
            # 停止シグナルを送信
            self.synth_queue.put(None)

    def shorten_tts_comment(self, comment: str) -> str:
        """TTS向けのコメントをコンフィグに応じて短縮する"""
        maxlen = self.config.get("tts_text_max_length", 40)
        if maxlen == 0:
            return comment
        if len(comment) <= maxlen:
            return comment
        omit_message = self.config.get("tts_message_for_omitting", "...")
        return f"{comment[0:maxlen]} {omit_message}"

    def cevio_play(self, cast: str):
        """CeVIOを呼び出すための関数を生成する関数（Windows専用）"""
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
                    if self.config.get("debug", False): 
                        print(f"text '{text}' has dispatched to CeVIO.")
                    state.Wait()
                except Exception as e:
                    print('CeVIO error: TTS sound is not generated...')
                    if self.config.get("debug", False): 
                        print(e.args)
            return play
        except ImportError:
            print("CeVIO is not available on this platform")
            return self.gtts_play

    def gtts_play(self, text: str, lang: str):
        """gTTSを利用して音声合成・再生・削除を行う"""
        tts_file = None
        try:
            # 音声合成段階
            if self.config.get("debug", False):
                print(f"TTS: Starting synthesis for text='{text}', lang='{lang}'")
            
            tts = gTTS(text, lang=lang)
            tts_file = os.path.join(self.tmp_dir, f'cnt_{datetime.now().microsecond}.mp3')
            
            if self.config.get("debug", False): 
                print(f'TTS: Saving to file: {tts_file}')
            
            tts.save(tts_file)
            
            # ファイルが正常に作成されたかチェック
            if not os.path.exists(tts_file):
                print(f"TTS error: File was not created: {tts_file}")
                return
                
            file_size = os.path.getsize(tts_file)
            if self.config.get("debug", False):
                print(f"TTS: File created successfully: {tts_file} (size: {file_size} bytes)")
            
            if file_size == 0:
                print(f"TTS error: Empty file created: {tts_file}")
                return
            
            # 音声再生段階 - プラットフォーム別に最適な方法を選択
            play_success = False
            
            # macOSでは最初からafplayを使用（playsoundは不安定）
            if is_macos:
                try:
                    # デバッグ情報を強化
                    print(f"TTS: Using afplay for macOS")
                    print(f"TTS: File path: {tts_file}")
                    print(f"TTS: File exists: {os.path.exists(tts_file)}")
                    if os.path.exists(tts_file):
                        print(f"TTS: File size: {os.path.getsize(tts_file)} bytes")
                        # 絶対パスを使用
                        abs_path = os.path.abspath(tts_file)
                        print(f"TTS: Absolute path: {abs_path}")
                        
                        # subprocessを使用してより詳細なエラー情報を取得
                        import subprocess
                        try:
                            result = subprocess.run(['afplay', abs_path], 
                                                  capture_output=True, 
                                                  text=True, 
                                                  timeout=10)
                            if result.returncode == 0:
                                play_success = True
                                print("TTS: afplay completed successfully")
                            else:
                                print(f"TTS warning: afplay failed with code {result.returncode}")
                                if result.stderr:
                                    print(f"TTS stderr: {result.stderr}")
                        except subprocess.TimeoutExpired:
                            print("TTS error: afplay timeout")
                        except FileNotFoundError:
                            print("TTS error: afplay command not found")
                            # フォールバック: os.systemを試す
                            result = os.system(f"afplay '{abs_path}'")
                            if result == 0:
                                play_success = True
                    else:
                        print(f"TTS error: File does not exist: {tts_file}")
                except Exception as afplay_error:
                    print(f'TTS afplay error: {afplay_error}')
                    import traceback
                    traceback.print_exc()
            
            # Method 1: pygame (高い優先度、クロスプラットフォーム対応)
            if pygame_available and not play_success:
                try:
                    if self.config.get("debug", False):
                        print(f"TTS: Attempting pygame: {tts_file}")
                    pygame.mixer.init()
                    pygame.mixer.music.load(tts_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    pygame.mixer.quit()
                    if self.config.get("debug", False):
                        print("TTS: Pygame completed successfully")
                    play_success = True
                except Exception as play_error:
                    print(f'TTS pygame error: {play_error}')
                    if self.config.get("debug", False):
                        import traceback
                        traceback.print_exc()
                    try:
                        pygame.mixer.quit()
                    except:
                        pass
            
            # Method 2: playsound (macOS以外で試行)
            if playsound_available and not play_success and not is_macos:
                try:
                    if self.config.get("debug", False):
                        print(f"TTS: Attempting playsound: {tts_file}")
                    playsound(tts_file, True)
                    if self.config.get("debug", False):
                        print("TTS: Playsound completed successfully")
                    play_success = True
                except Exception as play_error:
                    print(f'TTS playsound error: {play_error}')
                    if self.config.get("debug", False):
                        import traceback
                        traceback.print_exc()
            
            # Method 3: Other system-specific commands
            if not play_success:
                try:
                    if platform.system() == 'Windows':
                        if self.config.get("debug", False):
                            print(f"TTS: Attempting Windows winsound: {tts_file}")
                        import winsound
                        winsound.PlaySound(tts_file, winsound.SND_FILENAME)
                        play_success = True
                    elif platform.system() == 'Darwin':  # macOS
                        if self.config.get("debug", False):
                            print(f"TTS: Attempting macOS afplay: {tts_file}")
                        result = os.system(f"afplay '{tts_file}'")
                        if result == 0:
                            play_success = True
                            if self.config.get("debug", False):
                                print("TTS: afplay completed successfully")
                        else:
                            print(f"TTS warning: macOS afplay failed with code {result}")
                    elif platform.system() == 'Linux':
                        if self.config.get("debug", False):
                            print(f"TTS: Attempting Linux audio commands: {tts_file}")
                        # Try aplay first, then paplay
                        result = os.system(f"aplay '{tts_file}' 2>/dev/null")
                        if result != 0:
                            result = os.system(f"paplay '{tts_file}' 2>/dev/null")
                        if result == 0:
                            play_success = True
                        else:
                            print(f"TTS warning: Linux audio commands failed")
                except Exception as sys_error:
                    print(f'TTS system playback error: {sys_error}')
                    if self.config.get("debug", False):
                        import traceback
                        traceback.print_exc()
            
            if not play_success:
                print('TTS error: All playback methods failed')
                if not pygame_available:
                    print("TTS info: pygame not available (recommended: pip install pygame)")
                if not playsound_available and not is_macos:
                    print(f"TTS info: playsound not available - {import_error}")
            
        except Exception as synthesis_error:
            print(f'TTS synthesis error: {synthesis_error}')
            if self.config.get("debug", False):
                import traceback
                traceback.print_exc()
        
        finally:
            # ファイル削除（必ず実行）
            if tts_file and os.path.exists(tts_file):
                try:
                    os.remove(tts_file)
                    if self.config.get("debug", False):
                        print(f"TTS: File deleted successfully: {tts_file}")
                except Exception as delete_error:
                    print(f"TTS file deletion error: {delete_error}")

    def determine_tts(self):
        """どのTextToSpeechを利用するかをconfigから選択して再生用の関数を返す"""
        kind = self.config.get("tts_kind", "gTTS").strip().upper()
        if kind == "CEVIO" and platform.system() == 'Windows':
            cast = self.config.get("cevio_cast", "さとうささら")
            return self.cevio_play(cast)
        else:
            return self.gtts_play

    def voice_synth(self):
        """音声合成(TTS)の待ち受けスレッド"""
        tts_func = self.determine_tts()
        
        while self.is_running:
            try:
                q = self.synth_queue.get(timeout=1)
                if q is None:  # 停止シグナル
                    break
                    
                text = q[0]
                lang = q[1]

                if self.config.get("debug", False): 
                    print(f'TTS Debug: text="{text}", lang="{lang}"')

                # 読み上げ対象言語のフィルタリング
                read_only_langs = self.config.get("read_only_these_lang", [])
                if read_only_langs and lang not in read_only_langs:
                    if self.config.get("debug", False): 
                        print(f'TTS Skip: language "{lang}" not in read_only_these_lang')
                    continue

                # テキストを短縮
                text = self.shorten_tts_comment(text)
                
                # 音声合成実行
                tts_func(text, lang)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS thread error: {e}")
                if self.config.get("debug", False):
                    import traceback
                    traceback.print_exc()
        
        print("TTS音声合成スレッドが終了しました")

    def update_config(self, new_config: Dict[str, Any]):
        """設定を更新"""
        self.config.update(new_config)
        
        # TTS有効/無効が変わった場合の処理
        if self.is_enabled() and not self.is_running:
            self.start()
        elif not self.is_enabled() and self.is_running:
            self.stop()