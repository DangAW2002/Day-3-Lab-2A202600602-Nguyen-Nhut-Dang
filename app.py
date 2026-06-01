import os
import sys
import time
import json
import re
from dotenv import load_dotenv
import streamlit as st

# Đảm bảo thư mục gốc nằm trong python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent.agent import ReActAgent
from src.tools.tools import check_stock, get_discount, calc_shipping, get_product_price, calculate_tax

# Cấu hình SEO và thiết lập trang Streamlit ở chế độ Wide
st.set_page_config(
    page_title="ReAct Agent Analytics Engine",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load biến môi trường
load_dotenv()

# Inject CSS tùy chỉnh cho giao diện Premium Glassmorphism
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Giao diện font chữ và nền tối hiện đại */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, .title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Hiệu ứng màu gradient cho tiêu đề chính */
    .main-title {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #8E2DE2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #A0AEC0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Thẻ Glassmorphism cao cấp cho các bước của Agent */
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    .step-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    
    /* Tùy chỉnh màu sắc cụ thể cho từng loại bước */
    .thought-header {
        color: #FBBF24; /* Vàng */
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .action-header {
        color: #60A5FA; /* Xanh dương */
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .observation-header {
        color: #34D399; /* Xanh lá */
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .final-header {
        background: linear-gradient(90deg, #A855F7, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }

    /* CSS cho các số liệu Metric cao cấp */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px 20px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E2E8F0;
        margin: 5px 0;
        font-family: 'Outfit', sans-serif;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CẤU HÌNH -----------------
st.sidebar.markdown("<h2 style='font-family: Outfit; font-weight: 600; color: #E2E8F0;'>⚙️ Cấu hình Tác tử</h2>", unsafe_allow_html=True)

# 1. Chọn LLM Provider
provider_opt = ["MIMO (Mặc định)", "Google / Gemini", "OpenAI", "Local Model (Phi-3 CPU)"]
provider_select = st.sidebar.selectbox("LLM Provider", provider_opt)

# Ánh xạ nhà cung cấp
if provider_select == "MIMO (Mặc định)":
    provider_type = "mimo"
elif provider_select == "Google / Gemini":
    provider_type = "google"
elif provider_select == "OpenAI":
    provider_type = "openai"
else:
    provider_type = "local"

# 2. Điều chỉnh API Keys tùy chọn (Tự động điền từ file .env nếu có)
api_key_override = None
base_url_override = None

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='font-family: Outfit; font-weight: 500; font-size:1.1rem; color: #CBD5E0;'>🔑 Thông tin API Keys</h3>", unsafe_allow_html=True)

if provider_type == "mimo":
    default_endpoint = os.getenv("LLM_ENDPOINT", "https://token-plan-sgp.xiaomimimo.com/v1")
    default_key = os.getenv("MIMO_API_KEY", "")
    
    mimo_endpoint = st.sidebar.text_input("MIMO Endpoint", value=default_endpoint)
    mimo_key = st.sidebar.text_input("MIMO API Key", value=default_key, type="password")
    
    api_key_override = mimo_key if mimo_key else None
    base_url_override = mimo_endpoint if mimo_endpoint else None
    model_name = st.sidebar.text_input("Model Name", value=os.getenv("DEFAULT_MODEL", "mimo-v2.5-pro"))

elif provider_type == "google":
    default_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password")
    
    api_key_override = gemini_key if gemini_key else None
    model_name = st.sidebar.text_input("Gemini Model", value="gemini-1.5-flash")

elif provider_type == "openai":
    default_key = os.getenv("OPENAI_API_KEY", "")
    openai_key = st.sidebar.text_input("OpenAI API Key", value=default_key, type="password")
    
    api_key_override = openai_key if openai_key else None
    model_name = st.sidebar.text_input("OpenAI Model", value="gpt-4o-mini")

else:
    model_name = "local"
    model_path = st.sidebar.text_input("Đường dẫn Model .gguf", value=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"))

# 3. Điều chỉnh tham số suy luận ReAct
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='font-family: Outfit; font-weight: 500; font-size:1.1rem; color: #CBD5E0;'>🧠 Tham số ReAct Loop</h3>", unsafe_allow_html=True)
max_steps = st.sidebar.slider("Số lượt suy luận tối đa (max_steps)", min_value=1, max_value=12, value=6)

# ----------------- MAIN APP INTERFACE -----------------
st.markdown("<div class='main-title'>ReAct Agent Analytics Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Tương tác trực quan và theo dõi luồng tư duy ReAct thực tế trong E-commerce Assistant</div>", unsafe_allow_html=True)

# Hiển thị thông báo trạng thái của môi trường
col_status1, col_status2 = st.columns(2)
with col_status1:
    st.info(f"🟢 **Provider:** {provider_select} | **Model:** `{model_name if provider_type != 'local' else model_path}`")
with col_status2:
    st.success("🛠️ **Công cụ E-commerce khả dụng:** `check_stock`, `get_discount`, `calc_shipping`, `get_product_price`, `calculate_tax`")

# Tạo 2 Tabs trực quan hóa cuộc đối sánh
tab_agent, tab_evaluation = st.tabs(["🤖 ReAct Agent Suite", "📊 Chatbot vs Agent Evaluation"])

with tab_agent:
    # Nhập câu hỏi từ người dùng
    user_query = st.text_input(
        "👤 Nhập câu hỏi mua sắm của bạn:",
        value="I want to buy 2 iPhones using code student and ship to Hanoi. Total cost?",
        placeholder="Ví dụ: Kiểm tra kho iPhone và tính tiền ship đến Hanoi...",
        key="agent_query_input"
    )

    # Nút chạy suy luận
    run_agent = st.button("🚀 Khởi động ReAct Agent loop", type="primary")

    # Thiết lập đối tượng Provider động
    def get_provider():
        try:
            if provider_type == "google":
                from src.core.gemini_provider import GeminiProvider
                return GeminiProvider(model_name=model_name, api_key=api_key_override)
            elif provider_type == "openai":
                from src.core.openai_provider import OpenAIProvider
                return OpenAIProvider(model_name=model_name, api_key=api_key_override)
            elif provider_type == "local":
                from src.core.local_provider import LocalProvider
                if not os.path.exists(model_path):
                    st.error(f"Không tìm thấy tệp mô hình cục bộ tại: `{model_path}`")
                    return None
                return LocalProvider(model_path=model_path)
            else:
                from src.core.llm_provider import LLMProvider
                return LLMProvider(model_name=model_name, api_key=api_key_override, base_url=base_url_override)
        except Exception as e:
            st.error(f"Lỗi khởi tạo Provider: {e}")
            return None

    if run_agent:
        if not user_query:
            st.warning("Vui lòng nhập câu hỏi trước khi chạy!")
        else:
            provider = get_provider()
            if provider:
                # Khai báo cấu trúc tools tĩnh của bài Lab
                tools_spec = [
                    {
                        "name": "check_stock",
                        "description": "Check the current stock of an item in the warehouse. Args: item_name (str).",
                        "func": check_stock
                    },
                    {
                        "name": "get_discount",
                        "description": "Retrieve discount percentage for a coupon code. Args: coupon_code (str).",
                        "func": get_discount
                    },
                    {
                        "name": "calc_shipping",
                        "description": "Calculate shipping cost based on weight and destination. Args: weight (float), destination (str).",
                        "func": calc_shipping
                    },
                    {
                        "name": "get_product_price",
                        "description": "Retrieve the base price of a product. Args: item_name (str).",
                        "func": get_product_price
                    },
                    {
                        "name": "calculate_tax",
                        "description": "Calculate the sales tax (VAT) based on subtotal and destination. Args: subtotal (float), destination (str).",
                        "func": calculate_tax
                    }
                ]

                # Xóa các số liệu từ lần chạy trước để tính toán chính xác cho lượt chạy này
                from src.telemetry.metrics import tracker
                tracker.session_metrics = []

                # Khởi tạo ReActAgent
                agent = ReActAgent(llm=provider, tools=tools_spec, max_steps=max_steps)

                # Setup khu vực hiển thị live logs
                status_container = st.empty()
                timeline_container = st.empty()
                
                status_container.markdown("⏳ **Đang thiết lập kết nối LLM và kích hoạt ReAct loop...**")
                
                # Ghi nhận thời gian bắt đầu
                start_time = time.time()
                
                # Thực thi suy luận (chạy trong khối try-catch và hiển thị kết quả)
                with st.spinner("Agent đang phân tích câu hỏi và tương tác với các công cụ..."):
                    try:
                        # Chạy Agent
                        final_result = agent.run(user_query)
                        
                        # Hoàn tất chạy
                        end_time = time.time()
                        duration = end_time - start_time
                        status_container.markdown(f"✅ **Agent đã hoàn tất suy luận sau {duration:.2f} giây!**")
                        
                        # ----------------- PHÂN TÍCH VÀ HIỂN THỊ DỮ LIỆU TELEMETRY -----------------
                        st.markdown("<h3 style='font-family: Outfit; font-weight:600; color: #CBD5E0;'>📊 Biểu đồ Giám sát cuộc gọi (Telemetry Dashboard)</h3>", unsafe_allow_html=True)
                        
                        # Đọc log sự kiện mới nhất để phân tích Token và chi phí
                        prompt_tokens = 0
                        completion_tokens = 0
                        total_tokens = 0
                        cost_est = 0.0
                        loops_count = 0
                        
                        # Phân tích sơ bộ dựa trên lịch sử suy luận
                        for entry in agent.history:
                            if entry["role"] == "assistant":
                                loops_count += 1
                        
                        # Trích xuất dữ liệu thực tế từ Performance Tracker (nếu có dữ liệu)
                        from src.telemetry.metrics import tracker
                        if tracker.session_metrics:
                            prompt_tokens = sum(m.get("prompt_tokens", 0) for m in tracker.session_metrics)
                            completion_tokens = sum(m.get("completion_tokens", 0) for m in tracker.session_metrics)
                            total_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
                            cost_est = sum(m.get("cost_estimate", 0.0) for m in tracker.session_metrics)
                        else:
                            # Fallback tính gần đúng nếu không có Tracker
                            for entry in agent.history:
                                content_len = len(entry["content"])
                                if entry["role"] == "user":
                                    prompt_tokens += content_len // 4
                                else:
                                    completion_tokens += content_len // 4
                            total_tokens = prompt_tokens + completion_tokens
                            # Ước lượng chi phí fallback cho MIMO
                            cost_est = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000

                        # Hiển thị các khối Metrics
                        st.markdown(f"""
                        <div class='metric-container'>
                            <div class='metric-card'>
                                <div class='metric-lbl'>⏱️ Thời gian chạy (Latency)</div>
                                <div class='metric-val'>{duration:.2f}s</div>
                                <div style='font-size:0.8rem; color:#A0AEC0;'>Tổng thời gian phản hồi</div>
                            </div>
                            <div class='metric-card'>
                                <div class='metric-lbl'>🔄 Lượt suy luận (Steps)</div>
                                <div class='metric-val'>{loops_count} / {max_steps}</div>
                                <div style='font-size:0.8rem; color:#A0AEC0;'>Thought-Action Loops</div>
                            </div>
                            <div class='metric-card'>
                                <div class='metric-lbl'>🏷️ Tổng số Token</div>
                                <div class='metric-val'>{total_tokens:,}</div>
                                <div style='font-size:0.8rem; color:#A0AEC0;'>P: {prompt_tokens:,} | C: {completion_tokens:,}</div>
                            </div>
                            <div class='metric-card'>
                                <div class='metric-lbl'>💵 Chi phí ước tính</div>
                                <div class='metric-val'>${cost_est:.6f}</div>
                                <div style='font-size:0.8rem; color:#A0AEC0;'>Theo cấu giá {provider_type.upper()}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # ----------------- HIỂN THỊ DÒNG TƯ DUY (REASONING TIMELINE) -----------------
                        st.markdown("<h3 style='font-family: Outfit; font-weight:600; color: #CBD5E0; margin-top:20px;'>🧠 Dòng suy luận & Lịch sử Công cụ (Reasoning Trace)</h3>", unsafe_allow_html=True)
                        
                        # Render từng phần tử trong lịch sử tư duy
                        step_index = 0
                        for msg in agent.history:
                            role = msg["role"]
                            content = msg["content"].strip()
                            
                            if role == "user":
                                # Đây là câu hỏi gốc hoặc Observation của công cụ
                                if content.startswith("Observation:"):
                                    obs_content = content.replace("Observation:", "").strip()
                                    st.markdown(f"""
                                    <div class='step-card' style='border-left: 5px solid #34D399; background: rgba(52, 211, 153, 0.02);'>
                                        <div class='observation-header'>🔍 OBSERVATION (Kết quả thực thi)</div>
                                        <pre style='background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; color: #E2E8F0; font-family: monospace; font-size:0.9rem; border: 1px solid rgba(255,255,255,0.05);'>{obs_content}</pre>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                # Phân tách phản hồi của LLM thành Thought, Action, Final Answer
                                # Tìm kiếm Thought và Action
                                thought_match = re.search(r"Thought\s*:\s*(.*?)(?=Action:|Final\s*Answer:|$)", content, re.DOTALL | re.IGNORECASE)
                                action_match = re.search(r"Action\s*:\s*([a-zA-Z0-9_-]+)\s*\(([^)]*)\)", content, re.DOTALL | re.IGNORECASE)
                                final_match = re.search(r"Final\s*Answer\s*:\s*(.*)", content, re.DOTALL | re.IGNORECASE)
                                
                                step_index += 1
                                
                                # Hiển thị Thought
                                if thought_match:
                                    thought_text = thought_match.group(1).strip()
                                    st.markdown(f"""
                                    <div class='step-card' style='border-left: 5px solid #FBBF24;'>
                                        <div class='thought-header'>🧠 THOUGHT (Tư duy của Agent - Bước {step_index})</div>
                                        <div style='color: #CBD5E0; font-size:1rem; line-height: 1.6;'>{thought_text}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Hiển thị Action
                                if action_match:
                                    tool_name = action_match.group(1).strip()
                                    tool_args = action_match.group(2).strip()
                                    st.markdown(f"""
                                    <div class='step-card' style='border-left: 5px solid #60A5FA; background: rgba(96, 165, 250, 0.02);'>
                                        <div class='action-header'>⚙️ ACTION (Gọi công cụ hệ thống)</div>
                                        <div style='color: #E2E8F0; font-size:1.05rem; font-family: monospace; font-weight: bold;'>
                                            👉 Gọi hàm: <span style='color: #93C5FD;'>{tool_name}</span>(<span style='color: #F87171;'>{tool_args}</span>)
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                # Hiển thị Final Answer
                                if final_match:
                                    final_text = final_match.group(1).strip()
                                    st.markdown(f"""
                                    <div class='step-card' style='border-left: 5px solid #EC4899; background: linear-gradient(135deg, rgba(168, 85, 247, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%);'>
                                        <div class='final-header'>🤖 FINAL ANSWER (Câu trả lời cuối cùng)</div>
                                        <div style='color: #F3F4F6; font-size:1.1rem; line-height: 1.6;'>{final_text}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        # ----------------- HIỂN THỊ KẾT QUẢ CUỐI CÙNG -----------------
                        st.markdown("---")
                        st.markdown("<h2 style='font-family: Outfit; font-weight:700; color: #F3F4F6;'>🤖 Phản hồi hoàn chỉnh từ Agent</h2>", unsafe_allow_html=True)
                        st.markdown(final_result)
                        
                    except Exception as ex:
                        st.error(f"Đã xảy ra lỗi trong quá trình thực thi ReAct Agent: {ex}")

with tab_evaluation:
    st.markdown("<h3 style='font-family: Outfit; font-weight:600; color: #CBD5E0; margin-top:10px;'>📊 Evaluation & Analysis Dashboard</h3>", unsafe_allow_html=True)
    st.markdown("So sánh khoa học và đánh giá hiệu năng thực tế giữa mô hình Chatbot tĩnh truyền thống và ReAct Agent trên cùng một kịch bản phức tạp.")
    
    battle_query = st.text_input(
        "👤 Nhập câu hỏi đối sánh kịch bản:",
        value="I want to buy 2 iPhones using code student and ship to Hanoi. Total cost?",
        placeholder="Ví dụ: Kiểm tra kho iPhone và tính tiền ship đến Hanoi...",
        key="battle_query_input"
    )
    
    run_battle = st.button("📊 Khởi động Thử nghiệm & Đối sánh", type="primary", key="run_battle_btn")
    
    if run_battle:
        if not battle_query:
            st.warning("Vui lòng nhập câu hỏi đối sánh!")
        else:
            # Lấy đối tượng provider động
            provider = get_provider()
            if provider:
                # 1. Chạy Standard Chatbot
                chatbot_status = st.empty()
                chatbot_status.markdown("💬 **Standard Chatbot đang phản hồi trực tiếp (Direct LLM call)...**")
                cb_start = time.time()
                
                cb_system = (
                    "You are a standard helpful e-commerce conversational assistant. You must answer the user's question directly to the best of your knowledge. "
                    "Note: You do NOT have access to any external databases or tools. If asked about stock, prices, shipping, or discounts, you must answer based only on what you know. "
                    "Never say you cannot help; try to answer but do not call any functions since you don't have them."
                )
                
                try:
                    cb_response = provider.generate(battle_query, system_prompt=cb_system)
                    if isinstance(cb_response, dict):
                        cb_response_str = cb_response.get("content", "")
                    else:
                        cb_response_str = str(cb_response)
                except Exception as cb_err:
                    cb_response_str = f"Lỗi gọi Chatbot LLM: {cb_err}"
                    
                cb_duration = time.time() - cb_start
                chatbot_status.markdown(f"✅ **Chatbot đã phản hồi sau {cb_duration:.2f} giây!**")
                
                # 2. Chạy ReAct Agent
                agent_status = st.empty()
                agent_status.markdown("🤖 **ReAct Agent đang lập luận đa bước (Thought-Action-Observation loop)...**")
                agent_start = time.time()
                
                tools_spec = [
                    {
                        "name": "check_stock",
                        "description": "Check the current stock of an item in the warehouse. Args: item_name (str).",
                        "func": check_stock
                    },
                    {
                        "name": "get_discount",
                        "description": "Retrieve discount percentage for a coupon code. Args: coupon_code (str).",
                        "func": get_discount
                    },
                    {
                        "name": "calc_shipping",
                        "description": "Calculate shipping cost based on weight and destination. Args: weight (float), destination (str).",
                        "func": calc_shipping
                    },
                    {
                        "name": "get_product_price",
                        "description": "Retrieve the base price of a product. Args: item_name (str).",
                        "func": get_product_price
                    },
                    {
                        "name": "calculate_tax",
                        "description": "Calculate the sales tax (VAT) based on subtotal and destination. Args: subtotal (float), destination (str).",
                        "func": calculate_tax
                    }
                ]
                
                from src.telemetry.metrics import tracker
                tracker.session_metrics = []
                
                agent_obj = ReActAgent(llm=provider, tools=tools_spec, max_steps=max_steps)
                
                try:
                    agent_response = agent_obj.run(battle_query)
                    agent_duration = time.time() - agent_start
                    agent_status.markdown(f"✅ **Agent đã hoàn tất suy luận sau {agent_duration:.2f} giây!**")
                except Exception as ag_err:
                    agent_response = f"Lỗi gọi ReAct Agent: {ag_err}"
                    agent_duration = time.time() - agent_start
                    agent_status.markdown(f"❌ **Agent gặp lỗi!**")
                
                ag_loops = 0
                for entry in agent_obj.history:
                    if entry["role"] == "assistant":
                        ag_loops += 1
                
                # Render So sánh Side-by-side
                st.markdown("<h3 style='font-family: Outfit; font-weight:600; color: #E2E8F0; margin-top:20px; text-align: center;'>📊 PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM</h3>", unsafe_allow_html=True)
                
                col_cb_box, col_ag_box = st.columns(2)
                
                with col_cb_box:
                    st.markdown(f"""
                    <div style='background: rgba(148, 163, 184, 0.05); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 12px; padding: 20px; min-height: 350px;'>
                        <h4 style='color: #94A3B8; font-family: Outfit; margin-top:0;'>💬 Chatbot Baseline (Direct LLM)</h4>
                        <p style='color: #CBD5E0; font-size: 0.9rem; font-weight: bold;'>⚠️ Trạng thái: Độ chính xác thấp (Ảo tưởng thông tin)</p>
                        <p style='color: #CBD5E0; font-size: 0.85rem;'><b>Độ trễ phản hồi:</b> {cb_duration:.2f}s | <b>Lượt lập luận:</b> 1 (Không gọi công cụ)</p>
                        <hr style='border-color: rgba(148, 163, 184, 0.1);'/>
                        <div style='color: #E2E8F0; font-size: 0.95rem; line-height: 1.6;'>
                            {cb_response_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_ag_box:
                    st.markdown(f"""
                    <div style='background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 20px; min-height: 350px;'>
                        <h4 style='color: #34D399; font-family: Outfit; margin-top:0;'>🤖 ReAct Agent (Tool-enabled Loop)</h4>
                        <p style='color: #6EE7B7; font-size: 0.9rem; font-weight: bold;'> Xác thực dữ liệu gốc (Factual Grounding)</p>
                        <p style='color: #CBD5E0; font-size: 0.85rem;'><b>Độ trễ phản hồi:</b> {agent_duration:.2f}s | <b>Lượt lập luận:</b> {ag_loops} (Tương tác công cụ thực tế)</p>
                        <hr style='border-color: rgba(16, 185, 129, 0.1);'/>
                        <div style='color: #E2E8F0; font-size: 0.95rem; line-height: 1.6;'>
                            {agent_response}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Collapsible trace for the agent in the column
                    with st.expander("🔍 Xem dòng suy luận ReAct chi tiết của Agent"):
                        for msg in agent_obj.history:
                            role = msg["role"]
                            content = msg["content"].strip()
                            if role == "user" and content.startswith("Observation:"):
                                st.code(content.replace("Observation:", "").strip(), language="json")
                            elif role == "assistant":
                                st.markdown(content)
                                
                # Bảng so sánh chỉ số định lượng
                st.markdown("<h4 style='font-family: Outfit; font-weight:600; color: #CBD5E0; margin-top:30px;'>📊 Phân tích Đối sánh Định lượng</h4>", unsafe_allow_html=True)
                st.table([
                    {"Tiêu chí so sánh": "Truy cập công cụ & Kho dữ liệu", "Standard Chatbot": "❌ Không hỗ trợ (Tự đoán mò tri thức tĩnh)", "ReAct Agent": " Hỗ trợ đầy đủ (Truy xuất kho thời gian thực)"},
                    {"Tiêu chí so sánh": "Hiện tượng Ảo tưởng (Hallucination)", "Standard Chatbot": "⚠️ Cao (Bịa giá trị kho hàng, chiết khấu và thuế)", "ReAct Agent": " Thấp (Fact-grounded dựa trên API thời gian thực)"},
                    {"Tiêu chí so sánh": "Khả năng suy luận đa bước (System 2)", "Standard Chatbot": "❌ Không (Sinh token liên tục một lượt)", "ReAct Agent": " Đầy đủ (Suy luận Thought-Action-Observation khép kín)"},
                    {"Tiêu chí so sánh": "Độ trễ trung bình (Latency)", "Standard Chatbot": f" Nhanh ({cb_duration:.2f}s)", "ReAct Agent": f" Chậm hơn ({agent_duration:.2f}s do suy luận đa bước)"},
                    {"Tiêu chí so sánh": "Độ phù hợp nghiệp vụ", "Standard Chatbot": "Thích hợp cho hỏi đáp xã giao đơn giản", "ReAct Agent": "🏆 Tối ưu cho quy trình E-commerce và tự động hóa"}
                ])

# Footer thẩm mỹ
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #718096; font-size: 0.85rem; margin-top:20px; font-weight:300;'>"
    "ReAct Agent Dashboard • Thiết kế cao cấp cho Lab 3 Agentic AI Course • Hỗ trợ MIMO, OpenAI, Gemini"
    "</div>", 
    unsafe_allow_html=True
)
