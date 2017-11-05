#!/usr/bin/python
import pigpio
import sys

leftServo=4
rightServo=17
minAngle=45
maxAngle=135
pulseWidth0=500
pulseWidth180=2500

# accepts 1 command line argument (between 0.0 and 1.0) that is the position of the paddle
def paddle(val, pi):
	if val < 0 or val > 1:
		print("first command line argument must be float between 0 and 1")
		return
	angle = minAngle + val * (maxAngle - minAngle)
	pulseWidth = pulseWidth0 + (pulseWidth180 - pulseWidth0) * angle / 180
	pulseWidth = int(pulseWidth)
	pi.set_servo_pulsewidth(leftServo, pulseWidth)
	pi.set_servo_pulsewidth(rightServo, pulseWidth)
