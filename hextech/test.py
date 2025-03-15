import os
from openai import OpenAI
# from api_key import OPENAI_API_KEY, OPENAI_MODEL
# 初始化客户端

# client = OpenAI(api_key=OPENAI_API_KEY)  # 替换为您的实际API密钥
def list_available_models():
    """
    列出当前API密钥可以访问的所有模型
    
    返回:
        list: 可用模型列表
    """
    try:
        # 获取所有可用模型
        models = client.models.list()
        
        # 提取模型ID并排序
        model_ids = [model.id for model in models.data]
        model_ids.sort()
        
        return model_ids
    
    except Exception as e:
        return f"发生错误: {str(e)}"

def chat_with_gpt(prompt, model="gpt-4.5-preview-2025-02-27"):
    """
    使用ChatGPT API发送请求并获取回复-
    -
    参数:
        prompt (str): 发送给模型的提示文本
        model (str): 使用的模型名称，默认为gpt-3.5-turbo
        
    返回:
        str: 模型的回复文本
    """
    try:
        # 创建聊天完成请求
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一名经验丰富的专业英雄联盟分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        # 提取回复文本
        reply = response.choices[0].message.content
        return reply
    
    except Exception as e:
        return f"发生错误: {str(e)}"
def chat_with_QWQ(prompt, model="QwQ-32B"):
    url = "https://api.suanli.cn/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-fvwDqnkpXzE71zIzNXBzHAXvDotJiKZDHxatmtcKV1OJoyIB",
        "Content-Type": "application/json"
    }
    data = {
        "model": "free:QwQ-32B",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }


def chat_with_ollama(prompt, model="qwen2:5"):
    """
    使用本地部署的Ollama API发送请求并获取回复
    
    参数:
        prompt (str): 发送给模型的提示文本
        model (str): 使用的模型名称，默认为qwen2:5
        
    返回:
        str: 模型的回复文本
    """
    try:
        import requests
        
        # Ollama API的默认地址
        url = "http://localhost:11434/api/generate"
        
        # 准备请求数据
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        # 发送POST请求
        response = requests.post(url, json=data)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析响应
        result = response.json()
        return result["response"]
        
    except Exception as e:
        return f"发生错误: {str(e)}"


# response = requests.post(url, headers=headers, json=data)
# # 假设response是您的API响应
# response_json = response.json()
# print(response_json)

# 示例使用
# if __name__ == "__main__":
prompt = """你是一名经验丰富的专业英雄联盟分析师，请根据以下信息，为我提供英雄选择建议和相应的游戏思路：
    敌方禁用英雄：[]
    敌方选择英雄：[金克丝, 卡萨丁, 塞恩]
    我方禁用英雄：[]
    我方选择英雄：[墨菲特，亚索， 赛娜]
    我的游戏位置：bottom
    请根据以上信息，为我提供一些建议，包括但不限于：
    1. 我的英雄选择推荐（不少于3个）
    2. 推荐英雄的理由
    3. 推荐英雄的游戏思路，包括个人对线思路和团战配合思路
    根据以上要求，将结果组织成以下格式返回：
    [
        {{
            "hero": "英雄名",
            "reason": "具体理由",
            "strategy": [
                "策略1",
                "策略2",
                "策略3"
            ]
        }},
        {{
            "hero": "英雄名",
            "reason": "具体理由",
            "strategy": [
                "策略1",
                "策略2",
                "策略3"
            ]
        }},
        {{
            "hero": "英雄名",
            "reason": "具体理由",
            "strategy": [
                "策略1",
                "策略2",
                "策略3"
            ]
        }}
    ]"""
# reponse = chat_with_ollama(prompt, model="deepseek-r1:7b")
# print(reponse)
    # 获取当前工作目录
    # current_dir = os.getcwd()
    # print(f"当前工作目录: {current_dir}")
    # print("正在查询可用模型...")
    # available_models = list_available_models()
    
    # if isinstance(available_models, list):
    #     print(f"找到 {len(available_models)} 个可用模型:")
    #     for model in available_models:
    #         print(f"- {model}")
    # else:
    #     print(available_models)  # 打印错误信息
# import requests
# import json


# # 从响应中提取助手的消息内容
# assistant_message = response_json['choices'][0]['message']['content']

# # 清理内容（移除思考过程）
# if '<think>' in assistant_message:
#     # 移除思考部分
#     clean_content = assistant_message.split('</think>')[-1].strip()
# else:
#     clean_content = assistant_message

# # 解析JSON
# try:
#     # recommendations = json.loads(clean_content)
    
#     # 现在recommendations是一个Python列表，包含三个英雄推荐
#     # for rec in recommendations:
#     #     print(f"英雄: {rec['hero']}")
#     #     print(f"理由: {rec['reason']}")
#     #     print("策略:")
#     #     for strategy in rec['strategy']:
#     #         print(f"- {strategy}")
#     print(clean_content)
        
# except json.JSONDecodeError as e:
#     print(f"JSON解析错误: {e}")
#     print("原始内容:", clean_content)
# 打印响应
# print(response.status_code)
# print(response.json())
import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-0093051937df469db157c1dfb848c5cf", 
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-plus", # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': """假设你是一位专业的英雄联盟BP分析师，请根据以下信息，为我提供英雄选择建议和相应的游戏思路：
敌方禁用英雄：['莫甘娜', '亚索', '伊莉丝', '诺手', '杰斯']
敌方选择英雄：['锤石', '克烈', '卡兹克', '凯莎']
我方禁用英雄：['韦鲁斯', '诺克萨斯之手', '塔姆', '伊芙琳']
我方选择英雄：['潘森', '千珏', '亚索', '潘森']
我的游戏位置：bottom
请根据以上信息，为我提供一些建议，包括但不限于：
1. 我的英雄选择推荐（3个）
2. 推荐英雄的理由
3. 推荐英雄的游戏思路，包括个人对线思路和团战配合思路
根据以上要求，将结果严格组织成以下格式输出，不需要多余的文字。
[
{
"hero": "卡莎",
"reason": "能够灵活调整输出位置，配合队友进场完成单点秒杀",
"strategy": [
"优先升级Q技能提升爆发",
"利用E技能隐身调整位置",
"大招突进收割残血目标"
]
}
]"""}],
    )
    
print(completion.choices[0].message.content)