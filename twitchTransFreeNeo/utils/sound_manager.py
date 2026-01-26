#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
サウンド通知マネージャー
クロスプラットフォーム対応のサウンド再生機能
"""

import platform
import subprocess
import threading
from typing import Optional


class SoundManager:
    """サウンド通知を管理するクラス"""

    # サウンドタイプ
    SOUND_NEW_MESSAGE = "new_message"
    SOUND_TRANSLATION = "translation"
    SOUND_CONNECT = "connect"
    SOUND_DISCONNECT = "disconnect"
    SOUND_ERROR = "error"

    def __init__(self):
        self.enabled = False
        self.volume = 0.5  # 0.0 - 1.0
        self._system = platform.system()
        self._sound_thread: Optional[threading.Thread] = None

    def set_enabled(self, enabled: bool):
        """サウンド通知の有効/無効を設定"""
        self.enabled = enabled

    def set_volume(self, volume: float):
        """音量を設定 (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def play(self, sound_type: str = SOUND_NEW_MESSAGE):
        """サウンドを再生（非同期）"""
        if not self.enabled:
            return

        # 別スレッドで再生（UIをブロックしない）
        self._sound_thread = threading.Thread(
            target=self._play_sound,
            args=(sound_type,),
            daemon=True
        )
        self._sound_thread.start()

    def _play_sound(self, sound_type: str):
        """プラットフォーム別のサウンド再生"""
        try:
            if self._system == "Darwin":  # macOS
                self._play_macos(sound_type)
            elif self._system == "Windows":
                self._play_windows(sound_type)
            elif self._system == "Linux":
                self._play_linux(sound_type)
        except Exception as e:
            print(f"[WARNING] サウンド再生エラー: {e}")

    def _play_macos(self, sound_type: str):
        """macOSでサウンドを再生"""
        # macOS システムサウンドを使用
        sound_map = {
            self.SOUND_NEW_MESSAGE: "Ping",
            self.SOUND_TRANSLATION: "Pop",
            self.SOUND_CONNECT: "Glass",
            self.SOUND_DISCONNECT: "Basso",
            self.SOUND_ERROR: "Sosumi",
        }
        sound_name = sound_map.get(sound_type, "Ping")
        sound_path = f"/System/Library/Sounds/{sound_name}.aiff"

        # afplayコマンドで再生
        volume_arg = str(self.volume)
        subprocess.run(
            ["afplay", "-v", volume_arg, sound_path],
            capture_output=True,
            timeout=5
        )

    def _play_windows(self, sound_type: str):
        """Windowsでサウンドを再生"""
        try:
            import winsound

            # Windows システムサウンドを使用
            sound_map = {
                self.SOUND_NEW_MESSAGE: winsound.MB_OK,
                self.SOUND_TRANSLATION: winsound.MB_OK,
                self.SOUND_CONNECT: winsound.MB_OK,
                self.SOUND_DISCONNECT: winsound.MB_OK,
                self.SOUND_ERROR: winsound.MB_ICONHAND,
            }
            sound_flag = sound_map.get(sound_type, winsound.MB_OK)
            winsound.MessageBeep(sound_flag)
        except ImportError:
            # winsoundが使えない場合はベル音
            print("\a", end="", flush=True)

    def _play_linux(self, sound_type: str):
        """Linuxでサウンドを再生"""
        # paplayまたはaplayを試行
        try:
            # PulseAudioのpaplayを試す
            subprocess.run(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                capture_output=True,
                timeout=5
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            try:
                # ALSAのaplayを試す
                subprocess.run(
                    ["aplay", "-q", "/usr/share/sounds/alsa/Front_Center.wav"],
                    capture_output=True,
                    timeout=5
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # 最終手段：ベル音
                print("\a", end="", flush=True)

    def play_beep(self):
        """シンプルなビープ音を再生"""
        if not self.enabled:
            return

        threading.Thread(target=self._beep, daemon=True).start()

    def _beep(self):
        """ビープ音を再生"""
        try:
            if self._system == "Windows":
                import winsound
                winsound.Beep(800, 200)  # 800Hz, 200ms
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass


# グローバルインスタンス
_sound_manager: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    """サウンドマネージャーのシングルトンを取得"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager
