import display
import random
import buttons
import mch22
import time
from fpga_wishbone import FPGAWB
import sys
import json
from machine import Pin
from neopixel import NeoPixel

powerPin = Pin(19, Pin.OUT)
dataPin = Pin(5, Pin.OUT)
np = NeoPixel(dataPin, 1)
powerPin.on()
# APP_PATH = "/".join(__file__.split("/")[:-1])
# Add Application path to sys path to import modules as if they were root modules
sys.path.append('sd/apps/python/gps')
from custom_adafruit_gps import GPS

print("running")
with open("/sd/apps/python/gps/bitstream.bin", "rb") as f:
    mch22.fpga_load(f.read())
print("FPGA loaded")
# setup UART
# (30e6/9600)-2
c = FPGAWB()
c.queue_write(2, 4, 3123)
c.exec()

animate = 1


##### Setup filename
def init():
  tracknr = 0
    # get counter and increment with 1 
  with open("/sd/apps/python/gps_logger/counter.txt", "r") as countFile:
    counter = countFile.read()     
    tracknr = counter 
    print(bool(c))
    if counter :
      counter = int(counter) + 1
    else :
      counter = 1 
    print(counter)

  # countFile.close()
  countFile = open("/sd/apps/python/gps_logger/counter.txt", "w")
  countFile.write(str(counter))
  countFile.close()

  # new file 
  fileName = "/sd/apps/python/gps_logger/route_{}.geojson".format(counter)
  opening = { 
    "type": "FeatureCollection",
    "Features": [ ]
  }
  file = open(fileName, "a")
  file.write(json.dumps(opening))
  file.close()
  print("file initialized")
  return fileName, tracknr


def showGPS(lat,lon,i, animate) :
  # display.drawFill(0xffffff) 
  w =  display.width()
  h = display.height()
  display.drawFill(display.BLACK)
  display.drawText(int((w - display.getTextWidth("Niene is here:","roboto_regular18")) /2), 10, "Niene is here:", display.WHITE, "roboto_regular18")
  display.drawPng( int((w-250)/2), 50, "/sd/apps/python/gps_logger/auto_{}.png".format(animate))
  
  display.drawText(int((w - display.getTextWidth('Latitude: {0:.6f} degrees'.format(lat),"roboto_regular18")) /2), 180, 'Latitude: {0:.6f} degrees'.format(lat) , display.WHITE, "roboto_regular18")
  display.drawText(int((w - display.getTextWidth('Longitude: {0:.6f} degrees'.format(lon),"roboto_regular18")) /2), 205, 'Longitude: {0:.6f} degrees'.format(lon) , display.WHITE, "roboto_regular18")
  display.flush()
  np[0]= (5,5,5)
  np.write()


def showNone() :
  # display.drawFill(0xffffff) 
  display.drawFill(display.BLACK)
  display.drawText(30, 10, "No Signal", display.RED, "roboto_regular18")
  display.flush()
  np[0] = (50,0,0)
  np.write()


def main():
  # gps init
  gps = GPS( debug=True)
  result = init()
  fileName = result[0]
  last_print = time.time()
  id = 0
  # start tracking 
  animate = 1


  while True:
    
    gps.update() 
    current = time.time()
    print(current)
    print(gps.debug)
    if current - last_print >= 1.0:
        last_print = current
        if not gps.has_fix:
            showNone()  
            print(gps.satellites)
            print(gps.fix_quality)
            print('Waiting for fix...')
            continue
        # print('=' * 40)  # Print a separator line.
        print('Latitude: {0:.6f} degrees'.format(gps.latitude))
        print('Longitude: {0:.6f} degrees'.format(gps.longitude))
      
        print(gps.fix_quality)
        if animate == 4 : 
          animate = 1
        else: 
          animate = animate + 1
        showGPS(gps.latitude, gps.longitude,id, animate)
        id += 1 

        data =   {
          "type": "Feature",
          "properties": {
            "id": id, 
            "tracknr":  result[1],
            "time": gps.timestamp_utc,
            "quality": gps.fix_quality,
            "satellites": gps.satellites,
            "altitude": gps.altitude_m,
            "speed" : gps.speed_knots
          },
          "geometry": {
            "type": "Point",
            "coordinates": [
              gps.longitude,
              gps.latitude
            ]
          }
        }

        with open(fileName, "a") as file :
          file.write(json.dumps(data))
          file.write(',\n')

main()