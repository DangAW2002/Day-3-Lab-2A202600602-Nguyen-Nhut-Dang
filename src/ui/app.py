import os
import sys
import re
import json
import streamlit as st
import time

# Đảm bảo thư mục gốc dự án có trong PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agent.agent import ReActAgent
from tests.test_react_self_extending import get_llm_provider

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Self-Extending Agent Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Áp dụng Custom CSS cho phong cách Premium Dark/Sleek
st.markdown("""
<style>
    /* Gradient background và fonts */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #FF8F8F;
    }
    
    /* Sleek sidebar */
    .css-1d391kg {
        background-color: #0E1117;
    }
    
    /* Hộp Kỹ năng (Skill Cards) */
    .skill-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .skill-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: #FF4B4B;
        transform: translateY(-2px);
    }
    .skill-title {
        font-weight: bold;
        color: #FF8F8F;
        font-size: 1.1rem;
        margin-bottom: 4px;
    }
    .skill-desc {
        font-size: 0.9rem;
        color: #C5C6C7;
        line-height: 1.3;
    }
    .skill-path {
        font-family: monospace;
        font-size: 0.75rem;
        color: #888;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    try:
        llm = get_llm_provider()
        st.session_state.agent = ReActAgent(llm=llm)
        st.session_state.provider_name = f"{llm.__class__.__name__} ({llm.model_name})"
        st.session_state.init_error = None
    except Exception as e:
        st.session_state.init_error = str(e)

# Hàm New Chat
def start_new_chat():
    st.session_state.messages = []
    st.rerun()

# --- SIDEBAR: Cấu hình và Quản lý Skills ---
with st.sidebar:
    st.markdown("## 🧠 CẤU HÌNH HỆ THỐNG")
    
    if st.session_state.init_error:
        st.error(f"Lỗi khởi tạo LLM Provider: {st.session_state.init_error}")
    else:
        st.success(f"Active Provider:\n**{st.session_state.provider_name}**")
        
    # Nút New Chat
    st.button("🔄 New Chat / Reset", on_click=start_new_chat, use_container_width=True)
    
    # Cấu hình Max Steps
    max_steps = st.slider("Số bước ReAct tối đa (Max Steps)", min_value=3, max_value=15, value=10)
    if "agent" in st.session_state:
        st.session_state.agent.max_steps = max_steps
        
    st.markdown("---")
    st.markdown("### 🛠️ DEBUG STUDIO")
    if "trigger_debug_modal" not in st.session_state:
        st.session_state.trigger_debug_modal = False
        
    if st.button("🔍 Xem Debug Logs", use_container_width=True):
        st.session_state.trigger_debug_modal = True
        
    st.markdown("---")
    st.markdown("### 🔌 CÔNG CỤ TỰ HỌC (DYNAMIC TOOLS)")
    st.markdown("*Nạp nóng thời gian thực từ registry json*")
    
    # Hiển thị Dynamic Tools quét từ registry
    if "agent" in st.session_state:
        dynamic_tools = st.session_state.agent.load_available_tools_metadata()
        if dynamic_tools:
            for name, info in dynamic_tools.items():
                args_info = info.get("arguments", {})
                if isinstance(args_info, str):
                    try:
                        import ast
                        args_info = ast.literal_eval(args_info)
                    except Exception:
                        try:
                            args_info = json.loads(args_info)
                        except Exception:
                            args_info = {}
                
                args_keys = list(args_info.keys()) if isinstance(args_info, dict) else []
                args_str = ", ".join(args_keys)
                st.markdown(f"""
                <div class="skill-card" style="border-left: 4px solid #FF4B4B;">
                    <div class="skill-title" style="color: #FF4B4B;">🔌 {name}({args_str})</div>
                    <div class="skill-desc">{info.get('description')}</div>
                    <div class="skill-path">📁 {info.get('file_path')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Chưa có công cụ tự học động nào được bổ sung.")
            
    st.markdown("---")
    st.markdown("### 📚 THƯ VIỆN KỸ NĂNG CÀI SẴN")
    st.markdown("*Quét động từ filesystem theo chuẩn Anthropic Agent Skills*")
    
    # Hiển thị Skills quét động từ filesystem
    if "agent" in st.session_state:
        skills = st.session_state.agent.load_available_skills_metadata()
        if skills:
            for skill in skills:
                st.markdown(f"""
                <div class="skill-card">
                    <div class="skill-title">⚙️ {skill['name']}</div>
                    <div class="skill-desc">{skill['description']}</div>
                    <div class="skill-path">📁 {skill['path']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Chưa tìm thấy Kỹ năng nào trong thư mục `skills/`.")

# --- MAIN PANEL: Chat Studio ---
st.markdown("<h1>🧠 Self-Extending ReAct Agent Studio</h1>", unsafe_allow_html=True)
st.markdown("### Trải nghiệm Sức mạnh Tự học và Tự mở rộng Kỹ năng Cục bộ")

# Hiển thị lịch sử hội thoại
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Nếu có các bước trung gian của Agent, hiển thị lại dạng expander
        if "steps" in message:
            for step in message["steps"]:
                with st.expander(f"💭 {step['title']}", expanded=False):
                    st.code(step["content"], language=step.get("lang", "text"))

# Nhận câu hỏi từ người dùng
if prompt := st.chat_input("Nhập yêu cầu của bạn tại đây..."):
    # Hiển thị câu hỏi người dùng trên UI
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Khởi tạo giao diện trả lời của Agent
    with st.chat_message("assistant"):
        # Chứa danh sách các bước trung gian hiển thị trên giao diện
        ui_steps_log = []
        
        # Gọi sinh stream từ agent
        if "agent" in st.session_state:
            agent = st.session_state.agent
            
            # Giao diện status đang suy luận
            status_placeholder = st.status("🤖 Agent đang suy luận và lập kế hoạch...", expanded=True)
            
            try:
                # Để stream các bước, chúng ta sẽ tự chạy vòng lặp thô của ReActAgent
                # và hiển thị lên Streamlit thời gian thực.
                # Trích xuất lịch sử hội thoại mức cao rút gọn từ session state (trừ tin nhắn user cuối cùng vừa thêm)
                conversation_history = []
                for msg in st.session_state.messages[:-1]:
                    conversation_history.append({"role": msg["role"], "content": msg["content"]})
                
                # Khởi tạo history của Agent gồm tin nhắn cũ và tin nhắn mới nhất
                agent.history = []
                for msg in conversation_history:
                    agent.history.append({"role": msg["role"], "content": msg["content"]})
                agent.history.append({"role": "user", "content": prompt})
                
                steps_count = 0
                final_answer = ""
                
                while steps_count < agent.max_steps:
                    steps_count += 1
                    status_placeholder.update(label=f"💭 Lượt suy luận thứ {steps_count}/{agent.max_steps}...", state="running")
                    
                    system_prompt = agent.get_system_prompt()
                    context_prompt = ""
                    for msg in agent.history:
                        role_prefix = "User: " if msg["role"] == "user" else "Assistant: " if msg["role"] == "assistant" else "System/Observation: "
                        context_prompt += f"{role_prefix}{msg['content']}\n\n"
                        
                    # 1. LLM Sinh Thought + Action
                    # 1. Stream Thought và Reasoning từ Model thời gian thực
                    full_reasoning = ""
                    full_content = ""
                    
                    with status_placeholder:
                        st.markdown(f"**Thinking nội bộ của Model {steps_count}:**")
                        thinking_box = st.empty()
                        st.markdown(f"**Tư duy (Thought) {steps_count}:**")
                        thought_box = st.empty()
                        
                    try:
                        # Gọi stream từ LLM provider
                        stream_generator = agent.llm.stream(
                            context_prompt,
                            system_prompt=system_prompt,
                            stop=["Observation:", "System/Observation:", "Observation: "]
                        )
                        
                        for chunk in stream_generator:
                            chunk_type = chunk["type"]
                            chunk_content = chunk["content"]
                            
                            if chunk_type == "reasoning":
                                full_reasoning += chunk_content
                                thinking_box.info(full_reasoning)
                            elif chunk_type == "content":
                                full_content += chunk_content
                                thought_box.info(full_content)
                                
                    except Exception as stream_err:
                        # Fallback về generate nếu stream bị lỗi kết nối
                        st.warning(f"Lỗi streaming, đang thử lại bằng generate thường: {stream_err}")
                        llm_response = agent.llm.generate(
                            context_prompt,
                            system_prompt=system_prompt,
                            stop=["Observation:", "System/Observation:", "Observation: "]
                        )
                        full_content = llm_response["content"]
                        full_reasoning = llm_response.get("reasoning_content") or ""
                        
                    response_text = full_content.strip()
                    reasoning_content = full_reasoning.strip()
                    
                    # 2. Sau khi stream xong, dọn dẹp và cập nhật hiển thị tĩnh
                    if reasoning_content:
                        thinking_box.info(reasoning_content)
                        ui_steps_log.append({"title": f"Model Thinking {steps_count}", "content": reasoning_content})
                    else:
                        thinking_box.write("*(Mô hình không sinh thinking ở lượt này)*")
                        
                    # Trích xuất thought sạch đã loại bỏ Action/Final Answer
                    thought_match = re.search(r"Thought:\s*(.*?)(?:Action:|$)", response_text, re.DOTALL)
                    thought_content = thought_match.group(1).strip() if thought_match else response_text
                    
                    thought_box.info(thought_content)
                    ui_steps_log.append({"title": f"Thought {steps_count}", "content": thought_content})
                    
                    agent.history.append({"role": "assistant", "content": response_text})
                    
                    # 2. Kiểm tra Final Answer
                    if "Final Answer:" in response_text:
                        final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
                        final_answer = final_match.group(1).strip() if final_match else response_text
                        status_placeholder.update(label="✅ Đã tìm ra câu trả lời cuối cùng!", state="complete", expanded=False)
                        break
                        
                    # 3. Phân tích Action
                    parsed = agent.parse_action(response_text)
                    if not parsed:
                        warning_msg = "Lỗi: Chưa gọi đúng định dạng Action. Yêu cầu LLM thử lại."
                        with status_placeholder:
                            st.warning(warning_msg)
                        ui_steps_log.append({"title": f"Lỗi định dạng Lượt {steps_count}", "content": warning_msg})
                        agent.history.append({"role": "user", "content": warning_msg})
                        continue
                        
                    tool_name, tool_args = parsed
                    # Hiển thị Action gọi Tool
                    with status_placeholder:
                        st.markdown(f"**⚙️ Gọi công cụ (Action):** `{tool_name}`")
                        st.code(json.dumps(tool_args, indent=2, ensure_ascii=False), language="json")
                    ui_steps_log.append({"title": f"Action {steps_count}: Gọi {tool_name}", "content": json.dumps(tool_args, indent=2, ensure_ascii=False), "lang": "json"})
                    
                    # 4. Thực thi công cụ và nhận Observation
                    observation = agent._execute_tool(tool_name, tool_args)
                    obs_str = str(observation)
                    
                    # Hiển thị Observation
                    with status_placeholder:
                        st.markdown("**🔍 Kết quả thu nhận (Observation):**")
                        st.code(obs_str[:2000] + "\n\n...[Đã cắt bớt hiển thị trên UI]..." if len(obs_str) > 2000 else obs_str)
                    ui_steps_log.append({"title": f"Observation {steps_count}", "content": obs_str})
                    
                    agent.history.append({"role": "user", "content": f"Observation: {obs_str}"})
                    
                if not final_answer:
                    final_answer = "Vượt quá giới hạn số bước ReAct tối đa mà chưa tìm ra kết quả."
                    status_placeholder.update(label="🚨 Thất bại (Timeout)", state="error", expanded=True)
                    
                # Hiển thị kết quả cuối cùng lên UI chat
                st.markdown(final_answer)
                
                # Lưu vào lịch sử chat kèm theo danh sách các bước để render lại khi refresh
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "steps": ui_steps_log
                })
                
            except Exception as e:
                st.error(f"Lỗi khi thực thi Agent: {e}")
                status_placeholder.update(label="🚨 Lỗi thực thi", state="error", expanded=True)

# --- ĐỊNH NGHĨA DIALOG MODAL CHO DEBUG STUDIO (STREAMLIT 1.58.0+) ---
@st.dialog("🛠️ Hệ thống Debug & Telemetry Logs", width="large")
def show_debug_dialog():
    # 1. Thu thập thông tin debug
    debug_data = {
        "active_provider": st.session_state.provider_name if "provider_name" in st.session_state else "Unknown",
        "max_steps": st.session_state.agent.max_steps if "agent" in st.session_state else 10,
        "total_messages": len(st.session_state.messages),
        "conversation_history_raw": st.session_state.messages,
    }
    
    # 2. Đọc logs telemetry gần nhất từ logs/ directory nếu có
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    recent_logs = []
    if os.path.exists(logs_dir):
        try:
            log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith(".log") or f.endswith(".json")]
            if log_files:
                latest_log = max(log_files, key=os.path.getmtime)
                with open(latest_log, "r", encoding="utf-8") as lf:
                    recent_logs = lf.readlines()[-30:] # Lấy 30 dòng logs gần nhất
        except Exception as e:
            recent_logs = [f"Không thể đọc log file: {str(e)}"]
            
    debug_data["recent_telemetry_logs"] = recent_logs
    
    debug_str = json.dumps(debug_data, indent=2, ensure_ascii=False)
    
    st.info("💡 Bạn có thể bấm vào biểu tượng **Copy** ở góc trên bên phải của hộp code dưới đây để lấy toàn bộ thông tin debug một cách dễ dàng.")
    st.code(debug_str, language="json")

# Kích hoạt mở modal dialog nổi độc lập (không ảnh hưởng giao diện chat chính ở sau)
if "trigger_debug_modal" in st.session_state and st.session_state.trigger_debug_modal:
    st.session_state.trigger_debug_modal = False
    show_debug_dialog()
