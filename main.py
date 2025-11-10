python
import logging
import json
import httpx  # 使用 httpx 替代 requests，因为它对异步和代理更友好
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

# --- 配置 ---
# Kimi API 的基础 URL
KIMI_API_BASE_URL = "https://api.kimi.com/coding"
# 我们伪造的 User-Agent
# 这里硬编码一个已知可用的版本，避免了动态获取的复杂性
USER_AGENT = "KimiCLI/0.2.0"

# --- 日志设置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Kimi API OpenAI Proxy",
    description="A lightweight proxy to add the correct User-Agent for Kimi API, making it compatible with any OpenAI client.",
    version="1.0.0"
)


# --- 核心代理逻辑 ---
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reverse_proxy(request: Request, path: str):
    """
    这是一个通用的反向代理端点，它会捕获所有请求。
    """
    # 1. 构造目标 URL
    target_url = f"{KIMI_API_BASE_URL}/{path}"

    # 2. 复制原始请求的 Headers，并添加/修改 User-Agent
    headers = dict(request.headers)
    headers["User-Agent"] = USER_AGENT
    # Host header 需要指向目标服务器
    headers["host"] = "api.kimi.com"

    # 移除在转发时可能引起问题的 headers
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)

    # 3. 获取请求体
    body = await request.body()

    # 4. 使用 httpx 客户端发起异步请求
    async with httpx.AsyncClient() as client:
        try:
            # 发起请求，注意 stream=True 用于处理流式响应
            proxied_request = client.build_request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body
            )

            logging.info(f"Proxying request: {request.method} {target_url}")

            # 发送请求并获取流式响应
            proxied_response = await client.send(proxied_request, stream=True)

            # 检查是否为 SSE (Server-Sent Events) 流式响应
            is_sse = proxied_response.headers.get('content-type', '').lower() == 'text/event-stream'

            if is_sse:
                # 如果是 SSE，我们以流的方式返回
                async def stream_generator():
                    async for chunk in proxied_response.aiter_bytes():
                        yield chunk

                # 复制原始响应的 headers
                response_headers = dict(proxied_response.headers)
                response_headers.pop("content-encoding", None)  # Let FastAPI handle encoding

                return StreamingResponse(
                    stream_generator(),
                    status_code=proxied_response.status_code,
                    headers=response_headers
                )
            else:
                # 如果是普通响应，一次性读取并返回
                response_body = await proxied_response.aread()

                response_headers = dict(proxied_response.headers)
                response_headers.pop("content-encoding", None)

                return Response(
                    content=response_body,
                    status_code=proxied_response.status_code,
                    headers=response_headers
                )

        except httpx.RequestError as e:
            error_message = f"Error proxying request to Kimi API: {e}"
            logging.error(error_message)
            return Response(
                content=json.dumps({"error": {"message": error_message, "type": "proxy_error"}}),
                status_code=502  # Bad Gateway
            )


# --- 根路径和健康检查 ---
@app.get("/")
def read_root():
    return {"message": "Kimi API Proxy is running. Point your OpenAI client to this server's URL."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}