import os
import sys
import json
import shutil

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from tests.test_react_self_extending import get_llm_provider

def cleanup_environment():
    """Dọn dẹp môi trường kiểm thử để đảm bảo tính khách quan."""
    print("🧹 Đang dọn dẹp môi trường kiểm thử...")
    
    # 1. Reset file registry JSON
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    registry_path = os.path.join(base_dir, "src", "tools", "tools_registry.json")
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump({}, f)
        
    # 2. Xóa tệp calculate_factorial.py nếu có
    factorial_tool_path = os.path.join(base_dir, "src", "tools", "dynamic", "calculate_factorial.py")
    if os.path.exists(factorial_tool_path):
        os.remove(factorial_tool_path)
        print(f"🗑️ Đã xóa tool calculate_factorial cũ tại {factorial_tool_path}")
        
    # 3. Tạo thư mục dynamic nếu chưa có
    os.makedirs(os.path.dirname(factorial_tool_path), exist_ok=True)
    print("✅ Đã hoàn tất dọn dẹp môi trường!")

def main():
    # Set encoding to UTF-8 for console output
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    cleanup_environment()
    
    print("\n🚀 [INTEGRATION TEST] Khởi chạy kiểm thử Luồng Tự tiến hóa Tool Động (Dynamic Tool Registry)...")
    
    # Khởi tạo LLM và Agent
    try:
        llm = get_llm_provider()
        agent = ReActAgent(llm=llm, max_steps=8)
        print(f"✅ Đã kết nối LLM: {llm.__class__.__name__} ({llm.model_name})")
    except Exception as e:
        print(f"🚨 Lỗi khởi tạo LLM/Agent: {str(e)}")
        sys.exit(1)
        
    # Câu hỏi yêu cầu Agent tự tạo công cụ tính giai thừa và sử dụng nó
    prompt = (
        "Hãy viết cho bản thân một công cụ Python tính giai thừa của một số nguyên n, "
        "đặt tên công cụ là calculate_factorial, viết code thuật toán tối ưu, "
        "sau đó hãy dùng chính công cụ đó để tính giai thừa của 6 và trả về kết quả cuối cùng."
    )
    
    print(f"\n💬 Prompt gửi Agent:\n'{prompt}'\n")
    
    # Chạy Agent ReAct
    result = agent.run(prompt)
    
    print("\n🏁 [AGENT RESPONSE FINAL ANSWER]:")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Kiểm tra xác thực các file vật lý được tạo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    factorial_tool_path = os.path.join(base_dir, "src", "tools", "dynamic", "calculate_factorial.py")
    registry_path = os.path.join(base_dir, "src", "tools", "tools_registry.json")
    
    # 1. Xác thực file code Python được tạo thành công
    if os.path.exists(factorial_tool_path):
        print(f"🎉 TEST PASS: Tệp Python của dynamic tool đã được tạo thành công tại: {factorial_tool_path}")
        print("\n--- Nội dung code của Tool tự tạo ---")
        with open(factorial_tool_path, "r", encoding="utf-8") as f:
            print(f.read())
        print("------------------------------------\n")
    else:
        print(f"❌ TEST FAIL: Không tìm thấy tệp Python của dynamic tool tại: {factorial_tool_path}")
        sys.exit(1)
        
    # 2. Xác thực metadata trong registry JSON
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    if "calculate_factorial" in registry:
        print("🎉 TEST PASS: Dynamic tool đã được đăng ký thành công vào tools_registry.json!")
        print(f"Siêu dữ liệu (Metadata): {json.dumps(registry['calculate_factorial'], indent=2, ensure_ascii=False)}")
    else:
        print("❌ TEST FAIL: Dynamic tool không được đăng ký vào tools_registry.json")
        sys.exit(1)
        
    # 3. Xác thực kết quả giai thừa 6 = 720 có xuất hiện trong câu trả lời cuối cùng
    if "720" in result:
        print("\n🎉 TEST PASS: Agent đã tính toán và trả về kết quả giai thừa của 6 chính xác bằng 720!")
    else:
        print("\n❌ TEST FAIL: Không tìm thấy kết quả tính toán 720 trong câu trả lời của Agent.")
        sys.exit(1)
        
    print("\n⭐️ TOÀN BỘ CHU TRÌNH TEST INTEGRATION: 100% SUCCESSFUL PASS! ⭐️")

if __name__ == "__main__":
    main()
