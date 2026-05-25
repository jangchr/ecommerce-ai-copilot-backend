# L14.5-A Pasted Reviews Next Roadmap Decision

状态：ready

## 当前 commit

fa21658

## 决策

Pasted Reviews Mode v1 完成后，下一步优先做输入体验打磨，而不是立刻做 Amazon URL。

## 原因

- Pasted Reviews 已经接近真实用户评论场景
- 不依赖外部抓取
- 不需要 Amazon 反爬处理
- 不需要登录或数据库
- 可以更快验证用户是否愿意使用评论驱动创意生成

## 推荐下一阶段

进入：

Pasted Reviews polish

优先级：

1. 输入指南
2. 示例评论库
3. 评论质量提示
4. 更明显的 paste guide
5. 输出质量评分规则
6. 公网 demo 引导优化

## 暂不优先做

- Amazon URL Product Mode
- Shopify URL
- TikTok Shop URL
- CSV 上传
- 登录
- 支付
- 数据库

## 后续触发 Amazon Beta 的条件

只有出现以下信号再优先做 Amazon：

- 多个真实用户明确要求 Amazon URL
- 用户不愿意手动粘贴评论
- 用户认为复制评论太麻烦
- 用户已经有真实 Amazon listing
- Pasted Reviews feedback 显示输入成本过高

## 结论

下一阶段优先优化 Pasted Reviews 输入体验。
