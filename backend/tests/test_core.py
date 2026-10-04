"""Các bài kiểm tra tự động cho phần nền tảng của Người 1.

Người phụ trách: Người 1 (Lead).
Người 8 sẽ mở rộng sau khi nhóm tích hợp.

Kiểm tra:
1. create_app thành công khi chưa có model.
2. Route có prefix /api/v1 chuẩn, không bị trùng lặp.
3. /docs và /openapi.json truy cập bình thường.
4. GET /api/v1/health trả 200 {"status": "ok"}.
5. GET /api/v1/models placeholder trả 503 SERVICE_UNAVAILABLE đúng cấu trúc.
6. POST /api/v1/predict placeholder trả 503 SERVICE_UNAVAILABLE đúng cấu trúc khi đủ dữ liệu.
7. POST /api/v1/predict thiếu trường bắt buộc trả 422 VALIDATION_ERROR đúng cấu trúc.
8. Route không tồn tại trả 404 NOT_FOUND theo cấu trúc lỗi chuẩn.
9. CORS preflight hoạt động cho origin hợp lệ trong CORS_ORIGINS.
10. CORS headers có mặt trên các phản hồi lỗi (404, 422, 503).
11. Ngoại lệ không dự kiến (500) trả cấu trúc chuẩn, không để lộ exception nội bộ,
    và vẫn giữ header CORS (sử dụng fixture riêng, không sửa app thực tế).
"""

from io import BytesIO
import pytest
from starlette.testclient import TestClient

from app.main import app, create_app


@pytest.fixture
def client() -> TestClient:
    """Fixture cung cấp TestClient cho app chính."""
    return TestClient(app, raise_server_exceptions=False)


def test_import_and_create_app() -> None:
    """Kiểm tra khởi tạo ứng dụng độc lập không cần model weights."""
    test_app = create_app()
    assert test_app is not None
    assert test_app.title == "Image VQA Demo"


def test_routes_prefix_and_no_duplication() -> None:
    """Kiểm tra prefix /api/v1 được cấu hình đúng một lần, không có /api/v1/api/v1."""
    openapi_paths = list(app.openapi()["paths"].keys())
    
    # Phải có các endpoint chính
    assert "/api/v1/health" in openapi_paths
    assert "/api/v1/models" in openapi_paths
    assert "/api/v1/predict" in openapi_paths

    # Tuyệt đối không có đường dẫn bị lặp prefix
    for path in openapi_paths:
        assert not path.startswith("/api/v1/api/v1"), f"Đường dẫn bị lặp prefix: {path}"




def test_docs_and_openapi(client: TestClient) -> None:
    """Kiểm tra /docs và /openapi.json hoạt động bình thường."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert schema["info"]["title"] == "Image VQA Demo"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/models" in schema["paths"]
    assert "/api/v1/predict" in schema["paths"]


def test_health_endpoint(client: TestClient) -> None:
    """GET /api/v1/health trả 200 và {"status": "ok"}."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_models_placeholder_returns_503(client: TestClient) -> None:
    """GET /api/v1/models trả 503 và cấu trúc lỗi SERVICE_UNAVAILABLE."""
    resp = client.get("/api/v1/models")
    assert resp.status_code == 503
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Chức năng đang chờ tích hợp." in data["error"]["message"]


def test_predict_placeholder_with_valid_inputs(client: TestClient) -> None:
    """POST /api/v1/predict trả 503 khi nhận đủ file, question, model_id."""
    fake_image_file = ("sample.jpg", BytesIO(b"\xff\xd8\xff\xe0...fake_image_bytes"), "image/jpeg")
    form_data = {
        "question": "Đây là di tích nào?",
        "model_id": "scratch",
    }
    resp = client.post(
        "/api/v1/predict",
        files={"file": fake_image_file},
        data=form_data,
    )
    assert resp.status_code == 503
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Chức năng đang chờ tích hợp." in data["error"]["message"]


def test_predict_missing_fields_returns_422(client: TestClient) -> None:
    """POST /api/v1/predict thiếu file và model_id trả 422 VALIDATION_ERROR chuẩn."""
    resp = client.post("/api/v1/predict", data={"question": "Có ai ở đây không?"})
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "file" in data["error"]["message"] or "model_id" in data["error"]["message"]


def test_not_found_route_returns_404(client: TestClient) -> None:
    """Đường dẫn không tồn tại trả HTTP 404 theo chuẩn format {"error": ...}."""
    resp = client.get("/api/v1/non_existent_route")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_cors_preflight_for_allowed_origin(client: TestClient) -> None:
    """CORS OPTIONS preflight trả về header access-control-allow-origin cho origin hợp lệ."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    resp = client.options("/api/v1/predict", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_headers_present_on_error_responses(client: TestClient) -> None:
    """CORS headers phải luôn xuất hiện trong response lỗi (404, 503) khi gửi từ origin hợp lệ."""
    # Kiểm tra trên lỗi 503 (placeholder endpoint)
    resp_503 = client.get("/api/v1/models", headers={"Origin": "http://localhost:5173"})
    assert resp_503.status_code == 503
    assert resp_503.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Kiểm tra trên lỗi 404
    resp_404 = client.get("/api/v1/not_found", headers={"Origin": "http://localhost:5173"})
    assert resp_404.status_code == 404
    assert resp_404.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_unhandled_exception_returns_500_with_cors_and_safe_message() -> None:
    """Ngoại lệ không dự kiến (500) trả cấu trúc JSON chuẩn, che giấu chi tiết nội bộ và giữ CORS.

    Sử dụng app fixture riêng để tạo route lỗi giả định nhằm không sửa đổi app thật.
    """
    test_app = create_app()

    @test_app.get("/api/v1/test-fault-injection")
    async def trigger_internal_fault() -> None:
        # Giả lập lỗi ném ra ngoại lệ có chứa thông tin nhạy cảm
        raise RuntimeError("CRITICAL_INTERNAL_DB_SECRET_KEY_123456")

    fault_client = TestClient(test_app, raise_server_exceptions=False)
    resp = fault_client.get(
        "/api/v1/test-fault-injection",
        headers={"Origin": "http://localhost:5173"},
    )

    assert resp.status_code == 500
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Đảm bảo không để lộ chuỗi nhạy cảm hoặc stack trace
    assert "CRITICAL_INTERNAL_DB_SECRET_KEY_123456" not in resp.text
    assert "traceback" not in resp.text.lower()
    # CORS vẫn hoạt động với lỗi 500
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
