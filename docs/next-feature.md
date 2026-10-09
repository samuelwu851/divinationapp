---
name: next-features
description: 易经模块接下来要加的功能（变卦、变卦的互错综、崔氏易林）
metadata: 
  node_type: memory
  type: project
  originSessionId: b4962684-3ef0-4fc6-bce7-b9820ad5ca62
---

易经速查当前进度：本卦（六爻可点变爻 + 爻辞 + 乾坤用九/用六）、卦辞、错/综/互卦小图（点开 popover 看带爻题前缀的爻辞）均已完成，macOS 上跑通。见 [[architecture-decisions]]。

**接下来要加（用户 2026-10-07 记下，计划 2026-10-08 起做）：**
1. **变卦**：由变爻（动爻）推出的那一卦，显示出来。内核 `core.flip` 已有单爻翻转；多爻变卦需要确认内核是否支持"一次多个动爻"。
2. **变卦的互 / 错 / 综卦**：对变卦也算出它的三个衍生卦并展示。
3. **崔氏易林**：为每一种"本卦 → 之卦"（64×64 = 4096 条）配一段林辞。数据源见 `divination-core/.../data/崔氏易林_繁體.txt`，内核已加 `yilin` 命令，UI 已展示。

**提醒**：新增功能按既定架构——内核逻辑写在 Python（`divination/`），只在 `divination/api.py` 的 `handle` 里加 `elif` 分发命令，C 桥和 Swift 调用机制不动（见 [[dispatch-architecture 文档]]，在 repo 的 docs/dispatch-architecture.md）。
