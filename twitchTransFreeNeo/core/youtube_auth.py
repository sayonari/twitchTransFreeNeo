#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube OAuth認証ヘルパー
YouTube Data API v3 の OAuth 2.0 認証を管理
"""

import os
import json
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Google OAuth ライブラリ
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    print("警告: Google認証ライブラリが利用できません。YouTube投稿機能は無効になります。")


# YouTube Data API v3 のスコープ
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl',
]

# OAuth クライアント設定テンプレート
# ユーザーは自分の client_id と client_secret を設定する必要がある
CLIENT_CONFIG_TEMPLATE = {
    "installed": {
        "client_id": "",
        "client_secret": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
    }
}


class YouTubeAuthManager:
    """YouTube OAuth認証マネージャー"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.credentials: Optional[Credentials] = None
        self.youtube_service = None
        self._token_path = self._get_token_path()

    def _get_token_path(self) -> Path:
        """トークン保存パスを取得"""
        # 設定ファイルと同じ場所に保存
        try:
            from ..utils.config_manager import ConfigManager
            config_dir = ConfigManager()._get_config_dir()
        except:
            config_dir = Path.home() / ".twitchTransFreeNeo"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "youtube_token.json"

    def has_credentials(self) -> bool:
        """認証情報があるかチェック"""
        client_id = self.config.get("youtube_client_id", "")
        client_secret = self.config.get("youtube_client_secret", "")
        return bool(client_id and client_secret)

    def is_authenticated(self) -> bool:
        """認証済みかチェック"""
        if not self.has_credentials():
            return False

        # トークンファイルが存在するかチェック
        if not self._token_path.exists():
            return False

        # トークンを読み込んで有効性をチェック
        try:
            self._load_credentials()
            return self.credentials is not None and self.credentials.valid
        except:
            return False

    def _load_credentials(self) -> bool:
        """保存されたトークンを読み込み"""
        if not GOOGLE_AUTH_AVAILABLE:
            return False

        try:
            if self._token_path.exists():
                self.credentials = Credentials.from_authorized_user_file(
                    str(self._token_path), YOUTUBE_SCOPES
                )

                # トークンが期限切れで、リフレッシュトークンがあれば更新
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_credentials()

                return self.credentials is not None and self.credentials.valid
        except Exception as e:
            print(f"[ERROR] トークン読み込みエラー: {e}")

        return False

    def _save_credentials(self):
        """トークンを保存"""
        if self.credentials:
            try:
                with open(self._token_path, 'w') as f:
                    f.write(self.credentials.to_json())
            except Exception as e:
                print(f"[ERROR] トークン保存エラー: {e}")

    def authenticate(self, callback=None) -> Tuple[bool, str]:
        """
        OAuth認証フローを実行

        Args:
            callback: 認証完了時のコールバック関数

        Returns:
            (成功したか, エラーメッセージ)
        """
        if not GOOGLE_AUTH_AVAILABLE:
            return False, "Google認証ライブラリが利用できません"

        client_id = self.config.get("youtube_client_id", "")
        client_secret = self.config.get("youtube_client_secret", "")

        if not client_id or not client_secret:
            return False, "YouTube APIのClient IDとClient Secretが設定されていません"

        try:
            # クライアント設定を作成
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
                }
            }

            # OAuth フローを作成
            flow = InstalledAppFlow.from_client_config(client_config, YOUTUBE_SCOPES)

            # ローカルサーバーで認証（ブラウザが開く）
            # run_local_server はブロッキングなので別スレッドで実行することも可能
            self.credentials = flow.run_local_server(
                port=8080,
                prompt='consent',
                success_message='認証が完了しました。このウィンドウを閉じてください。',
                open_browser=True
            )

            # トークンを保存
            self._save_credentials()

            # YouTube サービスを初期化
            self._init_youtube_service()

            if callback:
                callback(True, "認証成功")

            return True, "認証が完了しました"

        except Exception as e:
            error_msg = f"認証エラー: {e}"
            print(f"[ERROR] {error_msg}")
            if callback:
                callback(False, error_msg)
            return False, error_msg

    def authenticate_async(self, callback=None):
        """非同期で認証を実行（別スレッド）"""
        def run_auth():
            success, message = self.authenticate()
            if callback:
                callback(success, message)

        thread = threading.Thread(target=run_auth, daemon=True)
        thread.start()

    def _init_youtube_service(self):
        """YouTube APIサービスを初期化"""
        if not GOOGLE_AUTH_AVAILABLE or not self.credentials:
            return

        try:
            self.youtube_service = build('youtube', 'v3', credentials=self.credentials)
        except Exception as e:
            print(f"[ERROR] YouTube API初期化エラー: {e}")

    def get_youtube_service(self):
        """YouTube APIサービスを取得"""
        if not self.youtube_service:
            if self._load_credentials():
                self._init_youtube_service()
        return self.youtube_service

    def get_live_chat_id(self, video_id: str) -> Tuple[Optional[str], str]:
        """
        動画IDからライブチャットIDを取得

        Returns:
            (live_chat_id, エラーメッセージ)
        """
        service = self.get_youtube_service()
        if not service:
            return None, "YouTube APIが初期化されていません"

        try:
            response = service.videos().list(
                part='liveStreamingDetails',
                id=video_id
            ).execute()

            if not response.get('items'):
                return None, f"動画が見つかりません: {video_id}"

            video = response['items'][0]
            live_details = video.get('liveStreamingDetails', {})
            live_chat_id = live_details.get('activeLiveChatId')

            if not live_chat_id:
                return None, "この動画にはアクティブなライブチャットがありません"

            return live_chat_id, ""

        except Exception as e:
            return None, f"ライブチャットID取得エラー: {e}"

    def send_message(self, live_chat_id: str, message: str) -> Tuple[bool, str]:
        """
        ライブチャットにメッセージを送信

        Args:
            live_chat_id: ライブチャットID
            message: 送信するメッセージ

        Returns:
            (成功したか, エラーメッセージ)
        """
        service = self.get_youtube_service()
        if not service:
            return False, "YouTube APIが初期化されていません"

        try:
            body = {
                'snippet': {
                    'liveChatId': live_chat_id,
                    'type': 'textMessageEvent',
                    'textMessageDetails': {
                        'messageText': message
                    }
                }
            }

            service.liveChatMessages().insert(
                part='snippet',
                body=body
            ).execute()

            return True, ""

        except Exception as e:
            error_msg = str(e)
            # よくあるエラーの日本語化
            if 'quotaExceeded' in error_msg:
                return False, "YouTube APIのクォータを超過しました。しばらく待ってから再試行してください。"
            elif 'forbidden' in error_msg.lower():
                return False, "このチャットへの投稿権限がありません。"
            elif 'liveChatEnded' in error_msg:
                return False, "ライブチャットは終了しています。"
            else:
                return False, f"メッセージ送信エラー: {e}"

    def revoke_credentials(self) -> bool:
        """認証情報を取り消し"""
        try:
            if self._token_path.exists():
                self._token_path.unlink()
            self.credentials = None
            self.youtube_service = None
            return True
        except Exception as e:
            print(f"[ERROR] 認証取り消しエラー: {e}")
            return False


def open_google_cloud_console():
    """Google Cloud Consoleを開く"""
    webbrowser.open("https://console.cloud.google.com/apis/credentials")


def open_youtube_api_enable_page():
    """YouTube Data API v3 有効化ページを開く"""
    webbrowser.open("https://console.cloud.google.com/apis/library/youtube.googleapis.com")


def open_oauth_setup_guide():
    """OAuth設定ガイドページを開く（sayonari.com に設置予定）"""
    # 将来的には専用のガイドページを用意
    webbrowser.open("https://developers.google.com/youtube/v3/getting-started")
