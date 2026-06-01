import os
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from src.telemetry.logger import logger

def web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Tra cứu thông tin trên Internet sử dụng DuckDuckGo Search API (miễn phí, không cần Key).
    
    Args:
        query: Chuỗi từ khóa cần tìm kiếm.
        max_results: Số lượng kết quả tối đa muốn trả về (mặc định là 5).
        
    Returns:
        Danh sách các dictionary chứa thông tin: title, href (URL), body (snippet).
    """
    logger.log_event("TOOL_USE_START", {"tool": "web_search", "query": query})
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            formatted_results = []
            if results:
                for r in results:
                    formatted_results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
            logger.log_event("TOOL_USE_END", {"tool": "web_search", "status": "success", "results_count": len(formatted_results)})
            return formatted_results
    except Exception as e:
        logger.log_event("TOOL_USE_END", {"tool": "web_search", "status": "error", "error": str(e)})
        # Trả về lỗi dưới dạng chuỗi để LLM hiểu được thay vì crash chương trình chính
        return [{"error": f"Lỗi khi thực hiện tìm kiếm: {str(e)}"}]
