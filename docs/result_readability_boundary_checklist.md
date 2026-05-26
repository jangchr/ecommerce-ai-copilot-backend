# L16.0-D Result Readability Boundary Checklist

状态：ready

## 当前 commit

7ebae43

## 目标

定义 L16 Result Readability Polish 的边界。

## 允许做

- 前端布局优化
- 结果区标题优化
- copy / download 文案优化
- CTA 位置优化
- CSS mobile polish
- tests/test_frontend_probe_boundary.py 边界测试

## 不允许做

- 改 main.py workflow
- 改 schemas/api_contract.py
- 改生成结果 JSON contract
- 新增数据库
- 新增登录
- 新增支付
- 新增外部抓取
- 自动调用 Source Probe
- 自动调用 Amazon Shadow

## Debug 边界

继续保持：

- 不显示 data.debug
- 不显示 telemetry_summary
- 不显示 shadow_sources
- 不显示 memory_observability

## Product 边界

继续保持：

- Product Description Mode 使用 user_provided_description
- Pasted Reviews Mode 使用 user_pasted_reviews
- Stable demo 不变
- Amazon URL runtime 不启用

## 测试要求

每个前端小改后执行：

- tests.test_frontend_probe_boundary
- scripts/run_all_tests.py --fast

## 结论

L16 只做前端结果可读性，不动后端核心。
