#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import aiosqlite
import os
from typing import Optional, Tuple

class TranslationDatabase:
    """翻訳データベース管理クラス"""
    
    def __init__(self, db_path: str = "translations.db"):
        self.db_path = db_path
        self.max_size = 52428800  # 50MB
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        try:
            # 同期的な初期化
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message, target_lang)
                )
            ''')
            
            # インデックス作成
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_lang 
                ON translations(message, target_lang)
            ''')
            
            conn.commit()
            conn.close()
            
            print("翻訳データベースを初期化しました")
            
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
    
    async def save_translation(self, message: str, translation: str, target_lang: str) -> bool:
        """翻訳を保存"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    '''INSERT OR REPLACE INTO translations 
                       (message, target_lang, translation) 
                       VALUES (?, ?, ?)''',
                    (message, target_lang, translation)
                )
                await db.commit()
            return True
            
        except Exception as e:
            print(f"翻訳保存エラー: {e}")
            return False
    
    async def get_translation(self, message: str, target_lang: str) -> Optional[str]:
        """翻訳を取得"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''SELECT translation FROM translations 
                       WHERE message = ? AND target_lang = ?''',
                    (message, target_lang)
                )
                row = await cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            print(f"翻訳取得エラー: {e}")
            return None
    
    async def get_recent_translations(self, limit: int = 100) -> list:
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
    
    async def search_translations(self, search_term: str, limit: int = 50) -> list:
        """翻訳を検索"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''SELECT message, translation, target_lang, created_at 
                       FROM translations 
                       WHERE message LIKE ? OR translation LIKE ?
                       ORDER BY created_at DESC 
                       LIMIT ?''',
                    (f'%{search_term}%', f'%{search_term}%', limit)
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
            print(f"翻訳検索エラー: {e}")
            return []
    
    async def get_statistics(self) -> dict:
        """統計情報を取得"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 総翻訳数
                cursor = await db.execute('SELECT COUNT(*) FROM translations')
                total_count = (await cursor.fetchone())[0]
                
                # 言語別統計
                cursor = await db.execute(
                    '''SELECT target_lang, COUNT(*) 
                       FROM translations 
                       GROUP BY target_lang 
                       ORDER BY COUNT(*) DESC'''
                )
                lang_stats = await cursor.fetchall()
                
                # データベースサイズ
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
                       WHERE created_at < datetime('now', '-{} days')'''.format(keep_days)
                )
                await db.commit()
                return cursor.rowcount
                
        except Exception as e:
            print(f"翻訳クリーンアップエラー: {e}")
            return 0
    
    def check_size_and_cleanup(self) -> bool:
        """サイズチェックとクリーンアップ"""
        try:
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                if size >= self.max_size:
                    # サイズ超過時は削除して再作成
                    os.remove(self.db_path)
                    self._init_database()
                    print(f"データベースサイズが{self.max_size}Bを超過したため、リセットしました")
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
    
    def close(self):
        """データベースクローズ（非同期版では不要だが互換性のため）"""
        pass