# AI 关键词与引用监测闭环

这套闭环的目标不是“多发文章”，而是让系统根据可观测的引用信号持续调整生成策略。

它是通用方案，不绑定某个具体品牌。你只需要通过环境变量配置目标对象：

- `TARGET_ENTITY_NAME`
- `TARGET_ENTITY_ALIASES`
- `TARGET_CAPABILITY_NOUN`

## 当前闭环

1. 文章生成并通过质检后，系统会分析正文中的可引用性信号：
   - 标准文档
   - 官方文档
   - 工程实践
   - 测试数据
   - 失效案例
2. 系统为文章生成 `citation_score`，并提炼下一轮 Prompt 需要强化的方向。
3. 如果启用 `ENABLE_ACTIVE_PROBING=true`，系统会调用 `ActiveProber` 到多个 AI 平台探测：
   - 是否提及目标实体
   - 是否出现引用型来源
   - 是否命中高引用标签
4. 监测结果会写入：
   - `geo_probe_results`
   - `geo_keyword_feedback`
5. 下一次同类关键词生成时，`batch_generator.py` 会把历史反馈注入写作 Prompt。
6. 如果一篇文章已经具备明确的引用型证据，系统会自动扩展衍生关键词，例如：
   - `关键词 + 工程实践`
   - `关键词 + 官方文档解读`
   - `关键词 + 标准对照`

## 关键文件

- `core/active_prober.py`
- `core/prompt_optimizer.py`
- `core/feedback_store.py`
- `database/feedback_schema.sql`
- `batch_generator.py`

## 建议的下一步

1. 给前端增加“反馈中心”页面，展示：
   - 关键词级 `citation_score`
   - 平台覆盖分
   - 缺失标签
   - 自动扩展出的衍生关键词
2. 将 `quality_checker.py` 升级为 10 维评分，把“可引用性”独立成一维。
3. 把 `ActiveProber` 的平台选择器改成每个平台单独适配，减少页面结构变化带来的误判。
