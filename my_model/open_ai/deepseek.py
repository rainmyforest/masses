from openai import OpenAI
import httpx


def deepseek(role="You are a helpful assistant", content="Hello", models=0):
    client = OpenAI(api_key="sk-d068fc89856640819a7348ef30b97062", base_url="https://api.deepseek.com")
    if models == 0:
        model = "deepseek-v4-flash"
    else:
        model = "deepseek-v4-pro"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": content},
            ],
            stream=False
        )
        return response.choices[0].message.content
    except httpx.HTTPStatusError as exc:
        # 打印服务器返回的原始内容
        print(f"HTTP Error: {exc.response.status_code}")
        print(f"Response content: {exc.response.text}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# # 示例调用
# role = "You are a helpful assistant"
# content = "Hello"
# result = deepseek(role, content)
# print(result)
