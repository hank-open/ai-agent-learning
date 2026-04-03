"""
简单的 Claude API 调用
目的: 验证 API 连接和基础调用
"""

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()

def basic_call():
    """最简单的一次调用"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "你好，请自我介绍一下"
            }
        ]
    )

    print("Response:", message.content[0].text)
    print(f"Input tokens:  {message.usage.input_tokens}")
    print(f"Output tokens: {message.usage.output_tokens}")
    print(f"Cost: ${(message.usage.input_tokens * 0.0008 + message.usage.output_tokens * 0.004) / 1000:.4f}")

if __name__ == "__main__":
    basic_call()
