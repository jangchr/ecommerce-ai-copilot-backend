# L14.6 Pasted Reviews Input Guide Release Notes

状态：ready

## Commit

8219445

## Release 内容

Pasted Reviews Mode 增加输入指南。

## 新增内容

- What to paste
- Good example
- Weak example
- 中文输入指南
- 好评论 / 弱评论示例
- 更明确的用户评论输入提示

## 修复内容

修复中文模式下 Pasted Reviews guide copy 可能被英文覆盖的问题。

## 测试

- Frontend boundary test：PASS
- Fast gate：PASS，147 tests
- Public demo HTML check：PASS
- 中文 copy block check：PASS

## 当前可用能力

- Stable slug Product Mode
- Product Description Mode
- Pasted Reviews Mode
- Language Mode
- Pasted Reviews input guide
- Copy / Download
- Recent Generations
- Feedback Form
- Waitlist Form

## 边界

- 不改后端
- 不改 API
- 不改 workflow
- 不新增登录
- 不新增支付
- 不新增数据库

## 结论

L14.6 Pasted Reviews input guide release ready.
