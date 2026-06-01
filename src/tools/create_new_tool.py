import os
import json
import ast
import sys
from typing import Dict, Any

def create_new_tool(tool_name: str, code: str, description: str, arguments_spec: Dict[str, str]) -> str:
    """
    Công cụ đặc quyền tối cao: Tự động ghi file Python của tool mới, 
    kiểm tra lỗi cú pháp và đăng ký metadata vào tools_registry.json.
    
    Args:
        tool_name: Tên của tool mới (dạng snake_case trùng với tên hàm chính, ví dụ: get_stock_price).
        code: Mã nguồn Python đầy đủ của tool mới (phải chứa hàm trùng tên với tool_name).
        description: Mô tả chi tiết chức năng và cách sử dụng để LLM nhận biết.
        arguments_spec: Dict mô tả các đối số (ví dụ: {"ticker": "Mã cổ phiếu cần lấy (str)"}).
        
    Returns:
        Thông báo trạng thái ghi và đăng ký thành công hoặc báo lỗi cú pháp.
    """
    # 1. Kiểm tra tính hợp lệ của tên tool
    if not tool_name.isidentifier():
        return f"Lỗi: Tên tool '{tool_name}' không hợp lệ. Phải là tên biến Python snake_case hợp lệ."
        
    # 2. Kiểm tra lỗi cú pháp bằng AST parse trước khi ghi file
    try:
        ast.parse(code)
    except SyntaxError as e:
        err_msg = (
            f"Lỗi: Cú pháp mã nguồn Python không hợp lệ.\n"
            f"  Chi tiết: Dòng {e.lineno}: {e.msg}\n"
            f"  Đoạn code lỗi: {e.text.strip() if e.text else ''}"
        )
        return err_msg
    except Exception as e:
        return f"Lỗi phân tích cú pháp mã nguồn: {str(e)}"
        
    # 3. Tạo thư mục lưu trữ tools động nếu chưa có
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dynamic_dir = os.path.join(base_dir, "tools", "dynamic")
    os.makedirs(dynamic_dir, exist_ok=True)
    
    file_path = os.path.join(dynamic_dir, f"{tool_name}.py")
    
    try:
        # 4. Ghi file Python vật lý lên đĩa
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        # 5. Cập nhật registry metadata vào tools_registry.json
        registry_path = os.path.join(base_dir, "tools", "tools_registry.json")
        registry = {}
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as rf:
                    content = rf.read().strip()
                    if content:
                        registry = json.loads(content)
            except Exception:
                registry = {}
                
        # Cập nhật thông tin tool mới
        registry[tool_name] = {
            "description": description,
            "arguments": arguments_spec,
            "file_path": f"src/tools/dynamic/{tool_name}.py"
        }
        
        with open(registry_path, "w", encoding="utf-8") as wf:
            json.dump(registry, wf, indent=2, ensure_ascii=False)
            
        print(f"✅ Đã tạo và đăng ký thành công tool động '{tool_name}' tại {file_path}!")
        return f"Thành công: Đã tạo file code Python và đăng ký thành công tool '{tool_name}' vào registry! Bạn có thể sử dụng tool '{tool_name}' trực tiếp từ lượt gọi tiếp theo."
    except Exception as e:
        return f"Lỗi trong quá trình tạo và đăng ký tool '{tool_name}': {str(e)}"
