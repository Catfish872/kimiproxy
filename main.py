# main.py (v9.2.0 生产优化版)

import logging
import json
import httpx
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import StreamingResponse

# --- 配置 ---
# ★★★★★ 核心原则：严格遵守用户指定的上游 URL ★★★★★
KIMI_API_BASE_URL = "https://api.kimi.com/coding"
USER_AGENT = "KimiCLI/0.2.0"

# --- 日志设置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Kimi API OpenAI Proxy",
    description="An absolutely transparent proxy. It unconditionally forwards the model specified by the client to the designated upstream URL.",
    version="9.2.0"  # 版本号迭进
)

# --- 创建 /v1 路由 ---
router_v1 = APIRouter(prefix="/v1")


async def stream_proxy_handler(target_url: str, headers: dict, body: bytes):
    """
    一个透明的字节流代理。它从上游获取所有数据块并立即转发给客户端。
    这种设计天然支持所有SSE（Server-Sent Events）负载，包括常规内容、思维链、工具调用等。
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", target_url, headers=headers, content=body) as response:
                if response.status_code != 200:
                    error_content = await response.aread()
                    logging.error(
                        f"Upstream server returned an error: {response.status_code} - {error_content.decode()}")
                    yield json.dumps({"error": {
                        "message": f"Kimi API Error: {response.status_code} - {error_content.decode()}",
                        "type": "upstream_error"}}).encode('utf-8')
                    return

                # ★★★★★ 修改(1)：移除调试日志 ★★★★★
                # 原始的调试日志已被移除，使生产环境日志更清洁。
                # try/except 块仍然保留，以防止潜在的解码错误（虽然我们不再打印）。
                async for chunk in response.aiter_bytes():
                    try:
                        # 仅在需要深度调试时取消注释以下行
                        # chunk_text = chunk.decode('utf-8').strip()
                        # if chunk_text:
                        #     logging.info(f"[RAW CHUNK]: {chunk_text}")
                        pass
                    except:
                        pass
                    yield chunk
        except httpx.RequestError as e:
            logging.error(f"Streaming proxy error: {e.__class__.__name__} - {e}")
            yield json.dumps({"error": {"message": f"Proxy request failed: {str(e)}", "type": "proxy_error"}}).encode(
                'utf-8')


@router_v1.post("/chat/completions")
async def chat_completions(request: Request):
    target_url = f"{KIMI_API_BASE_URL}/v1/chat/completions"

    body = await request.body()
    is_stream = False

    # --- 智能模式切换逻辑 ---
    try:
        request_data = json.loads(body)
        is_stream = request_data.get("stream", False)

        # 检查是否使用了我们定义的虚拟 "thinking" 模型
        if request_data.get("model") == "kimi-for-coding-thinking":
            logging.info("Virtual model 'kimi-for-coding-thinking' detected. Enabling thinking mode.")
            request_data["thinking"] = True
            request_data["model"] = "kimi-for-coding"
            body = json.dumps(request_data).encode('utf-8')
            logging.info(f"Modified request body for upstream: {body.decode('utf-8')}")

    except json.JSONDecodeError:
        logging.warning("Received a request with a non-JSON body. Passing through without modification.")
        pass

    headers_to_forward = dict(request.headers)
    headers_to_forward["host"] = "api.kimi.com"
    headers_to_forward["user-agent"] = USER_AGENT
    headers_to_forward.pop("content-length", None)
    headers_to_forward.pop("transfer-encoding", None)
    headers_to_forward["connection"] = "close"

    if is_stream:
        response_headers = {"Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache",
                            "Connection": "keep-alive"}
        return StreamingResponse(stream_proxy_handler(target_url, headers_to_forward, body), headers=response_headers,
                                 media_type="text/event-stream")
    else:
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                proxied_response = await client.post(url=target_url, headers=headers_to_forward, content=body)
            response_headers = dict(proxied_response.headers)
            response_headers.pop("content-length", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("connection", None)
            return Response(content=proxied_response.content, status_code=proxied_response.status_code,
                            headers=response_headers)
        except httpx.RequestError as e:
            logging.error(f"Non-streaming proxy error: {e.__class__.__name__} - {e}")
            return Response(content=json.dumps({"error": {"message": str(e), "type": "proxy_error"}}), status_code=502)


# ★★★★★ 核心原则：/v1/models 只是一个给客户端UI看的、非限制性的“便利贴” ★★★★★
@router_v1.get("/models")
async def list_models():
    """
    Provides a comprehensive list of potential models to the client UI.
    This list DOES NOT restrict which model can be used in the completions endpoint.
    It's a convenience feature for model selection in UIs like ChatBox.
    """
    return {
        "object": "list",
        "data": [
            {"id": "kimi-for-coding", "object": "model", "owned_by": "moonshot-ai"},
            {"id": "kimi-for-coding-thinking", "object": "model", "owned_by": "moonshot-ai"},
        ]
    }


# 将 /v1 路由注册到主应用
app.include_router(router_v1)


# --- 根路径 (用于简单验证) ---
@app.get("/")
def read_root():
    return {"status": "running"}
