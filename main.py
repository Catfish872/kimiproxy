# main.py (最终正确、严格遵循 OpenAI 规范的版本)

import logging
import json
import httpx
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import StreamingResponse

# --- 配置 ---
KIMI_API_BASE_URL = "https://api.kimi.com/coding"
KIMI_MODEL_NAME = "kimi-for-coding"
USER_AGENT = "KimiCLI/0.2.0"

# --- 日志设置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Kimi API OpenAI Proxy",
    description="An OpenAI-compatible API for Kimi API.",
    version="1.1.0"
)

# --- 创建一个 /v1 路由 ---
# 这样可以确保所有路径都严格符合 OpenAI 的 /v1/.. 规范
router_v1 = APIRouter(prefix="/v1")


# --- 实现 /v1/models 端点 ---
@router_v1.get("/models")
async def list_models():
    """
    严格按照 OpenAI 规范，返回模型列表。
    只包含我们代理的 Kimi 模型。
    """
    model_data = {
        "object": "list",
        "data": [
            {
                "id": KIMI_MODEL_NAME,
                "object": "model",
                "created": 1677610602,
                "owned_by": "moonshot-ai",
            }
        ],
    }
    return model_data


# --- 实现 /v1/chat/completions 端点 ---
@router_v1.post("/chat/completions")
async def chat_completions(request: Request):
    """
    严格按照 OpenAI 规范，处理聊天请求。
    这个函数会调用我们成功的伪装路由。
    """
    target_url = f"{KIMI_API_BASE_URL}/v1/chat/completions"

    # 复制客户端发来的 headers，并强制替换 User-Agent
    headers = dict(request.headers)
    headers["User-Agent"] = USER_AGENT
    headers["host"] = "api.kimi.com"
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)
    headers.pop("connection", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            proxied_request = client.build_request(
                method="POST",
                url=target_url,
                headers=headers,
                content=body
            )

            logging.info(f"Proxying to: {target_url}")

            proxied_response = await client.send(proxied_request, stream=True)

            if 'text/event-stream' in proxied_response.headers.get('content-type', ''):
                return StreamingResponse(
                    proxied_response.aiter_bytes(),
                    status_code=proxied_response.status_code,
                    headers=dict(proxied_response.headers)
                )
            else:
                response_body = await proxied_response.aread()
                return Response(
                    content=response_body,
                    status_code=proxied_response.status_code,
                    headers=dict(proxied_response.headers)
                )

        except httpx.RequestError as e:
            logging.error(f"Proxying error: {e}")
            return Response(
                content=json.dumps({"error": {"message": str(e), "type": "proxy_error"}}),
                status_code=502
            )


# 将 /v1 路由注册到主应用
app.include_router(router_v1)


# --- 健康检查和根路径 ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def read_root():
    return {"message": "Kimi API Proxy is running. Use /v1/models and /v1/chat/completions endpoints."}
