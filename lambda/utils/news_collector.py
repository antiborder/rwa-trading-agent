"""ニュース収集"""
import os
import requests
from typing import Dict, List, Optional
from utils.logger import logger


def fetch_cryptopanic_news() -> List[Dict[str, str]]:
    """CryptoPanic APIからニュースを取得"""
    try:
        auth_token = os.getenv("CRYPTOPANIC_AUTH_TOKEN") or os.getenv("AUTH_TOKEN")
        if not auth_token:
            logger.warning("CRYPTOPANIC_AUTH_TOKEN is not set; skipping CryptoPanic news fetch")
            return []

        # CryptoPanic APIの実装（APIキーが必要な場合）
        # ここでは例として実装
        # Docs: Base=https://cryptopanic.com/api/developer/v2, News endpoint=GET /posts/
        url = "https://cryptopanic.com/api/developer/v2/posts/"
        params = {
            "auth_token": auth_token,  # APIキーが必要
            "public": "true",  # public=true で Public Usage Mode
            "filter": "hot",
            "kind": "news",
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning(
                f"CryptoPanic returned non-200 status: {response.status_code}, body={response.text[:500]}"
            )
            return []

        data = response.json()
        news_items = []
        for item in data.get("results", [])[:10]:  # 最新10件
            news_items.append({
                "title": item.get("title", ""),
                # Docs: original_url is the original article; url is the Cryptopanic-hosted article
                "url": item.get("original_url") or item.get("url", ""),
                "source": "cryptopanic"
            })
        return news_items
    except Exception as e:
        logger.warning(f"Failed to fetch CryptoPanic news: {str(e)}")
    return []


def collect_news() -> Dict[str, any]:
    """全ニュースソースから情報を収集"""
    all_news = []
    fetch_status = {}
    failed_sources = []
    
    # CryptoPanic API（優先）
    cryptopanic_news = fetch_cryptopanic_news()
    if cryptopanic_news:
        all_news.extend(cryptopanic_news)
        fetch_status["cryptopanic"] = True
    else:
        fetch_status["cryptopanic"] = False
        failed_sources.append("cryptopanic")
    
    # ニューステキストを結合
    news_text = "\n".join([
        f"[{item['source']}] {item['title']}" for item in all_news
    ])
    
    source_urls = [item['url'] for item in all_news]
    
    return {
        "news_items": all_news,
        "news_text": news_text,
        "source_urls": source_urls,
        "fetch_status": fetch_status,
        "failed_sources": failed_sources
    }

