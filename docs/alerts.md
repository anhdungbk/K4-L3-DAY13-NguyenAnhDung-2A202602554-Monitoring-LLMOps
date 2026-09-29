# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1: API latency SLO breach

- Severity: warning.
- Duration: P95 `latency_ms` > 3000 ms trong 5 phút.
- Kênh thông báo: Slack `#llmops-alerts`.
- SLI/SLO liên quan: `fast_successful_requests`, target 99.5% trong 28 ngày.
- Ảnh hưởng tới người dùng: câu trả lời chậm, có nguy cơ làm cạn error budget.
- Ba bước kiểm tra đầu tiên: xem panel Latency/TTFT; lọc `response_sent` chậm theo `correlation_id`; mở trace tương ứng để so sánh retrieval với generation.
- Mitigation tạm thời: tắt incident nếu là practice, giảm concurrency hoặc dùng fallback/retry có giới hạn; không tắt logging/tracing.
- Owner: `llmops-on-call`.

## Alert 2: API error rate high

- Severity: critical.
- Duration: `error_rate_pct` > 2% trong 5 phút.
- Kênh thông báo: Slack `#llmops-alerts`.
- SLI/SLO liên quan: error-rate guardrail tối đa 2%.
- Ảnh hưởng tới người dùng: request thất bại hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: xem panel Errors và breakdown `error_type`; tìm `request_failed` theo correlation ID; kiểm tra trace/span retrieval của một request thất bại.
- Mitigation tạm thời: disable incident gây lỗi, kiểm tra dependency retrieval, và chỉ retry các lỗi có thể retry với backoff.
- Owner: `llmops-on-call`.

## Alert 3: Retrieval success degraded

- Severity: warning.
- Duration: `retrieval_success_rate_pct` < 90% trong 10 phút.
- Kênh thông báo: Slack `#llmops-alerts`.
- SLI/SLO liên quan: retrieval success guardrail tối thiểu 90%.
- Ảnh hưởng tới người dùng: câu trả lời thiếu ngữ cảnh nên quality proxy có thể giảm.
- Ba bước kiểm tra đầu tiên: xem retrieval success ở panel Errors; lấy request có `tool_success=false`; mở trace để kiểm tra child observation `retrieval`.
- Mitigation tạm thời: kiểm tra vector-store/retriever, dùng fallback corpus nếu an toàn, sau đó xác nhận recovery bằng workload mới.
- Owner: `llmops-on-call`.
