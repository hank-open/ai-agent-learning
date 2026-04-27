"""
多轮对话示例
目的: 理解消息历史和对话上下文
"""

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()

def multi_turn_conversation():
    """模拟多轮对话"""

    messages = []

    # 第 1 轮
    user_input_1 = "我的名字叫 Alice，我是一个数据科学家"
    messages.append({"role": "user", "content": user_input_1})

    response_1 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=messages
    )

    assistant_response_1 = response_1.content[0].text
    messages.append({"role": "assistant", "content": assistant_response_1})

    print(f"User: {user_input_1}")
    print(f"Assistant: {assistant_response_1}\n")

    # 第 2 轮 (Claude 会记得 Alice 的身份)
    user_input_2 = "我的专长是什么？"
    messages.append({"role": "user", "content": user_input_2})

    response_2 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=messages
    )

    assistant_response_2 = response_2.content[0].text
    messages.append({"role": "assistant", "content": assistant_response_2})

    print(f"User: {user_input_2}")
    print(f"Assistant: {assistant_response_2}\n")

    # 第 3 轮
    user_input_3 = "推荐一个学习资源给我"
    messages.append({"role": "user", "content": user_input_3})

    response_3 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=messages
    )

    assistant_response_3 = response_3.content[0].text

    print(f"User: {user_input_3}")
    print(f"Assistant: {assistant_response_3}\n")

    # 总成本统计
    total_input = (response_1.usage.input_tokens +
                   response_2.usage.input_tokens +
                   response_3.usage.input_tokens)
    total_output = (response_1.usage.output_tokens +
                    response_2.usage.output_tokens +
                    response_3.usage.output_tokens)

    total_cost = (total_input * 0.0008 + total_output * 0.004) / 1000

    print(f"总 Token 数: {total_input + total_output}")
    print(f"总成本: ${total_cost:.4f}")
    print(f"\n注意: 第3轮的 input tokens={response_3.usage.input_tokens}，")
    print(f"比第1轮 input tokens={response_1.usage.input_tokens} 多很多，")
    print(f"因为每轮都要把完整历史传入！")
    

if __name__ == "__main__":
    multi_turn_conversation()
