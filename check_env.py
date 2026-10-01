"""설치된 패키지 버전과 한글 폰트 사용 가능 여부를 확인한다."""

import sys

import matplotlib
import numpy
import pandas
import yfinance
from matplotlib import font_manager

print(f"python     {sys.version.split()[0]}")
print(f"pandas     {pandas.__version__}")
print(f"numpy      {numpy.__version__}")
print(f"matplotlib {matplotlib.__version__}")
print(f"yfinance   {yfinance.__version__}")

installed = {f.name for f in font_manager.fontManager.ttflist}
if "Malgun Gothic" in installed:
    print("font       Malgun Gothic 사용 가능")
else:
    candidates = sorted(n for n in installed if "Gothic" in n or "Gulim" in n or "Batang" in n)
    print(f"font       Malgun Gothic 없음. 대체 후보: {candidates}")
