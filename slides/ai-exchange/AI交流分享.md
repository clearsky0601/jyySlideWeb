# AI 交流分享会

location: 215  
author: Tommy Song

[附上一张二维码]

----

## 今天想让大家带走什么？

- 知道 **Chatbot** 和 **Agent** 的区别
- 会用 Claude Code / Codex 做一些真实任务
- 知道什么时候该开新 session、压缩 context、使用 memory
- 能把 AI 接入科研工作流：读文献、写笔记、做图、做实验、做 slides
- 少踩几个坑：额度、上下文污染、误操作、模型选择

----

## Outline

- Agentic Coding：从聊天到真正做事
- Claude Code：常用命令、模式和小技巧
- Codex：本地任务、浏览器验证、Computer Use
- AI + 科研：绘图、Slides、NotebookLM、笔记软件
- 我的工具组合与主观经验

---

# Agentic Coding

从聊天到真正做事。

----

## 从 Chat 到 Agent

普通聊天：

- 你问一句，它答一句
- 主要输出文本
- 很少主动验证结果

Agent：

- 能读文件、跑命令、调工具、改代码
- 能根据结果继续下一步
- 能形成 **反馈循环**

![879](/media/uploads/ai-exchange/file-20260508170616326.png)

![400](/media/uploads/ai-exchange/IMG_7951.png)

----

## 先记住 6 个概念就够了

- **Token**：模型处理信息和计费的基本单位
- **Context**：模型当前一次能看见的工作空间
- **Session**：一次连续工作现场
- **Memory**：跨 session 保留的长期信息
- **MCP**：让 AI 连接外部工具的协议
- **Skills**：按需加载的专业能力包

> 先不用背术语，关键是知道它们会影响：价格、速度、准确性和可控性。

----

## Token：为什么会贵？

模型处理文本的最小单元。

- 1 token 大约等于 0.75 个英文单词，或约 1.5 个汉字
- **Input Token**：你输入、文件、工具结果、历史上下文
- **Output Token**：模型生成的内容，通常更贵
- **Cache Read / Write**：命中缓存后成本会明显下降

> 烧钱的本质：不是“问了几句话”，而是“塞了多少 token”。

https://platform.claude.com/docs/en/about-claude/pricing

![599](/media/uploads/ai-exchange/file-20260508133153719.png)

![808](/media/uploads/ai-exchange/file-20260508001443342.png)

----

## Context：为什么 AI 会忘、会乱？

Context 是模型一次“看得见”的工作空间。

- **Context Window**：一次最多能装下多少 token
- **Context Overflow**：超出窗口后，早期内容可能被截断
- **Context Compression**：旧对话被自动压缩成摘要
- **Context Pollution**：无关信息太多，输出质量下降
- **Context Engineering**：只把真正有用的信息放进去

> 一次性灌太多材料，不一定更聪明，很多时候只是更混乱。

![441](/media/uploads/ai-exchange/file-20260508133827516.png)

![476](/media/uploads/ai-exchange/file-20260508003804634.png)

----

## Session & Memory

**Session** 是一次连续工作现场：

- 有独立的 context window
- 可以通过 `/resume` 或 session id 恢复
- 适合按项目、按任务拆开

**Memory** 是跨 session 的长期信息：

- 项目说明、个人偏好、常用路径
- 例如 `CLAUDE.md`、`AGENTS.md`、自动 memory、笔记库

> Context = 这次我看见了什么；Memory = 下次我还应该记得什么。

----

## MCP & Skills

**MCP**：Model Context Protocol

- 标准化工具 / 资源调用协议
- 让 Claude、Codex 等接入 GitHub、Notion、浏览器、数据库、Anki……
- 可以理解成 AI 工具世界里的“接口标准”

**Skills**

- `instruction + 资源 + 脚本` 的专业知识包
- 不用时不占 context，用到时再加载
- 例：`pptx`、`frontend-design`、`obsidian-markdown`

----

## Agent 真正变强靠什么？

> 不是只靠更长提示词，而是靠工作流。

- **Feedback Loop**：做一步，看结果，再调整
- **Harness Engineering**：给 Agent 配工具、权限、规则和外壳
- **Orchestrator**：把复杂任务拆解、排序、并行
- **Delegation**：把搜索、审查、实现交给不同 subagent

----

## Feedback Loop：最重要的思维

Agent 调用工具 -> 拿到结果 -> 据此调整下一步。

典型例子：

- 跑测试 -> 失败 -> 读报错 -> 改代码 -> 再跑
- 编译论文 -> 报错 -> 查缺失包 -> 修 LaTeX -> 再编译
- 打开网页 -> 截图 -> 发现遮挡 -> 改 CSS -> 再看

> 没有反馈的 Agent，只是在猜。

----

## 怎么用起来？

- 选择入口：Claude Code / Codex / 其他 Agent 工具
- 解决认证：账号订阅、API Key、OAuth、中转站
- 控制成本：模型选择、context 管理、缓存、分任务开 session
- 建立习惯：每次让 AI 真的跑一下、看一下、验证一下

配图：

![667](/media/uploads/ai-exchange/IMG_7481.png)

推荐大家一个很有趣的短视频：

https://www.bilibili.com/video/BV15XQyBjEHc/?spm_id_from=333.337.search-card.all.click&vd_source=f4ff90f6cc9f047c8f715e66ae009eb7

----

## CC-Switch

https://github.com/farion1231/cc-switch

一句话介绍：

> 一个跨平台的 All-in-One assistant 工具，可以统一管理 Claude Code、Codex、OpenCode、openclaw、Gemini CLI 等工具入口。

适合：

- 多个模型 / 多个 provider 来回切换
- 本地统一管理 API Key、Base URL、模型配置
- 想快速比较不同 Agent 工具体验

----

## 配置 CC-Switch

核心配置：

- Base URL
- API Key
- Model
- Tool / Agent 类型

![499](/media/uploads/ai-exchange/file-20260508133003455.png)

---

# Claude Code

适合做什么？

- 理解一个陌生代码库
- 修改代码、跑测试、修 bug
- 批量重构、写脚本、整理文档
- 让 AI 在终端里形成可验证的工作流

----

## Claude Code 的常用工作姿势

不要一上来就说“帮我改一下”。

更推荐这样：

```text
先读这个项目的 README、package.json 和入口文件。
告诉我它的技术栈、启动方式、核心模块。
先不要改代码。
```

然后再说：

```text
现在帮我实现 xxx。
改完后跑测试或启动服务验证。
```

----

## Claude Code：上下文相关命令

这些命令解决“对话越来越长”的问题。

- `/context`：查看当前 session 的上下文占用
- `/compact`：压缩当前对话，释放 context
- `/resume`：恢复之前的 session
- `claude -c`：命令行直接继续最近一次 session
- `claude -r <session-id>`：按指定 session id 恢复

> 长任务不要硬撑，该 compact 就 compact，该开新 session 就开新 session。

----

## Claude Code：控制方向的命令

这些命令解决“AI 走偏了怎么办”。

- `/rewind`：回到之前某个 turn，重新走一遍
- `/config`：打开配置面板，调整权限、模型等
- `/model`：切换模型
- `/effort`：调整 reasoning budget
- `claude --verbose`：打开详细日志，排查 MCP、hook、权限问题

----

## Claude Code：工程化能力

- `/mcp`：查看和管理 MCP 服务器
- `/agents`：管理 subagents
- Hooks：在特定事件触发 shell 脚本
- Skills：让 Claude 按需加载专门能力

适合做：

- 自动注入项目背景
- 自动检查危险命令
- 给不同任务分配不同 agent
- 让 Claude 接入浏览器、GitHub、数据库、Anki 等外部系统

----

## Claude Code 的几个 Mode

权限光谱：从“先想清楚”到“全自动执行”。

- **Default**：每次工具调用都确认，适合新手和关键目录
- **Plan mode**：只读不写，适合先分析方案
- **Accept edits**：自动接受编辑，适合方向明确的批量改动
- **Bypass permissions**：跳过权限确认，只建议在沙盒、容器、临时 worktree 使用

> Tips：按住 **Shift + Tab** 可以快速切换模式。

----

## Claude Code Demo：研究一个陌生项目

可以现场演示：

```text
请先不要改代码。
阅读 README、依赖文件和入口文件。
告诉我：
1. 这个项目是做什么的
2. 技术栈是什么
3. 怎么启动
4. 核心模块在哪里
5. 如果我要加一个功能，应该从哪里入手
```

----

## Claude Code Demo：让它闭环验证

关键提示词：

```text
实现后请你自己验证。
如果有测试就跑测试；
如果是前端就启动服务并检查页面；
如果是脚本就用一个最小样例运行。
最后告诉我验证命令和结果。
```

重点不是“AI 写了什么”，而是“它有没有验证”。

---

# Codex

Codex 更适合：

- 本地 workspace 里的代码修改和文件操作
- 浏览器 / 前端页面验证
- Computer Use：操作桌面应用
- 长任务中持续读文件、改文件、跑命令
- 和你一起做“本机真实环境”的工作

----

## Why Codex？

- 对本地 repo 的协作感更强
- 浏览器验证、截图检查、Computer Use 体验更完整
- 适合把任务从“回答问题”推进到“完成一个本地交付物”
- 对文件、终端、前端预览的闭环更自然

> Claude Code 和 Codex 不一定二选一，可以按任务搭配。

----

## Claude Code vs Codex：我怎么选？

| 场景 | 更推荐 |
|---|---|
| 终端里快速改项目 | Claude Code / Codex 都可以 |
| 需要本地浏览器截图验证 | Codex |
| 需要桌面应用操作 | Codex Computer Use |
| 需要 Claude 生态 MCP / Hooks | Claude Code |
| 想比较多个模型 / provider | CC-Switch |
| 长期项目记忆和固定规则 | 两边都要配置好项目说明 |

----

## Codex Demo：修改一份 Markdown

可以现场演示这件事：

```text
请阅读这份 Markdown slides。
帮我把它改成更适合 30 分钟分享的结构：
1. 保留原来的图片
2. 统一 slide 分隔符
3. 每个技术点都加一个可演示的小例子
4. 直接修改原文件，并备份一份
```

这类任务适合 Codex，因为它能直接在本地文件系统里完成。

----

## Codex Demo：前端闭环

适合演示：

```text
启动这个前端项目。
打开本地页面。
截图检查布局。
如果文字溢出、按钮重叠、画面空白，请直接修复。
最后告诉我访问地址和验证结果。
```

重点：

- 不是只写代码
- 还要真的打开页面看
- 修改后再验证

---

# AI + 科研

AI 可以帮科研做什么？

- 读论文：提炼问题、方法、贡献、局限
- 写笔记：把散乱内容整理成结构化知识
- 做图：流程图、框架图、示意图、配色参考
- 做 slides：从论文 / 笔记生成讲稿结构
- 做实验辅助：写脚本、画曲线、整理结果

----

## 当下做图的痛点

- 直接调提示词，很难一次得到满意的图
- 时间长，迭代慢，成本高
- 模型容易把文字、结构、风格混在一起
- 论文图需要准确，不只是“好看”

所以我的建议：

> 不要指望一次生成最终图，而是找到 AI 最擅长的部分。

----

## AI 绘图更适合帮哪几件事？

- 布局参考
- icon / 元素风格
- 配色方案
- 视觉隐喻
- 初稿探索
- 局部重绘

不建议完全交给 AI 的部分：

- 关键公式
- 精确坐标
- 论文中的严谨文字
- 最终可投稿版本的排版细节

----

## 我的科研绘图流程

1. 先用文字说清楚这张图要表达什么
2. 让 AI 生成 2-3 个结构草图
3. 选一个布局方向
4. 分开迭代：布局、icon、配色、文案
5. 用最好模型生成高质量初稿
6. 最后进 PPT / Figma / draw.io / LaTeX 里重排

![792](/media/uploads/ai-exchange/e49cedda3449b4d3830fdd3df4f4fbe1.jpg)

（图片由 GPT-image2 生成）

----

## 一个可复用的绘图提示词

```text
我要做一张论文方法框架图。
主题是：[你的方法主题]
图中必须包含：[模块 A]、[模块 B]、[模块 C]
它们之间的关系是：[数据如何流动]
风格要求：
- 学术论文风格
- 简洁、清晰、适合放在 slides
- 不要复杂背景
- 文字只用英文短词

请先给我 3 个布局方案，不要直接出图。
```

----

## 多模态模型和工具选择

可以关注：

- nanobanana
- nanobanana2
- GPT-image2
- 其他图像生成 / 编辑模型

![678](/media/uploads/ai-exchange/file-20260508165422773.png)

> 正式分享前建议更新一版：模型名字、价格、效果都变得很快。

----

## 推荐阅读

- https://x.com/hitw93/status/2032091246588518683?s=46
- https://x.com/JustinLin610/status/2037116325210829168
- https://mp.weixin.qq.com/s/tO15UKQG0WtTBTNz8QLQjQ

---

# 工具组合与心得

把前面的工具串成自己的长期工作流。

----

## Slides / NotebookLM / BrowserUse / ComputerUse

这些工具可以串成一个科研工作流：

- NotebookLM：围绕论文、资料做问答和总结
- Slides：把笔记转成汇报结构
- BrowserUse：需要网页操作时自动浏览、搜索、填写
- ComputerUse：需要操作桌面软件时接管 GUI
- Obsidian：沉淀自己的长期知识库

----

## 笔记软件怎么选？

可以从这几个维度比较：

- 多设备同步
- 隐私性
- Markdown 兼容性
- 离线可用性
- AI 接入难度
- 长期可迁移性

----

## Notion / Obsidian / Word / OneNote / 幕布

| 工具 | 优点 | 注意点 |
|---|---|---|
| Notion | 协作强、数据库强、界面友好 | 离线和迁移成本要考虑 |
| Obsidian | 本地 Markdown、可控、插件丰富 | 同步和插件配置需要折腾 |
| Word | 正式文档、格式稳定、审阅强 | 知识库和链接能力弱 |
| OneNote | 手写、课堂笔记、多设备体验好 | Markdown 和导出不够理想 |
| 幕布 | 大纲整理快 | 长期知识管理能力有限 |

----

## 我的工具组合

可以按任务分工：

- Obsidian：长期笔记和个人知识库
- NotebookLM：围绕一批文献快速问答
- Claude Code / Codex：本地项目、脚本、文档和自动化
- 图像模型：科研图初稿、配色、视觉方案
- PPT / Figma / draw.io：最终排版和精修

![675](/media/uploads/ai-exchange/9AD3E7E9-D653-4567-B70F-DB751CCD7307.png)

----

## 一点小小的心得

- 用好模型做关键任务，用便宜模型做批量任务
- 复杂任务要拆小，不要一次塞满
- 让 AI 自己验证结果，而不是只让它“生成”
- 保存好的提示词、项目说明和工作流
- 不要迷信某一个工具，工具会变，方法更重要
- 别掉队，但也不用焦虑，只和过去的自己比较

----

## 我的主观模型感受

🤩 顶级旗舰  
Claude Opus 系列、GPT 旗舰系列

👊 国产模型  
Mimo、GLM、DeepSeek、Kimi 等

![668](/media/uploads/ai-exchange/file-20260508161805277.png)

![656](/media/uploads/ai-exchange/file-20260508161216146.png)

（纯主观感受，正式分享前建议更新到当天版本。）

![636](/media/uploads/ai-exchange/Agentic 带模型～.png)

----

## 更加重要的是：形成自己的工作流

![870](/media/uploads/ai-exchange/file-20260508135717731.png)

工具会变：

- 今天是 Claude Code / Codex
- 明天可能是新的 Agent 工具
- 模型名字和价格也会一直变

但长期有效的是：

- 会拆任务
- 会控制上下文
- 会让 AI 验证
- 会把经验沉淀成模板和笔记

----

## 结束页

Stay curious, keep exploring!

Have a good day! 😃

