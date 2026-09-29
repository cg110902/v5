---
# ==============================================================================
# 💡【Novel Studio 5.0 全题材通用编剧细纲契约 · Universal Beats Frontmatter】
# 🔴 核心必填：chapter_id, volume_id, title, chapter_type, timeline, location,
#             present_characters (id+name+role+want+fear+status_in+底牌显隐决策),
#             epistemology (认知盲区防火墙), 物理断章刀口。
# 🟢 动态增量【按需申报·无变动保持空列表[]】：foreshadowing_deltas, state_deltas,
#                                         relation_deltas, new_entities, locked_facts。
# 🌐 规范口径：一句话原则（字段 ≤ 15字），严禁小作文；动态增量按需按实申报。
# ==============================================================================
chapter_id: "{{slot:chapter_id|ch_XXX}}"
volume_id: "{{slot:volume_id|vol_01}}"
title: "{{slot:title|章节名}}"
chapter_type: "{{slot:chapter_type|Escalation}}" # 5波形遥测: Incubation(铺垫) | Escalation(升级) | Climax(爆发) | Payoff(兑现) | Repose(松弛)
timeline: "{{slot:timeline|时空历法时间}}"
location: "{{slot:location|核心场景名（主场景·微观现场）}}"

# 0. 宏观航标与天下大势注入（外部世界暗流对微观场景的施压）
narrative_spine:
  thread: "{{slot:thread|主线·核心冲突推进}}"
  volume_phase: "{{slot:volume_phase|分卷阶段（如：阶段一·破局求存）}}"
  macro_goal: "{{slot:macro_goal|本阶段跨章核心战役/剧情目标（≤25字）}}"
  active_milestone: "{{slot:active_milestone|无}}"
  macro_event_ref: "{{slot:macro_event_ref|EVT-001}}" # 关联 state/macro_events.json

# 1. 场景微观物理规则与感官锚点（视觉/听觉/温度触感，严禁嗅觉）
scene_environment:
  sensory_focus: "{{slot:env_sensory|核心感官聚焦：视觉、听觉、温度触感（严禁嗅觉，≤30字）}}"
  environment_rules:
    - "{{slot:env_rule_1|空间物理法则与客观限制（如：大阵压制/灵堂禁武/巡夜司宵禁，≤20字）}}"

# 2. 动态角色追踪（动机、偏见、生理负荷与底牌决策 · 严禁死者登场 · 每项 ≤ 15字）
present_characters:
  - id: "{{slot:char_1_id|p_001}}"
    name: "{{slot:char_1_name|主角名}}"
    role: "protagonist"
    want: "{{slot:char_1_want|本章即时行动诉求（≤15字）}}"
    fear: "{{slot:char_1_fear|本章即时忌惮/软肋（≤15字）}}"
    status_in: "{{slot:char_1_status_in|入场生理/战力状态（≤15字）}}"
    deployed_cards: [] # 本章决定打出的底牌池（如：["TC-001: 淬毒飞针"]）
    concealed_cards: [] # 本章刻意隐瞒保留的底牌（如：["TC-002: 破虚指"]）
  - id: "{{slot:char_2_id|p_002}}"
    name: "{{slot:char_2_name|核心对手或重要配角名}}"
    role: "{{slot:char_2_role|antagonist}}" # antagonist(对手) | deuteragonist(副主) | supporting(重要配角)
    want: "{{slot:char_2_want|本章核心算计/试探目的（≤15字）}}"
    fear: "{{slot:char_2_fear|忌惮之处/死穴（≤15字）}}"
    status_in: "{{slot:char_2_status_in|入场状态（≤15字）}}"
    cognitive_bias: "{{slot:char_2_bias|对主角/局势的当前主观误判（≤20字）}}"

# 3. 信息认知界限与情报防火墙（绝杀全知天眼穿帮 · 仅记录核心关键盲区）
epistemology:
  known:
    "{{slot:char_1_id|p_001}}":
      - "{{slot:char_1_knows|知晓的关键事实（≤20字）}}"
    "{{slot:char_2_id|p_002}}":
      - "{{slot:char_2_knows|对方知晓的有限事实（≤20字）}}"
  blind_spots:
    "{{slot:char_2_id|p_002}}":
      - "{{slot:char_2_blind|对方绝对不知晓的致命秘密（≤20字）}}"

# 4. 动态增量声明（按需申报：本章无变动保持空列表 []，严禁硬编）
foreshadowing_deltas: []
# 伏笔参考语法:
# - id: "GUN-001"
#   action: "stir"  # plant(埋下) | stir(激化/波澜) | resolve(爆裂回收)
#   note: "在场线索细节与因果推进"

state_deltas:
  character_status: {}
  # 状态参考: p_001: "筑基初期·状态更新" ｜ p_005: "deceased" (阵亡一票否决)

  items: []
  # 道具流转参考:
  # - id: "it_001"
  #   holder_change: "新持有者角色名"
  #   charges_delta: -1

  debts: []
  # 恩怨誓约参考:
  # - source: "p_001"
  #   target: "p_002"
  #   type: "blood_feud"  # blood_feud(血仇) | grudge(过节) | favor(人情) | promise(誓约)
  #   desc: "具体恩怨内容"
  #   action: "record"  # record(新结成) | settle(彻底平账)

relation_deltas: []
new_entities: []
locked_facts: []
---

{{slot:engine_briefing_dossier}}

# 第 {{slot:chapter_id|ch_XXX}} 章 《{{slot:title|章节名}}》 编剧细纲

---

## 🎯 一、 戏眼与有效增量（Spine & Delta）

- **本章核心戏眼**：
  {{slot:dramatic_goal|一句话矛盾对抗核心（≤25字）}}
- **局势实质转变（不可逆物理增量）**：
  - 核心实质行动：{{slot:dramatic_action|主角或对手采取的不可逆外部行动（≤25字）}}
  - 局势实质转变：{{slot:situational_shift|外部环境、人际关系或危机状态的实质变化（≤25字）}}
- **商业网文爽点与即时兑现（Instant Payoff）**：
  - 兑现类型：{{slot:payoff_type|战利品获得 / 阶层跃迁 / 信息差碾压 / 声望反转}}
  - 兑现详情：{{slot:payoff_desc|当章实质落袋收益与反差打脸具体呈现（≤25字）}}
- **绝对负向写作围栏（写手必守死线）**：
  1. 【规则/战力围栏】：{{slot:taboo_logic|不可打破的世界法则、战力破坏力实物标尺或客观限制}}
  2. 【人设/动机围栏】：{{slot:taboo_persona|在场角色绝不可出现的降智妥协、面瘫无脑或油腻倒贴}}
  3. 【叙事/防注水围栏】：严禁重复前情科普；恪守通用十条红线（禁嗅觉、禁省略号切幕、禁冷笑垄断等）。

---

## 🎬 二、 双幕动作阶梯（Action Ladder · 严禁写死长对白，只定攻防台阶）

### 场景一：{{slot:scene_1_title|场景名}}
- **空间与物理清场**：{{slot:scene_1_space|发生地点}}（全场物理清场，抽走多余道具拐杖，聚焦冲突利益）
- **核心动作阶梯**：
  - 阶梯一（起势/施压）：{{slot:scene_1_step1|动作与动机交锋第一步}}
  - 阶梯二（对抗/交锋）：{{slot:scene_1_step2|局势升级与阻碍对撞}}
  - 阶梯三（转折/代价）：{{slot:scene_1_step3|阶段性结果与转场承接}}
- **对白核心（仅规划 1 组关键潜台词，其余由写手临场发挥）**：
  - {{slot:scene_1_dialogue|关键对白潜台词要点}}

### 场景二：{{slot:scene_2_title|场景名}}
- **空间与物理清场**：{{slot:scene_2_space|发生地点}}
- **核心动作阶梯**：
  - 阶梯一（升级/逼近）：{{slot:scene_2_step1|危机升级与正面交锋}}
  - 阶梯二（破局/反制）：{{slot:scene_2_step2|主角破局手段或反击动作}}
  - 阶梯三（停格定势）：{{slot:scene_2_step3|高潮定格切口}}
- **对白核心（仅规划 1 组关键潜台词，其余由写手临场发挥）**：
  - {{slot:scene_2_dialogue|关键对白潜台词要点}}

---

## 🪝 三、 章末定格·断章刀口（Cliffhanger · 拒绝抒情总结，停在动作瞬间）

- **绝杀断章刀型**：
  - [x] **【A: 动作骤停刀】**（刀锋止于咽喉前一寸、手掌按在门环上）
  - [ ] **【B: 认知反转刀】**（撕下伪装、发现幕后主使是至亲）
  - [ ] **【C: 绝境倒计时刀】**（最后一根香点燃、杀手脚步停在门槛前）

- **物理定格画面**：
  {{slot:cliffhanger|一句话具体画面停格}}
