import json, math, urllib.request, sys
exec(open("scratch/mys_points.py").read().split("# candidate")[0])
# EB: try offsets of the shared points (north side = left in LHT going east-north-east)
pts = {"P3":(12.95501,77.54466),"P4":(12.95228,77.54074),"P5":(12.94959,77.53675)}
for dlat in (0.00006, 0.00012, -0.00006):
    for dlon in (0, -0.00006, 0.00006):
        p4=(12.95228+dlat,77.54074+dlon); p3=(12.95501+dlat,77.54466+dlon); p5=(12.94959+dlat,77.53675+dlon)
        a=leg(p4,p3,55,55)[0]; b=leg(p5,p4,55,55)[0]
        print(dlat,dlon,"seg3 EB",a,"(522)","seg4 EB",b,"(526)")
