# -*- coding: utf-8 -*-
"""配置读写：配置文件位于程序目录下的 config.json，用户可直接编辑或通过设置界面修改。"""
import json
import os
import sys

APP_NAME = "随译 ScreenTranslator"
APP_VERSION = "1.1.0"


def base_dir() -> str:
    """程序运行目录：打包后为 exe 所在目录，开发时为项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(base_dir(), "config.json")

DEFAULT_CONFIG = {
    "engine": "auto",           # auto(自动回退) | deepl | bing | google | llm
    "llm": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",  # 豆包(火山方舟) OpenAI 兼容地址
        "api_key": "",
        "model": "",
    },
    "target_lang": "zh-CN",      # 目标语言
    "monitor_interval": 2.5,     # 屏幕实时翻译轮询间隔（秒）
    "auto_translate_clipboard": True,  # 复制文本时自动翻译
    "hotkeys": {
        "screenshot": "ctrl+shift+t",   # 截图翻译
        "clipboard": "ctrl+shift+c",    # 翻译剪贴板
        "text": "ctrl+shift+w",         # 文本翻译窗口
        "settings": "ctrl+shift+s",     # 设置
        "monitor": "ctrl+shift+r",      # 屏幕实时翻译开关
    },
}


def load() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝默认值
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _deep_merge(cfg, user_cfg)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[config] 读取配置失败，使用默认配置: {e}")
    return cfg


def save(cfg: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[config] 保存配置失败: {e}")


def _deep_merge(base: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
