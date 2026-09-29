# Novel Studio 5.0 数据契约与全息模型规范 (RFC_DATA_SCHEMA)

> **文档标识**：RFC-5001-SCHEMA  
> **状态**：APPROVED & FROZEN  
> **适用范围**：`engine/core/models.py`、`templates/`、`state/` 以及所有智能体数据总线交互。

---

## 一、 实体物理唯一 ID 规范矩阵 (Canonical Entity ID Matrix)

全书所有实体均拥有全生命周期不可变唯一物理 ID，作为底层持久化与跨章检索键：

| 前缀 | 实体类型 (Type) | 作用对象 | 示例 | 派发规则 |
|---|---|---|---|---|
| `p_` | `person` | 角色（主角恒定为 `p_001`） | `p_001`, `p_002` | 递增三位数字 |
| `it_` | `item` | 道具、武器、法宝、丹药、核心资产 | `it_001`, `it_002` | 递增三位数字 |
| `fac_` | `faction` | 势力、宗门、帮派、帝国、世家 | `fac_001`, `fac_002` | 递增三位数字 |
| `loc_` | `place` / `location` | 地理地点、秘境、关节点、建筑 | `loc_001`, `loc_002` | 递增三位数字 |
| `GUN-` | `line_gun` | 悬顶之剑 / 危机伏笔 (Chekhov's Gun) | `GUN-001` | 递增三位数字 |
| `KNO-` | `line_kno` | 核心信息差 / 绝密情报 (Knowledge Gap) | `KNO-001` | 递增三位数字 |
| `MIS-` | `line_mis` | 认知偏差 / 迷局误区 (Misconception) | `MIS-001` | 递增三位数字 |
| `DEBT-` | `debt` | 人际誓约、血仇、人情欠款 | `DEBT-001` 或 `DEBT-AUTO-<hash>` | 递增或自动派生 |
| `LOCK-` | `locked_fact` | 不可逆历史物理既定事实 | `LOCK-001` | 递增三位数字 |
| `ms_` | `milestone` | 分卷与长程战略剧情里程碑 | `ms_001` | 递增三位数字 |
| `EVT-` | `macro_event` | 天下大势宏观事件 / 外部时钟事件 | `EVT-001` | 递增三位数字 |

---

## 二、 角色动态演化与认知模型 (Dynamic Character Cognition)

在 5.0 中，角色不再是静态的属性清单，而是具备**时空演化动态向量**：

```json
{
  "id": "p_002",
  "name": "陆子羽",
  "type": "person",
  "role": "antagonist",
  "tier_rank": 3,
  "tier_name": "筑基中期",
  "power_benchmark": "飞剑断石，护体灵罡可御凡铁劲弩",
  "status": "active",
  "life_status": "alive",
  "faction": "青云剑宗",
  "location": "北灵城·谪仙楼",
  "last_seen_ch": 14,
  "cognition": {
    "long_term_goal": "夺取楚家古玉，借以晋升内门真传",
    "current_motive": "本章在楚府灵堂施压试探，逼迫楚家交出账册，试探楚凡是否装疯",
    "cognitive_bias": "误以为楚凡经脉尽废且无后台，视其为蝼蚁，但忌惮城主府巡夜司插手",
    "fear_threshold": "最怕事情闹大引来巡夜司副统领，自身私吞古玉的计划败露",
    "attitude_towards_mc": "contemptuous_but_cautious"
  },
  "physiology": {
    "injury_level": 0,
    "injury_desc": "完好无损",
    "stamina_pct": 100,
    "mana_pct": 95,
    "active_debuffs": []
  },
  "sensory_anchor": "一袭暗云纹青衫，腰悬白玉螭龙佩，右手拇指常无意识摩擦剑柄金丝",
  "micro_actions": ["冷哂时眼尾微下压", "拔剑前先正衣冠"],
  "address_matrix": {
    "楚凡": "楚世弟（面具）/ 楚家余孽（私下）",
    "赵青": "师弟"
  }
}
```

### 字段说明：
- `life_status`: 严格四态：`alive`（在世）、`deceased`（阵亡）、`missing`（失踪）、`unknown`（生死未卜）。阵亡角色严禁在正文活人出场；
- `cognition`: 角色动态三维认知向量，随每章剧情推进由引擎与细纲联动刷新；
- `physiology`: 生理与负荷状态（`injury_level`: 0~5 级），杜绝上一章重伤、本章生龙活虎的生理矛盾。

---

## 三、 主角底牌显隐决策与金手指矩阵 (Trump Matrix & Cheat Stage)

在 `state/current.json` 与细纲中强类型约束主角的底牌与金手指边界：

```json
{
  "cheat_system": {
    "name": "周天造化推演令",
    "current_tier": 1,
    "max_tier": 5,
    "unlocked_abilities": ["灵草药理绝对辨识", "初级破绽推演"],
    "cooldown_counter": 0,
    "cost_per_use": "每次消耗神魂念力 10 点，连续使用超 3 次引发神识剧痛",
    "growth_milestone": "吞噬第一块上品灵玉后解锁 Tier 2 (功法残篇补全)"
  },
  "trump_cards": [
    {
      "id": "TC-001",
      "name": "袖中淬毒暗弩",
      "visibility": "concealed",
      "cost": "消耗一次性机括",
      "lethality_tier": 3,
      "holder_strategy": "除非被逼入绝境死角，绝不在众目睽睽下动用"
    },
    {
      "id": "TC-002",
      "name": "破虚指残式",
      "visibility": "deployed_once",
      "cost": "抽取周身七成真元，右臂经脉剧痛麻木一炷香",
      "lethality_tier": 4,
      "holder_strategy": "本章决战关头用于一击定乾坤"
    }
  ]
}
```

---

## 四、 战力物理表现力标尺 (Power Benchmark Schema)

存储于 `state/power_scale.json`，为全书 1~9 阶战力绑定物理实物破坏力与防御力锚点：

```json
{
  "tiers": {
    "1": {
      "name": "炼气初期",
      "destructive_power": "单拳断木，碎薄砖，奔行速度略超骏马",
      "defensive_limit": "难御凡铁刀剑直刺，可抗寻常钝击",
      "range": "近身肉搏，拳风及丈",
      "taboo": "严禁在此阶出现隔空轰平房屋、刀气碎石等超标表现"
    },
    "2": {
      "name": "炼气后期",
      "destructive_power": "掌力碎裂尺许青石，兵刃灌注真气可斩铁甲",
      "defensive_limit": "肉身可抵挡寻常流矢擦伤，直击仍会破防流血",
      "range": "刀气外放三丈",
      "taboo": "严禁在此阶出现踏空而行、剑气化丝"
    },
    "3": {
      "name": "筑基期",
      "destructive_power": "飞剑御空百丈，剑芒可崩碎重城箭楼，劈开三丈巨石",
      "defensive_limit": "灵力护罩可抗百人步弓齐射数十息",
      "range": "百丈方圆神念笼罩",
      "taboo": "严禁在此阶摧毁整座山岳、截断大江"
    }
  }
}
```

---

## 五、 经济购买力平价 (PPP) 与复式记账流水 (Ledger Schema)

存储于 `state/ledger.json`：

```json
{
  "ppp_anchor": {
    "base_currency": "铜钱",
    "exchange_rates": {
      "白银": 1000,
      "黄金": 50000,
      "下品灵石": 100000
    },
    "commodity_benchmarks": {
      "热肉包子一个": "2 铜钱",
      "寻常三口之家一月温饱": "1 两白银 (1000 铜钱)",
      "凡俗精良百炼镔铁长刀": "15 两白银",
      "下品黄阶疗伤丹一瓶": "3 块下品灵石 (30 两黄金)"
    }
  },
  "pools": {
    "copper": 450,
    "silver": 128,
    "gold": 5,
    "spirit_stones": 12
  },
  "transactions": [
    {
      "chapter": 14,
      "type": "expense",
      "category": "consumable",
      "amount": { "silver": 5 },
      "desc": "在百味斋打点掌柜购买陈年醉仙酿一坛用于送礼",
      "verified_by_audit": true
    }
  ]
}
```

---

## 六、 时空拓扑与行路图谱 (Spatiotemporal Graph)

存储于 `state/spatiotemporal.json`：

```json
{
  "current_calendar_day": 42,
  "current_time_slot": "申时初刻",
  "locations": {
    "loc_001": {
      "name": "北灵城·楚宅",
      "coordinates": [10, 20]
    },
    "loc_002": {
      "name": "北灵城·谪仙楼",
      "coordinates": [12, 21],
      "distance_from_loc_001": {
        "walking_minutes": 25,
        "carriage_minutes": 10
      }
    },
    "loc_003": {
      "name": "落断山脉·黑风峡",
      "distance_from_loc_001": {
        "fast_horse_days": 2,
        "flying_boat_hours": 3
      }
    }
  }
}
```

---

## 七、 天下大势宏观时钟 (World Clock Schema)

存储于 `state/macro_events.json`：

```json
{
  "global_epoch": "大乾景泰三十七年·深秋",
  "active_currents": [
    {
      "id": "EVT-001",
      "title": "镇北王起兵叛乱，边境三州戒严",
      "impact_scope": "全郡粮价暴涨三成，城防宵禁提早至戌时初",
      "stage": "erupting",
      "urgency_to_scene": "high"
    },
    {
      "id": "EVT-002",
      "title": "青云剑宗十年一度开山收徒大典",
      "impact_scope": "各路散修与望族子弟齐聚北灵城，城内客栈爆满，治安摩擦频发",
      "stage": "brewing",
      "urgency_to_scene": "medium"
    }
  ]
}
```

---

## 八、 伏笔三态演进模型 (Three-State Foreshadowing Schema)

存储于 `state/lines.json`：

```json
{
  "id": "GUN-003",
  "title": "楚凡生母遗留的断裂铜簪",
  "category": "heritage_mystery",
  "state": "stirred",
  "planted_ch": 2,
  "stirred_ch": [8, 14],
  "target_ch": 22,
  "countdown_remaining": 8,
  "secret_desc": "并非寻常饰物，内嵌天元秘境通行玄符半枚，遇纯阳真火显露金文",
  "known_by": ["p_001"],
  "history": [
    { "chapter": 2, "action": "plant", "note": "整理灵堂遗物时贴身藏入内衣" },
    { "chapter": 8, "action": "stir", "note": "被陆子羽目光扫过，心头一凛掩住衣领" },
    { "chapter": 14, "action": "stir", "note": "接触到地火炭盆，簪身隐现灼热温意" }
  ]
}
```

---

## 九、 5.0 细纲任务卡标准 Frontmatter 规范 (Beats Schema)

必须 100% 格式化落盘于 `outlines/vol_XX/beats/ch_XXX.md` 头部：

```yaml
---
chapter_id: ch_015
volume_id: vol_01
title: 灵堂按剑，步步紧逼
chapter_type: Escalation  # Incubation | Escalation | Climax | Payoff | Repose
timeline: 景泰三十七年九月十四 申时
location: 北灵城·楚宅灵堂

# 1. 宏观航标与天下大势注入
narrative_spine:
  thread: 主线·古玉博弈与第一波退敌
  volume_phase: 阶段一：破局求存
  active_milestone: ms_001
  macro_event_ref: EVT-002  # 关联天下大势，注入时代背景压力

# 2. 空间感官与客观物理法则（严格禁用嗅觉）
scene_environment:
  sensory_focus: 白幡猎猎作响，炭盆火星微爆，空气带着深秋刺骨寒意（严禁嗅觉）
  environment_rules:
    - 灵堂百人注视，众目睽睽之下禁动绝杀杀招，违者遭城主府巡夜司拿办

# 3. 动态角色追踪（包含动机、偏见与生理状态）
present_characters:
  - id: p_001
    name: 楚凡
    role: protagonist
    want: 逼陆子羽立下三日生死文书，争取觉醒时间（≤15字）
    fear: 遗母铜簪被当场查验搜走（≤15字）
    status_in: 筑基初期·经脉微痛（≤15字）
    deployed_cards: []
    concealed_cards: ["TC-001: 袖中淬毒暗弩", "TC-002: 破虚指残式"]
  - id: p_002
    name: 陆子羽
    role: antagonist
    want: 借查账为名搜身，夺取古玉（≤15字）
    fear: 事情闹大招来巡夜司副统领（≤15字）
    status_in: 筑基中期·全盛状态（≤15字）
    cognitive_bias: 确信楚凡绝不敢当众翻脸，视其为案上鱼肉

# 4. 认知盲区与情报防火墙（绝杀全知穿帮）
epistemology:
  known:
    p_001: ["知晓陆子羽私吞宗门灵石有大亏空"]
    p_002: ["知晓楚家今日孤立无援，外援已被截断"]
  blind_spots:
    p_002: ["绝对不知楚凡昨夜已修复丹田并开辟至尊神海"]

# 5. 动态增量声明（无变动保持空列表 []）
foreshadowing_deltas:
  - id: GUN-003
    action: stir
    note: 炭火灼热令铜簪隐现温意，引发楚凡警觉
state_deltas:
  character_status: {}
  items: []
  debts:
    - source: p_001
      target: p_002
      type: blood_feud
      desc: 灵堂折辱逼迫楚家之仇，立下三日文书
      action: record
relation_deltas: []
new_entities: []
locked_facts:
  - id: LOCK-003
    desc: 楚凡与陆子羽正式在全族长老面前立下三日之约生死战，不可悔约
---
```
