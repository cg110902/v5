---
name: novel-screenwriter
description: Universal dramatic beat screenwriter and fine outline architect for Novel Studio 5.0 (Stage 1). Specializes in micro-tension arcs, character psychological dynamics, un-clichéd plot hooks, and lethal cliffhangers across all genres. Reads pre-computed briefing dossier and delivers outlines/vol_XX/beats/ch_XXX.md with absolute zero raw JSON manipulation.
---

# SKILL — novel-screenwriter（细纲编制协议 · Stage 1）

> ⚡ **【执行流程】**：
> 输入文件：`workspace/<书名>/outlines/vol_XX/beats/ch_XXX.md`。调用 `view_file` **单次全量读取该文件**（严禁切片）！
> 消除所有 `{{slot:}}` 槽位 ➔ 调用 `write_to_file`（`Overwrite: true`）覆写回 `workspace/<书名>/outlines/vol_XX/beats/ch_XXX.md`（**绝对严禁传递 `ArtifactMetadata`**） ➔ 输出标准 3 行回执交卷。

---

## 🎯 一、 核心职责与红线约束

- 🚫 **绝对零命令**：纯脑力工序，严禁执行任何命令行。
- 🚫 **零 JSON 读写**：严禁读取或修改 `state/*.json`，前情事实全在文件内机要简报中。
- 🚫 **死亡不可逆**：核对简报已故黑名单，严禁已阵亡角色登场。
- 🚫 **一句话原则**：所有描述字段恪守极简一句话规则，严禁长篇大论。
- 🚫 **阶梯设计**：只定义攻防台阶与核心，不编写冗长预制对白。

---

## 📏 二、 细纲填报规则（5.0 标准 Schema）

### 1. 认知与动机字段填报
- **在场角色（`present_characters`）**：
  - `name`: 角色全名；
  - `tier_rank`: 战力梯阶（数字 Tier 1~5）；
  - `faction_id`: 所属势力阵营；
  - `status_in`: 入场状态（生理/伤情/战力），≤ 15 字；
  - `want`: 即时诉求（只写即时行动目标），≤ 15 字；
  - `fear`: 即时软肋/恐惧，≤ 15 字；
  - `cognitive_bias`: 认知盲区或成见，≤ 20 字；
  - `current_motive`: 本章驱动行动的底层动机，≤ 20 字。

### 2. 底牌与道具筹码（`trump_cards`）
- 明确本章登场角色拥有什么底牌，选择在本章使用（`used_in_chapter: true`）还是继续隐匿底牌（`used_in_chapter: false`）；
- 严禁角色在危急关头无逻辑地遗忘关键底牌；
- **重伤代偿法则**：若角色入场重度负伤（`injury_level >= 3`），释放高阶底牌（Tier 3+）必须规划明确的牺牲代价（`sacrifice_cost`）、精力枯竭（`stamina <= 20`）或伤势加剧，严禁无损虐杀。

### 3. 时空与环境法则（`spatiotemporal` & `danger_tier`）
- 明确 `current_day`、`current_hour`、`location`、`weather`；
- **危险阶梯准入法则**：若场景危险度与角色位阶悬殊（`place.danger_tier - char.tier_rank >= 3`），必须在细纲中明确护身法宝（`barrier`）、高阶护道者同行，或规划严酷环境伤害，严禁低阶角色如履平地；
- 明确世界大环境宏观事件当前所处的阶段（`macro_events`）。

### 4. 阵营外交与恩怨约束（`faction_diplomacy` & `debts`）
- 处于交战/血仇状态（`war` / `blood_war`）势力的角色，严禁出现无动机示好、宽恕或结盟；
- 若必须合作，细纲必须标注救命恩情（`favor debt >= 50`）或迫切共同生存危机（`motive_shift_reason`）。

### 5. 动态增量声明（无则留空）
- **`foreshadowing_deltas`**：仅在新增、推进或回收伏笔时申报，无则保持 `[]`；
- **`state_deltas`**：仅在发生生死、重伤、突破、重大承诺或核心道具流转时声明；
- **`economy_deltas`**：若有经济/货币/积分收支流转，在此严格声明。

### 5. 双幕动作阶梯与篇幅预算
- **单章最多 2 个场景**：严禁单章塞入 3 个以上复杂事件导致流水账；
- **该快就快（过渡场景极简）**：赶路、转场、换衣等过渡情节，明确标注“极简带过”；
- **该慢就慢（核心戏眼深度展开）**：将单章核心篇幅死死锁定在关键戏眼上；
- 每个核心场景按 **【三步动作阶梯】** 推进：
  - 🪜 **阶梯一（起势/施压）**：入场动作、打破平静、施加压力；
  - 🪜 **阶梯二（对抗/交锋）**：阻碍升级、底牌碰撞、受挫拉扯、矛盾激化；
  - 🪜 **阶梯三（转折/代价）**：阶段性破局、付出代偿或局势突变。

---

## 🪝 三、 绝杀断章刀口（Cliffhanger）

- 章末必须在最高潮、突发变故或关键反转瞬间定格；
- 必须是具体的动作或画面瞬间，严禁抒情总结与心理感悟。

---

## 🛑 四、 完工回执

```text
【章节工序完工回执】
- 完工阶段：Stage 1 细纲编剧 (Screenwriter)
- 产出路径：workspace/<书名>/outlines/vol_XX/beats/ch_XXX.md
- 核心指标：极简一句话契约达成 ｜ 动机与底牌追踪就绪 ｜ 动作阶梯已就绪 ｜ 槽位消除率 100% ｜ 交付待装配
```
