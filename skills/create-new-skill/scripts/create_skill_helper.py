import os
import sys
import ast
import argparse
import subprocess

def check_syntax(file_path: str) -> bool:
    """Kiểm tra lỗi cú pháp của file Python bằng cách phân tích AST."""
    if not os.path.exists(file_path):
        print(f"Lỗi: File '{file_path}' không tồn tại.", file=sys.stderr)
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        print(f"Cú pháp file '{file_path}' hoàn toàn hợp lệ (AST parse successful).")
        return True
    except SyntaxError as e:
        print(f"Lỗi cú pháp tại file '{file_path}':", file=sys.stderr)
        print(f"  Dòng {e.lineno}: {e.text.strip() if e.text else ''}", file=sys.stderr)
        print(f"  Chi tiết: {e.msg}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi kiểm tra cú pháp '{file_path}': {str(e)}", file=sys.stderr)
        return False

def validate_frontmatter(md_path: str) -> bool:
    """Xác thực YAML Frontmatter của file SKILL.md mới sinh."""
    if not os.path.exists(md_path):
        print(f"Lỗi: File '{md_path}' không tồn tại.", file=sys.stderr)
        return False
        
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        if not content.startswith("---"):
            print("Lỗi: File SKILL.md bắt buộc phải bắt đầu bằng dấu gạch ngang '---'.", file=sys.stderr)
            return False
            
        lines = content.splitlines()
        yaml_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)
            
        metadata = {}
        for line in yaml_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip()] = v.strip()
                
        if "name" not in metadata:
            print("Lỗi Frontmatter: Thiếu trường 'name' của kỹ năng.", file=sys.stderr)
            return False
        if "description" not in metadata:
            print("Lỗi Frontmatter: Thiếu trường 'description' mô tả năng lực.", file=sys.stderr)
            return False
            
        print(f"Đặc tả Frontmatter hợp lệ:")
        print(f"  - Tên kỹ năng: {metadata['name']}")
        print(f"  - Mô tả: {metadata['description']}")
        return True
    except Exception as e:
        print(f"Lỗi khi đọc hoặc phân tích frontmatter SKILL.md: {str(e)}", file=sys.stderr)
        return False

def run_test(test_path: str) -> bool:
    """Chạy Unit Test tạm thời của kỹ năng và bắt lỗi stderr."""
    if not os.path.exists(test_path):
        print(f"Lỗi: File test '{test_path}' không tồn tại.", file=sys.stderr)
        return False
        
    print(f"Đang chạy thử nghiệm Unit Test: {test_path}...")
    try:
        # Sử dụng python của môi trường hiện tại
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        print("\n--- STDOUT ---")
        print(result.stdout or "(Trống)")
        
        if result.returncode == 0:
            print("\n✅ Unit Test chạy thành công hoàn hảo!")
            return True
        else:
            print("\n❌ Unit Test thất bại!", file=sys.stderr)
            print(f"Exit Code: {result.returncode}", file=sys.stderr)
            print("\n--- STDERR ---", file=sys.stderr)
            print(result.stderr or "(Trống)", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("\n❌ Lỗi: Unit Test chạy quá thời gian (Timeout 20 giây)!", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Lỗi khi thực thi test subprocess: {str(e)}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Helper script cho kỹ năng create-new-skill giúp Agent tự học.")
    parser.add_argument("--check-syntax", help="Đường dẫn tới file python cần kiểm tra lỗi cú pháp")
    parser.add_argument("--validate-frontmatter", help="Đường dẫn tới file SKILL.md cần xác thực frontmatter")
    parser.add_argument("--run-test", help="Đường dẫn tới file python unit test cần thực thi")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)
        
    success = True
    if args.check_syntax:
        success = success and check_syntax(args.check_syntax)
    if args.validate_frontmatter:
        success = success and validate_frontmatter(args.validate_frontmatter)
    if args.run_test:
        success = success and run_test(args.run_test)
        
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
