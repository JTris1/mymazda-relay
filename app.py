from flask import Flask, request, jsonify, render_template
from urllib.parse import urlparse, parse_qs
import pymazda
import requests
import re
import os

app = Flask(__name__)

# Read credentials from environment
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
DEFAULT_REGION = os.environ.get("REGION", "MNAO")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Environment variables USERNAME and PASSWORD must be set")


@app.route("/")
def hello_world():
  return render_template('index.html')


@app.route("/vehicles_html")
async def getVehicles_html() -> None:
    region = request.args.get('region') or DEFAULT_REGION
    client = pymazda.Client(USERNAME, PASSWORD, region)
    vehicles = await client.get_vehicles()
    await client.close()
    return render_template("vehicle.html", vehicles=vehicles, region=region)


@app.post("/vehicles")
async def getVehicles() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    client = pymazda.Client(USERNAME, PASSWORD, region)
    vehicles = await client.get_vehicles()
    await client.close()
    return jsonify(vehicles)


@app.post("/vehiclesStatus")
async def getStatus() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    status = await client.get_vehicle_status(vid)
    await client.close()
    return jsonify(status)

@app.post("/checkDoors")
async def checkDoors() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    status = await client.get_vehicle_status(vid)
    msg = "Doors seem ok."
    if any(status['doors'].values()):
        return "Doors open. Please check your vehicle."
    elif any(status['doorLocks'].values()):
        msg = "Some doors were unlocked. Will attempt to lock."
    if any(status['windows'].values()):
        msg += "Windows were open."
    await client.lock_doors(vid)
    await client.close()
    return msg


@app.post("/startEngine")
async def startEngine() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.start_engine(vid)
    await client.close()
    return "Success"


@app.post("/stopEngine")
async def stopEngine() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.stop_engine(vid)
    await client.close()
    return "Success"


@app.post("/lockDoors")
async def lockDoors() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.lock_doors(vid)
    await client.close()
    return "Success"


@app.post("/unlockDoors")
async def unlockDoors() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.unlock_doors(vid)
    await client.close()
    return "Success"


@app.post("/hazardLightsOn")
async def turn_on_hazard_lights() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.turn_on_hazard_lights(vid)
    await client.close()
    return "Success"


@app.post("/hazardLightsOff")
async def turn_off_hazard_lights() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.turn_off_hazard_lights(vid)
    await client.close()
    return "Success"


@app.post("/sendPOI")
async def sendPOI() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    latitude = float(r.get('latitude'))
    longitude = float(r.get('longitude'))
    name = r.get('name')
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.send_poi(vid, latitude, longitude, name)
    await client.close()
    return "Success"


@app.post("/sendPOIfromURL")
async def sendPOIfromURL() -> None:
    r = request.json or {}
    region = r.get('region') or DEFAULT_REGION
    vid = r.get('vid')
    u = urlparse(r.get('url'))
    q = parse_qs(u.query)
    if u.hostname == "maps.apple.com":
        name = q.get('q')[0]
        ll = q.get('ll')[0].split(',')
        latitude = float(ll[0])
        longitude = float(ll[1])
    elif "goo.gl" in (u.hostname or ""):
        res_ = requests.get(r.get('url'))
        latitude, longitude, name = get_google_coordinates(res_.url)
    elif u.hostname == "www.google.com":
        latitude, longitude, name = get_google_coordinates(r.get('url'))
    else:
        return "URL Not Supported Yet."
    client = pymazda.Client(USERNAME, PASSWORD, region)
    await client.send_poi(vid, latitude, longitude, name)
    await client.close()
    return "Success"


def get_google_coordinates(full_gmap_url):
    match = re.findall('place\/(.*?),(.*?)\/', full_gmap_url)
    return float(match[0][0]), float(match[0][1]), "Coordinate from Google Maps"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port)