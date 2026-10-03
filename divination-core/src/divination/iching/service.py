"""service —— 应用层门面：对外的唯一入口。

这一层把下面三层编排成"一个完整用例"，并负责和外界交换
朴素、可序列化的数据（给 Swift / 将来的网页用）：

    外界给我输入（如 6 个爻）
        → core 算出本卦、变卦
        → repository 查出它们的名字、卦辞、爻辞
        → 拼成一个朴素的结果（dict / 可转 JSON）返回

UI 和平台只认识这一层，不直接碰 core / repository / model。
依赖方向：service → core / repository → model，始终单向往下。
"""
