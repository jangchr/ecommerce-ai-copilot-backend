# L15.0-A Public Demo Conversion Polish Planning

状态：ready

## 当前 commit

d35bf1e

## 目标

规划 L15 Public Demo Conversion Polish。

目标不是继续增加复杂功能，而是让公网 demo 更容易被第一次打开的用户理解、试用、反馈和加入 waitlist。

## 当前问题

Public Demo 已经有很多能力：

- Product Description Mode
- Pasted Reviews Mode
- Language Mode
- Sample product
- Sample reviews
- Copy / Download
- Feedback Form
- Waitlist Form
- Debug advanced section

但新用户第一次打开时，可能会遇到：

- 不知道先点哪里
- 不知道哪个模式最适合自己
- 页面能力太多
- Feedback / Waitlist 不够醒目
- 主路径不够明确
- 移动端阅读成本可能偏高

## L15 目标

优化主路径：

1. 选择语言
2. 选择输入方式
3. 使用示例
4. 生成结果
5. 复制或下载
6. 提交反馈
7. 加入 waitlist

## 优先级

P0：

- Hero 文案更清楚
- Primary CTA 指向最容易成功的路径
- Product Description / Pasted Reviews 主路径更明显
- Feedback / Waitlist CTA 更清晰
- Debug advanced section 保持弱化

P1：

- 移动端可读性
- result 区块层级
- sample 按钮文案
- first-time user helper copy

P2：

- 更多视觉 polish
- conversion tracking 文档
- trial outreach copy

## 边界

- 不新增登录
- 不新增支付
- 不新增数据库
- 不新增外部抓取
- 不改后端 API
- 不改 workflow
- 不启用 Amazon URL Product Mode

## 结论

L15 应聚焦 public demo 转化，而不是继续扩功能。
