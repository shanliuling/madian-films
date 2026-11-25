# 蛋蛋人、阵战和地图动效

来自用户上传的 `zhanju-kit v3` 和后来本地更新过的工具包。《蒙古帝国》实际用过 `World`/`MapShot` 做欧亚地图、`qchar`/`qrig` 做人物、`eggfield` 做大头兵镜头，另用 `audio` 混音、`Film` 渲染。这里迁的是可复用代码，不是蒙古片的剧本、地图点位、角色、音乐或旧角标。

这是给导演挑的工具，不是第三套系列规则。先读在做的系列的 `SKILL.md`，再挑需要的模块；画风、人设、BGM、字幕、片尾以该系列为准。老镜头不用重做。

| 拍什么 | 可以用 |
|---|---|
| 一个人的动作或反应 | `qchar.Q()` 画侧面全身，`qchar.rider()` 画骑乘，`qrig.head(..., P={'front': True})` 画正面表情。服装在 `qcostume`，场景和转场在 `scenery`。 |
| 多路行军、城池换旗、地盘变化 | `World` 存底图、地点和归属，`MapShot` 存运镜、军队和路线；可在俯视与斜视间推拉。 |
| 从全局切进一场战斗 | `field` 画俯视阵形，`eggfield` 画斜视近景或自摆的阵列，`eggfx` 只按题材挑所需画面道具。 |
| 卡点、混音和预览 | `audio.onsets()` / `loud_sections()` 找切点，`audio.Mix` 合轨；`film.Film` 能跑静帧和分段渲染，也可以沿用本集的渲染入口。 |

《蒙古帝国》的做法可以借：地图交代**谁从哪来、哪一座城让局势变了**，近景交代**是谁做了决定、对手是什么反应**。不必照搬镜头、时间比例、水墨风或萌音。一个换旗、一次推近、一个反应特写，如果已经讲清楚，比再加几根箭头更有用。

## 人物与动作

已有分集脚本通常先 `import _env`，然后可 `from mapwar import qchar, qrig`；从仓库根目录直接运行的脚本可用 `from engine.mapwar import qchar, qrig`。例如，在已有 Cairo 画布上：

```python
spec = dict(head='round', gear='headband', robe=(.22, .32, .46))
J, P, S = qchar.Q(c, 960, 880, 480, spec, name='run', t=t, eye='fierce')
hand = qrig.to_world(P, S, J['hdf'])
```

`spec` 是造型（发型、服装、装备），放本系列或本集；`Q()` 的参数是此刻的动作和表情。同一个人跨集尽量复用造型。`sf/ef` 是肩肘，`hf/kf` 是髋膝，角度以朝下为零、朝前为正；`w` 转手中道具，`rot` 转全身，`eye/brow/mouth/fx` 控制表情。动作可以先排蓄力、出手、停顿、收势几个姿势，再用 `engine/action.py` 的关键帧连起来。要让招式字、火焰和武器跟着人动，用关节坐标，不把它们锁在屏幕一角。

## 地图

- **历史实地**：安装仓库依赖后，在仓库根目录运行 `python -m engine.mapwar.setup_data`。会把 [Natural Earth 向量](https://www.naturalearthdata.com/about/terms-of-use/)和 [basemap-data](https://pypi.org/project/basemap-data/) 提供的地形晕渲图放在 `engine/mapwar/data/`；只在用真实地形时下载，不随仓库发布。已有旧工具包的数据也可以直接传给 `World(cfg, data_dir)`。范围越大，`px_per_deg` 越要小。
- **虚构世界**：不把地球轮廓当成维斯特洛或斗气大陆。权游继续优先用自己的 `westeros.py` 和家徽旗；斗破按本集需要画宗门或路线。只想借行军叙事时，直接在自家底图上实现即可；确实要用 `World` 的易手功能时，可以给它自家的坐标和陆地、河流、湖泊 GeoJSON，传自定义 `data_dir` 并设 `relief_raster=False`，不读地球晕渲图。文件名和数据形式见下方。

`World` 的 `bbox` 依次是西、东、南、北；`sides` 用从 0 起的连续编号，给每方 `name`、`ink` 和 `night` 色；`cities` 是 `(名, x, y, 势力编号, 显示级别)`，`flips` 是 `{城名: [(成片秒, 新势力)]}`。自带地图的数据目录要有 `ne_50m_land.geojson`（Polygon/MultiPolygon）、`ne_10m_rivers_lake_centerlines.geojson`（LineString/MultiLineString）、`ne_10m_lakes.geojson`（Polygon/MultiPolygon），无河湖可给空 `FeatureCollection`。

在 `MapShot(world, scene)` 里，`camseg` 是镜头关键帧列表的列表，每个关键帧是 `(秒, x, y, zoom, tilt)`，`tilt=0` 为俯视、`1` 为斜视；`armies` 的 `path` 可用 `(秒, x, y, 兵力万数)`，`style` 接收时间并返回 `ink` 或 `night`，`frame(t)` 返回 PIL 图。地图可以让几路人马同时走，重要地点再给名字；如果需要表现占地，记住它是根据城池推算的示意，不是实测疆界。

```python
from engine.mapwar.mapshot import MapShot
from engine.mapwar.world import World

sides = {0: dict(name='赤旗', ink=(.5, .2, .15), night=(.8, .35, .25)),
         1: dict(name='蓝旗', ink=(.15, .3, .5), night=(.3, .55, .85))}
world = World(dict(bbox=(105, 125, 22, 40), px_per_deg=48, sides=sides,
                   cities=[('襄阳', 112.1, 32.0, 0, 2), ('建康', 118.8, 32.1, 1, 2)],
                   flips={'建康': [(3.0, 0)]}))
shot = MapShot(world, dict(camseg=[[(0, 115, 32, .62, 0), (4, 117, 32, .85, 1)]],
                          armies=[dict(n='先锋', o=0, path=[(0, 112.1, 32.0, 1),
                                                             (3, 118.8, 32.1, 1)])]))
shot.frame(3.2).save('map-preview.png')
```

## 声音和输出

优先沿用本系列的 BGM 与混音。BGM 重拍可以用来落换旗、撞击或人物动作，不必让每个镜头都卡拍。只有用户同意配音，才需要额外安装 `edge-tts`；`voice.build()` 调在线服务生成台词并按实测长度排时间，`voice.lay()` 在说话处压低音乐，`voice.at()` 可以拿到当前字幕。不要默认加配音、水印或片尾。

独立镜头可以用 `Film([(起秒, 止秒, fn), ...], total, audio=混音路径)`；`fn(镜头内秒数, 镜头长度, 成片秒数)` 返回 1920×1080 的 PIL 图。在脚本末尾调 `film.cli()` 后，`python 本集脚本.py render out/preview.mp4 2 0.5` 出 540p，最后一个参数换 `1` 出 1080p。是否先抽帧、要出哪种试看，仍按本系列与用户的约定。
