import requests
import json

def get_weather(city="Hanoi", format_type="text"):
    """
    Lấy thông tin thời tiết hiện tại cho một thành phố.
    
    Args:
        city (str): Tên thành phố (ví dụ: "Hanoi", "Tokyo")
        format_type (str): Kiểu hiển thị: 'text' (dễ đọc), 'compact' (ngắn gọn), 'json' (chi tiết đầy đủ)
    
    Returns:
        str hoặc dict: Thông tin thời tiết theo định dạng yêu cầu
    """
    try:
        # Sử dụng API wttr.in miễn phí
        if format_type == "json":
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        else:
            # Lấy dữ liệu text
            url = f"https://wttr.in/{city}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.text
            
            if format_type == "compact":
                # Chỉ lấy dòng đầu tiên (tóm tắt)
                lines = data.strip().split('\n')
                return lines[0] if lines else data
            else:  # text
                return data
    except requests.exceptions.RequestException as e:
        return f"Lỗi khi lấy thời tiết: {str(e)}"
    except Exception as e:
        return f"Lỗi không xác định: {str(e)}"