"""FastAPI メインアプリケーション"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.config import CORS_ORIGINS
from app.api import portfolio, judgments, transactions

app = FastAPI(
    title="RWA Trading Agent API",
    description="RWA Trading Agent バックエンドAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(portfolio.router)
app.include_router(judgments.router)
app.include_router(transactions.router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "RWA Trading Agent API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}


# Lambda用ハンドラー
handler = Mangum(app)

