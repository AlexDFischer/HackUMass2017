#import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import math
import pigpio
from lru import LRU
from paddle import paddle

visualization = True

minBallArea = 100 # it's uaually 400-500 but this is an acceptable minimum since noise is usually much smaller

howOftenPaddle = 1 #only move the paddle every few steps because pigpio crashes if we query it too often
frameNum = 0

# opencv does colors in BGR for some reason
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
ORANGE = (0, 165, 255)
PURPLE = (128, 0, 128)

pi=pigpio.pi()

frameSize = (320, 240)
xOffset = 50#int(frameSize[0] / 10)
yOffset = int(frameSize[1] / 10)
numBallLocations = 8 # the number of ball locations we will keep track of
numIntersectLocations = 4 # the number of ball-backboard intersection points we will keep track of
ballXLRU = LRU(numBallLocations)
ballYLRU = LRU(numBallLocations)
intLRU = LRU(numIntersectLocations)
for i in range(numBallLocations):
	ballXLRU.push(xOffset)
	ballYLRU.push(int(frameSize[1] / 2))
for i in range(numIntersectLocations):
	intLRU.push(frameSize[1] / 2);

print(ballXLRU.arr)
print(ballYLRU.arr)

camera = PiCamera()
camera.resolution = frameSize
camera.framerate = 10
rawCapture = PiRGBArray(camera, size=frameSize)
 
# allow the camera to warmup
time.sleep(0.1)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	frameNum = frameNum + 1
	start=time.time()
	image = frame.array
	method = "hsv"
	if (method == "hsv"):
		hsv=cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
		rth=cv2.inRange(hsv,(0, 150, 0), (10, 255, 255)) | cv2.inRange(hsv,(170, 150, 0), (180, 255, 255))
	else:
		b,g,r=cv2.split(image)
		ret,rth=cv2.threshold(r,180,255,cv2.THRESH_BINARY)
	contours,heirarchy = cv2.findContours(rth,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
	cx = 0
	cy = 0
	if len(contours) != 0:
		contour = max(contours, key=cv2.contourArea)
		# only if the area of the contour is sufficiently large do we consider it a ball
		area = cv2.contourArea(contour)
		if area >= minBallArea:
			moments=cv2.moments(contour)
			m00=moments['m00']
			if m00==0:
				m00=0.01
			cx=int(moments['m10']//m00)
			cy=int(moments['m01']//m00)
	if (cx != 0 and cy != 0):
		ballXLRU.push(cx)
		ballYLRU.push(cy)
	slope, intercept, r, p, stderr = stats.linregress(ballXLRU.arr, ballYLRU.arr)
	# if we don't get a vertical line of best fit
	if not math.isnan(slope) and r * r > 0.7:
		# intersection height is the value of the line at x = xOffset
		intPoint = int(intercept + xOffset * slope)
		intPOint = max(intPoint, yOffset)
		intPoint = min(intPoint, frameSize[1] - yOffset)
		intLRU.push(intPoint)
	avgIntPoint = 0
	for i in intLRU.arr:
		avgIntPoint = avgIntPoint + i
	avgIntPoint = avgIntPoint / numIntersectLocations
	# tell the paddle to move to the required location
	proportion = (avgIntPoint - yOffset) / float(frameSize[1] - 2 * yOffset)
	if frameNum % howOftenPaddle == 0:
		paddle(proportion, pi)
	
	end = time.time()
	print "time delay =", int((end-start) * 1000), "ms, r^2 =", r*r, ", proportion =", proportion
	if visualization:
		for i in range(numBallLocations):
			cv2.circle(image, (ballXLRU.arr[i], ballYLRU.arr[i]), 5, (128, 0, 128), thickness=-1)
		cv2.circle(image, (cx,cy), 5, GREEN, thickness=-1)
		cv2.rectangle(image, (xOffset, yOffset), (frameSize[0] - xOffset, frameSize[1] - yOffset), GREEN, thickness=2)
		if not math.isnan(slope):
			cv2.line(image, (0, int(intercept)), (frameSize[0], int(intercept + frameSize[0] * slope)), color=BLUE, thickness=3)
		cv2.circle(image, (xOffset, avgIntPoint), 5, color=ORANGE, thickness=-1)
		# show the frame
		cv2.imshow("Frame", image)
		key = cv2.waitKey(1) & 0xFF
	
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
