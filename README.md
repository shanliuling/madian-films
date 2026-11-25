# madian-films

「码点小人」短片的 skill：一个系列一个文件夹，各有自己的 `SKILL.md`（导演要求、系列固定、示例片），互不相干。`engine/` 是各系列共用的代码。

| 系列 | 给 AI 读的文件 | 类型 | 示例片 |
|---|---|---|---|
| 《权力的游戏》人物志 | [`series/asoiaf/SKILL.md`](series/asoiaf/SKILL.md) | 克制的历史叙事 | `series/asoiaf/ep01_ned/reference/ned_540p.mp4` |
| 《斗破苍穹》人物志 | [`series/doupo/SKILL.md`](series/doupo/SKILL.md) | 玄幻打斗 | `series/doupo/ep01_xiaoyan/reference/xiaoyan1_540p.mp4` |
| 蛋蛋人战局史 | [`series/danren/SKILL.md`](series/danren/SKILL.md) | 真实地图战局 + 蛋蛋兵阵战 + Q 版人物 | `series/danren/examples/`（楚汉、四渡赤水） |

- 给 AI 用：告诉它做哪个系列，让它只读那个系列的 `SKILL.md`（`AGENTS.md`、`CLAUDE.md` 也是这么写的）。两个系列的片子路子相反，读了另一个会带偏。
- 权游和斗破的代码依赖 `engine/`，要连仓库一起用。蛋蛋人系列自带全部代码（`series/danren/mapwar/`），不依赖 `engine/`，可以单独拷走；地图数据第一次用前在它的目录里运行 `python tools/setup_data.py` 下载。
- 加一个新系列：在 `series/` 下建一个文件夹，写它自己的 `SKILL.md`（这个系列是什么片子、用户对它说过的话、系列固定、集数、仓库里用到什么），再在上面的表里加一行。不要把它的东西写进别的系列的文件。

```
pip install -r requirements.txt
cd series/asoiaf/ep01_ned && python film.py full        # 540p；RES=1080 出 1080p
cd series/doupo/ep01_xiaoyan && python film.py          # 540p；RES=1080 出 1080p
```

仓库里的 BGM、地图轮廓素材和漫画参考图有版权，仓库请保持私有。
