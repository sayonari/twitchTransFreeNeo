#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """設定管理クラス - JSONベースの設定システム"""
    
    def __init__(self, config_file: str = "config.json"):
        # 実行ファイルと同じディレクトリに設定ファイルを配置
        import sys
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた場合
            application_path = os.path.dirname(sys.executable)
        else:
            # 通常のPythonスクリプトとして実行された場合
            application_path = os.path.dirname(os.path.abspath(__file__))
            # プロジェクトルートに配置（2階層上）
            application_path = os.path.dirname(os.path.dirname(application_path))
        
        self.config_file = os.path.join(application_path, config_file)
        self.config = self._load_default_config()
        
        # 設定ファイルが存在しない場合、デフォルト設定で作成
        if not os.path.exists(self.config_file):
            print(f"設定ファイル {self.config_file} が見つかりません。デフォルト設定で作成します。")
            self.save_config()
        
        self.load_config()
    
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
            "tts_read_username": True,  # 互換性のため残す
            "tts_read_username_input": True,
            "tts_read_username_output": True,
            "tts_read_content": True,
            "tts_read_lang": False,
            "tts_kind": "gTTS",  # gTTS, CeVIO
            "cevio_cast": "さとうささら",
            "tts_text_max_length": 30,
            "tts_message_for_omitting": "以下略",
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
                    loaded_config = json.load(f)
                # デフォルト設定にマージ
                self.config.update(loaded_config)
                return True
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
        return False
    
    def save_config(self) -> bool:
        """設定ファイルを保存する"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
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