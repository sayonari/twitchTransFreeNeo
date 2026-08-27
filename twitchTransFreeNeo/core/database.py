#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import aiosqlite
import os
from typing import Optional, List, Dict, Any

class TranslationDatabase:
    """翻訳データベース管理クラス"""

    MAX_SIZE = 52428800  # 50MB

    def __init__(self, db_path: Optional[str] = None):
        # 設定ファイルと同じディレクトリに置く
        # （相対パスだとカレントディレクトリ依存になり，.app 起動時などに
        #   書き込めず翻訳キャッシュが機能しなかった）
        if db_path is None:
            try:
                from ..utils.config_manager import get_application_path
                db_path = os.path.join(get_application_path(), "translations.db")
            except Exception as e:
                print(f"データベースパス解決エラー: {e}")
                db_path = "translations.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """データベース初期化（同期的に実行 - __init__から呼ばれるため）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    engine TEXT NOT NULL DEFAULT 'google',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message, target_lang, engine)
                )
            ''')

            # 旧スキーマ（エンジン列なし）からの移行
            # 翻訳エンジンを区別していなかったため，DeepL に切り替えても
            # 以前の Google の訳が返ってきてしまっていた
            self._migrate_add_engine_column(cursor)

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_lang
                ON translations(message, target_lang, engine)
            ''')

            conn.commit()
            self._purge_error_pages(conn)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"データベース初期化エラー: {e}")

    def _migrate_add_engine_column(self, cursor):
        """旧スキーマのテーブルに engine 列を足して作り直す"""
        try:
            cursor.execute("PRAGMA table_info(translations)")
            columns = [row[1] for row in cursor.fetchall()]
            if "engine" in columns:
                return

            print("翻訳キャッシュのスキーマを更新します（翻訳エンジンを区別するため）")
            cursor.execute("ALTER TABLE translations RENAME TO translations_old")
            cursor.execute("""
                CREATE TABLE translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    engine TEXT NOT NULL DEFAULT 'google',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message, target_lang, engine)
                )
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO translations (message, target_lang, translation, engine, created_at)
                SELECT message, target_lang, translation, 'google', created_at FROM translations_old
            """)
            cursor.execute("DROP TABLE translations_old")
            print("  → 既存の訳は Google のものとして引き継ぎました")
        except Exception as e:
            print(f"翻訳キャッシュの移行に失敗しました: {e}")

    def _purge_error_pages(self, conn):
        """翻訳サービスのエラーページ文面がキャッシュされた行を削除する

        残っていると Google が復旧しても同じ発言に対して
        エラー文が恒久的に再生されてしまうため，起動時に掃除する。
        候補を LIKE で粗く絞ってから厳密判定にかけることで，
        「それはエラーです」のような正当な翻訳を巻き込まないようにする
        """
        try:
            from .translator import TranslationEngine

            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, translation FROM translations
                   WHERE translation LIKE '%Server Error%'
                      OR translation LIKE '%all we know%'"""
            )
            bad_ids = [
                row[0] for row in cursor.fetchall()
                if TranslationEngine.is_error_page(row[1])
            ]

            if bad_ids:
                cursor.executemany(
                    "DELETE FROM translations WHERE id = ?",
                    [(i,) for i in bad_ids]
                )
                print(f"翻訳キャッシュ浄化: エラーページ文面 {len(bad_ids)} 件を削除")
        except Exception as e:
            print(f"翻訳キャッシュ浄化エラー: {e}")

    async def save_translation(self, message: str, translation: str, target_lang: str,
                               engine: str = "google") -> bool:
        """翻訳を保存"""
        try:
            # 翻訳サービスのエラーページ文面は保存しない
            # （保存すると同じ発言に対して恒久的に再生されてしまう）
            from .translator import TranslationEngine
            if TranslationEngine.is_error_page(translation):
                return False

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    '''INSERT OR REPLACE INTO translations
                       (message, target_lang, translation, engine)
                       VALUES (?, ?, ?, ?)''',
                    (message, target_lang, translation, engine)
                )
                await db.commit()
            return True
        except Exception as e:
            print(f"翻訳保存エラー: {e}")
            return False

    async def get_translation(self, message: str, target_lang: str,
                              engine: str = "google") -> Optional[str]:
        """翻訳を取得（同じ翻訳エンジンで訳したものだけを返す）"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''SELECT translation FROM translations
                       WHERE message = ? AND target_lang = ? AND engine = ?''',
                    (message, target_lang, engine)
                )
                row = await cursor.fetchone()
                if not row:
                    return None

                # 念のため取り出す側でも検証する
                # （古いバージョンが保存したエラー文面が残っていても再生しない）
                from .translator import TranslationEngine
                if TranslationEngine.is_error_page(row[0]):
                    return None
                return row[0]
        except Exception as e:
            print(f"翻訳取得エラー: {e}")
            return None

    async def get_recent_translations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """最近の翻訳履歴を取得"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''SELECT message, translation, target_lang, created_at
                       FROM translations
                       ORDER BY created_at DESC
                       LIMIT ?''',
                    (limit,)
                )
                rows = await cursor.fetchall()
                return [
                    {
                        'message': row[0],
                        'translation': row[1],
                        'target_lang': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"翻訳履歴取得エラー: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT COUNT(*) FROM translations')
                total_count = (await cursor.fetchone())[0]

                cursor = await db.execute(
                    '''SELECT target_lang, COUNT(*)
                       FROM translations
                       GROUP BY target_lang
                       ORDER BY COUNT(*) DESC'''
                )
                lang_stats = await cursor.fetchall()

                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    'total_translations': total_count,
                    'language_stats': [{'lang': row[0], 'count': row[1]} for row in lang_stats],
                    'database_size': db_size,
                    'database_size_mb': round(db_size / 1024 / 1024, 2)
                }
        except Exception as e:
            print(f"統計情報取得エラー: {e}")
            return {
                'total_translations': 0,
                'language_stats': [],
                'database_size': 0,
                'database_size_mb': 0
            }

    async def cleanup_old_translations(self, keep_days: int = 30) -> int:
        """古い翻訳を削除"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''DELETE FROM translations
                       WHERE created_at < datetime('now', ? || ' days')''',
                    (-keep_days,)
                )
                await db.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"翻訳クリーンアップエラー: {e}")
            return 0

    def check_size_and_cleanup(self) -> bool:
        """サイズチェックとクリーンアップ（同期的に実行）"""
        try:
            if os.path.exists(self.db_path):
                if os.path.getsize(self.db_path) >= self.MAX_SIZE:
                    os.remove(self.db_path)
                    self._init_database()
                    return True
            return False
        except Exception as e:
            print(f"データベースサイズチェックエラー: {e}")
            return False

    async def vacuum(self) -> bool:
        """データベース最適化"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('VACUUM')
                await db.commit()
            return True
        except Exception as e:
            print(f"データベース最適化エラー: {e}")
            return False
