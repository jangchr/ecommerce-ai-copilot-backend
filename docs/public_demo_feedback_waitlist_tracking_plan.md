# L15.0-F Public Demo Feedback and Waitlist Tracking Plan

状态：ready

## 当前 commit

d35bf1e

## 目标

规划 Feedback / Waitlist 的轻量追踪方式。

## 当前表单

Feedback Form：

https://docs.google.com/forms/d/e/1FAIpQLSftwZouinTX8Z_9APPqDKu0zXyQsMXcqqHf7eZXzZft9MyqVA/viewform?usp=dialog

Waitlist Form：

https://docs.google.com/forms/d/e/1FAIpQLSd5rBYj_42J8gJ1n1deEl0ePySMKe6yaZ8K0gIvSt62QgsSnQ/viewform?usp=publish-editor

## 当前状态

- Feedback Form 已接入
- Waitlist Form 已接入
- 暂不新增 analytics
- 暂不新增数据库
- 暂不新增用户账户

## 推荐追踪方式

继续使用手动 tracker 文档：

- 用户来源
- 是否打开 demo
- 是否成功生成
- 使用了哪个模式
- 是否提交 feedback
- 是否加入 waitlist
- 主要反馈

## 可观察问题

- 用户有没有看到 Feedback Form
- 用户有没有看到 Waitlist Form
- 用户是否理解两个表单区别
- 用户是否愿意填写
- 用户是否认为填写成本太高

## 暂不做

- Google Analytics
- PostHog
- 数据库事件
- 用户账户
- cookie tracking
- 支付转化 tracking

## 结论

L15 继续保持轻量 tracking，通过表单和手动 tracker 观察转化。
