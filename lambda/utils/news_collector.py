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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 200以外のステータスコードで例外を発生
        
        # パーサーのフォールバック
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except:
            soup = BeautifulSoup(response.content, 'html.parser')
        
        news_items = []
        
        # 複数のセレクターを試行（ロイターのHTML構造が変わった場合に対応）
        selectors = [
            ('a', {'class': 'text__text__1FZLe'}),
            ('a', {'class': 'text__text'}),
            ('a', {'data-testid': 'Link'}),
            ('article', {}),
            ('div[data-testid="MediaStoryCard"]', {}),
        ]
        
        articles = []
        for selector_type, attrs in selectors:
            if selector_type == 'a' and attrs:
                articles = soup.find_all('a', class_=attrs.get('class'), limit=10)
            elif selector_type == 'a' and 'data-testid' in attrs:
                articles = soup.find_all('a', attrs=attrs, limit=10)
            elif selector_type == 'article':
                articles = soup.find_all('article', limit=10)
            elif selector_type.startswith('div'):
                articles = soup.select('div[data-testid="MediaStoryCard"]', limit=10)
            
            if articles:
                logger.info(f"Found {len(articles)} articles using selector: {selector_type}")
                break
        
        if not articles:
            logger.warning("No articles found with any selector on Reuters page")
            return []
        
        for article in articles:
            # タイトルとURLを抽出
            title = None
            href = None
            
            if article.name == 'a':
                title = article.get_text(strip=True)
                href = article.get('href', '')
            else:
                # article要素の場合、内部のaタグを探す
                link = article.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                else:
                    # aタグがない場合、タイトル要素を探す
                    title_elem = article.find(['h2', 'h3', 'h4', 'span'], class_=lambda x: x and ('title' in x.lower() or 'headline' in x.lower()))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # URLは親要素から探す
                        parent_link = article.find_parent('a')
                        if parent_link:
                            href = parent_link.get('href', '')
            
            if title and href:
                # 相対URLを絶対URLに変換
                if href.startswith('/'):
                    href = f"https://www.reuters.com{href}"
                elif not href.startswith('http'):
                    href = f"https://www.reuters.com/{href}"
                
                news_items.append({
                    "title": title,
                    "url": href,
                    "source": "reuters"
                })
        
        if not news_items:
            logger.warning("Found articles but could not extract valid news items from Reuters")
        
        return news_items[:10]  # 最大10件に制限
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch Reuters page: {str(e)}")
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

