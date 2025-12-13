import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PROXY_API_KEY")
# 确保你的 .env 里 PROXY_BASE_URL 是 https://gcli.ggchan.dev/v1
base_url = "https://gcli.ggchan.dev/v1/chat/completions"

# 常见的 Gemini 模型名变体全集
candidates = [
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",  # Google 原生写法 (嫌疑最大)
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-pro",  # 旧版但常用
    "models/gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "google-gemini",  # 某些代理自定义的
]

print(f"正在连接: {base_url}")
print("-" * 50)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

for model in candidates:
    print(f"尝试模型名: {model.ljust(30)}", end="")

    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}]
    }

    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=10)

        # 获取回复内容
        content = "无内容"
        if response.status_code == 200:
            try:
                content = response.json()['choices'][0]['message']['content']
            except:
                content = str(response.text)[:50]
        else:
            content = f"HTTP {response.status_code}"

        # 核心判断：如果回复里包含 'not found'，说明这个模型名是错的
        if "not found" in content or "404" in content:
            print(f"❌ 失败 (名字不对)")
        else:
            print(f"✅ 成功!!! 回复: {content}")
            print(f"\n🎉 恭喜！请在 .env 里设置 TARGET_MODEL=\"{model}\"")
            break  # 找到对的就停止

    except Exception as e:
        print(f"❌ 异常")

print("-" * 50)