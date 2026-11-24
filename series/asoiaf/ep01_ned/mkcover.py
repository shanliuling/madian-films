"""第一集封面：python mkcover.py → out/cover.jpg（16:9）、out/cover_4x3.jpg、out/cover_3x4.jpg（抖音要后两张）"""
import _env, windows
from cover import cover
for shape, out in (('16:9', 'out/cover.jpg'), ('4:3', 'out/cover_4x3.jpg'), ('3:4', 'out/cover_3x4.jpg')):
    print(cover('stark', '奈德·史塔克', ['最重荣誉的人，', '为什么第一个死？'], 1, windows.get('title'), out, shape=shape))
