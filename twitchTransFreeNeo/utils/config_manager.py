#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
from typing import Dict, Any, Optional


def _is_writable(path: str) -> bool:
    """ディレクトリが書き込み可能かチェック"""
    try:
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except (IOError, OSError, PermissionError):
        return False


def get_user_data_dir() -> str:
    """ユーザーデータディレクトリを取得（クロスプラットフォーム対応）"""
    app_name = "twitchTransFreeNeo"

    if sys.platform == "win32":
        # Windows: %APPDATA%\twitchTransFreeNeo
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(base, app_name)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/twitchTransFreeNeo
        data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:
        # Linux: ~/.config/twitchTransFreeNeo
        base = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
        data_dir = os.path.join(base, app_name)

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_application_path() -> str:
    """設定・データベースを置くディレクトリを取得（バイナリ/スクリプト両対応）

    設定ファイルとデータベースを必ず同じ場所に置くため，モジュール関数として公開する
    （以前はデータベースだけ相対パスでカレントディレクトリに作られており，
      .app 起動時などに書き込めずキャッシュが機能していなかった）
    """
    if getattr(sys, 'frozen', False) or hasattr(sys, '__compiled__'):
        # Nuitkaまたはその他のバイナリ実行時
        # sys.argv[0] は実行ファイルへのパス
        exe_path = os.path.abspath(sys.argv[0])

        # Windows onefileモード対策: 実際のexeファイルの場所を使用
        # （一時ディレクトリではなく、ユーザーがexeを配置した場所）
        application_path = os.path.dirname(exe_path)

        # 書き込み不可の場合はユーザーのアプリデータディレクトリを使用
        if not _is_writable(application_path):
            application_path = get_user_data_dir()
            print(f"警告: 実行ディレクトリに書き込めません。データを {application_path} に保存します。")
    else:
        # 通常のPythonスクリプトとして実行された場合はプロジェクトルート（2階層上）
        application_path = os.path.dirname(os.path.abspath(__file__))
        application_path = os.path.dirname(os.path.dirname(application_path))

    return application_path


class ConfigManager:
    """設定管理クラス - JSONベースの設定システム"""

    def __init__(self, config_file: str = "config.json"):
        # 実行ファイルと同じディレクトリに設定ファイルを配置
        application_path = self._get_application_path()

        self.config_file = os.path.join(application_path, config_file)
        print(f"設定ファイルパス: {self.config_file}")

        self.config = self._load_default_config()

        # 設定ファイルが存在しない場合、デフォルト設定で作成
        if not os.path.exists(self.config_file):
            print(f"設定ファイル {self.config_file} が見つかりません。デフォルト設定で作成します。")
            self.save_config()

        self.load_config()

    def _get_application_path(self) -> str:
        """アプリケーションの実行パスを取得（バイナリ/スクリプト両対応）"""
        return get_application_path()

    def _is_writable(self, path: str) -> bool:
        """ディレクトリが書き込み可能かチェック"""
        return _is_writable(path)

    def _get_user_data_dir(self) -> str:
        """ユーザーデータディレクトリを取得（クロスプラットフォーム対応）"""
        return get_user_data_dir()

    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            # 必須設定
            "twitch_channel": "",
            "trans_username": "",
            "trans_oauth": "",
            
            # 基本設定
            "trans_text_color": "GoldenRod",
            "lang_trans_to_home": "ja",
            "lang_home_to_other": "en",
            "trans_to_home_only": False,  # True: 外国語→母語の一方向のみ翻訳（ボット向け）
            "show_by_name": True,
            "show_by_lang": True,
            
            # 翻訳エンジン設定
            "translator": "google",  # google, deepl
            "gas_url": "",
            "google_translate_suffix": "co.jp",
            
            # フィルタリング設定
            "ignore_lang": [],
            "ignore_users": ["Nightbot", "BikuBikuTest"],
            "ignore_line": ["http", "BikuBikuTest", "888", "８８８"],
            "ignore_www": ["w", "ｗ", "W", "Ｗ", "ww", "ｗｗ", "WW", "ＷＷ", "www", "ｗｗｗ", "WWW", "ＷＷＷ", "草"],
            "delete_words": [],
            
            # TTS設定
            "tts_enabled": False,
            "tts_in": True,
            "tts_out": True,
            "tts_read_username": False,  # 互換性のため残す
            "tts_read_username_input": False,
            "tts_read_username_output": False,
            "tts_read_content": True,
            "tts_read_lang": False,
            "tts_kind": "gTTS",  # gTTS, CeVIO
            "tts_speed": 1.4,        # 読み上げ速度（0.5〜2.5、1.0で等速）
            "tts_auto_speed": True,  # 長い発言を自動で速く読む
            "cevio_cast": "さとうささら",
            "tts_text_max_length": 50,
            "tts_message_for_omitting": "",
            "read_only_these_lang": [],
            
            # GUI設定
            "window_width": 1200,
            "window_height": 800,
            "theme": "light",  # light, dark
            "font_size": 12,
            
            # その他
            "view_only_mode": False,
            "debug": False,
            "auto_start": False
        }
    
    def load_config(self) -> bool:
        """設定ファイルを読み込む"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    loaded_config = json.loads(content)
                except json.JSONDecodeError as je:
                    # JSON形式エラー - 末尾カンマなどを修正して再試行
                    print(f"JSON形式エラー（修正を試みます）: {je}")
                    fixed_content = self._fix_json_content(content)
                    try:
                        loaded_config = json.loads(fixed_content)
                        print("JSON修正成功 - 修正後の設定を保存します")
                        # 修正後の設定を保存
                        self.config.update(loaded_config)
                        self.save_config()
                        return True
                    except json.JSONDecodeError:
                        print("JSON修正失敗 - デフォルト設定を使用します")
                        return False

                # 設定値の検証・修正（旧バージョンとの互換性）
                loaded_config = self._validate_and_fix_config(loaded_config)

                # デフォルト設定にマージ
                self.config.update(loaded_config)
                return True
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
        return False

    def _fix_json_content(self, content: str) -> str:
        """JSONコンテンツの一般的なエラーを修正"""
        import re

        # 末尾カンマを削除（オブジェクト内）
        # パターン: , の後に空白・改行があり、その後に } または ] がある
        content = re.sub(r',(\s*[}\]])', r'\1', content)

        return content

    def _validate_and_fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """設定値を検証し、無効な値を修正（旧バージョン互換性）"""
        # フォントサイズの範囲チェック (10-24)
        if "tts_speed" in config:
            try:
                speed = float(config["tts_speed"])
            except (TypeError, ValueError):
                speed = 1.0
            if not (0.5 <= speed <= 2.5):
                speed = min(max(speed, 0.5), 2.5)
                print(f"読み上げ速度を有効範囲に補正しました（{config['tts_speed']} → {speed}）")
            config["tts_speed"] = speed

        if "font_size" in config:
            font_size = config["font_size"]
            if not isinstance(font_size, (int, float)) or font_size < 10:
                config["font_size"] = 10
                print(f"フォントサイズを最小値(10)に修正しました（元の値: {font_size}）")
            elif font_size > 24:
                config["font_size"] = 24
                print(f"フォントサイズを最大値(24)に修正しました（元の値: {font_size}）")

        # ウィンドウサイズの範囲チェック
        if "window_width" in config:
            if not isinstance(config["window_width"], int) or config["window_width"] < 800:
                config["window_width"] = 1200
        if "window_height" in config:
            if not isinstance(config["window_height"], int) or config["window_height"] < 600:
                config["window_height"] = 800

        return config
    
    def save_config(self) -> bool:
        """設定ファイルを保存する

        直接上書きすると、書き込み中にアプリが終了した場合に
        設定ファイルが壊れてトークンごと失われる。
        一時ファイルへ書いてから置き換えることで、
        途中で中断されても元のファイルが残るようにする
        """
        tmp_path = f"{self.config_file}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # 認証情報を含むため、本人だけが読める権限にする
            try:
                os.chmod(tmp_path, 0o600)
            except OSError:
                pass

            os.replace(tmp_path, self.config_file)  # 置き換えは不可分に行われる
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """設定値を設定"""
        self.config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """全設定を取得"""
        return self.config.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """設定を一括更新"""
        self.config.update(updates)
    
    def reset_to_default(self) -> None:
        """設定をデフォルトにリセット"""
        self.config = self._load_default_config()
    
    def is_valid_config(self) -> tuple[bool, list[str]]:
        """設定の妥当性をチェック"""
        errors = []
        
        # 必須項目チェック（表示のみモードでも最低限必要）
        if not self.get("twitch_channel"):
            errors.append("必須項目が未設定: twitch_channel")
        
        # 表示のみモードでない場合の追加チェック
        if not self.get("view_only_mode", False):
            if not self.get("trans_username"):
                errors.append("必須項目が未設定: trans_username")
            if not self.get("trans_oauth"):
                errors.append("必須項目が未設定: trans_oauth")
        
        # 翻訳エンジンチェック
        if self.get("translator") not in ["google", "deepl"]:
            errors.append("翻訳エンジンは 'google' または 'deepl' を指定してください")
        
        # TTSチェック
        if self.get("tts_kind") not in ["gTTS", "CeVIO"]:
            errors.append("TTS種類は 'gTTS' または 'CeVIO' を指定してください")
        
        return len(errors) == 0, errors