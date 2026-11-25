"""角色库 · 长征（1935，四渡赤水）。红军灰布军装 + 八角帽；国民党军按派系换帽子和颜色。"""
GREY = (0.46, 0.50, 0.52); GREY_D = (0.36, 0.40, 0.42); PUT = (0.42, 0.44, 0.44)
KMT = (0.50, 0.47, 0.34); KMT_D = (0.40, 0.37, 0.27)

HJ = dict(head='round', gear='bajiao', modern_hair='short', uniform=GREY, limb=GREY_D, collar_tab=(0.82, 0.12, 0.1), puttee=PUT, shoe='straw', weapon='bayonet', skin=(0.92, 0.78, 0.62))
MZ = dict(head='round', gear='bajiao', modern_hair='long', mole=(-0.16, 0.24), uniform=GREY, limb=GREY_D, collar_tab=(0.82, 0.12, 0.1), puttee=PUT, shoe='straw', weapon=None, hs=1.0, skin=(0.95, 0.82, 0.68))
ZE = dict(head='square', gear='bajiao', modern_hair='short', beard='stubble', brow_w=1.7, uniform=GREY, limb=GREY_D, collar_tab=(0.82, 0.12, 0.1), puttee=PUT, shoe='straw', weapon=None, skin=(0.94, 0.80, 0.66))
ZD = dict(head='wide', gear='bajiao', modern_hair='short', uniform=GREY, limb=GREY_D, collar_tab=(0.82, 0.12, 0.1), puttee=PUT, shoe='straw', weapon=None, skin=(0.88, 0.72, 0.56))
JJ = dict(head='egg', gear=None, modern_hair='bald', beard='mustache', uniform=KMT, limb=KMT_D, cloak=(0.20, 0.20, 0.18), collar=(0.3, 0.28, 0.2), weapon=None, skin=(0.95, 0.82, 0.70))
ZY = dict(head='round', gear='helmet', capcol=(0.40, 0.44, 0.40), uniform=(0.48, 0.48, 0.40), limb=(0.38, 0.38, 0.31), puttee=(0.45, 0.45, 0.38), weapon='rifle', bandolier=(0.4, 0.3, 0.18), skin=(0.94, 0.80, 0.66))
CJ = dict(head='round', gear='junmao', uniform=(0.42, 0.44, 0.48), limb=(0.33, 0.35, 0.38), puttee=(0.40, 0.40, 0.42), weapon='rifle', skin=(0.94, 0.80, 0.66))
QJ = dict(head='round', gear='strawhat', uniform=(0.52, 0.46, 0.34), limb=(0.42, 0.37, 0.27), puttee=(0.5, 0.45, 0.35), shoe='straw', weapon='rifle', skin=(0.92, 0.78, 0.62))

CAST = dict(红军=HJ, 毛泽东=MZ, 周恩来=ZE, 朱德=ZD, 蒋介石=JJ, 中央军=ZY, 川军=CJ, 黔军=QJ)
