---
license: MIT
name: aircraft-whole-transaction-review
description: 审查飞机整机交易、租赁、适航、取回及财务回报。
version: 0.3.0
author: Hermes Agent Contributor
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [financial-risk, aircraft, aviation-finance, leasing, cape-town]
    related_skills: [aviation-engine-transaction-review, financing-lease-contract-review, corporate-credit-due-diligence, financial-analysis-report, cross-border-financial-regulatory-research]---

# 飞机整机交易与融资租赁审查

用于民航客机、货机、公务机和直升机的买卖、直租、售后回租、经营租赁、融资租赁及资产包交易。以MSN级资产、权属与登记、持续适航、运营现金流、维护状态和可执行取回路径为主线；不替代技术检验、独立估值、税务或正式法律意见。

## When to Use

- 飞机整机购置、出售、经营租赁、融资租赁和售后回租；
- 保税区SPV、头租转租、跨境融资和担保权益转让；
- 核验国籍、权利登记、国际利益、IDERA、适航和技术记录；
- 复核租金、LRF、维护储备金、返还补偿、残值、IRR、DSCR和LLCR；
- 评估承租人停航、破产、取回、过渡维修和再营销风险。

不要单独用于发动机深度审查；发动机模块加载`aviation-engine-transaction-review`。主体财务、合同版本和跨境法分别加载相关技能。

## Prerequisites

收集：机型、MSN、注册号、发动机ESN、APU序号、制造/交付日、机龄、FH/FC；买卖与租赁文件、Bill of Sale、付款和交付；CAAC/登记国登记摘录、国际登记处Priority Search Certificate（优先权检索证明）、IDERA；适航证、维修方案、AD/SB、技术记录、事故与改装；租金、保证金、储备金、返还条件；债务、保险、税务、估值和退出报价。

网络资料按A官方法源、B公告/合同、C行业研究、D媒体/顾问线索分级。D级资料只用于发现变量，不写入默认参数。

## How to Run

1. 复制`templates/aircraft-model-input.json`并替换全部项目参数；
2. 用`terminal`运行`python scripts/aircraft_lease_model.py input.json --output result.json`；
3. 检查`validation`、`base`、`scenarios`和`hard_flags`；
4. 运行`python scripts/test_aircraft_lease_model.py`，全部测试通过；
5. 按`templates/aircraft-review-report.md`形成报告，保留输入、结果和证据台账。

## Quick Reference

- 模型输入：`templates/aircraft-model-input.json`
- 资产台账：`templates/aircraft-asset-register.csv`
- 证据风险台账：`templates/evidence-risk-register.csv`
- 交割先决条件：`templates/aircraft-closing-checklist.csv`
- 报告模板：`templates/aircraft-review-report.md`
- 来源规则：`references/sources-and-evidence.md`
- 模型口径：`references/financial-model-methodology.md`

## Procedure

### 1. MSN级特定化和结构还原

每架飞机单独登记MSN、注册号、发动机ESN、APU及实际位置。绘制制造商—卖方—所有人/SPV—出租人—承租人/运营人—MRO—资金方的权属、租赁、占有、维修、保险和付款链。任何MSN冲突均不得静默修正。

### 2. 权属、登记与顺位

分别核验国籍登记、所有权/占有权/抵押登记、国际利益及优先权。登记不替代真实权属，Bill of Sale不替代顺位检索。将《开普敦公约》母公约与航空器议定书作为整体，结合交易时点、债务人所在地、登记国、对象门槛及相关国家第39、40、50、53、54、55条声明判断适用；取得对象搜索证书并核对制造商、通用型号、序列号、登记类型、登记时间、权利人、转让和注销状态。

### 3. 适航和运营资格

核验国籍证、适航证、运营规范、维修方案、适航指令、重大改装、噪声/无线电文件、技术记录和维修放行。无适航证、证件失效、记录严重缺失或进口型号认可障碍为阻断。运营人航线、时刻、机队利用率和维修资源只能由当前证据支持。

### 4. 维护状态和返还条件

按机身重检、发动机PR/LLP、APU、起落架、部件和内饰建立FH/FC/月历事件台账。储备金遵循`期初＋收取－合格报销－退款/转让＝期末`；保证金不是收入。返还补偿、储备金留存和残值不得对同一技术状态重复计值。

### 5. 运营与承租人现金流

第一还款来源同时看承租人整体经营现金流和飞机航线/机队贡献。客运模型核验ASK、RPK、客座率、收益率及CASK；货运核验ATK、载运率和收益率。缺少逐航线数据时只做限定分析，不用行业平均替代。

### 6. 出租人财务模型

模型逐年列示：购置/交付成本、基本租金、停租、储备金收取和报销、技术管理、保险/SPV、维护事件、过渡/取回、债务本息、税费、出售费用和净残值。输出LRF、项目NPV/IRR、权益IRR、CFADS、DSCR、LLCR、债务余额、储备金缺口、承租人租赁名义NPC和租金定价区间。

项目IRR不混入融资；权益IRR完整列债务提款和偿付。CFADS不把债务提款、保证金或应返还储备金作为收入。LLCR仅使用债务存续期CFADS现值。残值必须来自独立估值或明确情景。

租金区间采用“双边约束”：出租人下限为使项目现金流按目标项目收益率折现后NPV等于零的初始月租金；承租人上限为各年租前可用现金扣除维护储备金和承租人额外现金成本后可承担的最低初始月租金。若下限高于上限，触发`NO_FEASIBLE_RENT_CORRIDOR`。租前可用现金必须来自承租人项目预算或历史运营数据，折旧、融资提款和未经验证的收入倍数不得作为现金来源。

当前脚本为年度确定性审计模型，适合项目初筛、年度租金和偿债能力复算；不替代月度交割模型、浮动利率曲线、DSRA/现金清扫、逐月FH/FC维修触发或复杂税务模型。存在期中交割、建造付款、气球款、套保或非典型现金流时，必须另建月度模型并与本模型勾稽。

### 7. 压力测试

至少测试：租金中断6/12个月、利用率下降、维护提前、维修成本+20%/+40%、储备金不足、取回延迟6/12个月、过渡维修增加、残值-20%/-40%/-60%、利率+100/+200bp、外汇错配和承租人破产。

### 8. 取回、注销与再营销

形成违约通知—合同终止—破产/法院程序—IDERA或本地注销—适航放行—海关税费—调机/运输—过渡维修—再租/出售链。IDERA不等于不经安全、海关和司法程序即可物理取回。

### 9. 门禁与交付

红色问题阻断；黄色未关闭仅可有条件通过或待补件。每项风险写明证据、影响、缓释、责任人、期限和转绿条件。

## Hard Gates

- MSN、发动机或APU不能特定，实物与文件不一致；
- 权属链断裂、重复出售/融资或关键顺位无法清除；
- 双重国籍、适航证失效、重大AD/维修或技术记录缺口；
- 国际登记/IDERA/本地登记路径与交易结构不一致；
- 未取得对象搜索证书，或对象描述、国家声明及在先国际利益未核清；
- 维护事件、储备金、返还补偿和残值重复计值；
- 出租人最低可接受租金高于承租人现金流最高可承受租金；
- 基础或合理压力情景持续DSCR低于1.00且无补足；
- 取回、注销、出口或再营销路径在目标法域无法落地；
- 仅依赖未经独立评估的高残值才能达到回报门槛。

## Pitfalls

- 把机身、发动机、APU权属和价值合并；
- 把登记证当作所有权最终证明；
- 把维护储备金全部当作自由现金；
- FH/FC/月历触发年份与模型事件不勾稽；
- 返还补偿、半寿调整和残值重复计值；
- 用账面净值或单一评估替代压力净残值；
- 用行业平均租金、机价、利用率或残值固化默认参数；
- 把IDERA描述为无条件私力取回授权。

## Verification

- [ ] MSN、ESN、APU和实际位置逐架对应
- [ ] 权属链、登记链和国际利益分别核验
- [ ] 国籍、适航、维修方案及技术记录完整性有结论
- [ ] 储备金、报销、返还和余额闭环
- [ ] 维护事件与FH/FC/月历触发勾稽
- [ ] 项目IRR、权益IRR、DSCR、LLCR和NPC可复算
- [ ] 出租人租金下限、承租人租金上限和当前报价位置可复算
- [ ] 残值、返还补偿和储备金无重复计值
- [ ] 压力情景及取回链已运行
- [ ] 报告披露证据等级、资料时点和限制
