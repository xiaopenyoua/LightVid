from pathlib import Path
from dotenv import load_dotenv
import os
import json

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'lightvid.db'}"

# TMDB API 配置
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

# 默认语言
LANGUAGE = "zh-CN"
TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")

# 预置解析接口配置
def get_default_parse_configs():
    """从环境变量读取预置解析接口配置"""
    configs_str = os.getenv("DEFAULT_PARSE_CONFIGS", "[]")
    try:
        return json.loads(configs_str)
    except json.JSONDecodeError:
        print("[Config] 解析 DEFAULT_PARSE_CONFIGS 失败，使用空列表")
        return []

DEFAULT_PARSE_CONFIGS = get_default_parse_configs()
