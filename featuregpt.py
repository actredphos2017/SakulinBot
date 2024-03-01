from openai import OpenAI

client = OpenAI(
    api_key='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',
)

if __name__ == '__main__':
    chat_stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "你好，你能为我做什么",
            }
        ],
        model="gpt-3.5-turbo"
    )
    print(chat_stream)
