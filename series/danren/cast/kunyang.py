"""角色库 · 昆阳之战（公元23年，新莽末）。汉军尚赤，新朝尚黄。"""
from .chuhan import HAN
LX = dict(head='round', gear='guan', brow_w=1.2, armor=(0.20, 0.22, 0.30), limb=(0.16, 0.17, 0.24), cape=(0.80, 0.10, 0.07), weapon='sword', rim=(0.92, 0.74, 0.30), skin=(0.97, 0.85, 0.72))          # 刘秀
WY = dict(head='wide', gear='guan', beard='goatee', brow_w=1.6, armor=(0.86, 0.66, 0.18), limb=(0.62, 0.45, 0.10), cape=(0.36, 0.16, 0.42), weapon='sword', rim=(0.98, 0.86, 0.45), skin=(0.93, 0.78, 0.62))  # 王邑
XIN = dict(head='round', gear='han', tabard='新', armor=(0.88, 0.66, 0.14), limb=(0.66, 0.48, 0.10), weapon='spear', pauldron=False, rim=(0.5, 0.36, 0.1), skin=(0.95, 0.82, 0.68))                          # 新军兵
JWB = dict(head='wide', gear='headband', beard='wild', brow_w=1.8, armor=(0.50, 0.34, 0.14), limb=(0.40, 0.27, 0.10), cape=None, weapon='dao', tiger=True, scale=False, rim=(0.8, 0.6, 0.25), skin=(0.86, 0.68, 0.52), hs=1.0)   # 巨毋霸
WF = dict(head='round', gear='guan', beard='goatee', armor=(0.62, 0.12, 0.10), limb=(0.48, 0.09, 0.08), cape=None, weapon=None, rim=(0.85, 0.6, 0.3), skin=(0.94, 0.80, 0.66))                              # 王凤（守将）
CAST = dict(刘秀=LX, 王邑=WY, 新军=XIN, 汉兵=HAN, 巨毋霸=JWB, 王凤=WF)
