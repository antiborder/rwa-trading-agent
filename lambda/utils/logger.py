"""ログ管理"""
import json
import logging
from datetime import datetime
from typing import Any, Dict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_to_json(level: str, message: str, **kwargs: Any) -> Dict[str, Any]:
    """JSON形式でログを出力"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
    
    if level == "ERROR":
        logger.error(json.dumps(log_entry, ensure_ascii=False))
    elif level == "WARNING":
        logger.warning(json.dumps(log_entry, ensure_ascii=False))
    elif level == "INFO":
        logger.info(json.dumps(log_entry, ensure_ascii=False))
    else:
        logger.debug(json.dumps(log_entry, ensure_ascii=False))
    
    return log_entry

