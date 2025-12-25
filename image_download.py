import requests
import os

image_url = "https://i.imgur.com/8ZqX0yQ.png"
save_dir = "./image"
save_path = os.path.join(save_dir, "Aichi_Kanon.png")

# 确保目录存在
os.makedirs(save_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/143.0.0.0 Safari/537.36"
}

try:
    response = requests.get(image_url, headers=headers, stream=True)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    print(f"图片已成功保存到 {os.path.abspath(save_path)}")

except requests.exceptions.RequestException as e:
    print("下载图片失败:", e)
