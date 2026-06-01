import os
import re
import json
import sys
import subprocess
from typing import List, Dict, Any, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

# Import các core tools nguyên tử tĩnh
from src.tools.web_search import web_search
from src.tools.fetch_web_content import fetch_web_content
from src.tools.file_io import read_file, write_file
from src.tools.create_new_tool import create_new_tool
import importlib.util

class ReActAgent:
    """
    Một ReAct Agent (Tác tử ReAct) chuyên nghiệp tuân thủ nghiêm ngặt vòng lặp Thought-Action-Observation.
    Hỗ trợ kiến trúc Agent Skills chuẩn hóa của Anthropic và nạp nóng Dynamic Tool Registry.
    """
    
    def __init__(self, llm: LLMProvider, max_steps: int = 8):
        self.llm = llm
        self.max_steps = max_steps
        self.history = []
        self.skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "skills"
        )
        self.tools_registry_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "tools", 
            "tools_registry.json"
        )

    def parse_frontmatter(self, content: str) -> Dict[str, str]:
        """
        Phân tích cú pháp YAML frontmatter tự viết siêu nhẹ (không phụ thuộc vào PyYAML) 
        để trích xuất siêu dữ liệu (name, description) của Skill từ SKILL.md.
        """
        metadata = {}
        content = content.strip()
        if not content.startswith("---"):
            return metadata
            
        lines = content.splitlines()
        yaml_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)
            
        for line in yaml_lines:
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip()
        return metadata

    def load_available_skills_metadata(self) -> List[Dict[str, str]]:
        """
        Quét thư mục skills/ trên filesystem để lấy danh sách siêu dữ liệu (Level 1 Metadata) 
        của tất cả các Kỹ năng đang khả dụng.
        """
        skills_metadata = []
        if not os.path.exists(self.skills_dir):
            return skills_metadata
            
        try:
            # Quét tất cả các thư mục con trong skills/
            for entry in os.scandir(self.skills_dir):
                if entry.is_dir():
                    skill_md_path = os.path.join(entry.path, "SKILL.md")
                    if os.path.exists(skill_md_path):
                        with open(skill_md_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        meta = self.parse_frontmatter(content)
                        if "name" in meta and "description" in meta:
                            meta["path"] = f"skills/{entry.name}/SKILL.md"
                            skills_metadata.append(meta)
        except Exception as e:
            logger.log_event("SKILLS_METADATA_READ_ERROR", {"error": str(e)})
            
        return skills_metadata

    def load_available_tools_metadata(self) -> Dict[str, Any]:
        """
        Đọc tools_registry.json để lấy danh sách các dynamic tools đang có.
        """
        if not os.path.exists(self.tools_registry_path):
            return {}
        try:
            with open(self.tools_registry_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception as e:
            logger.log_event("TOOLS_METADATA_READ_ERROR", {"error": str(e)})
        return {}

    def get_system_prompt(self) -> str:
        """
        Xây dựng System Prompt động kết hợp các Core Tools nguyên tử tĩnh,
        các Dynamic Tools tự học (nạp nóng từ registry) và danh sách Available Skills.
        """
        # Danh sách Core Tools nguyên tử tĩnh
        core_tools_desc = """
1. `web_search(query)`: Tra cứu thông tin trên Internet qua DuckDuckGo không cần API key. Trả về tiêu đề, URL và snippet.
2. `fetch_web_content(url)`: Tải xuống và làm sạch mã HTML của một trang web, chỉ giữ lại văn bản thuần hữu ích để đọc tài liệu.
3. `read_file(path)`: Đọc nội dung của một file văn bản từ ổ đĩa cục bộ (sử dụng để nạp chi tiết Kỹ năng hoặc đọc mã nguồn).
4. `write_file(path, content)`: Ghi nội dung văn bản vào một file trên ổ đĩa.
5. `run_command(cmd)`: Thực thi lệnh trong terminal (sử dụng để chạy thử code, kiểm thử hoặc chạy các script của Kỹ năng/Tools).
6. `create_new_tool(tool_name, code, description, arguments_spec)`: Tạo và đăng ký một công cụ (Tool) vật lý mới bằng code Python hoàn chỉnh. Tham số:
   - `tool_name` (str): Tên snake_case của tool mới (phải trùng với hàm chính, ví dụ: fetch_stock_data).
   - `code` (str): Mã nguồn Python hoàn chỉnh của tool (chứa hàm chính).
   - `description` (str): Mô tả chi tiết khi nào nên sử dụng tool này để gọi sau này.
   - `arguments_spec` (dict): Dict mô tả kiểu dữ liệu và ý nghĩa các tham số đầu vào.
"""

        # Đọc danh sách Kỹ năng khả dụng (Level 1)
        skills = self.load_available_skills_metadata()
        skills_desc_list = []
        for skill in skills:
            skills_desc_list.append(f"- **{skill['name']}** (Đường dẫn: `{skill['path']}`): {skill['description']}")
            
        available_skills_desc = "\n".join(skills_desc_list) if skills_desc_list else "*(Hiện tại chưa có kỹ năng động nào được cài đặt trên hệ thống)*"

        # Đọc danh sách Dynamic Tools tự học (Level 1)
        dynamic_tools = self.load_available_tools_metadata()
        dynamic_tools_desc_list = []
        for name, info in dynamic_tools.items():
            args_info = info.get("arguments", {})
            # Thử parse an toàn nếu arguments lưu dưới dạng chuỗi (do LLM sinh hoặc do lỗi parse trước đó)
            if isinstance(args_info, str):
                try:
                    import ast
                    args_info = ast.literal_eval(args_info)
                except Exception:
                    try:
                        args_info = json.loads(args_info)
                    except Exception:
                        args_info = {"args": args_info}
            
            # Format các đối số
            if isinstance(args_info, dict):
                args_desc_parts = []
                for k, v in args_info.items():
                    if isinstance(v, dict):
                        v_str = ", ".join(f"{sk}: {sv}" for sk, sv in v.items())
                        args_desc_parts.append(f"{k} ({v_str})")
                    else:
                        args_desc_parts.append(f"{k}: {v}")
                args_str = ", ".join(args_desc_parts)
            else:
                args_str = str(args_info)
                
            dynamic_tools_desc_list.append(f"- **{name}({args_str})**: {info.get('description')} (Đường dẫn: `{info.get('file_path')}`)")
            
        available_dynamic_tools_desc = "\n".join(dynamic_tools_desc_list) if dynamic_tools_desc_list else "*(Hiện tại chưa có công cụ tự học động nào được bổ sung)*"

        return f"""Bạn là một ReAct Agent (Tác tử Trí tuệ) có khả năng tự tiến hóa và tự học theo kiến trúc Anthropic Agent Skills và nạp nóng Dynamic Tool Registry.
Bạn tuân thủ nghiêm ngặt quy trình tư duy ReAct (Thought -> Action -> Observation).

### 🛠️ CÁC CÔNG CỤ CỐT LÕI (CORE TOOLS):
Bạn có quyền truy cập trực tiếp vào các công cụ hệ thống nguyên tử sau bằng cú pháp gọi hàm:
{core_tools_desc}

### 🔌 CÁC CÔNG CỤ TỰ BỔ SUNG ĐỘNG (DYNAMIC TOOLS):
Bạn có thể gọi trực tiếp các công cụ tự bổ sung động dưới đây bằng cú pháp gọi hàm tương tự như Core Tools thông thường:
{available_dynamic_tools_desc}

### 🧠 CÁC KỸ NĂNG KHẢ DỤNG HIỆN TẠI (AVAILABLE AGENT SKILLS):
Môi trường ảo của bạn đã được tích hợp sẵn các Kỹ năng chuyên nghiệp dưới đây (Dưới dạng các thư mục filesystem chứa tệp hướng dẫn `SKILL.md`):
{available_skills_desc}

### 📖 CƠ CHẾ TỰ TIẾN HÓA VÀ MỞ RỘNG (SELF-EXTENDING):
1. **Tự tạo công cụ mới**: Nếu người dùng yêu cầu thực hiện một tác vụ chuyên môn phức tạp mà các công cụ hiện tại chưa xử lý tốt, bạn có thể tự thiết kế thuật toán, viết mã nguồn Python hoàn chỉnh và gọi tool `create_new_tool` để đăng ký một Tool mới tinh vào hệ thống!
2. **Nạp nóng và sử dụng**: Ngay sau khi `create_new_tool` trả về thành công, ở câu hỏi tiếp theo (hoặc lượt tiếp theo), Tool đó sẽ tự động được đăng ký và bạn có thể gọi trực tiếp nó qua cú pháp gọi hàm chuẩn!
3. **Đọc Kỹ năng (Progressive Disclosure)**: Khi nhận được yêu cầu phù hợp với một Kỹ năng ở trên, hành động đầu tiên bạn BẮT BUỘC phải làm là gọi công cụ `read_file` để đọc tệp hướng dẫn `SKILL.md` tương ứng của kỹ năng đó (ví dụ: `read_file(path="skills/create-new-skill/SKILL.md")`).

### 📝 ĐỊNH DẠNG PHẢN HỒI (BẮT BUỘC TUÂN THỦ):
Khi nhận được yêu cầu từ người dùng, bạn BẮT BUỘC phải suy luận theo định dạng từng khối như sau ở mỗi lượt:

Thought: dòng tư duy suy luận logic của bạn về bước tiếp theo. Giải thích tại sao bạn gọi công cụ này và bạn kỳ vọng nhận được gì.
Action: tên_công_cụ(các_tham_số)
Observation: kết quả trả về từ việc thực thi công cụ (Hệ thống sẽ cung cấp kết quả này cho bạn, bạn tuyệt đối KHÔNG tự bịa ra phần này).

... (Lặp lại chu trình Thought -> Action -> Observation nếu cần thiết để giải quyết bài toán nhiều bước)

Thought: Tôi đã có đầy đủ thông tin để trả lời người dùng.
Final Answer: câu trả lời hoàn chỉnh, chính xác và chi tiết cuối cùng của bạn cho người dùng.

### ⚠️ QUY TẮC CỰC KỲ QUAN TRỌNG:
1. Bạn chỉ được gọi **MỘT** công cụ duy nhất trong mỗi lượt phản hồi (chỉ sinh ra duy nhất một dòng `Action: ...` ở mỗi lượt).
2. Định dạng gọi Action bắt buộc phải chính xác. Tham số truyền vào hàm có thể viết dưới dạng JSON hoặc định dạng Python thông thường (ví dụ: `web_search(query="gemini sdk")` hoặc `create_new_tool(tool_name="calculate_factorial", ...)`).
3. Nếu người dùng yêu cầu một chức năng phức tạp hoặc nghiệp vụ chuyên sâu chưa có công cụ nào xử lý trực tiếp, hãy lập tức nghĩ đến việc thiết kế và tự viết một Tool mới cho bản thân bằng `create_new_tool`!
"""

    def parse_action(self, text: str) -> Optional[tuple]:
        """
        Phân tích cú pháp thông minh và linh hoạt để trích xuất Tool Name và Arguments từ phản hồi của LLM.
        Sử dụng phân tích cú pháp AST của Python để đạt độ an toàn và chính xác tuyệt đối đối với các cấu trúc phức tạp.
        """
        # Tìm dòng Action: tool_name(arguments)
        match = re.search(r"Action:\s*(\w+)\((.*)\)", text, re.DOTALL)
        if not match:
            return None
            
        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        
        if not raw_args:
            return tool_name, {}
            
        # 1. Thử parse bằng AST (Trình phân tích cú pháp Python chuẩn) - Cực kỳ mạnh mẽ cho keyword arguments phức tạp
        import ast
        try:
            # Bọc raw_args trong một lời gọi hàm giả để parse
            call_expr = f"func({raw_args})"
            parsed_ast = ast.parse(call_expr)
            call_node = parsed_ast.body[0].value
            
            if isinstance(call_node, ast.Call):
                parsed_args = {}
                
                # Xử lý các keyword arguments
                for kw in call_node.keywords:
                    try:
                        # ast.literal_eval an toàn cho dict, list, string, number, boolean, None
                        parsed_args[kw.arg] = ast.literal_eval(kw.value)
                    except Exception:
                        # Fallback nếu chứa cấu trúc phức tạp, dùng ast.unparse để lấy chuỗi
                        val_str = ast.unparse(kw.value).strip()
                        # Bóc tách dấu nháy ngoài cùng nếu có
                        if val_str.startswith(("'", '"')) and val_str.endswith(("'", '"')):
                            val_str = val_str[1:-1]
                        # Clean các ký tự xuống dòng escape
                        val_str = val_str.replace('\\n', '\n').replace('\\t', '\t')
                        parsed_args[kw.arg] = val_str
                        
                # Xử lý các positional arguments (nếu có, map thành đối số đầu tiên)
                if call_node.args and not parsed_args:
                    try:
                        first_arg = ast.literal_eval(call_node.args[0])
                        parsed_args = {"query": first_arg, "url": first_arg, "path": first_arg, "content": first_arg}
                    except Exception:
                        first_arg_str = ast.unparse(call_node.args[0]).strip()
                        if first_arg_str.startswith(("'", '"')) and first_arg_str.endswith(("'", '"')):
                            first_arg_str = first_arg_str[1:-1]
                        parsed_args = {"query": first_arg_str, "url": first_arg_str, "path": first_arg_str, "content": first_arg_str}
                        
                if parsed_args:
                    return tool_name, parsed_args
        except Exception:
            # Bỏ qua lỗi AST để chuyển sang fallback truyền thống bên dưới
            pass
            
        # 2. Fallback 1: Thử parse nếu đối số là một chuỗi JSON hợp lệ
        try:
            cleaned_json = raw_args.replace("'", '"')
            parsed_args = json.loads(cleaned_json)
            if isinstance(parsed_args, dict):
                return tool_name, parsed_args
            else:
                return tool_name, {"_raw": parsed_args}
        except json.JSONDecodeError:
            pass
            
        # 3. Fallback 2: Thử parse định dạng Python keyword arguments thủ công bằng Regex
        parsed_args = {}
        kw_matches = re.finditer(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|({.*?})|(\[.*?\])|(\w+))", raw_args, re.DOTALL)
        has_keywords = False
        
        for kw in kw_matches:
            has_keywords = True
            key = kw.group(1)
            val = next(v for v in kw.groups()[1:] if v is not None)
            
            val = val.strip()
            if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
                try:
                    val = json.loads(val.replace("'", '"'))
                except Exception:
                    pass
            elif val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.isdigit():
                val = int(val)
                
            parsed_args[key] = val
            
        if has_keywords:
            return tool_name, parsed_args
            
        # 4. Fallback 3: Nếu chỉ là một chuỗi đơn thuần (ví dụ: web_search("query string"))
        cleaned_str = re.sub(r"^[\"']|[\"']$", "", raw_args).strip()
        return tool_name, {"query": cleaned_str, "url": cleaned_str, "path": cleaned_str, "content": cleaned_str}

    def run(self, user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Vận hành vòng lặp ReAct Loop (Thought-Action-Observation) thông minh.
        Hỗ trợ truyền bối cảnh lịch sử hội thoại mức cao (high-level conversation history)
        để tạo chatbot multi-turn mà không làm phình to context.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        print(f"\n🤖 [AGENT] Bắt đầu suy luận ReAct cho yêu cầu: '{user_input}'...")
        
        # Thiết lập lịch sử trò chuyện tạm thời cho lượt suy luận hiện tại
        self.history = []
        if conversation_history:
            for msg in conversation_history:
                self.history.append({"role": msg["role"], "content": msg["content"]})
                
        # Thêm yêu cầu hiện tại của người dùng vào lịch sử suy luận
        self.history.append({"role": "user", "content": user_input})
        
        steps = 0
        
        while steps < self.max_steps:
            steps += 1
            print(f"\n💭 [AGENT] Lượt suy luận thứ {steps}/{self.max_steps}...")
            
            # 1. Gọi LLM sinh phản hồi
            system_prompt = self.get_system_prompt()
            
            try:
                # Ghép lịch sử chat thành prompt ngữ cảnh
                context_prompt = ""
                for msg in self.history:
                    role_prefix = "User: " if msg["role"] == "user" else "Assistant: " if msg["role"] == "assistant" else "System/Observation: "
                    context_prompt += f"{role_prefix}{msg['content']}\n\n"
                
                # Gọi LLM sinh Thought + Action
                llm_response = self.llm.generate(
                    context_prompt, 
                    system_prompt=system_prompt,
                    stop=["Observation:", "System/Observation:", "Observation: "]
                )
                response_text = llm_response["content"].strip()
                
                print(f"\n{response_text}\n")
                
                # Đưa Thought + Action của LLM vào lịch sử chat
                self.history.append({"role": "assistant", "content": response_text})
                
                # 2. Kiểm tra xem LLM đã đưa ra câu trả lời cuối cùng chưa
                if "Final Answer:" in response_text:
                    final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
                    final_answer = final_match.group(1).strip() if final_match else response_text
                    logger.log_event("AGENT_END", {"steps": steps, "status": "completed"})
                    return final_answer
                    
                # 3. Phân tích cú pháp gọi Tool (Action)
                parsed = self.parse_action(response_text)
                if not parsed:
                    warning_msg = "Lỗi: Bạn chưa đưa ra câu trả lời cuối cùng (Final Answer) và cũng không gọi đúng định dạng Action (ví dụ: Action: tool_name(arguments)). Vui lòng kiểm tra lại quy tắc định dạng phản hồi."
                    print(f"⚠️ [PARSER ERROR] {warning_msg}")
                    self.history.append({"role": "user", "content": warning_msg})
                    continue
                    
                tool_name, tool_args = parsed
                print(f"⚙️ [EXECUTE TOOL] Đang thực thi công cụ '{tool_name}' với tham số: {tool_args}...")
                
                # 4. Thực thi công cụ
                observation = self._execute_tool(tool_name, tool_args)
                
                # Đảm bảo observation được chuyển thành string sạch
                obs_str = str(observation)
                print(f"🔍 [OBSERVATION] Kết quả nhận được:\n{obs_str[:800]}..." if len(obs_str) > 800 else f"🔍 [OBSERVATION] Kết quả nhận được:\n{obs_str}")
                
                # Đưa kết quả Observation vào lịch sử chat
                self.history.append({"role": "user", "content": f"Observation: {obs_str}"})
                
            except Exception as e:
                error_msg = f"Lỗi hệ thống trong vòng lặp ReAct: {str(e)}"
                print(f"🚨 [SYSTEM ERROR] {error_msg}")
                logger.log_event("AGENT_ERROR", {"error": str(e)})
                return error_msg
                
        timeout_msg = "Không thể tìm ra câu trả lời cuối cùng trong giới hạn số bước cho phép."
        logger.log_event("AGENT_END", {"steps": steps, "status": "timeout"})
        return timeout_msg

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Điều phối thực thi các Core Tools nguyên tử tĩnh và các Dynamic Tools tự học của Agent.
        """
        try:
            if tool_name == "web_search":
                query = args.get("query") or args.get("q") or next(iter(args.values()))
                return web_search(query=query)
                
            elif tool_name == "fetch_web_content":
                url = args.get("url") or next(iter(args.values()))
                return fetch_web_content(url=url)
                
            elif tool_name == "read_file":
                path = args.get("path") or next(iter(args.values()))
                return read_file(path=path)
                
            elif tool_name == "write_file":
                path = args.get("path") or args.get("filepath")
                content = args.get("content") or args.get("data")
                if not path or not content:
                    keys = list(args.keys())
                    if len(keys) >= 2:
                        path = args[keys[0]]
                        content = args[keys[1]]
                return write_file(path=path, content=content)
                
            elif tool_name == "run_command":
                cmd = args.get("cmd") or args.get("command") or next(iter(args.values()))
                
                # Chạy command trong môi trường hiện tại một cách an toàn bằng subprocess
                logger.log_event("TOOL_USE_START", {"tool": "run_command", "command": cmd})
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = result.stdout or ""
                error = result.stderr or ""
                full_output = f"stdout:\n{output}\nstderr:\n{error}" if error else output
                logger.log_event("TOOL_USE_END", {"tool": "run_command", "status": "success" if result.returncode == 0 else "failed"})
                return full_output
                
            elif tool_name == "create_new_tool":
                tool_name_arg = args.get("tool_name")
                code = args.get("code")
                description = args.get("description") or ""
                arguments_spec = args.get("arguments_spec") or {}
                if not tool_name_arg or not code:
                    keys = list(args.keys())
                    if len(keys) >= 2:
                        tool_name_arg = args[keys[0]]
                        code = args[keys[1]]
                return create_new_tool(
                    tool_name=tool_name_arg,
                    code=code,
                    description=description,
                    arguments_spec=arguments_spec
                )
                
            else:
                # Kiểm tra xem có phải là Dynamic Tool tự học trong Registry hay không
                dynamic_tools = self.load_available_tools_metadata()
                if tool_name in dynamic_tools:
                    logger.log_event("DYNAMIC_TOOL_USE_START", {"tool": tool_name, "args": args})
                    
                    # Định vị tệp runner.py và python interpreter
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    runner_path = os.path.join(current_dir, "..", "tools", "runner.py")
                    python_exe = sys.executable  # Trình thông dịch Python của conda environment hiện tại
                    
                    # Thực thi subprocess cô lập hoàn toàn
                    cmd = [python_exe, runner_path, tool_name, json.dumps(args, ensure_ascii=False)]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=15,
                        encoding="utf-8"
                    )
                    
                    output = (result.stdout or "").strip()
                    error = (result.stderr or "").strip()
                    
                    logger.log_event("DYNAMIC_TOOL_USE_END", {
                        "tool": tool_name, 
                        "status": "success" if result.returncode == 0 else "failed"
                    })
                    
                    if result.returncode != 0:
                        return f"Lỗi thực thi trong dynamic tool '{tool_name}':\n{error}"
                    return output
                else:
                    return f"Lỗi: Công cụ '{tool_name}' không tồn tại. Vui lòng chọn một công cụ khả dụng."
                
        except Exception as e:
            return f"Lỗi khi thực thi công cụ '{tool_name}': {str(e)}"
