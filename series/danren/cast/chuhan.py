"""角色库 · 楚汉（演义戏曲扮相）。同一个人在不同片子里用同一份参数，长相才一致；新片往这里加人。
每个角色是一份给 mapwar.qrig.draw / mapwar.qchar.Q 的参数表。"""
XY = dict(head='square', gear='bawang2', beard='hang', brow_w=1.4, armor=(0.15, 0.14, 0.17), limb=(0.12, 0.11, 0.14), cape=(0.72, 0.07, 0.05), flags='kao', kao=True, weapon='ji2', skin=(0.95, 0.80, 0.66))
FK = dict(head='wide', gear='headband', beard='wild', brow_w=1.6, armor=(0.42, 0.24, 0.12), limb=(0.36, 0.20, 0.10), cape=None, weapon='dao', shield='beast', tiger=True, scale=False, rim=(0.7, 0.5, 0.25), skin=(0.90, 0.72, 0.56), hs=1.0)
HAN = dict(head='round', gear='han', tabard='汉', armor=(0.55, 0.09, 0.07), limb=(0.45, 0.08, 0.06), weapon='spear', pauldron=False, rim=(0.85, 0.6, 0.3), skin=(0.96, 0.84, 0.70))

LB = dict(head='round', gear='mian', beard='goatee', robe=(0.13, 0.12, 0.15), collar=(0.80, 0.14, 0.10), belt=(0.80, 0.14, 0.10), bixi=True, emblem=True, weapon=None, skin=(0.96, 0.84, 0.70))
HX = dict(head='square', gear='guan', armor=(0.30, 0.38, 0.50), limb=(0.24, 0.30, 0.40), cape=(0.20, 0.28, 0.45), weapon='sword', rim=(0.8, 0.82, 0.9), skin=(0.96, 0.84, 0.70))
ZL = dict(head='round', gear='guan', robe=(0.88, 0.90, 0.92), collar=(0.25, 0.42, 0.62), belt=(0.25, 0.42, 0.62), trim=(0.25, 0.42, 0.62), weapon='fan', skin=(0.97, 0.86, 0.74))
XH = dict(head='round', gear='guan', beard='long', robe=(0.45, 0.30, 0.18), collar=(0.15, 0.1, 0.08), belt=(0.15, 0.1, 0.08), weapon='scroll', skin=(0.95, 0.82, 0.68))
FZ = dict(head='round', gear='oldbun', hair=(0.88, 0.88, 0.9), beard='long', beardcol=(0.92, 0.92, 0.94), browcol=(0.85, 0.85, 0.88), robe=(0.45, 0.45, 0.5), collar=(0.15, 0.15, 0.18), belt=(0.15, 0.15, 0.18), weapon=None, skin=(0.93, 0.80, 0.68))
YJ = dict(head='round', gear='bun', hairback=True, robe=(0.88, 0.30, 0.38), collar=(0.98, 0.85, 0.55), belt=(0.98, 0.85, 0.55), pibo=True, blush=True, weapon='sword', skin=(0.99, 0.88, 0.80))
TZ = dict(head='round', gear='douli', beard='goatee', robe=(0.50, 0.42, 0.30), collar=(0.25, 0.2, 0.15), belt=(0.25, 0.2, 0.15), trim=(0.3, 0.24, 0.16), weapon=None, skin=(0.90, 0.74, 0.58))

CAST = dict(项羽=XY, 樊哙=FK, 汉兵=HAN, 刘邦=LB, 韩信=HX, 张良=ZL, 萧何=XH, 范增=FZ, 虞姬=YJ, 亭长=TZ)
