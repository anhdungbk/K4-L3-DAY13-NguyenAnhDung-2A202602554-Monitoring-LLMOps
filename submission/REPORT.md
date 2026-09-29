# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Anh Dũng    
- **MSSV:** 2A202602554
- **Lớp:** K4-L3A
- **Repository URL:** 
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602554`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 — 45 records; thiếu required fields: 40; thiếu enrichment: 40; correlation ID: 0; PII leak: 0 | 100/100 — 21 records; thiếu required/enrichment: 0; 10 correlation ID; PII leak: 0 | Sau CP1 đã đo trên file log mới, không trộn baseline. |
| `validate_dashboard.py` | Hợp lệ: 6/6 panel | Chưa thực hiện CP2 | Dashboard contract hợp lệ. |
| `pytest` | 22 passed (1.07s) | 23 passed (1.02s) sau CP1 | Đã bổ sung test CCCD/thẻ. |
| Số traces hợp lệ | Workload CP0 đã gửi 10 request HTTP 200 khi `tracing_enabled: true` | Chờ kiểm tra trực quan và evidence trên Langfuse | Prompt `day13-chat` label `production` chưa tồn tại, app dùng local fallback. |
| Số PII leak | 0 | 0 | Validator CP1 không phát hiện PII nguyên văn. |
| Latency P95 / TTFT P95 | Chưa tổng hợp dashboard runtime | Chưa thực hiện CP2 | Log response có latency/TTFT. |
| Retrieval success rate | Chưa tổng hợp dashboard runtime | Chưa thực hiện CP2 | Request baseline trả HTTP 200. |

### CP0 — Setup và baseline (2026-09-29)

- `GET http://127.0.0.1:8000/health` trả HTTP 200 với `ok: true` và `tracing_enabled: true`.
- Đã chạy `scripts/load_test.py`: 10/10 request trả HTTP 200.
- `data/logs.jsonl` đã tồn tại, với 45 records tại thời điểm ghi baseline.
- Langfuse đã được bật trong API. Cần mở đúng project Langfuse cá nhân để xác nhận các trace mới và lưu evidence; không mở/chụp API Keys.
- Trong workload, Langfuse báo không tìm thấy prompt `day13-chat` ở label `production` (HTTP 404), nên app fallback sang prompt local. Đây là phần cần tạo/cấu hình ở CP2, không chặn baseline CP0.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xoá `structlog` context ở đầu mỗi request, dùng `x-request-id` nếu client gửi hoặc sinh `req-<8-hex>`, bind vào context và trả lại qua response header `x-request-id`.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash` (SHA-256 rút gọn), `session_id`, `feature`, `model` và `env`; response log thêm latency, TTFT, token, cost, quality và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` chạy sau context/timestamp nhưng trước JSON file writer và console renderer, scrub đệ quy mọi string trong event. Pattern bao phủ email, số điện thoại Việt Nam, CCCD 12 số và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** Xoá `data/logs.jsonl` baseline, chạy workload 10 request mới. `validate_logs.py` đạt 100/100: 21 records, 0 thiếu required/enrichment, 10 correlation IDs, 0 PII leak. Kiểm tra response có `x-request-id: req-manual01` và `x-response-time-ms: 0.88`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chờ thao tác tạo prompt/version và kiểm tra trace trực tiếp trên Langfuse Cloud; không dùng trace ID của người khác.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` (agent root) → `retrieval` (retriever) và `fake-llm-generation` (generation). Hai child observation tắt capture raw input/output; generation ghi model, usage và cost.
- **Cách nối trace với log:** `correlation_id` đã được bind vào structured log CP1 và trace metadata của root observation.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 — labels `baseline` và `production` sau rollback.
- **Version/label candidate:** Version 2 — label `candidate`.
- **Trace ID của mỗi version:** v1 (`production`/`baseline`): `aa7cc798db899b4137365aaabdc1edf8`; v2 (`candidate`): `963204dd54aa2750c5518c6ba65701d3`.
- **Cách promote và rollback `production`:** Đã gắn `production` vào v2 để promote, sau đó gắn lại vào v1 để rollback; label `candidate` vẫn trỏ v2.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `scripts/render_dashboard.py` sinh `evidence/11-dashboard-overview.html` từ `data/logs.jsonl`; đủ latency/TTFT, traffic, errors/retrieval, cost, tokens và quality; time range 60 phút, refresh target 30 giây và threshold theo contract.
- **SLO và lý do chọn:** SLO `fast_successful_requests`: request có `response_sent` với latency không quá 3000 ms, target 99.5% trong 28 ngày. Ngưỡng 3000 ms khớp panel latency contract.
- **Cách tính error budget:** 0.5% tổng request trong cửa sổ; ví dụ 100,000 request cho phép tối đa 500 request lỗi hoặc vượt ngưỡng latency.
- **Ba alert và runbook tương ứng:** `api_latency_slo_breach` (P95 > 3000 ms/5m), `api_error_rate_high` (>2%/5m), `retrieval_success_degraded` (<90%/10m); tất cả gửi Slack `#llmops-alerts`, có owner và runbook trong `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
