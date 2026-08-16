# 飞机整机交易审查

审查飞机整机交易、租赁、适航、取回及财务回报。

## 安装

方式一（通过Hermes技能中心）：

```bash
hermes skills install https://raw.githubusercontent.com/x18815379395-wq/hermes-aircraft-whole-transaction-review/main/SKILL.md
```

方式二（手动安装，从GitHub克隆）：

```bash
git clone https://github.com/x18815379395-wq/hermes-aircraft-whole-transaction-review.git ~/.hermes/skills/financial-risk/aircraft-whole-transaction-review
hermes reload-skills
```

> 注意：`hermes skills install` 方式需要Hermes Agent支持从GitHub URL安装SKILL.md。若不支持，请使用手动克隆方式。

## 使用方法

覆盖飞机估值方法（市场法/成本法/收益法）、租赁结构分析（经营租赁/融资租赁/售后回租）、适航与登记审查、跨境取回风险、租金定价区间与双边定价模型、20项交割先决条件、硬风险旗标。

具体使用方法请参考技能的 `SKILL.md` 文件。

## 许可证

MIT

## 作者

Hermes Agent Contributor
