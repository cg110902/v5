---
name: novel-drafter
description: Universal plot drafting and creative narrative generator for Novel Studio 5.0 (Stage 2). Unchains full creative compute to produce high-tension raw story drafts across any genre, strictly inheriting beat facts, dynamic cognition, and trump card matrices.
---

# SKILL — novel-drafter（起草先锋 · Stage 2）

## 📇 本卡速览

| 项 | 内容 |
|---|---|
| **角色职责** | 初稿起草写手。依照细纲动作阶梯与动态认知创作高沉浸商业网文初稿 |
| **输入工件** | `<workspace>/pack.md`（自完备装配包，**单次全量读取**） |
| **输出工件** | `<workspace>/manuscript/vol_XX/raw/ch_XXX_v1.md` |
| **核心任务** | 落实攻防动作阶梯 ➔ 展现主角内心算盘与即时博弈 ➔ 篇幅锁定 2000~3000 字 ➔ 物理落盘 |
| **约束红线** | 细纲法定事实 100% 继承 ｜ 限知视角不透视 ｜ 绝对零命令 ｜ 禁传 `ArtifactMetadata` |
| **完工动作** | 输出 3 行标准回执，**立即停机** |

> ⚡ **【执行流程】**：`view_file` **单次全量读取** `pack.md`（严禁切片） ➔ 展开起草 ➔ `write_to_file`（`Overwrite: true`）写入目标文件 ➔ 交卷停机。

---

## 🎯 一、 创作执行规范

### 1. 限知视角沉浸与主角内心博弈
- **贴身主观沉浸**：镜头死死锁定在主角第一感官之内。严禁旁白随意跨时空转入反派密室剧透阴谋；
- **写足主角内心算盘**：保留主角鲜活的**利益权衡、危机警惕与即时算盘**，赋予角色活人感；
- **底牌抉择严格落实**：细纲中声明“隐藏”的底牌，主角在正文中必须刻意隐瞒；声明“打出”的底牌，必须写足其出手时机与代价。

### 2. 戏眼攻防三回合（该快就快，该慢就慢）
- **核心戏眼写足过程**：严格按细纲规划的【三步动作阶梯】推进（起势/施压 $\rightarrow$ 对抗/交锋 $\rightarrow$ 转折/代价），打满攻防拉扯；
- **过渡利落**：转场、赶路等过渡环节简洁明快带过，不拖泥带水；
- **侧面烘托**：写对手之强、杀气之重，多用周围环境微动与围观者本能退缩来侧面衬托。

### 3. 人物动态活人感（拒绝无脑 NPC）
- 对白与行动紧扣当期动机（Want）与忌惮（Fear）；
- 反派行动基于实际利益或生存危机，严禁无脑跳脸嘲讽。

---

## 🛑 二、 完工回执 (统一 3 行)

```text
【章节工序完工回执】
- 完工阶段：Stage 2 初稿起草 (Drafter)
- 产出路径：manuscript/vol_XX/raw/ch_XXX_v1.md
- 核心指标：字数 [N] 字 ｜ 细纲事实 100% 继承 ｜ 戏眼攻防已打满 ｜ 工具物理落盘交付
```
