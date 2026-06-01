import requests
import re
from bs4 import BeautifulSoup
from src.telemetry.logger import logger

def fetch_web_content(url: str, max_chars: int = 8000) -> str:
    """
    Tải nội dung trang web từ một URL, lọc bỏ mã HTML/CSS/JS rác 
    và trả về văn bản sạch có ích để LLM đọc và nghiên cứu tài liệu.
    
    Args:
        url: Đường dẫn trang web cần đọc.
        max_chars: Số lượng ký tự tối đa trả về để tránh quá tải context (mặc định 8000).
        
    Returns:
        Văn bản thuần của trang web hoặc thông báo lỗi.
    """
    logger.log_event("TOOL_USE_START", {"tool": "fetch_web_content", "url": url})
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML bằng BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Loại bỏ các thẻ rác không chứa thông tin hữu ích cho LLM
        for script_or_style in soup(["script", "style", "header", "footer", "nav", "aside", "noscript", "iframe"]):
            script_or_style.decompose()
            
        # Trích xuất văn bản thuần
        text = soup.get_text(separator="\n")
        
        # Làm sạch khoảng trắng dư thừa
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Cắt bớt văn bản nếu vượt quá giới hạn ký tự
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n...[Đã cắt bớt nội dung để tránh quá tải Context]..."
            
        logger.log_event("TOOL_USE_END", {"tool": "fetch_web_content", "status": "success", "length": len(text)})
        return text
        
    except Exception as e:
        logger.log_event("TOOL_USE_END", {"tool": "fetch_web_content", "status": "error", "error": str(e)})
        return f"Lỗi khi tải hoặc phân tích nội dung trang web: {str(e)}"
