import json, math, urllib.request
exec(open("scratch/probe_polyline.py").read().split("def route")[0])  # decode, hv, key
def route(a, b, h=None):
    def ll(p):
        d={"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if h is not None: d["location"]["heading"]=h
        return d
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.polyline.encodedPolyline,routes.distanceMeters"})
    x=json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], decode(x["polyline"]["encodedPolyline"])
d, P = route((12.94784,77.53419),(12.95769,77.55265))   # full eastbound (validated 2547 m)
print("full EB", d)
cum=[0]
for i in range(1,len(P)): cum.append(cum[-1]+hv(P[i-1],P[i]))
for i in range(0,len(P),3): print(i, round(cum[i]), P[i])
json.dump(P, open("scratch/mys_poly_EB.json","w"))
d, P = route((12.95228,77.54074),(12.95501,77.54466), 55)
print("seg3 EB", d); print([P[i] for i in range(0,len(P),max(1,len(P)//12))])
