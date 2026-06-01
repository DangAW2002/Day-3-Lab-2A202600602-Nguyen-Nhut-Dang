---
name: create-new-skill
description: Kỹ năng đặc quyền tự tiến hóa: Tự thiết kế, viết tài liệu SKILL.md hướng dẫn (chứa YAML Frontmatter), viết các script thực thi và Unit Test, chạy thử nghiệm terminal, tự debug sửa lỗi code để sinh và đăng ký một Kỹ năng (Skill) mới dựa trên yêu cầu của người dùng mà không cần re-run hệ thống.
---

# Kỹ năng tự bổ sung Kỹ năng mới (create-new-skill)

Kỹ năng này cho phép Agent tự tiến hóa năng lực của bản thân bằng cách thiết kế và lưu trữ các Kỹ năng (Skills) mới dưới dạng cấu trúc thư mục filesystem-based chuẩn Anthropic.

---

## 🛠️ Quy trình 6 bước thực thi bắt buộc:

### 1. Phân tích yêu cầu (Analysis)
Xác định rõ:
- Tên kỹ năng mới: viết ở dạng kebab-case (chỉ chứa chữ thường, số, dấu gạch ngang, ví dụ: `calculate-factorial`).
- Mục tiêu, đầu vào, xử lý logic, đầu ra.
- Xác định xem kỹ năng này có cần viết thêm mã nguồn Python thực thi (scripts) hay chỉ cần hướng dẫn tư duy.

### 2. Nghiên cứu tài liệu (Research)
- Gọi công cụ `web_search` để tra cứu các thư viện Python tốt nhất giải quyết tác vụ.
- Gọi công cụ `fetch_web_content` để đọc tài liệu API của thư viện nếu cần thiết.

### 3. Lập kế hoạch kiến trúc (Planning)
Thiết kế cấu trúc thư mục Skill mới:
```
skills/<new-skill-name>/
├── SKILL.md            ← Tài liệu đặc tả kỹ năng và YAML frontmatter
└── scripts/            ← Chứa mã nguồn Python thực thi
    └── <script-name>.py
```

### 4. Viết mã nguồn & Tài liệu (Implementation)
- Tạo thư mục `skills/<new-skill-name>/` và thư mục `skills/<new-skill-name>/scripts/` (bằng cách dùng tool `write_file`).
- Viết file `skills/<new-skill-name>/SKILL.md` chứa YAML Frontmatter chuẩn:
  ```yaml
  ---
  name: <new-skill-name>
  description: <Mô tả chi tiết năng lực và khi nào nên dùng để Agent chính sau này nhận biết>
  ---
  
  # Tên Kỹ năng
  
  ## Hướng dẫn sử dụng
  [Hướng dẫn chi tiết cách dùng tool run_command để chạy scripts của kỹ năng này nếu có]
  ```
- Viết mã nguồn Python giải quyết logic nghiệp vụ phức tạp vào file `skills/<new-skill-name>/scripts/<script-name>.py`.
- Viết một file Unit Test tạm thời `skills/<new-skill-name>/scripts/test_temp.py` để kiểm thử logic.

### 5. Kiểm thử & Tự sửa lỗi (Testing & Debugging)
Sử dụng công cụ kiểm thử đặc quyền `skills/create-new-skill/scripts/create_skill_helper.py` thông qua `run_command` để kiểm tra chất lượng sản phẩm theo thứ tự sau:

1. **Xác thực YAML Frontmatter của SKILL.md**:
   ```bash
   run_command(cmd="python skills/create-new-skill/scripts/create_skill_helper.py --validate-frontmatter skills/<new-skill-name>/SKILL.md")
   ```
2. **Kiểm tra cú pháp (Syntax checking) của code Python**:
   ```bash
   run_command(cmd="python skills/create-new-skill/scripts/create_skill_helper.py --check-syntax skills/<new-skill-name>/scripts/<script-name>.py")
   ```
3. **Chạy Unit Test và bắt lỗi logic**:
   ```bash
   run_command(cmd="python skills/create-new-skill/scripts/create_skill_helper.py --run-test skills/<new-skill-name>/scripts/test_temp.py")
   ```
- Nếu bất kỳ bước nào báo lỗi (exit code phi 0, hoặc có thông báo lỗi):
  - Phân tích kỹ thông báo lỗi được helper in ra.
  - Tìm nguyên nhân logic (syntax, import thiếu thư viện, logic sai).
  - Viết lại/Sửa lại file code bằng `write_file` để sửa lỗi.
  - Lặp lại quá trình chạy kiểm thử cho đến khi **100% kiểm thử thành công**.
- Xóa file test tạm thời `test_temp.py` sau khi hoàn tất.

### 6. Đóng gói & Hoàn thành (Deployment)
- Đảm bảo file `SKILL.md` mới và các file script hoạt động hoàn hảo.
- Trả về kết quả cuối cùng thông báo cho người dùng rằng bạn đã tự học và tích hợp thành công Kỹ năng mới vào hệ thống. Ở lượt gọi tiếp theo, Agent chính sẽ tự quét và nhận thức được Kỹ năng này để sử dụng ngay lập tức mà không cần re-run hệ thống chính!

---

## 💡 Ví dụ tạo một Skill thành công:

Nếu người dùng yêu cầu: "Hãy tự tạo cho mình kỹ năng giải mã Base64", bạn sẽ tạo cấu trúc:

#### 1. File `skills/decode-base64/SKILL.md`:
```yaml
---
name: decode-base64
description: Giải mã các chuỗi văn bản bị mã hóa định dạng Base64 về dạng văn bản thuần sạch.
---

# Kỹ năng giải mã Base64

## Hướng dẫn
Khi có yêu cầu giải mã chuỗi Base64, hãy gọi script phụ trợ:
`run_command(cmd="python skills/decode-base64/scripts/decoder.py --data '<chuỗi_base64>'")`
```

#### 2. File `skills/decode-base64/scripts/decoder.py`:
```python
import base64
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()
    
    try:
        decoded = base64.b64decode(args.data).decode("utf-8")
        print(decoded)
    except Exception as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```
