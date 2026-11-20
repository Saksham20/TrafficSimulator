import json, math, urllib.request, sys
sys.path.insert(0,".")
from segments_mysore_road import GOOGLE_SB, GOOGLE_NB
exec(open("scratch/mys_points.py").read().split("# candidate")[0])
def L(a,b):
    return leg(a[:2], b[:2], a[2] if len(a)>2 else None, b[2] if len(b)>2 else None)
for i in range(5):
    a,b=GOOGLE_SB[i],GOOGLE_SB[i+1]; s=hv(a,b); w=L(a,b)
    c,d=GOOGLE_NB[i+1],GOOGLE_NB[i]; s2=hv(c,d); e=L(c,d)
    print(f"seg {i+1} WB straight {s:5.0f} google {w[0]:5d} ({w[0]/s:.2f})   EB straight {s2:5.0f} google {e[0]:5d} ({e[0]/s2:.2f})")
print("full WB", L((12.95769,77.55265,250),(12.94784,77.53419,235)), "full EB", L((12.94784,77.53419,55),(12.95769,77.55265)))
