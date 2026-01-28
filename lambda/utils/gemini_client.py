"""Gemini API クライアント"""
import google.generativeai as genai
from typing import Dict, Tuple
from config import GEMINI_API_KEY
from utils.logger import logger


class GeminiClient:
    """Gemini 3 Flash クライアント"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
    
    def analyze_market(self, news_text: str, price_data: Dict) -> Tuple[int, str]:
        """
        市場分析を実行
        
        Returns:
            (confidence_score, reasoning_text)
        """
        prompt = f"""
あなたは金融市場の分析エキスパートです。以下の情報を基に、RWA（現実資産トークン）のポートフォリオ最適化の判断を行ってください。

## 最新ニュース
{news_text}

## 現在の価格情報
{self._format_price_data(price_data)}

## タスク
1. ニュースの内容と現在の価格/騰落率を比較分析してください
2. Confidence Score (1-10) を算出してください
   - 1-3: 情報不足、判断不可
   - 4-7: 弱いシグナル、アクション不要
   - 8-10: 強いシグナル、アクション検討
3. 判断根拠を明確に説明してください

## 出力形式
以下のJSON形式で回答してください：
{{
    "confidence_score": <1-10の整数>,
    "reasoning": "<判断根拠のテキスト説明>"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            return result["confidence_score"], result["reasoning"]
        except Exception as e:
            logger.error(f"Failed to analyze market with Gemini: {str(e)}")
            return 0, f"分析エラー: {str(e)}"
    
    def optimize_portfolio(self, reasoning: str, current_allocations: Dict[str, float]) -> Dict[str, float]:
        """
        ポートフォリオ最適化
        
        Returns:
            目標資産比率の辞書 (例: {{"PAXG/USDT": 0.6, "USDT": 0.4}})
        """
        prompt = f"""
あなたはポートフォリオ最適化のエキスパートです。以下の情報を基に、最適な資産配分を決定してください。

## 分析結果
{reasoning}

## 現在の資産配分
{self._format_allocations(current_allocations)}

## 取引対象資産
- PAXG/USDT (Gold)
- SLVON/USDT (Silver - iShares Silver Trust Ondo Tokenized)
- SPYON/USDT (S&P500)
- QQQON/USDT (NASDAQ)
- TSLAX/USDT (Tesla)
- NVDAX/USDT (NVIDIA)
- MSTRX/USDT (MicroStrategy)
- ONDO/USDT (US Treasury)
- USDT (現金)

## タスク
1. 各資産の目標配分比率を決定してください（合計100%）
2. リスクを分散し、ニュースに基づいた合理的な配分にしてください

## 出力形式
以下のJSON形式で回答してください：
{{
    "PAXG/USDT": <0.0-1.0の数値>,
    "SLVON/USDT": <0.0-1.0の数値>,
    "SPYON/USDT": <0.0-1.0の数値>,
    "QQQON/USDT": <0.0-1.0の数値>,
    "TSLAX/USDT": <0.0-1.0の数値>,
    "NVDAX/USDT": <0.0-1.0の数値>,
    "MSTRX/USDT": <0.0-1.0の数値>,
    "ONDO/USDT": <0.0-1.0の数値>,
    "USDT": <0.0-1.0の数値>
}}
合計が1.0になることを確認してください。
"""
        
        try:
            response = self.model.generate_content(prompt)
            allocations = self._parse_allocations(response.text)
            return allocations
        except Exception as e:
            logger.error(f"Failed to optimize portfolio with Gemini: {str(e)}")
            # エラー時は現在の配分を維持
            return current_allocations
    
    def _format_price_data(self, price_data: Dict) -> str:
        """価格データをフォーマット"""
        lines = []
        for symbol, data in price_data.items():
            lines.append(f"{symbol}: ${data['price']:.4f} ({data['change_24h']:+.2f}%)")
        return "\n".join(lines)
    
    def _format_allocations(self, allocations: Dict[str, float]) -> str:
        """資産配分をフォーマット"""
        lines = []
        for symbol, ratio in allocations.items():
            lines.append(f"{symbol}: {ratio*100:.1f}%")
        return "\n".join(lines)
    
    def _parse_response(self, text: str) -> Dict:
        """Geminiの応答をパース"""
        import json
        import re
        
        # JSON部分を抽出
        json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # フォールバック: 数値を抽出
        score_match = re.search(r'"confidence_score":\s*(\d+)', text)
        reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', text)
        
        return {
            "confidence_score": int(score_match.group(1)) if score_match else 0,
            "reasoning": reasoning_match.group(1) if reasoning_match else text
        }
    
    def _parse_allocations(self, text: str) -> Dict[str, float]:
        """ポートフォリオ配分をパース"""
        import json
        import re
        
        # JSON部分を抽出
        json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # フォールバック: キーと値のペアを抽出
        allocations = {}
        for symbol in ["PAXG/USDT", "SLVON/USDT", "SPYON/USDT", "QQQON/USDT", 
                       "TSLAX/USDT", "NVDAX/USDT", "MSTRX/USDT", "ONDO/USDT", "USDT"]:
            pattern = f'"{symbol}":\\s*([\\d.]+)'
            match = re.search(pattern, text)
            if match:
                allocations[symbol] = float(match.group(1))
        
        # 合計が1.0になるように正規化
        total = sum(allocations.values())
        if total > 0:
            allocations = {k: v/total for k, v in allocations.items()}
        
        return allocations

