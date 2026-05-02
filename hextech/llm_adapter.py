import os
import json
import openai
import requests
from openai import OpenAI
from cache_manager import Cache
from PyQt5.QtCore import Qt, QThread, pyqtSignal,QObject
# from api_key import OPENAI_API_KEY, OPENAI_MODEL

class LLMHandler(QObject):  # 继承自QObject
    # 信号必须定义为类变量
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, use_api:bool):
        super().__init__()  # 调用父类的初始化方法
        self.max_retries = 3
        self.cache = Cache()
        self.use_api = use_api
        # api_key = OPENAI_API_KEY
        # model = OPENAI_MODEL
        # if use_api:
        #     self.init_api_client(api_key, model)


    def run_in_thread(self, bp_data):
        """在单独的线程中运行LLM请求"""
        try:
            result = self.get_result(bp_data)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"处理请求时出错: {str(e)}")

    def process_async(self, bp_data):
        """创建并启动一个线程来处理LLM请求"""
        thread = QThread()
        # 将当前实例移动到线程中
        self.moveToThread(thread)
        # 连接信号和槽
        thread.started.connect(lambda: self.run_in_thread(bp_data))
        self.finished.connect(thread.quit)
        self.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        # 启动线程
        thread.start()
        return thread
    
    def init_api_client(self, api_key: str,model: str = "gpt-4-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model



    def create_prompt(self,bp_data):
        try:
            prompt = f'''
            假设你是一位专业的英雄联盟BP分析师，请根据以下信息，为我提供英雄选择建议和相应的游戏思路：
            敌方禁用英雄：{bp_data['their_team_bans']}
            敌方选择英雄：{bp_data['their_team_picks']}
            我方禁用英雄：{bp_data['my_team_bans']}
            我方选择英雄：{bp_data['my_team_picks']}
            我的游戏位置：{bp_data['my_position']}
            请根据以上信息，考虑英雄胜率，对线强度，团队配合等因素，为我提供一些建议，包括但不限于：
            1. 我的英雄选择推荐（3个）
            2. 推荐英雄的理由
            3. 推荐英雄的游戏思路，包括个人对线思路和团战配合思路
            根据以上要求，将结果严格组织成以下格式输出，不需要多余的文字。
            [
                {{
                    "hero": "卡莎",
                    "reason": "能够灵活调整输出位置，配合队友进场完成单点秒杀",
                    "strategy": [
                        "优先升级Q技能提升爆发",
                        "利用E技能隐身调整位置",
                        "大招突进收割残血目标"
                    ]
                }}
            ]
            '''
        except Exception as e:
            raise Exception(f"读取BP数据失败: {str(e)}")
            return ""
        return prompt


    
    def get_result(self,bp_data):
        prompt = self.create_prompt(bp_data)
        #print(f"prompt: {prompt}")
        # 使用同步方法获取结果
        response_text = self.get_suggestion_sync(prompt)
        #print(f"response_text: {response_text}")
        
        # 解析JSON结果
        try:
            result = json.loads(response_text)
            # 直接返回结果，因为我们的提示已经要求返回正确的格式
            return result
        except json.JSONDecodeError:
            #print("JSON解析错误")
            return self.get_default_recommendations()


    def get_default_recommendations(self):
        recommendations = [
            {
                "hero": "卡莎",
                "reason": "高机动性ADC，具备强大的收割能力和生存能力",
                "strategy": "• 优先升级Q技能提升爆发\n• 利用E技能隐身调整位置\n• 大招突进收割残血目标"
            },
            {
                "hero": "艾希",
                "reason": "强力控制型ADC，全局支援能力强",
                "strategy": "• 利用W技能远程消耗\n• 大招先手开团或远程支援\n• 注意保持安全输出位置"
            },
            {
                "hero": "希维尔",
                "reason": "推线能力强，团战AOE输出高",
                "strategy": "• 利用W技能快速清线\n• E技能抵挡关键控制\n• 大招团队加速追击或撤退"
            }
        ]
        return recommendations
    

    def chat_with_qwen(self,prompt, model="qwen-plus"):
        """
        使用阿里云百炼API发送请求并获取回复
        
        参数:
            prompt (str): 发送给模型的提示文本
            system_message (str): 系统消息，默认为"You are a helpful assistant."
            model (str): 使用的模型名称，默认为qwen-plus
            
        返回:
            str: 模型的回复文本
        """
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key="sk-0093051937df469db157c1dfb848c5cf", 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        try:
            # 创建聊天完成请求
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': "你是一位专业的英雄联盟BP分析师。"},
                    {'role': 'user', 'content': prompt}
                ],
                stream=False,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.8
            )
            
            # 提取回复文本
            reply = completion.choices[0].message.content
            return reply
            
        except Exception as e:
            return f"访问API失败: {str(e)}"
        
    def chat_with_ollama(self,prompt,model="llama2"):
        try:
         
            # Ollama API的默认地址
            url = "http://192.168.5.33:11434/api/generate"
            
            # 准备请求数据
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "max_tokens":1000,
            }
            #print(f"data: {data}")
            # 发送POST请求
            response = requests.post(url, json=data)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析响应
            result = response.json()["response"]
            clean_content = result.split('</think>')[-1].strip()
            cleaned_string = clean_content.strip("```json\n")
            #print(cleaned_string)
            return cleaned_string
        
        except Exception as e:
            return f"发生错误: {str(e)}"
        

    def chat_with_api(self,prompt):
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名经验丰富的专业英雄联盟分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                # stream=False,
                # response_format={"type": "json_object"},
                max_tokens=1000,
            )
            
            # 提取回复文本
            reply = response.choices[0].message.content
            return reply
        
        except Exception as e:
            return f"发生错误: {str(e)}"
        
    def get_suggestion_sync(self, prompt: str) -> str:
        """同步方式获取LLM建议，不使用流式返回"""
        #print(f"prompt: {prompt}")
        cached = self.cache.get(prompt)
        if cached:
            return cached

        for attempt in range(self.max_retries):
            try:
                if self.use_api:
                    response = self.chat_with_api(prompt)
                else:
                    #response = self.chat_with_ollama(prompt,model="qwen2.5:latest")
                    response = self.chat_with_qwen(prompt,model="qwen-plus-latest")
                final_output = response
                #print(f"final_output: {final_output}")
                # 验证JSON格式
                try:
                    import json
                    json.loads(final_output)  # 尝试解析JSON
                    self.cache.set(prompt, final_output)
                except json.JSONDecodeError as e:
                    #print(f"JSON解析错误: {str(e)}")
                    #print(f"问题字符串: {final_output}")  # JSON格式无效，不缓存
                    pass
                
                return final_output
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return str(e)
                
        return ""  # 如果所有尝试都失败，返回空字符串
