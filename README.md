# Kimi for Coding OpenAI 兼容代理

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg?logo=docker)](https://www.docker.com/)

一个将 Kimi `kimi-for-coding` 模型 API 转换为 OpenAI `chat/completions` 格式的代理服务器。它允许您在任何支持 OpenAI API 标准的客户端或应用程序（如 ChatBox, NextChat, VSCode 插件等）中无缝使用 Kimi 的强大编码模型。

## 核心特性

- **OpenAI 格式兼容**: 完全兼容 OpenAI 的 `/v1/chat/completions` 和 `/v1/models` API 接口。
- **透明代理**: 无条件转发客户端指定的模型参数，不进行任何限制。
- **流式与非流式支持**: 支持流式（Server-Sent Events）和非流式两种响应模式。
- **部署简单**: 提供 Docker 和 Docker Compose 配置，支持一键式服务器部署，同时也支持传统的本地 Python 环境部署。
- **高性能**: 基于 FastAPI 和 httpx 构建，提供高性能的异步处理能力。

## API 密钥获取

要使用此代理，您需要一个有效的 Kimi For Coding API Key 密钥。

1.  访问 Kimi 官方网站并登录您的账户。
2.  打开 [Kimi 会员计划页面](https://www.kimi.com/membership/pricing)。
3.  根据您的需求，订阅任一付费会员计划（如 Andante, Moderato, Allegretto）。这些计划包含了对 `Kimi For Coding` 模型的 API 调用额度。
4.  订阅成功后，在您的账户或开发者设置中找到您的 API 密钥 (API Key)。

## 部署指南

您可以选择以下任意一种方式进行部署。

### 1. 服务器部署 (推荐，使用 Docker)

这是最推荐的部署方式，稳定、省心且易于管理。

**前提条件:**
*   已安装 [Docker](https://www.docker.com/get-started) 和 [Docker Compose](https://docs.docker.com/compose/install/)。

**步骤:**

1.  克隆本仓库到您的服务器：
    ```bash
    git clone https://github.com/Catfish872/kimiproxy.git
    cd kimiproxy
    ```

2.  在项目根目录下，使用 Docker Compose 一键启动服务：
    ```bash
    docker-compose up -d
    ```
    此命令会在后台构建并启动容器。服务将在 `11435` 端口上运行。

3.  **管理服务:**
    *   查看日志: `docker-compose logs -f`
    *   停止服务: `docker-compose down`
    *   重启服务: `docker-compose restart`

### 2. 本地部署 (用于开发和测试)

**前提条件:**
*   Python 3.11 或更高版本。

**步骤:**

1.  克隆本仓库：
    ```bash
    git clone https://github.com/Catfish872/kimiproxy.git
    cd kimiproxy
    ```

2.  创建并激活虚拟环境 (推荐):
    ```bash
    python -m venv venv
    source venv/bin/activate  # on Windows use `venv\Scripts\activate`
    ```

3.  安装依赖项：
    > **注意**: 项目代码使用了 `httpx`，请确保 `requirements.txt` 文件内容正确。
    ```bash
    pip install -r requirements.txt
    ```

4.  启动应用服务器：
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 11435
    ```
    服务现在运行在 `http://localhost:11435`。

## 使用方法

### 客户端配置

在您的 AI 客户端（如 ChatBox）中，进行如下配置：

-   **API 地址 (API Base URL / Endpoint)**: `http://<您的服务器IP或域名>:11435/v1`
-   **API 密钥 (API Key)**: 填入您从 Kimi 获取的 API 密钥。
-   **模型 (Model)**: 选择或手动填入 `kimi-for-coding` 或 `kimi-for-coding-thinking`。

### 请求输入/输出结构

本项目完全遵循 OpenAI 的 Chat Completions API 结构。

**请求 URL**: `POST /v1/chat/completions`

**请求体 (JSON Body)**:
```json
{
  "model": "kimi-for-coding", // 或者 "kimi-for-coding-thinking"
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "用 Python 写一个快速排序算法"
    }
  ],
  "stream": false, // 设置为 true 以获取流式响应
  "temperature": 0.7,
  // ... 其他 OpenAI 支持的参数
}
```

**响应体 (非流式)**:
与 OpenAI 格式一致的 JSON 对象。

**响应体 (流式)**:
符合 Server-Sent Events (SSE) 规范的数据块流。

### cURL 请求示例

#### 标准模式 (非流式)

```bash
curl http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的KIMI_API_KEY>" \
  -d '{
    "model": "kimi-for-coding",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

#### 思维链模式 (流式)

```bash
curl http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的KIMI_API_KEY>" \
  -d '{
    "model": "kimi-for-coding-thinking",
    "messages": [{"role": "user", "content": "帮我规划一个为期三天的北京旅游路线"}],
    "stream": true
  }'
```

## 模型支持

本代理通过 `/v1/models` 端点向客户端声明支持以下模型：

-   `kimi-for-coding`: 标准的 Kimi 编码模型。
-   `kimi-for-coding-thinking`: **虚拟模型**。选择此模型后，代理会自动在发送给 Kimi 的请求中加入 `"thinking": true` 参数，以激活模型的思维链输出，非常适合需要观察模型推理过程的场景。

## 项目文件结构

```
.
├── .github/              # GitHub Actions 工作流 (如果存在)
├── __pycache__/          # Python 缓存目录
├── docker-compose.yml    # Docker Compose 配置文件，用于一键部署
├── Dockerfile            # Docker 镜像构建文件
├── main.py               # FastAPI 应用主文件
└── requirements.txt      # Python 依赖项列表
```

### `requirements.txt` 内容修正

为了确保项目能正常运行，请确认 `requirements.txt` 文件内容如下，它使用 `httpx` 来处理异步网络请求：

```text
fastapi
uvicorn
httpx
```

## 许可证

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。
