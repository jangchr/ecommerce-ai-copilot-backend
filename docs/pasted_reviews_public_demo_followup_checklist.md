# L14.5-F Pasted Reviews Public Demo Follow-up Checklist

状态：ready

## 目标

整理 Pasted Reviews Mode 公网后续检查项。

## 每次部署后检查

- Public Demo 可打开
- Pasted Reviews Mode 可见
- Use sample reviews 可用
- Generate from reviews 可用
- English 模式可生成
- 中文模式可生成
- 中文无乱码
- Copy / Download 可用
- Recent Generations 可用
- Feedback / Waitlist 可见

## API 检查

- /api/v1/generate-from-reviews 返回 200
- output_language=en 可用
- output_language=zh-CN 可用
- source_type=user_pasted_reviews
- 不返回 telemetry_summary
- 不返回 shadow_sources
- 不返回 memory_observability

## 浏览器检查

- Ctrl + F5 强刷
- 检查页面不是旧缓存
- 检查 Render 部署 commit 正确
- 检查手机窄屏布局

## 结论

Pasted Reviews 后续每次发布都应检查中英文和 debug 边界。
