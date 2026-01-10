"""ニュース収集"""
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from utils.logger import logger
from config import NEWS_SOURCES


def fetch_cryptopanic_news() -> List[Dict[str, str]]:
    """CryptoPanic APIからニュースを取得"""
    try:
        # CryptoPanic APIの実装（APIキーが必要な場合）
        # ここでは例として実装
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth_token": "",  # APIキーが必要
            "public": "true",
            "filter": "hot"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_items = []
            for item in data.get("results", [])[:10]:  # 最新10件
                news_items.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": "cryptopanic"
                })
            return news_items
    except Exception as e:
        logger.warning(f"Failed to fetch CryptoPanic news: {str(e)}")
    return []


def scrape_reuters() -> List[Dict[str, str]]:
    """ロイターからニュースをスクレイピング"""
    try:
        url = NEWS_SOURCES["reuters"]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            news_items = []
            # ロイターのHTML構造に応じて調整が必要
            articles = soup.find_all('a', class_='text__text__1FZLe', limit=10)
            for article in articles:
                title = article.get_text(strip=True)
                href = article.get('href', '')
                if title and href:
                    news_items.append({
                        "title": title,
                        "url": f"https://www.reuters.com{href}" if href.startswith('/') else href,
                        "source": "reuters"
                    })
            return news_items
    except Exception as e:
        logger.warning(f"Failed to scrape Reuters: {str(e)}")
    return []


def scrape_investing() -> List[Dict[str, str]]:
    """Investing.comからニュースをスクレイピング"""
    try:
        url = NEWS_SOURCES["investing"]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            news_items = []
            # Investing.comのHTML構造に応じて調整が必要
            articles = soup.find_all('article', limit=10)
            for article in articles:
                title_elem = article.find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    if title and href:
                        news_items.append({
                            "title": title,
                            "url": f"https://jp.investing.com{href}" if href.startswith('/') else href,
                            "source": "investing"
                        })
            return news_items
    except Exception as e:
        logger.warning(f"Failed to scrape Investing.com: {str(e)}")
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
    
    # ロイター（スクレイピング）
    reuters_news = scrape_reuters()
    if reuters_news:
        all_news.extend(reuters_news)
        fetch_status["reuters"] = True
    else:
        fetch_status["reuters"] = False
        failed_sources.append("reuters")
    
    # Investing.com（スクレイピング）
    investing_news = scrape_investing()
    if investing_news:
        all_news.extend(investing_news)
        fetch_status["investing"] = True
    else:
        fetch_status["investing"] = False
        failed_sources.append("investing")
    
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

