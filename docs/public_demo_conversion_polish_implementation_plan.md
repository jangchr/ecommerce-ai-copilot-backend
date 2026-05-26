# L15.0-H Public Demo Conversion Polish Implementation Plan

状态：ready

## 当前 commit

d35bf1e

## 推荐实现方式

小步前端 patch，不用 Codex，优先由用户执行 PowerShell。

## 第一批实现

L15.1-A Hero and Primary CTA Polish

预计修改：

- static/index.html
- tests/test_frontend_probe_boundary.py

内容：

- Hero copy
- Quick start buttons
- No login required note
- Product Description / Pasted Reviews mode chooser

## 第二批实现

L15.2-A Feedback and Waitlist CTA Polish

预计修改：

- static/index.html
- tests/test_frontend_probe_boundary.py

内容：

- Feedback CTA 更明显
- Waitlist CTA 更明显
- 结果区后增加 CTA reminder

## 第三批实现

L15.3-A Mobile Readability Polish

预计修改：

- static/index.html
- tests/test_frontend_probe_boundary.py

内容：

- spacing
- button wrapping
- helper text density
- result section readability

## 测试要求

每批代码改动后执行：

- tests.test_frontend_probe_boundary
- scripts/run_all_tests.py --fast

## 提交策略

代码改动：

单独提交。

文档记录：

5 到 10 个一批统一提交。

## 边界

- 不改后端
- 不改 API
- 不改 workflow
- 不新增登录
- 不新增支付
- 不新增数据库

## 结论

L15 可以继续用 PowerShell patch 小步推进。
