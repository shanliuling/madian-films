# Q 版角色、马、动作编排、斜视角大头兵 —— 用法

## 1. 角色 = 一份参数表

角色库在 `cast/`，每个角色是一个 dict，交给 `qchar.Q()` 或 `qrig.draw()` 画。常用的键：

| 键 | 含义 |
|---|---|
| `head` | 头型：`round` 圆、`square` 方、`wide` 宽 |
| `skin` `hair` | 肤色、发色 |
| `gear` | 头上戴的：`bawang2` 霸王盔（两根雉鸡翎）、`han` 兵盔、`headband` 抹额、`mian` 冕旒、`guan` 进贤冠、`bun` 女子高髻（步摇、花钿）、`oldbun` 老者发髻、`douli` 斗笠 |
| `beard` `beardcol` `browcol` `brow_w` | 胡子：`hang` 垂须、`goatee` 山羊胡、`long` 长须、`wild` 络腮；胡子色、眉色、眉粗 |
| `armor` `limb` `scale` `pauldron` | 铠甲色、四肢色、是否鳞甲纹、是否肩甲 |
| `kao` `flags='kao'` `cape` | 戏曲大靠（护心镜、靠肚、靠腿、披膊）、四面靠旗、披风颜色 |
| `robe` `collar` `belt` `trim` `bixi` `emblem` `pibo` | 长袍模式（给了 `robe` 颜色就不画腿和铠甲）：袍色、交领色、腰带色、下摆镶边、蔽膝、胸前团纹、披帛 |
| `tabard` `tiger` `shield` | 号衣上的字、虎皮、盾（`beast` 兽面盾） |
| `weapon` | `ji2` 霸王戟、`ji` 戟、`spear` 矛、`dao` 大刀、`sword` 剑、`fan` 羽扇、`scroll` 竹简、`None` 空手 |
| `blush` | 腮红 |

新角色的做法：复制一个最接近的，改头型、头饰、配色、兵器。新朝代要新服装时，在 `qcostume.py` 里加零件（仿照 `hat()`、`robe()`、`kao_front()` 的写法），骨架和表情不用动。加完用 `python tools/castsheet.py cast.xxx out.jpg` 看定妆。

## 2. 画一个角色

```python
from mapwar.qchar import Q, rider
from cast.chuhan import XY, LB, YJ

Q(c, x, 脚底y, 身高, XY, 朝向(1右/-1左), '姿势', t, eye='fierce', brow='angry', mouth='shout', fx=('anger',), flags=False, sf=1.9, ef=2.3)
rider(c, x, 地面y, 身高, XY, 朝向, t, gait='gallop', rear=0.0, 其余同上)     # 骑马；rear 0→1 扬蹄
```
- 姿势：`stand` `idle` `fold`（拢袖）`cheer` `point` `kneel` `walk` `run`。后面的关键字参数会覆盖姿势里的同名关节角，用来微调。
- `Q()` 返回 `(关节表 J, 姿势 P, 尺度 S)`；要在手上画东西时用 `qrig.to_world(P, S, J['hdf'])` 取手的屏幕坐标。
- 关节角（弧度，**0 = 朝下，正 = 朝前**）：`sf/ef` 前臂的肩和肘，`sb/eb` 后臂，`hf/kf` 前腿的髋和膝，`hb/kb` 后腿，`lean` 上身前倾，`hd` 低头，`w` 兵器角度，`rot` 整体旋转（空翻），`sq` 压扁（落地缓冲），`hs` 头的大小。
- 表情：
  - `eye`：`dot` `dot2`（大眼）`glint`（有神）`fierce` `shock` `closed` `happy` `squeeze` `dizzy` `lady`
  - `brow`：`angry` `worried` `raised` `flat` `none`
  - `mouth`：`flat` `smirk` `smile` `shout` `o` `grit` `wavy` `lips`
  - `fx`（元组）：`sweat` 汗、`tear` 泪、`anger` 怒气、`shocklines` 惊、`q` 问号、`stars` 眼冒金星
- 其他开关：`flags=False` 隐藏靠旗；`ride=True` 骑姿（不画后腿）；`arm_under_head=False` 让长袍角色的前臂画在头的上层。
- 把角色压成剪影、去色这类处理在合成时做（见 `examples/chuhan_q/film.py` 的 `compose(sil=..., gray=...)`）。

## 3. 人物镜头的合成

`examples/chuhan_q/film.py` 的 `compose()` 是一个可照搬的写法：背景 `scenery.landscape()` → `under` 层（地面道具）→ 人物层 → `top` 层（手里的东西、前景芦苇）→ 调色（压暗、去色、辉光、闪白、抖动、推镜）→ 文字。
两个人有接触的戏（相拥、托住、交缰绳）：先分别摆姿势，再把必须压在对方身上的那只手或那件东西放到 `top` 层单独画。

## 4. 动作编排（`examples/chuhan_q/fight.py`）

- **关键帧**：`KX = build([(时刻, dict(只写这一刻变化的量)), ...])`，没写的量沿用上一帧；`pose_at(KX, ta)` 平滑插值。跑动的摆腿、击飞后的翻滚由 `procedural()` 按速度自动加。
- **时间变形**：`SLOWS = [(动作时刻起, 止, 倍率), ...]` 定义慢放和顿帧窗口；`act(影片时刻)` ↔ `film_of(动作时刻)` 互相换算，用来把某个动作点对到鼓点上。
- **冲击感**：击中瞬间两帧反色的冲击帧、集中线 `focus_lines`、地面冲击环 `ring`、火花 `sparks`、碎块 `debris`、地裂 `crack`、兵器尖的拖尾 `trail`、拟声大字 `sfx`、镜头 `CAM` 关键帧 + 抖动。
- 把一段动作插进成片：`fight.frame(动作片里的时刻)` 直接返回一帧，在总时间线里按"击中点对齐鼓点"取时刻（示例里是彭城撞击的那一拍）。
- 设计新动作时：先写 4–6 个关键姿势抽静帧看，再补中间帧和特效。

## 4.5 近现代服装和正面特写

- 军装：`uniform=颜色` 换掉长袍/铠甲，`collar_tab` 领章、`puttee` 绑腿、`shoe='straw'` 草鞋、`cloak` 披风、`bandolier` 子弹带、`sam_browne` 武装带；帽子 `gear='bajiao'/'junmao'/'helmet'/'strawhat'`；头发 `modern_hair='short'/'long'/'bald'`；兵器 `weapon='rifle'` 或 `'bayonet'`（上刺刀）。
- 胡子 `beard='mustache'/'full'/'stubble'`（stubble 是剃过的胡茬点），痣 `mole=(dx, dy)`（以头半径为单位）。
- 正面大头：`qrig.head(c, x, y, R, spec, P)`，`P['front']=True` 时五官居中、两只耳朵、帽子和头发画正面版。表情照常用 `eye / brow / mouth / fx`，惊讶可用 `mouth='gasp'`。身子和抬起的手自己画几笔即可，写法见 `examples/sidu/film.py` 的 `bust()`（拿电话时手要画在头的上层）。
- 角色参数表示例：`cast/sidu.py`。

## 5. Q 版马（`mapwar.qhorse`）

`horse(c, x, 蹄底y, 马背高, 毛色, 朝向, t, gait='stand'|'walk'|'gallop', rear=0..1, head_a=低头角, cloth=鞍鞯色, sheen=高光色)`，返回鞍点的屏幕坐标。`qchar.rider()` 已经把人放在鞍上；人和马的比例用 `hk`（马背高 / 人的尺度，默认 1.3）调。

## 6. 斜视角大头兵战场（`mapwar.eggfield`）

**走模拟**（适合两军对撞、溃逃）：
```python
from mapwar import eggfield as E
units = [E.Unit('H', 'spear', 行数, 列数, 间距, [(t, x, y, 朝向度), ...], vuln=0.12, rout=溃逃时刻, flee=(1, -0.5)),   # 步兵方阵
         E.Unit('C', 'cav', 16, 0, 2.4, [(0, -58, 0, 0), (4.6, 12, 0, 0), ...], shape='wedge', charge=3.6, vuln=0.0)]  # 楔形骑兵
S = E.simulate(units)                    # 不给 units 就是内置示例：一支楔形骑兵撞进 36 块步兵方阵
img, cam, ts = E.render(影片时刻, S, keys) # keys: [(仿真秒, 目标x, 目标y, 距离, 俯仰(90=正俯视), 朝向, 跟随骑兵权重), ...]
```
- 撞击时刻在 `S['imp'][0]`；`render` 在撞击后自动慢放一段。把"影片时刻 = 撞击时刻"对到鼓点上。
- 镜头建议：开场正俯视交代兵力 → 俯冲到冲锋方的**侧前方**（朝向 120–150 度一带能看到冲锋方的脸）→ 撞击后拉回俯视看溃逃。
- 往画面上标字：`cam.proj(世界坐标)` 得到 960×540 下的屏幕坐标，乘 2。

**自己摆**（适合有明确构图的镜头，比如主角带队凿穿）：`E.scene(cam, F, 楚方掩码, 骑兵掩码, t, 平端兵器掩码, hero=主角下标, night=True, torches=举火把掩码)`，`F` 是每个兵的 `pos / z / face / state / fall / phase / spd` 数组。写法见 `examples/chuhan_q/breakout.py`：用公式算每个兵何时被撞、往哪边让开、谁倒地。

**不乱的要点**（已经做在渲染里）：按屏幕上的大小分三级，最远只画色块和一根兵器线，近处才画脸、表情、汗滴；兵器亮色加粗；溃逃的兵不画兵器、换惊慌脸；主角放大 1.5 倍并带翎子和披风。两军的长相用 `eggfield.set_looks(a, b)` 改（键：body 衣服、head 头色、hat 帽子 `helmet/bajiao/junmao/strawhat`、weapon `spear/ji/rifle`、band、plume、shaft 等），不用改源码。

**近现代战场**：`scene()` 的 `F` 里可以再给 `fire`（开枪时刻，枪口火光）、`dao`（举大刀冲锋）、`crouch`（蹲在掩体后）；`props=` 传沙包、弹坑这类和兵一起按远近排序的东西，`under=` / `over=` 传画在兵下面（战壕、河、浮桥）和上面（曳光弹、爆炸、手榴弹、飞机）的回调，零件都在 `mapwar.eggfx`。写法见 `examples/sidu/battles.py`。

**地图上的蛋蛋兵**：`MapShot` 的 `sc['egg'] = {势力下标或军队名: dict(body, hat, hatcol, star, weapon, plume, band, shaft)}`；`hat='ancient'` + `weapon='spear'/'ji'` 是古代兵，骑兵军队（`cav=1`）自动骑马；近现代用军帽并背枪。蛋蛋兵比火柴人大，用 `sc['fig_scale']`（0.4–0.6）减人数。

## 7. 署名（`mapwar.brand`）

```
python -m mapwar.brand 成片.mp4 输出.mp4 账号名 片尾第二行 [--corner] [--dim 230]
```
右下角一枚较淡的红印章（片尾页出现前收掉），最后 1.7 秒压暗并浮现印章、账号名和第二行。右上角半透明"@账号名"角标默认不加，用户要求时才加 `--corner`（代码里 `corner=True`）。`--dim` 是片尾页压暗程度（默认 170）。同时重新编码到适合上传的体积。要单独取图层：`brand.watermark()`、`brand.endcard()`、`brand.seal()`。
商单：`--logo 图片` 在左上角加对方 logo，白底图会自动抠成透明底。
