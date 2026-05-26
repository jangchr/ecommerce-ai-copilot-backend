# L18 Public Demo Release Notes

Commit: 4e40ef7

## 用户可见变化

- 首屏更清楚地说明 demo 用途
- 用户先选择起点，而不是面对多个表单
- 产品想法和用户反馈路径分开
- 中文模式下输入引导、按钮、结果区和最近生成记录更完整
- 生成结果不再需要滑到页面底部寻找
- 底部反馈和试用名单入口去重

## 技术边界

未修改：

- 后端 API
- workflow
- schema
- storage
- deployment config

主要修改：

- static/index.html
- tests/test_frontend_probe_boundary.py
