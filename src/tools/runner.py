import sys
import os
import json
import importlib.util

def main():
    # 1. Kiểm tra đối số truyền vào
    if len(sys.argv) < 3:
        print("Lỗi: Thiếu đối số. Cách dùng: python runner.py <tool_name> <json_arguments>", file=sys.stderr)
        sys.exit(1)
        
    tool_name = sys.argv[1]
    args_json = sys.argv[2]
    
    # 2. Parse JSON arguments
    try:
        args = json.loads(args_json)
        if not isinstance(args, dict):
            print("Lỗi: Các đối số truyền vào phải là một JSON Object (Dictionary).", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Lỗi: Không thể parse JSON arguments: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    # 3. Định vị tệp Python của tool động
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dynamic_tool_path = os.path.join(current_dir, "dynamic", f"{tool_name}.py")
    
    if not os.path.exists(dynamic_tool_path):
        print(f"Lỗi: Không tìm thấy tệp code của dynamic tool tại: {dynamic_tool_path}", file=sys.stderr)
        sys.exit(1)
        
    # 4. Thêm thư mục gốc của dự án vào sys.path để các dynamic tools có thể import chéo
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    # Thêm thư mục tools và dynamic vào sys.path để import dễ dàng
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    dynamic_dir = os.path.join(current_dir, "dynamic")
    if dynamic_dir not in sys.path:
        sys.path.insert(0, dynamic_dir)
        
    # 5. Nạp module động qua importlib
    try:
        spec = importlib.util.spec_from_file_location(tool_name, dynamic_tool_path)
        if spec is None or spec.loader is None:
            print(f"Lỗi: Không thể tạo import spec từ {dynamic_tool_path}", file=sys.stderr)
            sys.exit(1)
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[tool_name] = module
        spec.loader.exec_module(module)
        
        # 6. Kiểm tra xem hàm chính trùng tên tool_name có tồn tại không
        if not hasattr(module, tool_name):
            print(f"Lỗi: Module '{tool_name}' không định nghĩa hàm '{tool_name}'", file=sys.stderr)
            sys.exit(1)
            
        tool_func = getattr(module, tool_name)
        
        # 7. Thực thi hàm logic và trả về kết quả
        result = tool_func(**args)
        
        # 8. In kết quả ra stdout (nếu là dict/list thì serialize JSON, nếu không thì in chuỗi)
        if isinstance(result, (dict, list)):
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(str(result))
            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Lỗi thực thi trong Dynamic Tool '{tool_name}': {str(e)}\n\nChi tiết lỗi:\n{tb}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
