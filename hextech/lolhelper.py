import warnings
from urllib3.exceptions import InsecureRequestWarning
import psutil
import base64
import requests

warnings.simplefilter('ignore', InsecureRequestWarning)

# 与lol客户端通信
class LoLHelper:
    port = str
    token = str
    author = dict

    def __init__(self, port: str, token: str):
        self.port = port
        self.token = token
        # 添加身份验证
        tokens = base64.b64encode(("riot:%s" % token).encode())
        self.author = { "Authorization":"Basic %s" % tokens.decode() }
        

    def get(self, api: str):
        result = requests.get(
            url = ("https://127.0.0.1:%s%s" % (self.port, correct(api))),
            headers = self.author,
            verify = False
        )
        if result.status_code == 200:
            try:
                data = result.json()
            finally:
                result.close()
        else:
            data = None
        return data

    def post(self, api: str, data: str):
        result = requests.post(
            url = "https://127.0.0.1:%s%s" % (self.port, correct(api)),
            headers = self.author,
            verify = False,
            json = data
        )
        if result.status_code == 200:
            try:
                result.encoding = "utf-8"
                return result.text
            finally:
                result.close()
        else:
            return ""

    def patch(self, api: str, data: str):
        result = requests.patch(
            url = "https://127.0.0.1:%s%s" % (self.port, correct(api)),
            headers = self.author,
            verify = False,
            json = data
        )
        if result.status_code == 200:
            try:
                result.encoding = "utf-8"
                return result.text
            finally:
                result.close()
        else:
            return ""

    def put(self, api: str, data: str):
        result = requests.put(
            url = "https://127.0.0.1:%s%s" % (self.port, correct(api)),
            headers = self.author,
            verify = False,
            json = data
        )
        if result.status_code == 200:
            try:
                result.encoding = "utf-8"
                return result.text
            finally:
                result.close()
        else:
            return ""
    
    def delete(self, api: str):
        return requests.delete(
            url = "https://127.0.0.1:%s%s" % (self.port, correct(api)),
            headers = self.author,
            verify = False
        ).status_code


def correct(api:str):
    if api[0] != "/":
        return "/%s" % api
    return api


def checkProcessAlive(processName: str):
    for x in psutil.process_iter():
        if x.name().removesuffix(".exe") == processName:
            return True
    return False


def LolHelper_init():
    try:
        port = None
        token = None
        
        # 查找英雄联盟客户端进程
        for process in psutil.process_iter():
            if process.name().removesuffix(".exe") == "LeagueClientUx":
                try:
                    cmds = process.cmdline()
                    # 从进程命令行参数中提取端口和令牌
                    for cmd in cmds:
                        ary = cmd.split("=")
                        if ary[0] == "--remoting-auth-token":
                            token = ary[1]
                        if ary[0] == "--app-port":
                            port = ary[1]
                    break
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    raise RuntimeError(f"无法访问League Client进程: {str(e)}")
        
        if port is None or token is None:
            raise ValueError("无法获取League Client的端口或令牌")
            
        return LoLHelper(port, token)
        
    except Exception as e:
        raise RuntimeError(f"初始化LoLHelper时发生错误: {str(e)}")
    



