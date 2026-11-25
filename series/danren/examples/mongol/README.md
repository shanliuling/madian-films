# 谁惹了蒙古（《蒙古帝国》）

用这套工具做过的一部成片的源码，只作参考：看真实地图行军、蛋蛋兵战场、Q 版小品、双 BGM 接法和配音怎么写。不要照抄结构。

- `script.py` 时间线和节拍；`film.py` 总镜头表；`geo.py` 地图数据（城池、易手、行军）；`fights.py` 战场镜头；`skits.py` Q 版人物小品；`mcast.py` 角色；`mix.py`、`splice.py` 双 BGM 拼接 + 旁白 + 萌音 + 音效；`vo.py` 配音。
- 源码保持当时的原样，里面的绝对路径（`/home/ubuntu/kunyang/zhanju-kit` 等）指向当时的机器。要重跑，把它们改成本系列目录（`mapwar/` 所在处），`geo.py` 里读的旧版地图数据在 `geo_old.py`。
- 原 BGM、配音音频和成片没有放进仓库。
