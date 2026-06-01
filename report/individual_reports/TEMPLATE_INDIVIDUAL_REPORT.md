# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thanh Toàn
- **Student ID**: 2A202600633
- **Date**: 02/06/2026

---

## I. Technical Contribution (15 Points)

Trong bài Lab này, tôi đã đóng góp quan trọng vào việc hoàn thiện cấu trúc logic cốt lõi của tác tử, tối ưu hóa tính tương thích hệ thống và xây dựng giao diện vận hành trực quan. Các đóng góp cụ thể bao gồm:

1. **Kiến trúc Tác tử ReAct Hợp nhất và Các Công cụ Bổ sung (`src/agent/agent.py` & `src/tools/tools.py`):**
   - Thiết kế và cài đặt lớp `ReActAgent` đa năng, tương thích hoàn toàn với cả các công cụ thương mại điện tử phục vụ chấm điểm bài Lab và các công cụ nạp động Anthropic-style.
   - Trực tiếp đề xuất, cài đặt và tích hợp **2 công cụ thương mại điện tử nâng cao** mới:
     - `get_product_price(item_name: str)`: Tra cứu chính xác giá bán gốc của sản phẩm (ví dụ: iPhone = $999.00, Macbook = $1999.00), giúp tác tử có dữ liệu thực tế để tính toán hóa đơn mà không cần người dùng cung cấp hay tự ảo tưởng giá.
     - `calculate_tax(subtotal: float, destination: str)`: Tính thuế giá trị gia tăng (VAT/Sales Tax) tự động dựa trên tổng tiền và địa điểm giao hàng (ví dụ: Hà Nội = 10%, Đà Nẵng = 8%).
   - Sử dụng cơ chế **dynamic import** cho các thư viện cốt lõi ngoài bài Lab để tránh hoàn toàn lỗi `ModuleNotFoundError` khi triển khai trên các môi trường khác nhau.
   - Xây dựng cơ chế tương thích đầu ra đa nhà cung cấp, tự động phát hiện và chuyển đổi kết quả dạng `dict` (OpenAI, Gemini) và `str` thô (MIMO custom provider) một cách liền mạch mà không gây crash hệ thống.

2. **Cài đặt Giao diện Dashboard Giám sát (`app.py`):**
   - Xây dựng ứng dụng **Streamlit Web Application** hoàn chỉnh với ngôn ngữ thiết kế Glassmorphism hiện đại và tông màu tối (Dark mode) sang trọng.
   - Thiết kế màn hình giám sát trực quan quá trình suy luận ReAct theo thời gian thực (Thought $\rightarrow$ Action $\rightarrow$ Observation $\rightarrow$ Final Answer) sử dụng các thẻ HTML tùy chỉnh và CSS nâng cao.
   - Tích hợp biểu đồ theo dõi hiệu năng Telemetry thời gian thực: Thời gian phản hồi (Latency), số lượt suy luận (Steps), Token tiêu thụ và chi phí USD ước tính của từng phiên làm việc.

---

## II. Debugging Case Study (10 Points)

Trong quá trình phát triển và kiểm thử hệ thống ReAct Agent, tôi đã sử dụng hệ thống Telemetry/Logs để phát hiện và khắc phục hai sự cố nghiêm trọng sau:

### Case Study 1: Lỗi sai định dạng tham số gọi công cụ (`check_stock`)
- **Mô tả lỗi:** Ở bước suy luận đầu tiên, mô hình LLM sinh ra Action dạng từ khóa không mong muốn: `Action: check_stock(iPhones=1)`. Do hệ thống chưa xử lý tốt tham số từ khóa động, hàm thực thi ném lỗi:
  `Lỗi khi thực thi công cụ 'check_stock': check_stock() got an unexpected keyword argument 'iPhones'`.
- **Nguồn Log:** `logs/2026-06-01.log` hoặc `task-107.log` (Lượt 1).
- **Chẩn đoán:** Hàm `check_stock(item_name: str)` trong `tools.py` nhận tham số dạng vị trí (positional argument). Khi LLM sinh ra định dạng từ khóa hoặc JSON dạng `{iPhones: 1}`, bộ phân tích cú pháp trích xuất thành đối số từ khóa `**clean_dict` khiến Python ném lỗi không tìm thấy tham số `iPhones`.
- **Giải pháp xử lý:** Cải tiến hàm điều phối `_execute_tool` trong `src/agent/agent.py`. Thiết lập cơ chế tự động chuyển đổi đối số thông minh: nếu có danh sách đối số vị trí `_args` thì giải nén gọi hàm trực tiếp; nếu là dict tham số nhưng không khớp tên biến, tự động giải nén khóa thô `_raw` hoặc ép kiểu chuỗi để chuyển chính xác vào hàm nhận. Kết quả là Agent tự nhận diện lỗi và tự động sửa sai ở bước 2 bằng lệnh gọi `check_stock("iphone")` thành công.

### Case Study 2: Lỗi phân tích cú pháp do Regex bắt tham số tham lam (Greedy Regex Parsing)
- **Mô tả lỗi:** Khi LLM sinh ra phản hồi dài chứa cả Action và các phần mô tả giả lập kèm dấu ngoặc đơn khác, bộ phân tích cú pháp trích xuất tham số của công cụ `get_discount` chứa toàn bộ đoạn văn bản phía sau, dẫn đến lỗi:
  `Lỗi khi thực thi công cụ 'get_discount': get_discount() got an unexpected keyword argument 'query'`.
- **Nguồn Log:** `task-107.log` (Lượt 3).
- **Chẩn đoán:** Regex cũ sử dụng cơ chế so khớp tham lam với cờ `re.DOTALL`: `Action:\s*(\w+)\((.*)\)`. Ký tự `.*` đã nuốt toàn bộ văn bản từ dấu mở ngoặc đầu tiên đến tận dấu đóng ngoặc cuối cùng của toàn bộ câu trả lời (ở phần bảng Markdown phí ship). Kết quả là chuỗi tham số thô bị phình to chứa cả nội dung Observation và Final Answer giả lập, sau đó rơi vào khối xử lý Fallback và gọi hàm sai mục tiêu.
- **Giải pháp xử lý:** Tôi đã sửa đổi biểu thức chính quy thành cơ chế **non-greedy** chỉ so khớp các ký tự bên trong cặp ngoặc đơn đầu tiên: `Action:\s*(\w+)\(([^)]*)\)`. Việc loại bỏ `re.DOTALL` và thay bằng `[^)]*` giúp đảm bảo lời gọi Action luôn được đóng gói gọn gàng và phân tích chính xác trên một dòng, giúp Agent đạt độ tin cậy tuyệt đối và hoàn thành xuất sắc luồng suy luận chỉ trong 4 bước tối ưu.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning (Khả năng tư duy):**
    Khối `Thought` đóng vai trò là "không gian nháp" (scratchpad) giúp mô hình chia nhỏ các truy vấn phức tạp thành các bước lập kế hoạch rõ ràng trước khi hành động. So với Chatbot thông thường (chỉ đoán từ tiếp theo trực tiếp), ReAct giúp giảm thiểu hiện tượng ảo tưởng (hallucination) vì mô hình buộc phải phân tích logic: "Tôi đang có gì? Tôi cần tìm gì tiếp theo?".

2.  **Reliability (Độ tin cậy):**
    Agent đôi khi có hiệu năng kém hơn Chatbot trong các câu hỏi Q&A đơn giản hoặc các tác vụ không cần công cụ. Trong các kịch bản này, việc bắt buộc chạy qua ReAct Loop làm tăng đáng kể độ trễ (latency), tiêu tốn lượng token lớn và có rủi ro bị kẹt vòng lặp vô hạn hoặc lỗi cú pháp phân tích (Parser Error). Do đó, việc kết hợp linh hoạt cơ chế định tuyến (router) để chỉ kích hoạt ReAct khi cần thiết là cực kỳ quan trọng.

3.  **Observation (Ý nghĩa của phản hồi từ môi trường):**
    Phản hồi `Observation` hoạt động như một vòng phản hồi khép kín (closed-loop feedback). Nó cung cấp cho LLM thông tin thực tế từ thế giới thực (ví dụ: số lượng tồn kho thực tế, phí vận chuyển chính xác). Khi công cụ trả về lỗi hoặc không có dữ liệu, mô hình có thể tự nhận biết và điều chỉnh hướng đi ở bước tiếp theo (như đã chứng minh ở Case Study 1 khi Agent tự động sửa lỗi định dạng gọi hàm).

---

## IV. Future Improvements (5 Points)

Để mở rộng và phát triển hệ thống tác tử này lên quy mô sản xuất (Production-ready), tôi đề xuất các hướng cải tiến sau:

- **Scalability (Khả năng mở rộng):**
  Xây dựng cơ chế hàng đợi bất đồng bộ (Asynchronous Queue) cho các cuộc gọi công cụ. Thay vì chặn luồng chính để chờ kết quả (như gọi API vận chuyển), Agent có thể gửi yêu cầu công cụ vào hàng đợi và xử lý các tác vụ suy luận khác song song, tối ưu hóa thời gian phản hồi của hệ thống.
  
- **Safety (Đảm bảo an toàn):**
  Triển khai mô hình **Supervisor LLM** hoặc các cổng bảo mật (Guardrails) như Llama Guard để kiểm duyệt các Action trước khi thực thi thực tế trên Terminal/Hệ thống (đặc biệt là lệnh `run_command`), ngăn chặn hoàn toàn nguy cơ tấn công tiêm lệnh (Command Injection).
  
- **Performance (Tối ưu hiệu năng):**
  Sử dụng **Vector Database** (Cơ sở dữ liệu vectơ) để thực hiện tìm kiếm và chọn lọc công cụ động (Dynamic Tool Retrieval). Khi hệ thống mở rộng lên hàng trăm công cụ, thay vì nhét toàn bộ mô tả vào System Prompt (gây phình to Token), Agent sẽ tự truy vấn ngữ nghĩa để chỉ lấy ra 3-5 công cụ phù hợp nhất cho ngữ cảnh hiện tại.
