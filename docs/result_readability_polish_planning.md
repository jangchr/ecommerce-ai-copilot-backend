# L16.0-A Result Readability Polish Planning

状态：ready

## 当前 commit

7ebae43

## 目标

规划 L16 Result Readability Polish。

当前 demo 已经可以生成结果，但结果区下一步要更适合真实用户阅读、复制、判断和反馈。

## 当前问题

用户生成结果后，可能会遇到：

- Hook / Storyboard / Evaluation 信息较多
- 不知道最重要的结论在哪里
- 不知道哪些内容可以直接复制
- 不知道结果是否基于产品描述还是粘贴评论
- 不知道下一步该提交 feedback 还是加入 waitlist

## L16 目标

让结果区更像一个清晰的 Creative Brief：

1. Top summary
2. Hook
3. Storyboard
4. Why it works
5. Evidence / input source
6. Confidence / risks
7. Copy / download / feedback CTA

## 优先级

P0：

- 结果顶部增加简短 summary
- Hook 更醒目
- Storyboard 更容易扫读
- Evidence source 更清楚
- Feedback / Waitlist CTA 保持可见

P1：

- Copy buttons 更贴近各区块
- Markdown export 更清楚
- 中文结果区标题更自然
- 移动端结果区 spacing polish

P2：

- Brief score
- Result quality checklist
- Multiple output variants
- Saved result naming

## 边界

- 不改后端核心 workflow
- 不改 API contract
- 不新增数据库
- 不新增登录
- 不新增支付
- 不启用 Amazon URL Product Mode

## 结论

L16 应聚焦“生成后更好读、更好复制、更好判断”。
