"""
LLM 参数对比实验
目的: 理解 temperature, max_tokens 的影响
"""

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
import json

client = Anthropic()

def parameter_experiment():
    """对比不同 temperature 的输出"""

    prompt = "请给出一个创意的故事开头，关于一个机器人发现了一个秘密。输出不超过 50 字。"

    configs = [
        {"temperature": 0.0, "name": "确定性 (temp=0)"},
        {"temperature": 0.5, "name": "平衡 (temp=0.5)"},
        {"temperature": 1.0, "name": "创意 (temp=1.0)"},
    ]

    results = {}

    for config in configs:
        print(f"\n{'='*50}")
        print(f"配置: {config['name']}")
        print(f"{'='*50}")

        outputs = []
        total_cost = 0

        for i in range(3):
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                temperature=config["temperature"],
                messages=[{"role": "user", "content": prompt}]
            )

            output = response.content[0].text
            outputs.append(output)

            cost = (response.usage.input_tokens * 0.0008 +
                    response.usage.output_tokens * 0.004) / 1000
            total_cost += cost

            print(f"输出 {i+1}: {output}")
            print(f"Tokens: {response.usage.output_tokens}, 成本: ${cost:.4f}")

        unique_outputs = len(set(outputs))
        print(f"\n唯一输出数: {unique_outputs}/3  (1=完全确定, 3=完全随机)")
        print(f"总成本: ${total_cost:.4f}")

        results[config['name']] = {
            "outputs": outputs,
            "unique_count": unique_outputs,
            "total_cost": round(total_cost, 6)
        }

    with open("experiments/results/parameter_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n✓ 结果已保存到 experiments/results/parameter_results.json")

if __name__ == "__main__":
    import os
    os.makedirs("experiments/results", exist_ok=True)
    parameter_experiment()
