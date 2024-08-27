from flask import Flask, render_template, request, session, redirect, url_for
import openai
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于加密会话数据，建议使用一个随机生成的密钥

# 初始化 OpenAI 客户端
openai.api_key = os.getenv("OPENAI_API_KEY")

# 用于保存所有会话内容的文件路径
CHAT_HISTORY_FILE = "chat_history.txt"

def save_chat_history(messages):
    """保存会话内容到文件"""
    with open(CHAT_HISTORY_FILE, "a") as f:
        for message in messages[1:]:  # 跳过第一条系统消息
            f.write(f"{message['role'].capitalize()}: {message['content']}\n")
        f.write("\n")  # 添加空行分隔每个会话

def load_chat_history():
    """加载所有会话内容"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            return f.read()
    return ""

def clean_response(text):
    """清除 ** 号并在序号后换行"""
    text = re.sub(r'\*\*', '', text)  # 去除 ** 号
    text = re.sub(r'(\d+\.)\s*', r'\1\n', text)  # 在序号后添加换行符
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    if "messages" not in session:
        session["messages"] = [{"role": "system", "content": "You are a helpful assistant."}]

    if request.method == "POST":
        user_input = request.form["user_input"]

        # 添加用户消息到对话历史
        session["messages"].append({"role": "user", "content": user_input})

        try:
            # 请求 OpenAI API 获取回应
            completion = openai.ChatCompletion.create(
                model="gpt-4",  # 使用的模型
                messages=session["messages"],  # 提供当前对话历史
                max_tokens=150,  # 设置最大生成令牌数
                temperature=0.7,  # 设置生成文本的创新性（温度）
                top_p=1.0  # 设置核采样的累积概率阈值
            )

            # 获取 AI 的回应
            assistant_response = completion.choices[0].message["content"].strip()

            # 清理返回的文本
            assistant_response = clean_response(assistant_response)

            # 将 AI 的回应添加到对话历史
            session["messages"].append({"role": "assistant", "content": assistant_response})

            # 保存会话内容，包括当前问题和答案
            save_chat_history(session["messages"])

        except openai.error.OpenAIError as e:
            assistant_response = f"An OpenAI error occurred: {e}"
        except Exception as e:
            assistant_response = f"An unexpected error occurred: {e}"

    chat_history = load_chat_history()
    return render_template("index.html", messages=session["messages"][1:], chat_history=chat_history)

@app.route("/new_session")
def new_session():
    session.pop("messages", None)  # 清除对话历史
    # 清空聊天记录文件
    with open(CHAT_HISTORY_FILE, "w") as f:
        f.write("")
    return redirect(url_for("index"))

if __name__ == "__main__":
    # 清空聊天记录文件（重启时）
    with open(CHAT_HISTORY_FILE, "w") as f:
        f.write("")
    app.run(debug=True)
