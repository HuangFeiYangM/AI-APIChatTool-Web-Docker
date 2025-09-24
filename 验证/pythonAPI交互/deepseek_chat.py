import argparse
import os
import sys
from openai import OpenAI

def read_file(file_path):
    """
    读取文件内容，支持.md和.txt格式。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"错误：文件未找到 - {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"读取文件时出错：{e}")
        sys.exit(1)

def call_deepseek_api(api_key, question, model="deepseek-chat", system_prompt=None):
    """
    使用OpenAI兼容的SDK调用DeepSeek API
    """
    # 初始化OpenAI客户端，使用DeepSeek的base_url
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # 构建消息列表
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    
    try:
        # 调用API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False
        )
        
        # 提取回答
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        print(f"API调用失败：{e}")
        sys.exit(1)

def write_file(file_path, content):
    """
    将内容写入文件，支持.md和.txt格式。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"回答已成功写入到 {file_path}")
    except Exception as e:
        print(f"写入文件时出错：{e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='使用DeepSeek API进行文件对话：从输入文件读取问题，生成回答并输出到文件。')
    parser.add_argument('--input', type=str, required=True, help='输入文件路径（.md或.txt）')
    parser.add_argument('--output', type=str, required=True, help='输出文件路径（.md或.txt）')
    parser.add_argument('--api_key', type=str, help='DeepSeek API密钥（可选，优先使用环境变量DEEPSEEK_API_KEY）', default=None)
    parser.add_argument('--model', type=str, help='模型选择：deepseek-chat（默认）或deepseek-reasoner', default="deepseek-chat")
    parser.add_argument('--system_prompt', type=str, help='系统提示词（可选）', default=None)
    parser.add_argument('--system_file', type=str, help='系统提示词文件（可选，会覆盖--system_prompt）', default=None)
    
    args = parser.parse_args()
    
    # 获取API密钥：优先从命令行参数，其次从环境变量
    api_key = args.api_key or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("错误：未提供API密钥。请通过 --api_key 参数或设置环境变量 DEEPSEEK_API_KEY 来提供。")
        sys.exit(1)
    
    # 获取系统提示词
    system_prompt = args.system_prompt
    if args.system_file:
        system_prompt = read_file(args.system_file)
    
    # 读取输入文件
    question = read_file(args.input)
    print(f"已从 {args.input} 读取问题：{question[:100]}...")  # 打印前100字符作为预览
    
    # 调用API
    print(f"正在调用DeepSeek API（使用模型: {args.model}）...")
    answer = call_deepseek_api(api_key, question, args.model, system_prompt)
    
    # 写入输出文件
    write_file(args.output, answer)

if __name__ == "__main__":
    # 检查是否安装了openai库
    try:
        from openai import OpenAI
    except ImportError:
        print("错误：未找到openai库。请运行 'pip install openai' 安装。")
        sys.exit(1)
    
    main()
