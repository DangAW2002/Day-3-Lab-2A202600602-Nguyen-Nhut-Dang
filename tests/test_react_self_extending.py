import os
import sys
import json
from dotenv import load_dotenv

# Đảm bảo src có trong path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_compatible_provider import OpenAICompatibleProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider

def get_llm_provider():
    """
    Khởi tạo LLM Provider dựa trên cấu hình trong file .env.
    """
    load_dotenv()
    provider_type = os.getenv("DEFAULT_PROVIDER", "openai_compatible")
    
    if provider_type == "openai_compatible":
        base_url = os.getenv("COMPATIBLE_BASE_URL")
        api_key = os.getenv("COMPATIBLE_API_KEY")
        model_name = os.getenv("COMPATIBLE_MODEL_NAME", "mimo-v2.5-pro")
        return OpenAICompatibleProvider(model_name=model_name, base_url=base_url, api_key=api_key)
    elif provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider(model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"), api_key=api_key)
    elif provider_type == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider(model_name=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"), api_key=api_key)
    else:
        raise ValueError(f"Không hỗ trợ LLM provider: {provider_type}")

def run_self_extending_test():
    load_dotenv()
    
    print("--- 🚀 Bắt đầu Chạy Thử Nghiệm: Filesystem-based Self-Extending ReAct Agent (Chuẩn Anthropic) 🚀 ---")
    
    # 1. Khởi tạo LLM Provider từ cấu hình .env
    try:
        llm = get_llm_provider()
        print(f"✅ Đã khởi tạo LLM Provider: {llm.__class__.__name__} ({llm.model_name})")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo LLM Provider: {e}")
        return
        
    # 2. Khởi tạo ReAct Agent
    agent = ReActAgent(llm=llm, max_steps=12)
    print("✅ Đã khởi tạo ReActAgent với Anthropic Agent Skills (Level 1 Metadata loaded).")
    
    # 3. Định nghĩa yêu cầu tự tiến hóa
    prompt = """
    Tôi muốn bạn tự bổ sung một Kỹ năng mới có tên là 'calculate-factorial' để tính giai thừa của một số nguyên dương N.
    Hãy tự đọc hướng dẫn tạo kỹ năng mới tại skills/create-new-skill/SKILL.md để làm theo đúng quy trình 6 bước.
    Tạo cấu trúc thư mục skills/calculate-factorial/ chứa SKILL.md (YAML frontmatter đầy đủ) và thư mục scripts/ chứa script Python tối ưu thực hiện tính giai thừa.
    Sau khi tạo và kiểm thử thành công, hãy đọc file calculate-factorial/SKILL.md mới học này để nạp hướng dẫn và tính giai thừa của số 6, trả về kết quả cuối cùng cho tôi.
    """
    
    print("\n💬 Yêu cầu gửi tới Agent:")
    print("-" * 50)
    print(prompt.strip())
    print("-" * 50)
    
    # 4. Chạy Agent
    try:
        final_answer = agent.run(prompt)
        print("\n🏆 KẾT QUẢ CUỐI CÙNG TỪ AGENT:")
        print("-" * 50)
        print(final_answer)
        print("-" * 50)
        
        # 5. Xác minh xem skill đã được tạo thực tế trên đĩa chưa
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
        new_skill_dir = os.path.join(skills_dir, "calculate-factorial")
        skill_md_path = os.path.join(new_skill_dir, "SKILL.md")
        script_path = os.path.join(new_skill_dir, "scripts", "factorial.py")
        
        print("\n🔍 Kiểm tra thư viện vật lý của Kỹ năng mới:")
        if os.path.exists(new_skill_dir):
            print("✅ Thư mục kỹ năng 'skills/calculate-factorial/' đã được tạo vật lý thành công!")
        else:
            print("❌ Thư mục kỹ năng 'skills/calculate-factorial/' không tồn tại.")
            
        if os.path.exists(skill_md_path):
            print("✅ Tệp hướng dẫn 'skills/calculate-factorial/SKILL.md' đã được tạo thành công!")
            with open(skill_md_path, "r", encoding="utf-8") as f:
                print("\n--- Nội dung tệp SKILL.md mới sinh ---")
                print(f.read().strip())
                print("--------------------------------------")
        else:
            print("❌ Tệp 'skills/calculate-factorial/SKILL.md' không tồn tại.")
            
        if os.path.exists(script_path):
            print("✅ Script Python thực thi 'skills/calculate-factorial/scripts/factorial.py' đã được tạo thành công!")
        else:
            print("❌ Script Python thực thi không tồn tại.")
            
    except Exception as e:
        print(f"❌ Lỗi trong quá trình chạy thử nghiệm Agent: {e}")

if __name__ == "__main__":
    run_self_extending_test()
