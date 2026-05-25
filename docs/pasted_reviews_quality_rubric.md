# L14.5-E Pasted Reviews Quality Rubric

状态：ready

## 目标

定义 Pasted Reviews Mode 输出质量评分规则。

## 评分维度

### 1. Pain point grounding

好的输出应明确引用用户粘贴评论中的痛点。

### 2. Hook usefulness

Hook 应该：

- 直接抓住痛点
- 适合短视频开头
- 不夸大
- 不脱离评论证据

### 3. Storyboard usability

分镜应：

- 可拍摄
- 场景清楚
- 每个场景连接一个痛点
- 不需要高成本制作

### 4. Language quality

中文模式：

- 中文自然
- 不乱码
- 不出现 mojibake
- 不混乱夹杂英文

英文模式：

- 英文自然
- 不重复
- 不像模板

### 5. Evidence integrity

不能虚构外部评论。

只使用用户粘贴内容。

## 通过标准

- 有明确痛点
- Hook 可直接使用
- Storyboard 可拍
- 中文无乱码
- 不暴露 debug-only 字段

## 失败标准

- 输出和评论无关
- Hook 太泛
- 分镜不可拍
- 中文乱码
- 出现 telemetry_summary / shadow_sources / memory_observability

## 结论

质量评估应优先看是否从真实评论中提炼出可用创意。
