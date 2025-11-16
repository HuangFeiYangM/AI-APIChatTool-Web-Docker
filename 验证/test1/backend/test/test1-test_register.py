import requests

url = "http://localhost:8000/api/auth/register"
data = {
    "user": "test_register",
    "password": "pass",
    "deepseek_bool": True,
    "deepseek_api": "your_deepseek_api_key_here"  # 可选，如果您有 DeepSeek API 密钥
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())  # 返回 UserResponse 数据
