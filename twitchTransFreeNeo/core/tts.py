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
            # （os.getcwd() だと起動場所によって書き込めない場所を指すことがある）
            try:
                from ..utils.config_manager import get_application_path
                tmp_dir = os.path.join(get_application_path(), "tmp")
            except Exception:
                tmp_dir = os.path.join(os.getcwd(), "tmp")

        try:
            os.makedirs(tmp_dir, exist_ok=True)
        except OSError:
            # 書き込めない場合はホーム配下へ退避
            tmp_dir = os.path.join(os.path.expanduser("~"), ".twitchTransFreeNeo", "tmp")
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
            # 未読み上げのメッセージを破棄する
            # （残したままだと次回開始時に古い発言が読み上げられる）
            self._drain_queue()
            self.synth_queue.put(None)  # 停止シグナル

    def _drain_queue(self):
        """読み上げ待ちキューを空にする"""
        while True:
            try:
                self.synth_queue.get_nowait()
            except queue.Empty:
                break

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

            # 音声再生（長い発言は自動で速める）
            self._play_audio(tts_file, self.effective_speed(text))

        except Exception as e:
            print(f'TTS synthesis error: {e}')
        finally:
            self._cleanup_file(tts_file)

    # Google 翻訳と gTTS で異なる言語コードの対応表
    # （翻訳側のコードをそのまま渡すと gTTS が対応しておらず読み上げに失敗する）
    _GTTS_LANG_MAP = {
        'iw': 'he',      # ヘブライ語（翻訳APIは旧コード iw を返す）
        'jw': 'jv',      # ジャワ語
        'zh': 'zh-CN',
        'zh-cn': 'zh-CN',
        'zh-tw': 'zh-TW',
        'ma': 'mr',      # マラーティー語
        'in': 'id',      # インドネシア語（旧コード）
    }

    def _to_gtts_lang(self, lang: str) -> str:
        """翻訳側の言語コードを gTTS 用に変換"""
        if not lang:
            return 'en'
        mapped = self._GTTS_LANG_MAP.get(lang.lower())
        if mapped:
            return mapped
        # 地域バリアント（pt-BR など）は gTTS が解釈できる基底コードへ
        if '-' in lang and lang.lower() not in ('zh-cn', 'zh-tw'):
            return lang.split('-')[0]
        return lang

    # 読み上げ速度の下限・上限
    # 上限は聞き取りやすさを確認したうえで 2.5 とした
    # （それ以上も明瞭に再生できるが，実用的な範囲で頭打ちにする）
    MIN_SPEED, MAX_SPEED = 0.5, 2.5
    DEFAULT_SPEED = 1.4       # gTTS の読み上げは遅いため、既定を少し速めにする
    # 長文を自動で速める際の基準
    AUTO_SPEED_FROM = 30      # この文字数までは基準速度のまま
    AUTO_SPEED_FULL = 90      # この文字数で加速が最大になる
    AUTO_SPEED_GAIN = 0.5     # 基準速度の何割増しまで上げるか

    def playback_speed(self) -> float:
        """設定された読み上げ速度（1.0＝等速）"""
        try:
            speed = float(self.config.get("tts_speed", self.DEFAULT_SPEED))
        except (TypeError, ValueError):
            speed = 1.0
        return max(self.MIN_SPEED, min(speed, self.MAX_SPEED))

    def effective_speed(self, text: str) -> float:
        """実際に使う速度（長い発言は自動で速める）

        長文をそのままの速度で読むと読み上げが延々と続き，
        次のコメントに追いつかなくなるため
        """
        base = self.playback_speed()
        if not self.config.get("tts_auto_speed", True):
            return base

        length = len(text or "")
        if length <= self.AUTO_SPEED_FROM:
            return base

        span = max(self.AUTO_SPEED_FULL - self.AUTO_SPEED_FROM, 1)
        ratio = min((length - self.AUTO_SPEED_FROM) / span, 1.0)
        # 基準速度を速めに設定している人でも上限を超えないよう頭打ちにする
        return min(base * (1.0 + ratio * self.AUTO_SPEED_GAIN), self.MAX_SPEED)

    @staticmethod
    def _stretch_samples(samples, speed: float):
        """再生速度だけを変える（音の高さは変えない・WSOLA）

        重ね合わせる位置を相互相関で選ぶことで、継ぎ目の雑音を抑える。
        追加のソフトを入れなくても動くよう numpy だけで完結させている
        """
        import numpy as np

        if abs(speed - 1.0) < 0.01:
            return samples

        mono = samples.ndim == 1
        x = (samples[:, None] if mono else samples).astype(np.float32)
        n, ch = x.shape

        frame = 1024
        search = 256
        hop_syn = frame // 2
        hop_ana = int(round(hop_syn * speed))
        window = np.hanning(frame).astype(np.float32)[:, None]

        out = np.zeros((int(n / speed) + frame * 2, ch), dtype=np.float32)
        weight = np.zeros((out.shape[0], 1), dtype=np.float32)

        pos_ana = pos_syn = 0
        prev_tail = None
        while pos_ana + frame + search < n and pos_syn + frame < out.shape[0]:
            if prev_tail is None:
                best = pos_ana
            else:
                lo = max(0, pos_ana - search)
                hi = min(n - frame, pos_ana + search)
                ref = prev_tail[:, 0]
                candidates = np.arange(lo, hi, 32)
                scores = [
                    float(np.dot(x[c:c + len(ref), 0], ref))
                    for c in candidates if c + frame <= n
                ]
                best = int(candidates[int(np.argmax(scores))]) if scores else pos_ana

            out[pos_syn:pos_syn + frame] += x[best:best + frame] * window
            weight[pos_syn:pos_syn + frame] += window
            prev_tail = x[best + hop_syn:best + hop_syn + hop_syn]
            pos_ana = best + hop_ana
            pos_syn += hop_syn

        weight[weight < 1e-6] = 1.0
        result = np.clip(out / weight, -32768, 32767).astype(np.int16)
        result = result[:pos_syn + frame]
        return result[:, 0] if mono else result

    def _synthesize_audio(self, text: str, lang: str) -> Optional[str]:
        """gTTSで音声ファイルを生成"""
        gtts_lang = self._to_gtts_lang(lang)
        try:
            tts = gTTS(text, lang=gtts_lang)
        except Exception as e:
            # 未対応言語などはここで弾かれる。読み上げを諦めて次へ進む
            print(f"TTS error: 言語 '{lang}' (gTTS: '{gtts_lang}') は読み上げできません: {e}")
            return None

        # 同じマイクロ秒での衝突を避けるため連番を併用する
        self._file_seq = getattr(self, '_file_seq', 0) + 1
        tts_file = os.path.join(
            self.tmp_dir,
            f'tts_{datetime.now().strftime("%H%M%S%f")}_{self._file_seq}.mp3'
        )
        tts.save(tts_file)

        if not os.path.exists(tts_file) or os.path.getsize(tts_file) == 0:
            print(f"TTS error: Failed to create audio file")
            return None
        return tts_file

    def _play_audio(self, tts_file: str, speed: float = 1.0) -> bool:
        """プラットフォーム別に音声を再生"""
        # 速度指定があるときは、まず numpy で作り直して再生する
        # （追加のソフトを入れなくても全OSで同じように動く）
        if abs(speed - 1.0) > 0.01 and PYGAME_AVAILABLE:
            if self._play_stretched(tts_file, speed):
                return True

        # macOS: afplay（速度指定にも対応している）
        if IS_MACOS:
            if self._play_with_afplay(tts_file, speed):
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

    def _play_stretched(self, tts_file: str, speed: float) -> bool:
        """速度を変えた音声を組み立てて再生する"""
        try:
            import numpy as np
            import pygame.sndarray

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            source = pygame.mixer.Sound(tts_file)
            samples = pygame.sndarray.array(source)
            stretched = self._stretch_samples(samples, speed)
            sound = pygame.sndarray.make_sound(np.ascontiguousarray(stretched))

            sound.play()
            while pygame.mixer.get_busy():
                time.sleep(0.05)
            return True
        except Exception as e:
            if not TTSEngine._speed_warned:
                TTSEngine._speed_warned = True
                print(f"TTS: 速度変更に失敗したため通常速度で再生します: {e}")
            return False

    def _play_with_afplay(self, tts_file: str, speed: float = 1.0) -> bool:
        """macOSのafplayで再生（-r で読み上げ速度を指定できる）"""
        try:
            abs_path = os.path.abspath(tts_file)
            args = ['afplay']
            if abs(speed - 1.0) > 0.01:
                # -q 1 は速度変更時の品質を上げる指定
                args += ['-r', f'{speed:.2f}', '-q', '1']
            args.append(abs_path)
            result = subprocess.run(args, capture_output=True, timeout=60)
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

                # 本文の短縮は呼び出し元（_build_tts_text / _format_tts_text）で
                # 済んでいるため，ここでは再短縮しない
                # （以前は二重に適用され，ユーザー名を含めた全体が切られていた）
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
