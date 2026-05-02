# Hextech AI 辅助功能实现规划

## 一、项目架构

```
app/
├── ai/                           # AI 推荐引擎模块
│   ├── __init__.py
│   ├── bp_analyzer.py            # BP 推荐分析器
│   ├── team_analyzer.py          # 阵容分析器
│   ├── summoner_analyzer.py      # 召唤师分析器
│   ├── champion_evaluator.py     # 英雄评估器
│   └── recommendation.py         # 推荐结果封装
├── lol/                          # LCU 交互模块（已有）
│   ├── connector.py              # API 连接器
│   ├── listener.py               # 事件监听
│   └── opgg.py                   # OP.GG 数据
├── view/                         # UI 界面
│   ├── main_window.py            # 主窗口
│   ├── start_interface.py        # 启动界面
│   ├── bp_interface.py           # BP 推荐界面（新增）
│   ├── analysis_interface.py     # 分析界面（新增）
│   └── setting_interface.py      # 设置界面（新增）
└── common/                       # 通用模块（已有）
```

## 二、核心功能模块

### 2.1 BP 推荐系统

#### 数据输入
| 数据源 | 用途 | 获取方式 |
|--------|------|----------|
| OP.GG 梯队数据 | 版本强势英雄 | opgg.getTierList() |
| 英雄克制关系 | 克制/被克制分析 | opgg.getChampionBuild() → counters |
| 召唤师熟练度 | 个人擅长英雄 | connector.getChampionMastery() |
| BP 实时状态 | 当前选择情况 | WebSocket 监听 |
| 位置需求 | 阵容位置填充 | champ-select 事件 |

#### 推荐逻辑

```python
class BPRecommendation:
    """BP 推荐结果"""
    ban_suggestions: List[BanSuggestion]    # Ban 推荐
    pick_suggestions: List[PickSuggestion]  # Pick 推荐
    composition_analysis: CompositionAnalysis  # 阵容分析
    
class BanSuggestion:
    champion_id: int
    priority: float          # 推荐优先级 0-100
    reasons: List[str]       # 推荐理由
    
class PickSuggestion:
    champion_id: int
    position: str            # TOP/JUNGLE/MID/ADC/SUPPORT
    priority: float
    reasons: List[str]
    synergy_score: float     # 与队友配合度
    counter_score: float     # 对敌方克制度
    mastery_score: float     # 个人熟练度
```

#### 评分算法

```
PickScore = w1 * TierScore      # 版本强度 (OP.GG 梯队)
          + w2 * CounterScore   # 克制关系 (对位克制)
          + w3 * SynergyScore   # 阵容配合 (队友协同)
          + w4 * MasteryScore   # 个人熟练度
          + w5 * PositionScore  # 位置适配

BanScore = w1 * ThreatLevel     # 威胁程度 (对己方阵容)
         + w2 * EnemyMastery    # 敌方熟练度
         + w3 * TierScore       # 版本强度
```

### 2.2 赛前战术规划

#### 数据收集
```python
class PreGameAnalysis:
    """赛前分析"""
    enemy_summoners: List[SummonerProfile]   # 对方召唤师信息
    ally_summoners: List[SummonerProfile]    # 己方召唤师信息
    
class SummonerProfile:
    puuid: str
    name: str
    rank: RankInfo                     # 段位信息
    champion_masteries: List[Mastery]   # 英雄熟练度 Top10
    recent_matches: List[Match]         # 最近战绩
    position_preference: Dict[str, float]  # 位置偏好
    play_style: PlayStyle               # 游戏风格分析
```

#### 分析输出
- **位置预测**：基于历史数据预测敌方位置分配
- **威胁评估**：识别敌方绝活哥、高胜率英雄
- **Ban 建议**：针对性禁用推荐
- **战术建议**：针对敌方风格的对线/团战策略

### 2.3 对抗分析

#### 功能点
- **对线分析**：基于英雄克制数据的优劣势判断
- **关键时间点**：英雄强势期提示（6级、装备节点等）
- **团战分析**：双方阵容团战能力评估
- **资源控制**：龙魂、先锋等资源争夺建议

## 三、实现步骤

### Phase 1: 基础设施 (Week 1)
- [ ] 精简 main_window，移除不需要的界面
- [ ] 创建 AI 模块目录结构
- [ ] 封装 champion_evaluator 基础评估逻辑
- [ ] 实现 recommendation 数据结构

### Phase 2: 数据层 (Week 2)
- [ ] 扩展 opgg.py 数据获取能力
- [ ] 实现 summoner_analyzer 召唤师分析
- [ ] 添加英雄数据缓存机制
- [ ] 实现数据聚合接口

### Phase 3: BP 推荐 (Week 3-4)
- [ ] 实现 bp_analyzer 核心逻辑
- [ ] 创建 bp_interface UI 界面
- [ ] WebSocket 实时监听 BP 状态
- [ ] 推荐结果展示组件

### Phase 4: 赛前分析 (Week 5-6)
- [ ] 实现 team_analyzer 阵容分析
- [ ] 创建 analysis_interface UI
- [ ] 召唤师数据可视化
- [ ] 战术建议生成

### Phase 5: 优化完善 (Week 7-8)
- [ ] 性能优化（缓存、异步）
- [ ] UI/UX 优化
- [ ] 多语言支持
- [ ] 测试与 Bug 修复

## 四、技术要点

### 4.1 实时性保证
```python
# WebSocket 监听 BP 变化
@listener.subscribe(event='OnJsonApiEvent_lol-champ-select_v1_session')
async def onChampSelectChanged(event):
    analysis = await bp_analyzer.analyze(event['data'])
    signalBus.bpRecommendationUpdated.emit(analysis)
```

### 4.2 数据缓存策略
- OP.GG 数据：版本级缓存，过期自动更新
- 召唤师数据：会话级缓存，避免重复请求
- 英雄图标：本地持久化缓存

### 4.3 推荐算法可扩展
```python
class RecommendationEngine:
    """可插拔的推荐引擎"""
    evaluators: List[Evaluator]  # 评估器列表
    
    def add_evaluator(self, evaluator: Evaluator):
        self.evaluators.append(evaluator)
        
    async def evaluate(self, context: BPContext) -> List[Recommendation]:
        scores = []
        for evaluator in self.evaluators:
            scores.append(await evaluator.evaluate(context))
        return self.aggregate(scores)
```

## 五、界面设计

### BP 推荐界面
```
┌─────────────────────────────────────────────────────┐
│  BP 助手                              [模式: 排位]   │
├─────────────────────────────────────────────────────┤
│  禁用推荐                                            │
│  ┌─────┐ ┌─────┐ ┌─────┐                           │
│  │ 凯隐 │ │ 劫  │ │ 阿卡丽│  ← 优先级排序           │
│  │ 95% │ │ 88% │ │ 82%  │                          │
│  └─────┘ └─────┘ └─────┘                           │
├─────────────────────────────────────────────────────┤
│  选择推荐                                            │
│  ┌─────────────────────────────────────────────┐   │
│  │ 位置: 中单                                   │   │
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │   │
│  │ │ 阿狸 │ │ 辛德拉│ │ 乐芙兰│ │ 塞拉斯│            │   │
│  │ │ 92% │ │ 89% │ │ 85% │ │ 82% │            │   │
│  │ └─────┘ └─────┘ └─────┘ └─────┘            │   │
│  │ 推荐理由: 版本强势 + 克制敌方中单 + 熟练度高    │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  阵容分析                                            │
│  己方: 前期强开团能力 ★★★★☆  后期保障 ★★★☆☆        │
│  敌方: Poke消耗体系   保护能力 ★★★★☆               │
└─────────────────────────────────────────────────────┘
```

## 六、合规性声明

本工具所有功能均基于 LCU API 和公开数据源（OP.GG），不涉及：
- 游戏内存读取
- 游戏文件修改
- 游戏内实时数据获取
- 任何自动化操作客户端的行为

仅提供赛前分析和建议展示，完全符合游戏插件公约要求。
