#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import re
import aiohttp
from collections import OrderedDict
from typing import Optional, Dict, Any, Tuple
from deep_translator import GoogleTranslator
import deepl

class TranslationEngine:
    """翻訳エンジン統合クラス"""

    # 非公式 Google 翻訳 API（いずれも translate.google.com/m より安定）
    # DICT_URL は「訳文 + 検出言語」を1リクエストで返すため第一候補にする
    DICT_URL = "https://clients5.google.com/translate_a/t"
    GTX_URL = "https://translate.googleapis.com/translate_a/single"
    _UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

    # Google 障害時に返るエラーページの文面（翻訳結果として誤投稿しないため検出する）
    # 2026-08-24 頃から translate.google.com/m が間欠的に Error 500 を返し，
    # その HTML の本文がそのまま翻訳結果として通ってしまう問題への対策
    #
    # 判定は厳しめにする。"That's an error" だけで弾くと
    # 「それはエラーです」の英訳のような正当な翻訳まで捨ててしまうため，
    # (a) "Error 500 (Server Error)" 形式か，
    # (b) "That's an error" と "That's all we know" の同時出現
    # のいずれかを満たす場合だけをエラーページとみなす
    _ERROR_PAGE_RE = re.compile(r"Error \d{3} \(Server Error\)")
    _ERR_PHRASES = ("That's an error", "That’s an error", "That&#39;s an error")
    _ALL_WE_KNOW_PHRASES = ("That's all we know", "That’s all we know", "That&#39;s all we know")

    @classmethod
    def is_error_page(cls, text: str) -> bool:
        """Google のエラーページ文面かどうかを判定"""
        if not text:
            return False
        if cls._ERROR_PAGE_RE.search(text):
            return True
        has_error_phrase = any(p in text for p in cls._ERR_PHRASES)
        has_all_we_know = any(p in text for p in cls._ALL_WE_KNOW_PHRASES)
        return has_error_phrase and has_all_we_know

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.google_available = False
        self.deepl_translator = None
        # 言語検出のリクエストで得た訳文を短期保持し，直後の翻訳要求で再利用する
        # （検出と翻訳で API を2回叩かないための最適化）
        self._recent: "OrderedDict[Tuple[str, str], str]" = OrderedDict()
        self.deepl_error = ""
        self._deepl_warned = False
        self._init_translators()

    def _cache_put(self, text: str, target_lang: str, translation: str):
        """検出時に得た訳文を短期キャッシュへ"""
        self._recent[(text, target_lang)] = translation
        while len(self._recent) > 64:
            self._recent.popitem(last=False)

    def _cache_pop(self, text: str, target_lang: str) -> Optional[str]:
        """短期キャッシュから取り出す（1回限り）"""
        return self._recent.pop((text, target_lang), None)

    def _init_translators(self):
        """翻訳エンジンを初期化"""
        # Google Translator（deep-translatorは毎回インスタンスを作成するため、利用可能フラグのみ保持）
        self.google_available = True
        self.deepl_error = ""

        # DeepL Translator（APIキーがある場合のみ）
        deepl_api_key = self.config.get("deepl_api_key", "")
        if deepl_api_key:
            try:
                self.deepl_translator = deepl.Translator(deepl_api_key)
            except Exception as e:
                # 以前はここで Google も無効化したうえ、エラーを黙って握りつぶしていたため
                # DeepL を選んでいるのに Google へ送信され続けていた
                self.deepl_translator = None
                self.deepl_error = str(e)
                print(f"DeepL の初期化に失敗しました: {e}")
    
    async def detect_language(self, text: str) -> Optional[str]:
        """言語検出

        1. 文字種から確実に判定できるものはローカルで即決（通信不要）
        2. ラテン文字などはオンライン検出（訳文も同時に得てキャッシュする）
        3. それも失敗したらヒューリスティクスへフォールバック

        以前は deep-translator の single_detection(api_key=None) を使っていたが，
        これは必ず例外を送出するため実質ヒューリスティクスしか動作せず，
        ラテン文字の言語がすべて英語と誤判定されていた（2026-08 修正）
        """
        # 1. 文字種で確定できるもの（日本語・韓国語・中国語・キリル文字など）
        definite = self._detect_local_definite(text)
        if definite:
            if self.config.get("debug", False):
                print(f"言語検出結果(ローカル): {text[:30]}... → {definite}")
            return definite

        # 2. オンライン検出（母語への翻訳を兼ねる）
        home_lang = self.config.get("lang_trans_to_home", "ja")
        try:
            result = await self._request_dict_chrome(text, home_lang)
            if result:
                translation, detected = result
                if detected:
                    # 同時に得た訳文を短期キャッシュへ（直後の翻訳要求で再利用）
                    if translation and not self.is_error_page(translation):
                        self._cache_put(text, home_lang, translation)
                    detected = self._validate_cjk_detection(text, detected)
                    if self.config.get("debug", False):
                        print(f"言語検出結果: {text[:30]}... → {detected}")
                    return detected
        except Exception as e:
            print(f"言語検出エラー: {e}")

        # 2b. clients5 が落ちている場合は gtx でも検出できる
        # （ここを省くとラテン文字の言語がすべて英語に戻ってしまう）
        try:
            detected = await self._detect_with_gtx(text)
            if detected:
                detected = self._validate_cjk_detection(text, detected)
                if self.config.get("debug", False):
                    print(f"言語検出結果(gtx): {text[:30]}... → {detected}")
                return detected
        except Exception as e:
            print(f"言語検出エラー(gtx): {e}")

        # 3. フォールバック: 簡易的な言語推定
        return self._fallback_detect_language(text)

    async def _detect_with_gtx(self, text: str) -> Optional[str]:
        """gtx JSON API から検出言語のみを取得する"""
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "en",
            "dt": "t",
            "q": text,
        }
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                self.GTX_URL, params=params, headers={"User-Agent": self._UA}
            ) as response:
                if response.status != 200:
                    return None
                data = await response.json(content_type=None)

        # 応答の3番目の要素に検出言語が入る
        if isinstance(data, list) and len(data) > 2 and isinstance(data[2], str):
            return data[2]
        return None

    def _detect_local_definite(self, text: str) -> Optional[str]:
        """文字種だけで確実に言語を特定できる場合のみ返す（できなければ None）

        ここで返すのは「その文字が使われていれば言語が一意に決まる」ものに限る。
        キリル文字（ロシア語/ウクライナ語…）やアラビア文字（アラビア語/ペルシャ語…）
        のように複数言語で共有される文字はオンライン検出へ回す
        """
        if not text:
            return None

        # かな は日本語にしか使われない
        has_hiragana = any('぀' <= c <= 'ゟ' for c in text)
        has_katakana = any('゠' <= c <= 'ヿ' for c in text)
        if has_hiragana or has_katakana:
            return 'ja'

        # ハングルは韓国語にしか使われない
        if any('가' <= c <= '힯' or 'ᄀ' <= c <= 'ᇿ' for c in text):
            return 'ko'

        return None

    def _validate_cjk_detection(self, text: str, detected: str) -> str:
        """CJK言語検出の検証・補正"""
        if not detected:
            return detected

        # ひらがな・カタカナの有無をチェック
        has_hiragana = any('\u3040' <= c <= '\u309f' for c in text)
        has_katakana = any('\u30a0' <= c <= '\u30ff' for c in text)
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)

        # 日本語と判定されたが、ひらがな・カタカナがない場合
        if detected == 'ja' and has_cjk and not has_hiragana and not has_katakana:
            # CJK文字のみ = 中国語の可能性が高い
            return 'zh-CN'

        # 中国語と判定されたが、ひらがな・カタカナがある場合
        if detected in ['zh-CN', 'zh-TW', 'zh'] and (has_hiragana or has_katakana):
            return 'ja'

        return detected

    def _fallback_detect_language(self, text: str) -> Optional[str]:
        """フォールバック言語検出（ヒューリスティクス）"""
        try:
            # 各言語の文字カウント
            has_hiragana = any('\u3040' <= c <= '\u309f' for c in text)
            has_katakana = any('\u30a0' <= c <= '\u30ff' for c in text)
            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
            has_hangul = any('\uac00' <= c <= '\ud7af' or '\u1100' <= c <= '\u11ff' for c in text)

            # 日本語: ひらがな or カタカナが含まれている
            if has_hiragana or has_katakana:
                return 'ja'

            # 韓国語: ハングル文字が含まれている
            if has_hangul:
                return 'ko'

            # CJK文字のみ（ひらがな・カタカナなし）= 中国語の可能性が高い
            if has_cjk:
                return 'zh-CN'

            # 非ASCII文字の検出（その他の言語）
            # キリル文字（ロシア語等）
            if any('\u0400' <= c <= '\u04ff' for c in text):
                return 'ru'

            # アラビア文字
            if any('\u0600' <= c <= '\u06ff' for c in text):
                return 'ar'

            # タイ文字
            if any('\u0e00' <= c <= '\u0e7f' for c in text):
                return 'th'

            # デバナーガリー文字（ヒンディー語等）
            if any('\u0900' <= c <= '\u097f' for c in text):
                return 'hi'

            # ラテン文字ベースの言語は区別が困難なため英語をデフォルトに
            return 'en'
        except:
            return None
    
    async def translate_text(self, text: str, target_lang: str, source_lang: str = "auto") -> Optional[str]:
        """テキスト翻訳"""
        try:
            # Google翻訳エンジンが初期化されていない場合は再初期化
            if not self.google_available:
                self._init_translators()
                
            translator_type = self.config.get("translator", "google")

            if translator_type == "deepl":
                if self.deepl_translator:
                    return await self._translate_with_deepl(text, target_lang, source_lang)
                # DeepL を選んでいるのに使えない状態で Google へ流すと、
                # 利用者が意図しない送信先へチャットが送られてしまう
                if not self._deepl_warned:
                    self._deepl_warned = True
                    reason = self.deepl_error or "APIキーが設定されていません"
                    print(f"DeepL が利用できないため翻訳を行いません: {reason}")
                return None
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
        """Google翻訳（gtx JSON API を第一候補に，deep-translator へフォールバック）

        2026-08-24 頃から deep-translator が使う translate.google.com/m が
        間欠的に Error 500 を返すため，安定している translate_a/single
        (client=gtx) を優先し，エラーページ文面は破棄する
        """
        if self.config.get("debug", False):
            print(f"Google翻訳: {text[:30]}... → {target_lang} に翻訳中...")

        # 言語検出時に同じ訳文を取得済みなら再利用（API呼び出しを1回節約）
        cached = self._cache_pop(text, target_lang)
        if cached:
            if self.config.get("debug", False):
                print(f"Google翻訳結果(検出時に取得済): {cached[:30]}...")
            return cached

        # 第一候補: clients5 (訳文+検出言語を返す・最も安定)
        try:
            result = await self._request_dict_chrome(text, target_lang)
            if result and result[0] and not self.is_error_page(result[0]):
                if self.config.get("debug", False):
                    print(f"Google翻訳結果(clients5): {result[0][:30]}...")
                return result[0]
        except Exception as e:
            print(f"clients5翻訳エラー: {e}")

        # 第二候補: gtx JSON API
        try:
            result = await self._translate_with_gtx(text, target_lang)
            if result and not self.is_error_page(result):
                if self.config.get("debug", False):
                    print(f"Google翻訳結果(gtx): {text[:30]}... → {result[:30]}...")
                return result
        except Exception as e:
            print(f"gtx翻訳エラー: {e}")

        # 最終フォールバック: deep-translator（/m スクレイピング）
        try:
            if not self.google_available:
                self._init_translators()

            if not self.google_available:
                print("Google翻訳エラー: 翻訳エンジンが初期化できません")
                return None

            translator = GoogleTranslator(source='auto', target=target_lang)
            result = await asyncio.to_thread(translator.translate, text)

            if result and self.is_error_page(result):
                print("Google翻訳エラー: エラーページ応答を検出したため結果を破棄")
                return None

            if self.config.get("debug", False):
                print(f"Google翻訳結果: {text[:30]}... → {result[:30] if result else 'None'}...")

            return result
        except Exception as e:
            print(f"Google翻訳エラー: {e}")
            # より詳細なエラー情報
            if self.config.get("debug", False):
                import traceback
                traceback.print_exc()
            return None

    async def _request_dict_chrome(self, text: str, target_lang: str) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """clients5 translate_a/t を呼び，(訳文, 検出言語) を返す

        応答形式: [["訳文", "検出言語"], ...]（長文は複数要素に分割される）
        """
        params = {
            "client": "dict-chrome-ex",
            "sl": "auto",
            "tl": target_lang,
            "q": text,
        }
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                self.DICT_URL, params=params, headers={"User-Agent": self._UA}
            ) as response:
                if response.status != 200:
                    print(f"clients5翻訳エラー: HTTP {response.status}")
                    return None
                data = await response.json(content_type=None)

        if not data:
            return None

        # 稀に {"sentences": [...], "src": "en"} 形式で返ることがあるため両対応にする
        if isinstance(data, dict):
            sentences = data.get("sentences") or []
            translation = "".join(
                s.get("trans", "") for s in sentences if isinstance(s, dict)
            )
            return (translation or None, data.get("src"))

        if not isinstance(data, list):
            return None

        segments, detected = [], None
        for item in data:
            if isinstance(item, list) and item:
                if item[0]:
                    segments.append(str(item[0]))
                if detected is None and len(item) > 1 and item[1]:
                    detected = str(item[1])
            elif isinstance(item, str):
                segments.append(item)

        translation = "".join(segments) or None
        return (translation, detected)

    async def _translate_with_gtx(self, text: str, target_lang: str) -> Optional[str]:
        """Google翻訳 非公式 JSON API (translate_a/single, client=gtx)"""
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text,
        }
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                self.GTX_URL, params=params, headers={"User-Agent": self._UA}
            ) as response:
                if response.status != 200:
                    print(f"gtx翻訳エラー: HTTP {response.status}")
                    return None
                data = await response.json(content_type=None)
                if not data or not data[0]:
                    return None
                result = "".join(seg[0] for seg in data[0] if seg and seg[0])
                return result or None
    
    async def _translate_with_deepl(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """DeepL翻訳"""
        try:
            if not self.deepl_translator:
                print("DeepL翻訳エラー: DeepLトランスレーターが初期化されていません")
                return None
            
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
                    return None
            else:
                # DeepL が対応していない言語は翻訳しない
                # （利用者は DeepL を選んでいるため、黙って Google へ送らない）
                print(f"DeepL翻訳: 対応していない言語です: {target_lang}")
                return None
                
        except Exception as e:
            print(f"DeepL翻訳エラー: {e}")
            return None
    
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

    @staticmethod
    def langs_match(a: str, b: str) -> bool:
        """言語コードの同一性判定（地域バリアントを同一視）

        - "pt" と "pt-BR" / "pt-PT" は同一扱い
        - "zh-CN" と "zh-TW" は簡体字/繁体字で翻訳が異なるため区別を維持
        """
        if not a or not b:
            return False
        if a == b:
            return True
        a_base = a.split("-")[0].lower()
        b_base = b.split("-")[0].lower()
        if a_base == "zh" or b_base == "zh":
            return False
        return a_base == b_base

    def should_ignore_language(self, lang: str) -> bool:
        """言語を無視すべきかチェック"""
        if not lang:
            return False
        if lang in self.ignore_langs:
            return True
        # 地域バリアントを考慮（例: ignore_lang=["pt"] なら "pt-BR" も無視）
        return any(self.langs_match(lang, ig) for ig in self.ignore_langs)

    def determine_target_language(self, detected_lang: str, input_text: str) -> str:
        """翻訳先言語を決定"""
        home_lang = self.config.get("lang_trans_to_home", "ja")
        other_lang = self.config.get("lang_home_to_other", "en")

        # 入力テキストで言語指定があるかチェック
        if ":" in input_text:
            parts = input_text.split(":", 1)
            if len(parts) >= 2 and parts[0] in self.target_langs:
                return parts[0]

        # 一方向翻訳モード: 外国語 → 母語のみ
        # 母語の投稿は翻訳対象外にする（呼び出し側の「同言語ガード」でスキップされる）
        if self.config.get("trans_to_home_only", False):
            if self.langs_match(detected_lang, home_lang):
                return home_lang
            return home_lang

        # 自動判定（双方向）
        if self.langs_match(detected_lang, home_lang):
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