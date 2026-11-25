"""mapwar — 真实地图上的战局推演 + 垂直俯视阵战，代码逐帧渲染。
    util     缓动/噪声/字体/文字层 Txt
    world    World(cfg, data_dir)：任意范围的真实地理底图 + 城池归属 -> 势力范围、占地比例
    mapshot  MapShot(world, sc).frame(t)：斜视沙盘/垂直全局镜头，'ink' 与 'night' 两种风格
    field    俯视战场：兵种字形、阵型 mk、Battle / Wedge / Ring、箭雨、旗、河、镜头
    chars    人物素材：抠像、贴图、水墨底
    film     Film(shots).cli()：静帧 / 总览图 / 并行渲染
    audio    BGM 找拍剪接 + 合成音效
"""
from .util import SW, SH, FPS
