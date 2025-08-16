#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from async_google_trans_new import AsyncTranslator, constant
import deepl

class TranslationEngine:
    """翻訳エンジン統合クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.google_translator = None
        self.deepl_translator = None
        self._init_translators()
    
    def _init_translators(self):
        """翻訳エンジンを初期化"""
        try:
            # Google Translator
            suffix = self.config.get("google_translate_suffix", "co.jp")
            if suffix not in [url.split('.')[-1] for url in constant.DEFAULT_SERVICE_URLS]:
                suffix = "co.jp"
            self.google_translator = AsyncTranslator(url_suffix=suffix)
            print(f"Google翻訳エンジンを初期化しました (suffix: {suffix})")
            
            # DeepL Translator (API キーがある場合のみ)
            deepl_api_key = self.config.get("deepl_api_key", "")
            if deepl_api_key:
                self.deepl_translator = deepl.Translator(deepl_api_key)
                print("DeepL翻訳エンジンを初期化しました")
        except Exception as e:
            print(f"翻訳エンジン初期化エラー: {e}")
            self.google_translator = None
            self.deepl_translator = None
    
    async def detect_language(self, text: str) -> Optional[str]:
        """言語検出"""
        try:
            # Google翻訳エンジンが初期化されていない場合は再初期化
            if not self.google_translator:
                self._init_translators()
            
            if not self.google_translator:
                print("言語検出エラー: Google翻訳エンジンが初期化できません")
                return None
                
            if self.config.get("translator") == "deepl" and self.deepl_translator:
                # DeepLの場合はGoogleで検出
                if hasattr(self.google_translator, 'detect'):
                    detected = await self.google_translator.detect(text)
                    return detected[0] if detected else None
                else:
                    print("言語検出エラー: Google翻訳エンジンにdetectメソッドがありません")
                    return None
            else:
                if hasattr(self.google_translator, 'detect'):
                    detected = await self.google_translator.detect(text)
                    return detected[0] if detected else None
                else:
                    print("言語検出エラー: Google翻訳エンジンにdetectメソッドがありません")
                    return None
        except Exception as e:
            print(f"言語検出エラー: {e}")
            return None
    
    async def translate_text(self, text: str, target_lang: str, source_lang: str = "auto") -> Optional[str]:
        """テキスト翻訳"""
        try:
            # Google翻訳エンジンが初期化されていない場合は再初期化
            if not self.google_translator:
                self._init_translators()
                
            translator_type = self.config.get("translator", "google")
            
            if translator_type == "deepl" and self.deepl_translator:
                return await self._translate_with_deepl(text, target_lang, source_lang)
            elif translator_type == "google":
                return await self._translate_with_google(text, target_lang)
            elif self.config.get("gas_url"):
                return await self._translate_with_gas(text, target_lang, source_lang)
            else:
                return await self._translate_with_google(text, target_lang)
                
        except Exception as e:
            print(f"翻訳エラー: {e}")
            return None
    
    async def _translate_with_google(self, text: str, target_lang: str) -> Optional[str]:
        """Google翻訳"""
        try:
            if not self.google_translator:
                self._init_translators()
                
            if not self.google_translator:
                print("Google翻訳エラー: 翻訳エンジンが初期化できません")
                return None
            
            # デバッグ: 翻訳サーバーURLを表示
            if self.config.get("debug", False):
                suffix = self.config.get("google_translate_suffix", "co.jp")
                print(f"Google翻訳: translate.google.{suffix} を使用して翻訳中...")
                
            result = await self.google_translator.translate(text, target_lang)
            
            if self.config.get("debug", False):
                print(f"Google翻訳結果: {text[:30]}... → {result[:30] if result else 'None'}...")
                
            return result
        except Exception as e:
            print(f"Google翻訳エラー: {e}")
            return None
    
    async def _translate_with_deepl(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """DeepL翻訳"""
        try:
            if not self.deepl_translator:
                print("DeepL翻訳エラー: DeepLトランスレーターが初期化されていません")
                return await self._translate_with_google(text, target_lang)
            
            # DeepL言語コード変換
            deepl_lang_dict = {
                'de': 'DE', 'en': 'EN-US', 'fr': 'FR', 'es': 'ES', 
                'pt': 'PT-PT', 'it': 'IT', 'nl': 'NL', 'pl': 'PL', 
                'ru': 'RU', 'ja': 'JA', 'zh-CN': 'ZH', 'ko': 'KO'
            }
            
            deepl_target = deepl_lang_dict.get(target_lang, target_lang.upper())
            deepl_source = None if source_lang == "auto" else deepl_lang_dict.get(source_lang, source_lang.upper())
            
            # DeepL APIを正しく使用
            if deepl_target:
                # translate_text メソッドを使用
                result = await asyncio.to_thread(
                    self.deepl_translator.translate_text,
                    text,
                    target_lang=deepl_target,
                    source_lang=deepl_source
                )
                # DeepL APIの結果からテキストを取得
                if result:
                    return result.text if hasattr(result, 'text') else str(result)
                else:
                    print(f"DeepL翻訳エラー: 結果が空です")
                    return await self._translate_with_google(text, target_lang)
            else:
                # DeepLで対応していない言語はGoogleで翻訳
                print(f"DeepL翻訳: 対応していない言語 {target_lang}, Googleにフォールバック")
                return await self._translate_with_google(text, target_lang)
                
        except Exception as e:
            print(f"DeepL翻訳エラー: {e}")
            # フォールバック: Google翻訳
            return await self._translate_with_google(text, target_lang)
    
    async def _translate_with_gas(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Google Apps Script翻訳"""
        try:
            gas_url = self.config.get("gas_url")
            if not gas_url:
                return None
            
            payload = {
                "text": text,
                "source": source_lang,
                "target": target_lang
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(gas_url, json=payload) as response:
                    if response.status == 200:
                        return await response.text()
            return None
            
        except Exception as e:
            print(f"GAS翻訳エラー: {e}")
            return None


class LanguageDetector:
    """言語検出とフィルタリング"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ignore_langs = config.get("ignore_lang", [])
        self.target_langs = [
            "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca", 
            "ceb", "ny", "zh-CN", "zh-TW", "co", "hr", "cs", "da", "nl", "en", "eo", 
            "et", "tl", "fi", "fr", "fy", "gl", "ka", "de", "el", "gu", "ht", "ha", 
            "haw", "iw", "hi", "hmn", "hu", "is", "ig", "id", "ga", "it", "ja", "jw", 
            "kn", "kk", "km", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", 
            "mg", "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no", "ps", "fa", 
            "pl", "pt", "ma", "ro", "ru", "sm", "gd", "sr", "st", "sn", "sd", "si", 
            "sk", "sl", "so", "es", "su", "sw", "sv", "tg", "ta", "te", "th", "tr", 
            "uk", "ur", "uz", "vi", "cy", "xh", "yi", "yo", "zu"
        ]
    
    def should_ignore_language(self, lang: str) -> bool:
        """言語を無視すべきかチェック"""
        return lang in self.ignore_langs
    
    def determine_target_language(self, detected_lang: str, input_text: str) -> str:
        """翻訳先言語を決定"""
        home_lang = self.config.get("lang_trans_to_home", "ja")
        other_lang = self.config.get("lang_home_to_other", "en")
        
        # 入力テキストで言語指定があるかチェック
        if ":" in input_text:
            parts = input_text.split(":", 1)
            if len(parts) >= 2 and parts[0] in self.target_langs:
                return parts[0]
        
        # 自動判定
        if detected_lang == home_lang:
            return other_lang
        else:
            return home_lang
    
    def extract_target_language_from_text(self, text: str) -> tuple[str, str]:
        """テキストから言語指定を抽出"""
        if ":" in text:
            parts = text.split(":", 1)
            if len(parts) >= 2 and parts[0] in self.target_langs:
                return parts[0], parts[1].strip()
        return "", text