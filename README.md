# madian-films

「码点小人」短片的 skill：引擎代码、导演说明、系列设定和示例片。

- 给 AI 用：让它先读 [`SKILL.md`](SKILL.md)。支持 skill 的工具可以把整个仓库放进它的 skills 目录；其他工具在这个仓库里直接开工即可（`AGENTS.md`、`CLAUDE.md` 会把它引到 `SKILL.md`）。
- 系列：[`series/asoiaf/SERIES.md`](series/asoiaf/SERIES.md) 《权力的游戏》人物志。
- 示例片：[`series/asoiaf/ep01_ned/`](series/asoiaf/ep01_ned/)，成片在 `reference/ned_540p.mp4`。

```
pip install -r requirements.txt
cd series/asoiaf/ep01_ned && python film.py full        # 540p；RES=1080 出 1080p
```

仓库里的 BGM 和地图轮廓素材有版权，仓库请保持私有。
