"""Build a southbound DPR-route chain: points with headings; each leg must be ~1.0-1.15x straight."""
import json, math, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def leg(a, b, ha, hb):
    ll = lambda p, h: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}, "heading": h}}
    body = {"origin": ll(a, ha), "destination": ll(b, hb), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"]
E = 0.00012  # east offset for southbound carriageway (left-hand traffic)
S = [  # name, point, heading (southbound journey)
 ("SV Metro", (12.98455, 77.64529+E), 190),
 ("CMH jn (80ft)", (12.97880, 77.64655+E), 180),
 ("CMH Rd W", (12.97830, 77.64300), 270),
 ("100ft top", (12.97700, 77.64085+E), 180),
 ("100ft mid", (12.97153, 77.64106+E), 180),
 ("Domlur N", (12.96259, 77.64165+E), 180),
]
for i in range(len(S)-1):
    (na, a, ha), (nb, b, hb) = S[i], S[i+1]
    print(f"{na:14s}->{nb:14s} straight {hv(a,b):5.0f} google {leg(a,b,ha,hb):5d}")
