import os
from src.telemetry.logger import logger

def read_file(path: str) -> str:
    """
    Đọc nội dung của một file văn bản từ ổ đĩa.
    
    Args:
        path: Đường dẫn tuyệt đối hoặc tương đối tới file cần đọc.
        
    Returns:
        Nội dung của file hoặc thông báo lỗi nếu không đọc được.
    """
    logger.log_event("TOOL_USE_START", {"tool": "read_file", "path": path})
    try:
        if not os.path.exists(path):
            return f"Lỗi: Không tìm thấy file tại '{path}'"
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.log_event("TOOL_USE_END", {"tool": "read_file", "status": "success", "length": len(content)})
        return content
    except Exception as e:
        logger.log_event("TOOL_USE_END", {"tool": "read_file", "status": "error", "error": str(e)})
        return f"Lỗi khi đọc file '{path}': {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Ghi nội dung văn bản vào một file trên ổ đĩa. Nếu thư mục cha chưa tồn tại sẽ tự động tạo.
    
    Args:
        path: Đường dẫn lưu file.
        content: Nội dung văn bản cần ghi vào file.
        
    Returns:
        Thông báo trạng thái ghi thành công hoặc báo lỗi.
    """
    logger.log_event("TOOL_USE_START", {"tool": "write_file", "path": path})
    try:
        # Tạo thư mục cha nếu chưa có
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.log_event("TOOL_USE_END", {"tool": "write_file", "status": "success"})
        return f"Thành công: Đã ghi dữ liệu vào file '{path}'"
    except Exception as e:
        logger.log_event("TOOL_USE_END", {"tool": "write_file", "status": "error", "error": str(e)})
        return f"Lỗi khi ghi file '{path}': {str(e)}"
