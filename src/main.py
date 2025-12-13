import os
import sys
from openai import OpenAI
from dotenv import load_dotenv


class ChatApp:
    def __init__(self):
        # 1. 初始化配置
        load_dotenv()
        self.base_url = os.getenv("PROXY_BASE_URL")
        self.api_key = os.getenv("PROXY_API_KEY")

        # 默认模型 (兜底用)
        self.current_model = os.getenv("TARGET_MODEL", "gemini-1.5-flash")

        # 缓存模型列表
        self.available_models = []

        # 历史记录
        self.history = [
            {"role": "system", "content": "你是一个幽默风趣的AI助手。"}
        ]

        # 2. 建立客户端
        if not self.base_url or not self.api_key:
            print("❌ 错误：请检查 .env 文件配置")
            sys.exit(1)

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        # 3. 启动时自动拉取模型
        print("正在初始化，获取可用模型列表...")
        self._fetch_remote_models()

    def _fetch_remote_models(self):
        """内部方法：从服务器获取模型列表并缓存"""
        try:
            model_list = self.client.models.list()
            # 提取ID并排序
            self.available_models = sorted([m.id for m in model_list.data])
            print(f"✅ 初始化完成！缓存了 {len(self.available_models)} 个模型。")
        except Exception as e:
            print(f"⚠️ 警告：无法获取模型列表 ({e})")
            print("将仅使用 .env 中配置的默认模型。")
            self.available_models = []

    def select_model_ui(self):
        """交互式选择模型界面"""
        if not self.available_models:
            print("❌ 没有缓存的模型列表，无法切换 (可能由于初始化失败)。")
            # 允许手动输入作为备选
            manual = input("是否手动输入模型名? (y/n): ")
            if manual.lower() == 'y':
                new_name = input("请输入模型ID: ")
                if new_name:
                    self.current_model = new_name
                    print(f"✅ 已切换到: {self.current_model}")
            return

        print("\n--- 可用模型列表 ---")
        for idx, model_id in enumerate(self.available_models):
            # 标记当前正在使用的模型
            marker = "*" if model_id == self.current_model else " "
            print(f"[{idx + 1}]{marker} {model_id}")
        print("--------------------")

        choice = input(f"请输入序号切换模型 (当前: {self.current_model}, 回车取消): ")

        if not choice.strip():
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.available_models):
                self.current_model = self.available_models[idx]
                print(f"✅ 切换成功！当前模型: {self.current_model}")
            else:
                print("❌ 序号无效。")
        except ValueError:
            print("❌ 输入错误，请输入数字。")

    def run(self):
        """主循环"""
        print("\n" + "=" * 50)
        print(f"欢迎使用 Python Chat CLI")
        print(f"当前模型: {self.current_model}")
        print("指令提示:")
        print("  /model  - 切换模型")
        print("  /clear  - 清空对话历史")
        print("  /quit   - 退出程序")
        print("=" * 50 + "\n")

        while True:
            try:
                user_input = input("\n你: ").strip()

                # 处理空输入
                if not user_input:
                    continue

                # --- 指令处理区域 ---
                if user_input.lower() in ["/quit", "exit", "quit"]:
                    print("再见！")
                    break

                if user_input.lower() == "/model":
                    self.select_model_ui()
                    continue  # 跳过本次对话发送

                if user_input.lower() == "/clear":
                    self.history = [{"role": "system", "content": "你是一个幽默风趣的AI助手。"}]
                    print("🧹 记忆已清除。")
                    continue
                # ------------------

                # 正常对话逻辑
                self.history.append({"role": "user", "content": user_input})

                print(f"AI ({self.current_model}): ", end="", flush=True)

                response = self.client.chat.completions.create(
                    model=self.current_model,  # 使用动态变量
                    messages=self.history,
                    stream=True,
                    temperature=0.7,
                )

                full_reply = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        full_reply += content

                self.history.append({"role": "assistant", "content": full_reply})
                print("")  # 换行

            except KeyboardInterrupt:
                print("\n程序已停止。")
                break
            except Exception as e:
                print(f"\n❌ 请求错误: {e}")


if __name__ == "__main__":
    app = ChatApp()
    app.run()