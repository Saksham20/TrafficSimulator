import json, math, urllib.request
exec(open("scratch/mys_points.py").read().split("# candidate")[0])
WB = [(12.95769,77.55265),(12.95683,77.54892),(12.95501,77.54466),(12.95228,77.54074),(12.94959,77.53675),(12.94784,77.53419)]
# eastbound boundaries: on the Google eastbound line, i.e. after the Satellite loop, pick points at matching positions
EB = [(12.95769,77.55265),(12.95666,77.54841),(12.95488,77.54453),(12.95293,77.54136),(12.94909,77.53615),(12.94784,77.53419)]
for i in range(5):
    a,b = EB[i+1], EB[i]
    s = hv(a,b); e = leg(a,b)
    print(f"EB seg {i+1}: straight {s:5.0f} google {e[0]:5d} ({e[0]/s:.2f}) {e[1]}")
