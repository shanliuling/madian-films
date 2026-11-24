"""第一集封面：python mkcover.py → out/cover.jpg"""
import _env, windows
from cover import cover
print(cover('stark', '奈德·史塔克', ['最重荣誉的人，', '为什么第一个死？'], 1, windows.get('title'), 'out/cover.jpg'))
