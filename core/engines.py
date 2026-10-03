# -*- coding: utf-8 -*-
"""翻译引擎。

免费引擎（无需 Key）：
  - DeepL  网页接口（默认，国内可直连，质量高；免费层有限流，繁忙时自动降级）
  - Bing   微软翻译接口（部分网络可用）
  - Google 谷歌翻译接口（国内网络需代理）
付费引擎（推荐，效果最好）：
  - LLM    OpenAI 兼容的大模型 API（豆包/DeepSeek/OpenAI 等）
"""
import random
import time

import requests

TIMEOUT = 30

# 目标语言 -> 各引擎所需语言代码
LANG_MAP = {
    "zh-CN": {"deepl": "ZH",   "bing": "zh-Hans", "google": "zh-CN", "llm": "简体中文"},
    "en":    {"deepl": "EN",   "bing": "en",      "google": "en",     "llm": "English"},
    "ja":    {"deepl": "JA",   "bing": "ja",      "google": "ja",     "llm": "日语"},
    "ko":    {"deepl": "KR",   "bing": "ko",      "google": "ko",     "llm": "韩语"},
    "fr":    {"deepl": "FR",   "bing": "fr",      "google": "fr",     "llm": "法语"},
    "de":    {"deepl": "DE",   "bing": "de",      "google": "de",     "llm": "德语"},
    "es":    {"deepl": "ES",   "bing": "es",      "google": "es",     "llm": "西班牙语"},
    "ru":    {"deepl": "RU",   "bing": "ru",      "google": "ru",     "llm": "俄语"},
    "it":    {"deepl": "IT",   "bing": "it",      "google": "it",     "llm": "意大利语"},
    "pt":    {"deepl": "PT",   "bing": "pt",      "google": "pt",     "llm": "葡萄牙语"},
    "ar":    {"deepl": "AR",   "bing": "ar",      "google": "ar",     "llm": "阿拉伯语"},
    "vi":    {"deepl": "VI",   "bing": "vi",      "google": "vi",     "llm": "越南语"},
    "th":    {"deepl": "TH",   "bing": "th",      "google": "th",     "llm": "泰语"},
    "id":    {"deepl": "ID",   "bing": "id",      "google": "id",     "llm": "印尼语"},
    "tr":    {"deepl": "TR",   "bing": "tr",      "google": "tr",     "llm": "土耳其语"},
}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


class TranslateError(Exception):
    pass


class BaseEngine:
    name = "base"

    def translate(self, text: str, target_lang: str) -> str:
        raise NotImplementedError


class DeepLEngine(BaseEngine):
    """DeepL 网页免费接口（社区逆向实现）：国内可直连，无需 Key。"""
    name = "deepl"

    def translate(self, text, target_lang):
        tgt = LANG_MAP.get(target_lang, {}).get("deepl", "ZH")
        ts = self._timestamp()
        body = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_jobs",
            "params": {
                "jobs": [{
                    "kind": "default",
                    "raw_en_sentence": text,
                    "raw_en_context_before": [],
                    "raw_en_context_after": [],
                    "preferred_num_variants": 0,
                    "quality": "fast",
                    "timestamp": ts,
                }],
                "lang": {
                    "user_preferred_langs": ["en-US"],
                    "source_lang_user_selected": "EN",
                    "target_lang": tgt,
                },
                "priority": -1,
                "commonJobParams": {
                    "wasSpoken": False,
                    "transcribe_as": "",
                    "browserType": 1,
                    "formality": "default",
                },
                "timestamp": ts,
            },
            "id": random.randint(100000000, 999999999),
        }
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Origin": "https://www.deepl.com",
            "Referer": "https://www.deepl.com/translator",
        }
        try:
            resp = requests.post(
                "https://www2.deepl.com/jsonrpc?method=LMT_handle_jobs",
                json=body, headers=headers, timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise TranslateError(f"DeepL 接口请求失败: {e}") from e
        if resp.status_code == 429:
            raise TranslateError("DeepL 免费接口繁忙（限流），请稍后重试；或到设置中配置大模型 API Key 获得稳定翻译")
        if resp.status_code != 200:
            raise TranslateError(f"DeepL 接口返回 {resp.status_code}: {resp.text[:150]}")
        try:
            data = resp.json()
            beams = data["result"]["translations"][0]["beams"]
            result = beams[0]["postprocessed_sentence"].strip()
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise TranslateError(f"DeepL 接口响应解析失败: {e}") from e
        if not result:
            raise TranslateError("DeepL 接口返回空结果")
        return result

    @staticmethod
    def _timestamp() -> int:
        ts = int(time.time() * 1000)
        i = random.randint(4, 12) if ts % 1000 < 100 else 0
        return ts - ts % 1000 + i


class BingEngine(BaseEngine):
    """微软 Bing 免费接口：无需 Key。"""
    name = "bing"

    def translate(self, text, target_lang):
        to = LANG_MAP.get(target_lang, {}).get("bing", "zh-Hans")
        url = "https://www.bing.com/ttranslatev3?isVertical=1&IG=&IID=translator.5028"
        headers = {
            "User-Agent": UA,
            "Referer": "https://www.bing.com/translator",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"fromLang": "auto-detect", "text": text, "to": to}
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as e:
            raise TranslateError(f"Bing 接口请求失败: {e}") from e
        if isinstance(payload, dict) and payload.get("statusCode"):
            raise TranslateError(f"Bing 接口返回错误: {payload}")
        parts = []
        for item in payload if isinstance(payload, list) else []:
            for t in item.get("translations", []):
                if t.get("text"):
                    parts.append(t["text"])
        result = "\n".join(parts).strip()
        if not result:
            raise TranslateError("Bing 接口返回空结果")
        return result


class GoogleEngine(BaseEngine):
    """Google 免费接口：无需 Key，国内网络需代理。"""
    name = "google"

    def translate(self, text, target_lang):
        to = LANG_MAP.get(target_lang, {}).get("google", "zh-CN")
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": to, "dt": "t", "q": text}
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as e:
            raise TranslateError(f"Google 接口请求失败: {e}") from e
        parts = [seg[0] for seg in payload[0] if seg and seg[0]]
        result = "".join(parts).strip()
        if not result:
            raise TranslateError("Google 接口返回空结果")
        return result


class LLMEngine(BaseEngine):
    """OpenAI 兼容的大模型翻译：适配豆包(火山方舟)/DeepSeek/OpenAI 等。"""
    name = "llm"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or ""

    def _check(self):
        if not self.api_key:
            raise TranslateError("尚未配置大模型 API Key，请先到设置中填写")
        if not self.model:
            raise TranslateError("尚未配置模型名称，请先到设置中填写")

    def translate(self, text, target_lang):
        self._check()
        lang_name = LANG_MAP.get(target_lang, {}).get("llm", "简体中文")
        system = (
            f"You are a professional translator. Translate the user's text into {lang_name}. "
            "Preserve line breaks and original formatting. "
            "Return ONLY the translation. No explanations, no quotes, no notes."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            raise TranslateError(f"大模型接口请求失败: {e}") from e
        if resp.status_code != 200:
            raise TranslateError(f"大模型接口返回 {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
            result = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, ValueError) as e:
            raise TranslateError(f"大模型接口响应解析失败: {e}") from e
        if not result:
            raise TranslateError("大模型接口返回空结果")
        return result


def create_engine(cfg: dict) -> BaseEngine:
    engine = cfg.get("engine", "auto")
    if engine == "bing":
        return BingEngine()
    if engine == "google":
        return GoogleEngine()
    if engine == "llm":
        llm = cfg.get("llm", {})
        return LLMEngine(llm.get("base_url", ""), llm.get("api_key", ""), llm.get("model", ""))
    if engine == "deepl":
        return DeepLEngine()
    return FallbackEngine()


class FallbackEngine(BaseEngine):
    """自动回退链：依次尝试 DeepL → Bing → Google，全部失败时汇总错误。"""
    name = "auto"

    def __init__(self, order=None):
        self.engines = order or [DeepLEngine(), BingEngine(), GoogleEngine()]

    def translate(self, text, target_lang):
        errors = []
        for eng in self.engines:
            try:
                return eng.translate(text, target_lang)
            except TranslateError as e:
                errors.append(f"{eng.name}: {e}")
        detail = " | ".join(errors[:3])
        raise TranslateError(
            "免费翻译接口当前均不可用（" + detail + "）。"
            "建议到设置中配置大模型 API Key（DeepSeek/豆包，见 README），翻译更稳定自然。"
        )
