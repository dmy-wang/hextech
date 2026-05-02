# Hextech

基于 LCU API 的英雄联盟 AI 游戏辅助工具，提供 BP 推荐、赛前战术规划、对抗分析等智能功能。

## 功能特性

- 🎯 **BP 推荐** - 基于版本数据、克制关系、个人熟练度的智能英雄推荐
- 📊 **赛前分析** - 分析对手历史战绩、位置偏好、擅长英雄
- ⚔️ **对抗分析** - 阵容优劣势分析、针对性建议
- 🤖 **LLM 增强** - 支持接入大语言模型（DeepSeek/OpenAI/Anthropic）进行智能分析

## 技术栈

- Python 3.8+
- PyQt5 + PyQt-Fluent-Widgets
- LCU API (League Client Update)
- OP.GG 数据接口

## 快速开始

```bash
git clone https://github.com/dmy-wang/hextech.git
cd hextech
pip install -r requirements.txt
python main.py
```

## 许可证

GPLv3（非商用）
