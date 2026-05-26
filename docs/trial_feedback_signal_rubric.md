# L15.6-B Trial Feedback Signal Rubric

状态：ready

## 当前 commit

bb2d840

## 目标

定义第一轮真实用户反馈的信号判断规则。

## 强正向信号

满足任意一项：

- 用户主动说这个对自己的产品有用
- 用户成功生成并复制 / 下载结果
- 用户提交具体 feedback
- 用户加入 waitlist
- 用户问是否可以支持更多产品输入
- 用户愿意发第二个产品再试一次

## 中性信号

- 用户打开 demo 但没有完整生成
- 用户觉得方向有意思但目前不够清楚
- 用户喜欢某个模式但没有明确使用场景
- 用户只说 “looks good” 但没有细节

## 负向信号

- 用户不知道这个工具做什么
- 用户不知道应该点哪里
- 用户觉得生成结果不可用
- 用户觉得输入太麻烦
- 用户只想要 URL 自动抓取
- 用户不愿意粘贴评论或产品描述

## 需要特别记录的需求

- Amazon URL
- Shopify URL
- TikTok Shop URL
- CSV / bulk upload
- saved history
- team workspace
- pricing
- language quality
- mobile usability

## 判断规则

如果强正向信号 >= 2：

继续第二轮 outreach。

如果大多数反馈是“看不懂”：

回到 Public Demo copy polish。

如果大多数反馈是“想要 URL”：

进入 Shopify / Amazon input source planning。

如果大多数反馈是“结果不够好”：

进入 generation quality polish。

## 结论

该 rubric 用于避免凭感觉判断反馈。
