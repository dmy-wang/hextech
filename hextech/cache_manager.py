import json
import os
import time
from pathlib import Path
from utils import create_data_folder
class Cache:
    def __init__(self, cache_file="data/cache.json", expiry_seconds=3600):  # 默认过期时间为1小时
        self._cache = {}  # 使用字典存储缓存数据
        new_folder_path = create_data_folder("data")
        self.cache_file = os.path.join(new_folder_path, "cache.json")
        self.expiry_seconds = expiry_seconds
        self._load_cache()
    
    def _load_cache(self):
        """从文件加载缓存数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
        except Exception as e:
            #print(f"加载缓存文件失败: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """将缓存数据保存到文件"""
        try:
            # 确保目录存在
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
                
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # print(f"保存缓存文件失败: {e}")
            pass
    
    def get(self, key):
        """
        根据键获取缓存的数据
        如果数据存在但已过期，返回None
        """
        if key in self._cache:
            cache_item = self._cache[key]
            current_time = time.time()
            timestamp = cache_item.get('timestamp', 0)
            
            # 检查是否过期
            if current_time - timestamp > self.expiry_seconds:
                #print(f"缓存项 '{key}' 已过期")
                return None
            
            return cache_item.get('data')
        return None

    def set(self, key, value):
        """设置缓存的数据，并附带当前时间戳"""
        self._cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
        self._save_cache()
    
    def clear(self):
        """清空缓存"""
        self._cache = {}
        self._save_cache()
    
    def remove_expired(self):
        """移除所有过期的缓存项"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self._cache.items():
            timestamp = item.get('timestamp', 0)
            if current_time - timestamp > self.expiry_seconds:
                expired_keys.append(key)
        
        if expired_keys:
            for key in expired_keys:
                del self._cache[key]
            self._save_cache()
            return len(expired_keys)
        return 0
    
    def get_with_info(self, key):
        """
        获取缓存项及其元数据信息
        返回 (数据, 是否过期, 剩余有效时间)
        """
        if key in self._cache:
            cache_item = self._cache[key]
            current_time = time.time()
            timestamp = cache_item.get('timestamp', 0)
            age = current_time - timestamp
            is_expired = age > self.expiry_seconds
            remaining = max(0, self.expiry_seconds - age)
            
            return {
                'data': cache_item.get('data'),
                'expired': is_expired,
                'age': age,
                'remaining': remaining,
                'timestamp': timestamp
            }
        return None
    
    def set_expiry(self, seconds):
        """设置新的过期时间（秒）"""
        self.expiry_seconds = seconds