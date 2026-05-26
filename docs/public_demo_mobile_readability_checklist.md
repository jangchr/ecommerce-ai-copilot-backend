# L15.0-E Public Demo Mobile Readability Checklist

状态：ready

## 当前 commit

d35bf1e

## 目标

整理 Public Demo 移动端可读性检查清单。

## 需要检查

Hero：

- 标题是否换行合理
- 副标题是否过长
- CTA 是否明显

Language selector：

- English / 中文 是否容易点击
- 当前语言是否明显

Product Description Mode：

- 输入框宽度是否合适
- helper text 是否太挤
- 按钮是否换行正常

Pasted Reviews Mode：

- textarea 是否足够高
- input guide 是否太长
- sample buttons 是否过多
- review count preview 是否可读
- pain point preview 是否可读

Result 区域：

- Hook 是否醒目
- Storyboard 是否容易扫读
- Copy / Download 按钮是否可点击

Feedback / Waitlist：

- 是否容易找到
- 是否太靠后
- 是否需要重复 CTA

## 风险

- Pasted Reviews Mode 现在内容较多
- 小屏上按钮可能堆叠
- helper box 可能占用太多空间
- Result 区域可能过长

## 建议

L15 可先做：

- 按钮分组
- helper text 缩短
- mobile spacing polish
- result section spacing polish

## 边界

- 只做 checklist
- 不改代码
- 不改 API
- 不改 workflow

## 结论

移动端 polish 应优先关注 Pasted Reviews 区块和结果区块。
