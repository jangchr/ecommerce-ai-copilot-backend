# CrossGrowth Multi-Agent Demo Walkthrough

## 1. 项目定位

CrossGrowth 是一个面向电商短视频生产的多 Agent 协作工作台。

它不是一个普通的自动化脚本，也不是简单把多个步骤串起来。它的核心价值是：

- 从真实评论和商品信息中提取证据；
- 让不同 Agent 分别负责证据、策略、分镜、商品约束、关键帧、视频提示词、成本、风险和实验记录；
- 把每个 Agent 的输入、判断、输出、风险和交接结果展示出来；
- 最终生成可以给 Gemini、豆包、Runway、Pika、CapCut 等工具使用的视频生成包。

当前版本默认不调用真实外部视频 API，不需要 API key，也不会产生视频 API 成本。

---

## 2. 为什么这不是普通自动化

普通自动化流程通常是：

```text
Step 1 → Step 2 → Step 3 → Output

CrossGrowth 的多 Agent 工作流是：

Evidence Agent
→ Strategy Agent
→ Storyboard Agent
→ Asset Lock Agent
→ Keyframe Agent
→ Prompt Handoff Agent
→ Cost Agent
→ Risk Agent
→ Provider Job Agent
→ Experiment Agent

区别在于，每个 Agent 都不是简单“执行一步”，而是有自己的：

goal：这个 Agent 的目标；
input_artifacts：它接收哪些业务产物；
decision_summary：它做了什么判断；
output_artifacts：它产出了什么；
warnings：它发现了什么风险；
handoff_to：它把结果交给谁；
business_impact：它对业务有什么价值；
requires_human_review：是否需要人工确认。

所以它展示的是 Agent 协作能力，而不是普通流程自动化。

3. Agent 分工
Evidence Agent

负责从评论和商品信息中提取证据。

它会整理：

买家痛点；
买家 objections；
正面信号；
评论证据；
证据边界；
数据来源风险。

业务价值：

防止后续生成的视频脚本和广告话术脱离真实评论，减少 AI 胡编。

Strategy Agent

负责把评论证据转成营销角度。

它会判断：

目标用户是谁；
哪个痛点最适合当 Hook；
应该采用什么情绪触发点；
视频应该强调什么解决方案。

业务价值：

把零散评论变成一个可以转化的广告方向。

Storyboard Agent

负责生成短视频脚本和分镜。

它会产出：

Hook；
CTA；
TikTok 风格脚本；
Storyboard；
每个场景的画面目标；
每个场景的字幕或旁白。

业务价值：

把营销策略变成可拍摄、可生成的视频结构。

Asset Lock Agent

负责锁定商品视觉身份。

它会产出：

product_asset_lock；
商品 identity；
商品 category；
must_preserve；
must_not_change；
image_reference_rules；
human_review_required。

业务价值：

防止 Gemini、豆包、Runway、Pika 等视频工具把商品生成跑偏，比如颜色变了、材质变了、形状变了，或者变成了别的商品类别。

Keyframe Agent

负责把分镜变成关键帧计划。

它会产出：

keyframe_plan；
每个场景的 keyframe_goal；
product_position；
camera_direction；
motion_control；
overlay_text；
evidence_anchor；
risk_notes。

业务价值：

让外部视频工具不是自由发挥，而是按照更清晰的视频施工图生成。

Prompt Handoff Agent

负责生成外部视频工具可用的提示词。

它会产出：

Gemini video prompt；
Doubao video prompt；
general image-to-video prompt；
short motion prompt；
full handoff package；
negative prompt；
copy-ready generation brief。

业务价值：

CrossGrowth 不一定自己生成视频，而是先生成一份高质量的视频生成包，让用户可以复制到外部工具中测试效果。

Cost Agent

负责成本估算和付费风险控制。

它会产出：

provider cost estimate；
pricing_is_estimate；
requires_user_confirmation；
external_api_call_planned=false。

业务价值：

在接入真实视频 API 前，先告诉用户预计成本，避免 API 费用失控。

Risk Agent

负责检查证据边界和生成风险。

它会关注：

是否有 unsupported claims；
是否夸大评论证据；
是否出现医疗、安全、市场级绝对化表达；
是否需要人工复核。

业务价值：

降低广告话术和视频生成中的合规风险、夸大风险和证据不匹配风险。

Provider Job Agent

负责把视频生成变成一个可追踪任务。

它会记录：

video_job_id；
provider；
selected prompt；
cost_estimate；
provider_runtime；
status；
result_url；
history。

当前状态是 simulated provider flow：

ready_for_manual_export
→ queued
→ processing
→ external_result_ready

业务价值：

未来如果接真实视频 API，这个位置可以承接真实 submit / poll / result_url 流程。

Experiment Agent

负责记录外部视频实验。

它会记录：

tool_name；
prompt_type；
result_url；
preview_url；
actual_cost_usd；
product_consistency_score；
storyboard_following_score；
visual_quality_score；
ad_readiness_score；
overall_score；
notes；
failure_reason。

业务价值：

用户可以手动用 Gemini、豆包、Runway、Pika 生成视频，再把结果记录回来，用真实实验决定哪个工具值得接 API。

4. 演示流程
Step 1：输入商品和评论

演示时输入：

Product: Portable Mini Blender
Category: kitchen_appliance
Reviews:
- Hard to clean after one smoothie.
- Too loud for early mornings.
- Small enough for travel but the cup sometimes leaks in my bag.

说明：

用户只需要提供商品信息和评论，系统会从评论中提取真实买家痛点。

Step 2：生成评论证据和创意策略

展示：

buyer pain points；
buyer objections；
evidence quotes；
Hook；
CTA；
Storyboard。

讲解重点：

Evidence Agent 和 Strategy Agent 不是在凭空写广告，而是基于评论证据选择视频角度。

Step 3：展示 Multi-Agent Workflow

打开：

Business-grounded Multi-Agent Workflow

重点展示：

is_plain_automation=false；
agent_count=10；
每个 Agent 有 goal、decision、artifacts、handoff、warnings、business impact；
每个 Agent 都绑定真实业务产物。

讲解重点：

这里不是普通 Step 流程，而是每个 Agent 有独立职责和判断，并把产物交给下一个 Agent。

Step 4：展示 Product Asset Lock

在 External Video Tool Handoff 中展示：

Product Asset Lock；
must preserve；
must not change；
image reference rules；
human review required。

讲解重点：

视频模型很容易让商品跑偏，所以 Asset Lock Agent 会先锁定商品身份，要求外部工具保持商品类别、颜色、材质、形状和主商品 identity。

Step 5：展示 Keyframe Plan

展示：

Keyframe Plan；
recommended clip strategy；
scene count；
keyframe goal；
product position；
camera direction；
evidence anchor；
risk notes。

讲解重点：

Keyframe Agent 把视频拆成可控关键帧，不让视频模型自由发挥。

Step 6：展示外部视频工具 Handoff

展示：

Gemini prompt；
Doubao prompt；
image-to-video prompt；
negative prompt；
full handoff package。

讲解重点：

CrossGrowth 当前不直接调用外部视频 API，而是生成可以复制到 Gemini、豆包、Runway、Pika 的视频生成包。

Step 7：展示成本估算

展示：

Estimated API cost；
pricing_is_estimate；
requires_user_confirmation；
external_api_call_planned=false。

讲解重点：

在真实 API 接入前，系统先做成本闸门，避免直接产生费用。

Step 8：创建 Video Job

展示：

Create video job；
provider；
selected prompt；
provider payload；
cost estimate。

然后演示 simulated provider flow：

Submit provider job
→ queued
Poll provider status
→ processing
Complete simulated provider result
→ external_result_ready

讲解重点：

当前是模拟 provider 生命周期，不产生外部 API 调用。未来接真实 API 时可以替换 provider client。

Step 9：展示 External Video Experiments

展示：

tool_name；
prompt_type；
result_url；
scores；
actual_cost_usd；
notes。

讲解重点：

用户可以手动去 Gemini 或豆包生成视频，再把结果记录回来。这个记录会帮助判断未来哪个 provider 值得接真实 API。

5. 2 分钟演示话术

这个项目是一个面向电商短视频生产的多 Agent 协作系统。

用户输入商品和评论后，系统不会直接让一个模型随便生成广告，而是启动一条业务绑定的 Agent workflow。

Evidence Agent 先从评论中提取买家痛点和证据边界；Strategy Agent 选择营销角度；Storyboard Agent 生成短视频脚本和分镜；Asset Lock Agent 锁定商品视觉身份，防止视频生成时商品跑偏；Keyframe Agent 生成每个镜头的关键帧计划；Prompt Handoff Agent 生成 Gemini、豆包、Runway、Pika 可用的视频生成提示词；Cost Agent 估算 API 成本；Risk Agent 检查夸大和证据风险；Provider Job Agent 追踪视频任务状态；Experiment Agent 记录外部工具生成结果。

这个系统和普通自动化不一样。普通自动化只是 step by step 执行任务，而这里每个 Agent 都有自己的目标、输入、判断、输出、风险和交接对象，并且都绑定真实业务产物。

当前版本默认不调用真实外部视频 API，不需要 key，也不会产生费用。它先作为视频生成前的大脑和协作工作台，帮助用户低成本验证 Gemini、豆包、Runway 或 Pika 的实际效果。等实验结果证明某个工具质量和成本都可接受后，再考虑接入真实 API。

6. 5 分钟演示话术

CrossGrowth 的目标是解决一个真实问题：电商卖家有很多评论，但很难把这些评论快速转化成高质量短视频广告。

我不是简单做一个文案生成器，而是把这个过程拆成多个 Agent 协作。

第一步，Evidence Agent 读取商品评论，找出真实买家痛点、objections 和证据 quote。这样后面的广告不会胡编。

第二步，Strategy Agent 根据这些证据选择营销角度，比如应该打“便携”、“清洗麻烦”、“漏水风险”还是其他痛点。

第三步，Storyboard Agent 把策略变成 TikTok 视频脚本和分镜，包括 Hook、CTA、每个场景的画面和字幕。

第四步，Asset Lock Agent 锁定商品视觉身份。因为视频生成模型很容易把商品生成错，所以系统会明确告诉外部工具：产品类别不能变，颜色、材质、形状、包装和主商品 identity 不能跑偏。

第五步，Keyframe Agent 把分镜拆成更稳定的关键帧计划。每个镜头都有 keyframe goal、product position、camera direction、motion control、overlay text、evidence anchor 和 risk notes。

第六步，Prompt Handoff Agent 根据这些产物生成 Gemini、豆包、Runway、Pika 可直接使用的提示词。用户可以复制这些提示词去外部工具手动测试视频效果。

第七步，Cost Agent 做成本估算。因为视频 API 很贵，所以系统不会直接调用收费接口，而是先展示预计成本、是否需要用户确认，以及 external_api_call_planned=false。

第八步，Provider Job Agent 把视频生成变成一个可追踪任务。当前是 simulated provider flow，可以测试 queued、processing、external_result_ready 的生命周期，但不会产生真实费用。

第九步，Experiment Agent 允许用户把外部工具生成的视频结果记录回来，包括结果 URL、实际成本、商品一致性评分、分镜执行评分、视觉质量和广告可用度。

这条链路的重点是：它不是把自动化步骤包装成 Agent，而是每个 Agent 都有真实业务职责和真实业务产物。这个设计既能展示多 Agent 协作能力，也保留了评论分析、证据约束、视频分镜、成本控制和实验记录这些业务硬实力。

7. 当前不做什么

当前版本明确不做：

不真实调用 Gemini、豆包、Runway、Pika API；
不要求 API key；
不产生外部视频 API 成本；
不承诺自动生成最终视频；
不让用户无限制重试高成本视频生成；
不为了演示牺牲评论证据和业务约束。
8. 后续计划
下一步：Demo 收口
继续压缩 UI 重点；
准备固定 demo 样例；
准备截图或录屏；
明确 2 分钟和 5 分钟演示路径。
再下一步：Evaluation Agent

让系统帮助用户评价外部视频结果：

商品有没有跑偏；
是否按分镜执行；
是否符合评论证据；
是否适合广告投放；
是否值得继续花钱生成。
之后：Provider API 成本审查

在任何真实 API 接入前，先确认：

是否有免费额度；
单次生成多少钱；
失败重试成本；
API key 要求；
是否能接受月成本；
是否值得接入。
最后：真实 API 接入

只有当手动实验结果证明某个工具效果和成本都可接受后，才考虑真实接入：

provider client；
real submit；
real poll；
real result_url；
budget guard；
retry limit；
user confirmation。
