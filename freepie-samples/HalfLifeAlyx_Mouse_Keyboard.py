import math, time

# HL:A Mouse and Keyboard v1.0
#----------------------------------------------------------------------------
# INFO
#----------------------------------------------------------------------------
# This is controller script optimized for keyboard and mouse controls in HL:Alyx game. Use FreePIE to execute this script.
#
# *** Note: this script is optimized for Dual Controllers mode and Continuous move setting
#
# * Mouse wheel extends your arm
# * C button toggles left hand positions
# * WSAD is left controller trackpad used to move you around with Continuous mode
# * Right mouse button rotates arms to reach the backpack
# * Left mouse button is 'trigger' to grab an ammo. E button is left hand trigger by default
# * Middle mouse button is 'Menu' button used to pull the slider of your weapon
# * R is 'Grip' button to drop the clip
# * LeftCtrl is to crouch
# * F and G to move left hand forward and backward to reach the pockets
# * P for menu

# ACTIONS MAPPING

triggerKey = Key.E

systemKey = Key.Q

menuKey = Key.T

gripKey = Key.R

rightHandToggleKey = Key.RightShift

handUpKey = Key.V

leftHandToggleKey = Key.LeftShift

rightHandFreezeKey = Key.RightAlt

leftHandFreezeKey = Key.LeftAlt

handForwardKey = Key.F

handBackwardKey = Key.G

crouchKey = Key.LeftControl

# SETTINGS

# When hand is not active it is shifted to the special position
LeftHandShiftedPivot  = [-0.25, -0.3, -0.4, 0.0]
RightHandShiftedPivot = [ 0.25, -0.05, -0.6, 0.0]

# When Left hand is active
leftHandOffset = [ 0.0, -0.15, -0.6, 0.0]

leftHandSnappedOffset = [ -0.05, -0.15, 0.1, 0.0]

# Default hand positions from their pivot points
LeftHandLocalPosition  = [0.0, 0.0, 0.0, 0.0]
RightHandLocalPosition = [0.0, 0.0, 0.2, 0.0]

# Right hand pivot should be located behind the right eye position. IPD on GearVR is 0.064m so right eye is at 0.032m to the right
HandPivotOffset = [0.032, 0, -0.5, 0.0]

ArmMaxLength = 0.9

# When hand is in backpack position, hand offset is applied to reach correct spot
BackpackHandOffset = [0.2, 0.0, 0.2, 0.0]

MouseSensivity = 0.001

WheelSensivity = 0.25

StandingHeight = 1.7

CrouchHeight = 1.0

#----------------------------------------------------------------------------
#	Math Utility
#----------------------------------------------------------------------------

def normalize(v):
	vlength = math.sqrt(v.x **2 + v.y ** 2 + v.z ** 2)
	v[0] = v[0] / vlength
	v[1] = v[1] / vlength
	v[2] = v[2] / vlength
	return v

def magnitude(v):
	return math.sqrt(sum(v[i]*v[i] for i in range(len(v))))

def mul(u, v):
	return [ u[i]*v for i in range(len(u)) ]

def add(u, v):
	return [ u[i]+v[i] for i in range(len(u)) ]

def sub(u, v):
	return [ u[i]-v[i] for i in range(len(u)) ]

def dot(u, v):
	return sum(u[i]*v[i] for i in range(len(u)))

def normalize(v):
	vmag = magnitude(v)
	return [ v[i]/vmag  for i in range(len(v)) ]

def clampMagnitude(v, max):
	if ( (v[0]*v[0]+v[1]*v[1]+v[2]*v[2]) > max*max):
		return mul(normalize(v), max)
	return v

def max(a, b):
	if (a > b):
		return a
	else:
		return b
		
def min(a, b):
	if (a < b):
		return a
	else:
		return b

def moveTowards(a, b, maxStep):
	if (b > a):
		return a + min(b-a, maxStep)
	else:
		return a + max(b-a, -maxStep)

def lerp(a, b, t):
	return a * (1 - t) + b * t

def sign(x): return 1 if x >= 0 else -1

def clamp(v, min, max):
	if (v < min):
		v = min
	elif (v > max):
		v = max
	return v

# conjugate quaternion
def conj(q):
  return [-q[0], -q[1], -q[2], q[3]]

# multiplication of quaternion
def multiply(a, b):
  x0, y0, z0, w0 = a
  x1, y1, z1, w1 = b
  return [x1 * w0 - y1 * z0 + z1 * y0 + w1 * x0,
	  x1 * z0 + y1 * w0 - z1 * x0 + w1 * y0,
	  -x1 * y0 + y1 * x0 + z1 * w0 + w1 * z0,
	  -x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0]

# convert quaternion to euler
def quaternion2euler(q):
  yaw_pitch_roll = [0.0, 0.0, 0.0]
  # roll (x-axis rotation)
  sinr = +2.0 * (q[3] * q[0] + q[1] * q[2])
  cosr = +1.0 - 2.0 * (q[0] * q[0] + q[1] * q[1])
  yaw_pitch_roll[2] = math.atan2(sinr, cosr)

  # pitch (y-axis rotation)
  sinp = +2.0 * (q[3] * q[1] - q[2] * q[0])
  if (math.fabs(sinp) >= 1):
	yaw_pitch_roll[1] = math.copysign(math.pi / 2, sinp)
  else:
	yaw_pitch_roll[1] = math.asin(sinp)

  # yaw (z-axis rotation)
  siny = +2.0 * (q[3] * q[2] + q[0] * q[1]);
  cosy = +1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2]);
  yaw_pitch_roll[0] = math.atan2(siny, cosy);

  return yaw_pitch_roll

# convert euler to quaternion
def euler2quaternion(yaw_pitch_roll):
  cy = math.cos(yaw_pitch_roll[0] * 0.5);
  sy = math.sin(yaw_pitch_roll[0] * 0.5);
  cr = math.cos(yaw_pitch_roll[2] * 0.5);
  sr = math.sin(yaw_pitch_roll[2] * 0.5);
  cp = math.cos(yaw_pitch_roll[1] * 0.5);
  sp = math.sin(yaw_pitch_roll[1] * 0.5);

  return [cy * sr * cp - sy * cr * sp,
  cy * cr * sp + sy * sr * cp,
  sy * cr * cp - cy * sr * sp,
  cy * cr * cp + sy * sr * sp]

# rotate specified vector using yaw_pitch_roll
def rotatevec(yaw_pitch_roll, vec):
  q = euler2quaternion(yaw_pitch_roll)
  return multiply(multiply(q, vec), conj(q))

def cross(one, other):
	"""
	cross product of self and other vector
	the result is a new perpendicular vector to self and other
	the length of the new vector is defined as
	|cross product| = |self| * |other| * cos(theta)
	so the angle theta between self and other is calculated as follows
	theta = asin(|cross product| / (|self| * | other|))
	if self and other are unit vectors
	|self| = |other| = 1
	this simplifies to
	|cross product| = sin(theta)
	so you can use the cross product of two vectors two
	find the angle between these two vector, possible useful for shading/lightning
	"""
	return [one[1] * other[2] - one[2] * other[1], one[2] * other[0] - one[0] * other[2], one[0] * other[1] - one[1] * other[0] ]

def QuaternionLookRotation(forward, up):
	vector	= normalize(forward)
	vector2 = normalize(cross(up, vector))
	vector3 = normalize(cross(vector, vector2))
	m00 = vector2[0]
	m01 = vector2[1]
	m02 = vector2[2]
	m10 = vector3[0]
	m11 = vector3[1]
	m12 = vector3[2]
	m20 = vector[0]
	m21 = vector[1]
	m22 = vector[2]
	
	quaternion = [0,0,0,1]
	num8 = (m00 + m11) + m22
	if (num8 > 0.0):
		 num = math.sqrt(num8 + 1.0)
		 quaternion[3] = num * 0.5;
		 num = 0.5 / num;
		 quaternion[0] = (m12 - m21) * num;
		 quaternion[1] = (m20 - m02) * num;
		 quaternion[2] = (m01 - m10) * num;
		 return quaternion
	if ((m00 >= m11) and (m00 >= m22)):
		num7 = math.sqrt(((1.0 + m00) - m11) - m22)
		num4 = 0.5 / num7
		quaternion[0] = 0.5 * num7
		quaternion[1] = (m01 + m10) * num4
		quaternion[2] = (m02 + m20) * num4
		quaternion[3] = (m12 - m21) * num4
		return quaternion;
	if (m11 > m22):
		num6 = math.sqrt(((1.0 + m11) - m00) - m22)
		num3 = 0.5 / num6
		quaternion[0] = (m10+ m01) * num3
		quaternion[1] = 0.5 * num6
		quaternion[2] = (m21 + m12) * num3
		quaternion[3] = (m20 - m02) * num3
		return quaternion 
	num5 = math.sqrt(((1.0 + m22) - m00) - m11)
	num2 = 0.5 / num5
	quaternion[0] = (m20 + m02) * num2
	quaternion[1] = (m21 + m12) * num2
	quaternion[2] = 0.5 * num5
	quaternion[3] = (m01 - m10) * num2
	return quaternion
#----------------------------------------------------------------------------
#	Main Program
#----------------------------------------------------------------------------

if starting:
	# Guns iron sights in HL:A are not placed at the same position as the hand so we need to adjust hand position to match foresights line with the center of the eye
	gunOffset = [-0.012,-0.015,0,0]
	# Gun is not perfectly aligned with the hand orientation so we need to adjust hand rotation to aim along the iron sight line
	rightHandRotation = [56.2, 0.8, 0.0, 0.0]
	leftHandRotation =  [-30.0, 0.0, 0.0, 0.0]
	timestamp = time.time()
	leftClick = False
	rightClick = False
	isCrouch = False
	leftHandActive = True
	leftHandUp = False
	rightHandActive = True
	keyboardRIGHT = 0
	keyboardUP = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	mouseWheel = 0
	forwardOrientation = [0,0,0,0]
	headPositionOffset = [0,0,0,0]
	alvr.two_controllers = True
	alvr.override_head_position = True
	alvr.override_head_orientation = True
	alvr.override_controller_position = True
	alvr.override_controller_orientation = True
	touchId = alvr.Id("trackpad_touch")
	clickId = alvr.Id("trackpad_click")
	systemId = alvr.Id("system")
	menuId = alvr.Id("application_menu")
	gripId = alvr.Id("grip")

deltaTime = time.time() - timestamp

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	mouseBtnBack = mouse.getButton(3)
	mouseBtnFwd = mouse.getButton(4)
	
	keyboardAD = (keyboard.getKeyDown(Key.D) * 1.0 - keyboard.getKeyDown(Key.A) * 1.0)
	keyboardWS = (keyboard.getKeyDown(Key.W) * 1.0 - keyboard.getKeyDown(Key.S) * 1.0)
	
	keyboardUP = (keyboard.getKeyDown(Key.UpArrow) * 1.0 - keyboard.getKeyDown(Key.DownArrow) * 1.0)
	keyboardRIGHT = (keyboard.getKeyDown(Key.RightArrow) * 1.0 - keyboard.getKeyDown(Key.LeftArrow) * 1.0)
	
	rightHandRotation[0] += (keyboard.getPressed(Key.PageUp) * 0.1 - keyboard.getPressed(Key.PageDown) * 1.0)
	rightHandRotation[1] += (keyboard.getPressed(Key.NumberPadPlus) * 0.1 - keyboard.getPressed(Key.NumberPadMinus) * 1.0)
	
	gunOffset[0] += (keyboard.getPressed(Key.NumberPad6) * 0.001 - keyboard.getPressed(Key.NumberPad4) * 0.001)
	gunOffset[1] += (keyboard.getPressed(Key.NumberPad8) * 0.001 - keyboard.getPressed(Key.NumberPad2) * 0.001)
	
	diagnostics.watch(gunOffset[0]),diagnostics.watch(gunOffset[1])
	diagnostics.watch(HandPivotOffset[0]), diagnostics.watch(HandPivotOffset[1])
	diagnostics.watch(rightHandRotation[0]), diagnostics.watch(rightHandRotation[1])
	
	mouseWheel = lerp(mouseWheel, mouse.wheel, 30.0 * deltaTime)
	
	leftClick = mouse.leftButton
	
	if (keyboard.getPressed(rightHandToggleKey)):
		rightHandActive = not rightHandActive
		
	if (keyboard.getPressed(leftHandToggleKey)):
		leftHandActive = not leftHandActive
	
	# Right trackpad positions
	alvr.trackpad[0][0] = keyboardRIGHT
	alvr.trackpad[0][1] = keyboardUP + mouseBtnFwd * 1.0 - mouseBtnBack * 1.0 
	
	# Left trackpad positions
	alvr.trackpad[1][0] = keyboardAD
	alvr.trackpad[1][1] = keyboardWS
	
	leftTrackPadClick = alvr.trackpad[1][0] != 0 or alvr.trackpad[1][1] != 0
	
	alvr.buttons[1][touchId] = leftTrackPadClick
	alvr.buttons[1][clickId] = leftTrackPadClick
	
	lerpX5 = 5 * deltaTime
	lerpX10 = 10 * deltaTime
	lerpX30 = 30 * deltaTime
	
	desiredArmOrientation = [alvr.head_orientation[0], alvr.head_orientation[1], alvr.head_orientation[2]]
	
	if (mouse.rightButton):
		controllerOffsetX = lerp(controllerOffsetX, BackpackHandOffset[0], lerpX5)
		controllerOffsetY = lerp(controllerOffsetY, BackpackHandOffset[1], lerpX5)
		controllerOffsetZ = lerp(controllerOffsetZ, BackpackHandOffset[2], lerpX5)
		desiredArmOrientation[2] = math.radians(180)
		rightClick = True
	else:
		if (rightClick):
			controllerOffsetX = RightHandLocalPosition[0]
			controllerOffsetY = RightHandLocalPosition[1]
			controllerOffsetZ = RightHandLocalPosition[2]
			rightClick = False
	
	forwardOrientation[0] = moveTowards(forwardOrientation[0], desiredArmOrientation[0], lerpX5)
	forwardOrientation[1] = moveTowards(forwardOrientation[1], desiredArmOrientation[1], lerpX5)
	forwardOrientation[2] = moveTowards(forwardOrientation[2], desiredArmOrientation[2], lerpX5)
	
	mouseX = mouse.deltaX * MouseSensivity
	mouseY = mouse.deltaY * MouseSensivity
	
	if (mouseWheel != 0):
		controllerOffsetZ -= (mouseWheel) * WheelSensivity * deltaTime

	controllerOffsetX = clamp(controllerOffsetX, -ArmMaxLength*0.5, ArmMaxLength*0.5)
	controllerOffsetY = clamp(controllerOffsetY, -ArmMaxLength*0.5, ArmMaxLength*0.5)
	controllerOffsetZ = clamp(controllerOffsetZ, -ArmMaxLength, ArmMaxLength*0.5)
	
	# Head offset and crouching
	
	if (keyboard.getPressed(crouchKey)):
		isCrouch = not isCrouch
	
	if (isCrouch):
		headPositionOffset[1] = CrouchHeight
	else:
		headPositionOffset[1] = StandingHeight
	
	alvr.head_orientation[1] -= mouseX
	alvr.head_orientation[2] -= mouseY
	
	alvr.head_position[0] = lerp(alvr.head_position[0], headPositionOffset[0], lerpX10)
	alvr.head_position[1] = lerp(alvr.head_position[1], headPositionOffset[1], lerpX10)
	alvr.head_position[2] = lerp(alvr.head_position[2], headPositionOffset[2], lerpX10)
	
	rightHandLocalPosition = add(gunOffset, [controllerOffsetX, controllerOffsetY, controllerOffsetZ, 0] )
	# Local vector from controller pivot
	controllerOffsetVector = rotatevec( forwardOrientation, rightHandLocalPosition )
	
	controllerPivotVector = [alvr.head_position[0], alvr.head_position[1], alvr.head_position[2] ]
	
	if (not rightHandActive and not mouse.rightButton):
		controllerPivotVector  = add(controllerPivotVector, rotatevec( forwardOrientation, RightHandShiftedPivot ))
	else:
		controllerPivotVector  = add(controllerPivotVector, rotatevec( forwardOrientation, HandPivotOffset ))
	
	desiredRightHandPosition = add(controllerPivotVector, controllerOffsetVector)
	
	if (not keyboard.getKeyDown(rightHandFreezeKey)):
		alvr.controller_position[0][0] = lerp(alvr.controller_position[0][0], desiredRightHandPosition[0], lerpX30)
		alvr.controller_position[0][1] = lerp(alvr.controller_position[0][1], desiredRightHandPosition[1], lerpX30)
		alvr.controller_position[0][2] = lerp(alvr.controller_position[0][2], desiredRightHandPosition[2], lerpX30)
		
		alvr.controller_orientation[0][0] = forwardOrientation[0] + math.radians(rightHandRotation[2])
		alvr.controller_orientation[0][1] = forwardOrientation[1] + math.radians(rightHandRotation[1])
		alvr.controller_orientation[0][2] = forwardOrientation[2] + math.radians(rightHandRotation[0])
	
	leftHandOffset = [0,0,0,0]
	
	if (keyboard.getKeyDown(handForwardKey)):
		leftHandOffset[2] += -0.2 #move hand forward 
	elif (keyboard.getKeyDown(handBackwardKey)):
		leftHandOffset[2] += 0.2 #move hand backward
	if (keyboard.getPressed(handUpKey)):
		leftHandUp = not leftHandUp
	if (leftHandUp):
		leftHandOffset[1] = 0.3
		
	if (not keyboard.getKeyDown(leftHandFreezeKey)):
		desiredLeftHandRotation = [0,0,0,0]
		desiredLeftHandRotation[0] = alvr.head_orientation[0] + math.radians(leftHandRotation[2])
		desiredLeftHandRotation[1] = alvr.head_orientation[1] + math.radians(leftHandRotation[1])
		desiredLeftHandRotation[2] = alvr.head_orientation[2] + math.radians(leftHandRotation[0])
		
		if (leftHandActive):
			if (rightHandActive):
				desiredLeftHandPosition = add(desiredRightHandPosition, rotatevec( forwardOrientation,  leftHandOffset) )
				desiredLeftHandPosition = add(desiredLeftHandPosition, rotatevec(alvr.controller_orientation[0], leftHandSnappedOffset))
				desiredLeftHandRotation[0] = alvr.controller_orientation[0][0] + math.radians(leftHandRotation[2])
				desiredLeftHandRotation[1] = alvr.controller_orientation[0][1] + math.radians(leftHandRotation[1])
				desiredLeftHandRotation[2] = alvr.controller_orientation[0][2] + math.radians(leftHandRotation[0])
			else:
				leftHandOffset[2] += controllerOffsetZ
				desiredLeftHandPosition = add(alvr.head_position, rotatevec( forwardOrientation, add(leftHandOffset, [0,0,-0.6+controllerOffsetZ,0]) ) )
				desiredLeftHandRotation[0] = alvr.controller_orientation[0][0] + math.radians(leftHandRotation[2])
				desiredLeftHandRotation[1] = alvr.controller_orientation[0][1] + math.radians(leftHandRotation[1])
				desiredLeftHandRotation[2] = alvr.controller_orientation[0][2] + math.radians(leftHandRotation[0])
		else:
			desiredLeftHandPosition = add(alvr.head_position, rotatevec( alvr.head_orientation, add(leftHandOffset, LeftHandShiftedPivot) ))
	
		alvr.controller_position[1][0] = lerp(alvr.controller_position[1][0], desiredLeftHandPosition[0], lerpX30)
		alvr.controller_position[1][1] = lerp(alvr.controller_position[1][1], desiredLeftHandPosition[1], lerpX30)
		alvr.controller_position[1][2] = lerp(alvr.controller_position[1][2], desiredLeftHandPosition[2], lerpX30)
		
		alvr.controller_orientation[1][0] = desiredLeftHandRotation[0]
		alvr.controller_orientation[1][1] = desiredLeftHandRotation[1]
		alvr.controller_orientation[1][2] = desiredLeftHandRotation[2]
	
	alvr.trigger[1] = keyboard.getKeyDown(triggerKey)

	alvr.buttons[0][systemId] = keyboard.getKeyDown(systemKey)
	
	alvr.buttons[0][menuId] = keyboard.getKeyDown(menuKey) or mouse.middleButton
	
	# Controller buttons
	
	trackpadClickNow = (not rightClick and (mouseBtnFwd or mouseBtnBack or keyboardRIGHT != 0))
	
	alvr.buttons[0][clickId] = trackpadClickNow
	alvr.buttons[0][touchId] = True
	
	triggerPulledNow = leftClick
	
	alvr.buttons[0][gripId] = keyboard.getKeyDown(gripKey)
		
	alvr.trigger[0] = triggerPulledNow
	
	executeTime = time.time() - timestamp
	diagnostics.watch(executeTime)
	