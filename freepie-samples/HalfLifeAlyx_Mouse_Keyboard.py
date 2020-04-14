import math, time

# HL:A Mouse and Keyboard v0.9
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
triggerKey = Key.E
systemKey = Key.Q
menuKey = Key.T
gripKey = Key.R
handToggleKey = Key.C
handForwardKey = Key.F
handBackwardKey = Key.G
crouchKey = Key.LeftControl
#----------------------------------------------------------------------------
# Vector3D Math inspired by https://github.com/gunny26/python-3d-math
#----------------------------------------------------------------------------
class Vector3D(object):
	"""Vector in R³ """

	def __init__(self, x, y, z):
		"""
		3D coordinates given with x, y, z
		"""
		self.__data = [x, y, z]
	
	def x(self):
		return self.__data[0]
		
	def x_(self, v):
		self.__data[0] = v
		
	x = property(x, x_)


	def y(self):
		return self.__data[0]
		
	def y_(self, v):
		self.__data[0] = v
		
	y = property(y, y_)


	def z(self):
		return self.__data[0]
		
	def z_(self, v):
		self.__data[0] = v
		
	z = property(z, z_)
	
	@classmethod
	def from_list(cls, data):
		"""create class from 3 item tuple"""
		return cls(data[0], data[1], data[2])

	def __eq__(self, other):
		"""test equality"""
		return all((self[index] == other.__data[index] for index in range(3)))

	def nearly_equal(self, other):
		"""
		test nearly equality
		special for unittesting, to test if two floating point number are nearly
		equal, up to some degree of error
		"""
		return all((abs(self[index] - other.__data[index]) < 0.0001 for index in range(3)))
		
	def __richcmp__(self, other, method):
		if method == 0: # < __lt__
			pass
		elif method == 2: # == __eq__
			return self.__data[0] == other.__data[0] and self.__data[1] == other.__data[1] and self.__data[2] == other.__data[2]
		elif method == 4: # > __gt__
			pass
		elif method == 1: # <= lower_equal
			pass
		elif method == 3: # != __ne__
			return self.__data[0] != other.__data[0] or self.__data[1] != other.__data[1] or self.__data[2] != other.__data[2]
		elif method == 5: # >= greater equal
			pass

	def __len__(self):
		"""list interface"""
		return 3

	def __repr__(self):
		"""object representation"""
		return "Vector3D(%(x)f, %(y)f, %(z)f)" % self.__dict__

	def __str__(self):
		"""string output"""
		return "[%(x)f, %(y)f, %(z)f]" % self.__dict__

	def __add__(self, other):
		"""
		vector addition with another Vector class
		does not add up homogeneous part
		"""
		return Vector3D(self.__data[0] + other.__data[0], self.__data[1] + other.__data[1], self.__data[2] + other.__data[2])

	def __iadd__(self, other):
		"""
		vector addition with another Vector class implace
		does not add up homogeneous part
		"""
		self.__data[0] += other.__data[0]
		self.__data[1] += other.__data[1]
		self.__data[2] += other.__data[2]
		return self

	def __sub__(self, other):
		"""
		vector addition with another Vector class
		ignores homogeneous part
		"""
		return Vector3D(self.__data[0] - other.__data[0], self.__data[1] - other.__data[1], self.__data[2] - other.__data[2])

	def __isub__(self, other):
		"""
		vector addition with another Vector class implace
		ignores homogeneous part
		"""
		self.__data[0] -= other.__data[0]
		self.__data[1] -= other.__data[1]
		self.__data[2] -= other.__data[2]
		return self

	def __mul__(self, scalar):
		"""
		multiplication with scalar
		ignores homogeneous part
		"""
		return Vector3D(self.__data[0] * scalar, self.__data[1] * scalar, self.__data[2] * scalar)

	def __imul__(self, scalar):
		"""
		multiplication with scalar inplace
		ignores homogeneous part
		"""
		self.__data[0] *= scalar
		self.__data[1] *= scalar
		self.__data[2] *= scalar
		return self

	def __div__(self, scalar):
		"""
		division with scalar
		ignores homogeneous part
		"""
		return Vector3D(self.__data[0] / scalar, self.__data[1] / scalar, self.__data[2] / scalar)

	def __idiv__(self, scalar):
		"""
		vector addition with another Vector class
		ignores homogeneous part
		"""
		self.__data[0] /= scalar
		self.__data[1] /= scalar
		self.__data[2] /= scalar
		return self

	def length(self):
		"""return length of vector"""
		return math.sqrt(self.__data[0] * self.__data[0] + self.__data[1] * self.__data[1] + self.__data[2] * self.__data[2])

	def length_sqrd(self):
		"""retrun length squared"""
		return self.__data[0] **2 + self.__data[1] ** 2 + self.__data[2] ** 2

	def dot(self, other):
		"""
		homogeneous version, adds also h to dot product
		this version is used in matrix multiplication
		dot product of self and other vector
		dot product is the projection of one vector to another,
		for perpendicular vectors the dot prduct is zero
		for parallell vectors the dot product is the length of the other vector
		"""
		dotproduct = self.__data[0] * other.__data[0] + self.__data[1] * other.__data[1] + self.__data[2] * other.__data[2]
		return dotproduct

	def dot3(self, other):
		"""
		this is the non-homogeneous dot product of self and other,
		h is set to zero
		dot product of self and other vector
		dot product is the projection of one vector to another,
		for perpedicular vectors the dot prduct is zero
		for parallell vectors the dot product is the length of the other vector
		the dot product of two vectors represents also the sin of the angle
		between these two vectors.
		the dot product represents the projection of other onto self
		dot product = cos(theta)
		so theta could be calculates as
		theta = acos(dot product)
		"""
		dotproduct = self.__data[0] * other.__data[0] + self.__data[1] * other.__data[1] + self.__data[2] * other.__data[2]
		return dotproduct

	def cross(self, other):
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
		return Vector3D(
			self.__data[1] * other.__data[2] - self.__data[2] * other.__data[1],
			self.__data[2] * other.__data[0] - self.__data[0] * other.__data[2],
			self.__data[0] * other.__data[1] - self.__data[1] * other.__data[0])

	def normalized(self):
		"""
		return self with length=1, unit vector
		divide every value (x,y,z) by length of vector
		TODO: what about homgeneous part?
		"""
		return self / self.length()
	unit = normalized

	def project2d(self, shift_vec):
		"""
		project self to 2d
		simply divide x and y with z value
		and transform with valeus from shift_vec
		"""
		return (self.__data[0] / self.__data[2] + shift_vec[0], self.__data[1] / self.__data[2] + shift_vec[1])

	def project(win_width, win_height, fov, viewer_distance):
		"""
		project some vector (vec1) to 2D Screen
		vec1 - vector to project
		win_width - width of window
		win_height - height of screen
		fov - field of view
		viewer-distance - distance ov viewer in front of screen
		returns <tuple> (x, y)
		"""
		factor = fov / (viewer_distance + self.__data[2])
		x = self.__data[0] * factor + win_width / 2
		y = -self.__data[1] * factor + win_height / 2
		return x, y

	def angle_to(self, other):
		"""
		angle between self and other Vector object
		to calculate this, the dot product of self and other is used
		"""
		v1 = self.normalized()
		v2 = other.normalized()
		dotproduct = v1.dot(v2)
		return math.acos(dotproduct)

	def angle_to_unit(self, other):
		"""this version assumes that these two vectors are unit vectors"""
		return math.acos(self.dot(other))
		
	def rotateByEulerAngles(self, x, y, z):
		q = euler2quaternion([x, y, z])
		result = multiply(multiply(q, [self.__data[0], self.__data[1], self.__data[2], 1]), conj(q))
		return Vector3D(result[0], result[1], result[2])
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
  yaw_pitch_roll[2] = atan2(sinr, cosr)

  # pitch (y-axis rotation)
  sinp = +2.0 * (q[3] * q[1] - q[2] * q[0])
  if (fabs(sinp) >= 1):
	yaw_pitch_roll[1] = math.copysign(M_PI / 2, sinp)
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

#----------------------------------------------------------------------------
#	Main Program
#----------------------------------------------------------------------------

global timestamp, buttonsUpdateTime, forwardOrientation, controllerOffsetX, controllerOffsetY, controllerOffsetZ, leftClick, rightClick, isCrouch, touchX, touchY, lastTouchTime, handToggle, grabX, grabY, grabZ, headPositionOffset, mouseWheel, leftHandUp
global touchId,clickId

#ControllerPivotVector - placed at the right eye for better aiming
defaultPivotX = 0.0230
defaultPivotY = 0
defaultPivotZ = -0.5

if starting:
	#system.threadExecutionInterval = 10
	timestamp = time.time()
	leftClick = False
	rightClick = False
	isCrouch = False
	handToggle = False
	leftHandUp = False
	touchX = 0
	touchY = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	#controllerPivotVector = [defaultPivotX,defaultPivotY,defaultPivotZ]
	buttonsUpdateTime = 0
	forwardOrientation = [0,0,0]
	lastTouchTime = 0
	grabX = 0.2
	grabY = 0.0
	grabZ = 0.2
	headPositionOffset = [0,0,0]
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
	mouseWheel = 0


deltaTime = time.time() - timestamp

buttonsUpdateTime += deltaTime

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	keyboardX = (keyboard.getKeyDown(Key.D) * 1.0 - keyboard.getKeyDown(Key.A) * 1.0)
	keyboardY = (keyboard.getKeyDown(Key.W) * 1.0 - keyboard.getKeyDown(Key.S) * 1.0)
	mouseBtnBack = mouse.getButton(3)
	mouseBtnFwd = mouse.getButton(4)
	keyUp = keyboard.getKeyDown(Key.UpArrow)
	keyDown = keyboard.getKeyDown(Key.DownArrow)
	keyLeft = keyboard.getKeyDown(Key.LeftArrow)
	keyRight = keyboard.getKeyDown(Key.RightArrow)
	
	mouseWheel = lerp(mouseWheel, mouse.wheel, 60.0 * deltaTime)
	
	if (mouseBtnFwd or keyUp):
		touchY = 1.0
	elif (mouseBtnBack or keyDown):
		touchY = -1.0
	else:
		touchY = 0.0
	if (keyLeft):
		touchX = -1.0
	elif (keyRight):
		touchX = 1.0
	else:
		touchX = 0.0

	alvr.trackpad[0][0] = touchX
	alvr.trackpad[0][1] = touchY
	alvr.trackpad[1][0] = keyboardX
	alvr.trackpad[1][1] = keyboardY
	
	leftTrackPadClick = keyboardX != 0 or keyboardY != 0
		
	alvr.buttons[1][touchId] = leftTrackPadClick
	alvr.buttons[1][clickId] = leftTrackPadClick
	
	lerpX5 = 5 * deltaTime
	lerpX30 = 30 * deltaTime
	
	targetOrientation = [alvr.head_orientation[0], alvr.head_orientation[1], alvr.head_orientation[2]]
	leftClick = mouse.leftButton
	if (mouse.rightButton):
		controllerOffsetX = lerp(controllerOffsetX, grabX, lerpX5)
		controllerOffsetY = lerp(controllerOffsetY, grabY, lerpX5)
		controllerOffsetZ = lerp(controllerOffsetZ, grabZ, lerpX5)
		targetOrientation[2] = math.radians(180)
		rightClick = True
	else:
		if (rightClick):
			controllerOffsetX = 0
			controllerOffsetY = 0
			controllerOffsetZ = 0.15
			rightClick = False
		else:
			controllerOffsetX = clamp(controllerOffsetX, -0.4, 0.4)
			controllerOffsetY = clamp(controllerOffsetY, -0.4, 0.4)
			controllerOffsetZ = clamp(controllerOffsetZ, -0.9, 0.4)
	
	forwardOrientation[0] = moveTowards(forwardOrientation[0], targetOrientation[0], lerpX5)
	forwardOrientation[1] = moveTowards(forwardOrientation[1], targetOrientation[1], lerpX5)
	forwardOrientation[2] = moveTowards(forwardOrientation[2], targetOrientation[2], lerpX5)
	
	mouseX = mouse.deltaX * 0.001
	mouseY = mouse.deltaY * 0.001
	
	if (mouseWheel != 0):
		controllerOffsetZ -= (mouseWheel) * 0.1 * deltaTime

	if (leftClick or rightClick or mouseWheel):
		lastTouchTime = time.time()

	# Reset hand position
	if ( not leftClick and not rightClick and not mouseWheel and (time.time() - lastTouchTime) > 0.4 ):
		controllerOffsetX = lerp(controllerOffsetX, 0, 2 * deltaTime)
		controllerOffsetY = lerp(controllerOffsetY, 0, 2 * deltaTime)
		#controllerOffsetZ = lerp(controllerOffsetZ, 0, 2 * deltaTime)
	
	# Head offset and crouching
	
	if (keyboard.getPressed(crouchKey)):
		isCrouch = not isCrouch
	
	headOffset = [0, 0, 0]
	if (isCrouch):
		headOffset[1] = -0.5
	else:
		headOffset[1] = 0.0
	
	alvr.head_orientation[1] += -mouseX
	alvr.head_orientation[2] += -mouseY
	
	localForward = rotatevec( alvr.controller_orientation[0], [0,0,-1,0] )
	
	localForward[1] = 0
	
	localForward = normalize(localForward)
	
	localRight = rotatevec(alvr.controller_orientation[0], [1,0,0,0])
	
	#headPositionOffset = add( add(headPositionOffset, mul(localForward, (keyboardY * deltaTime))), mul(localRight, (keyboardX * deltaTime)))
	
	alvr.head_position[0] = headPositionOffset[0]
	alvr.head_position[1] = headPositionOffset[1] + lerp(alvr.head_position[1], headOffset[1], 10 * deltaTime)
	alvr.head_position[2] = headPositionOffset[2]
	
	rot = alvr.controller_orientation[0]
	rot[0] = lerp(rot[0], forwardOrientation[0], 0.2)
	rot[1] = lerp(rot[1], forwardOrientation[1] + math.radians(0), 0.2)
	rot[2] = lerp(rot[2], forwardOrientation[2] + math.radians(58), 0.2)
	
	# Local vector from controller pivot
	controllerOffsetVector = rotatevec( forwardOrientation, [controllerOffsetX, controllerOffsetY, controllerOffsetZ,0])
		
	controllerPivotVector  = rotatevec( forwardOrientation, [defaultPivotX, defaultPivotY, defaultPivotZ,0] )
	
	controllerPivotVector[0] += alvr.head_position[0]
	controllerPivotVector[1] += alvr.head_position[1]
	controllerPivotVector[2] += alvr.head_position[2]
	
	desiredControllerPosition = add(controllerPivotVector, controllerOffsetVector)
	
	#desiredControllerPosition[1] += headOffset[1]
	
	alvr.controller_position[0][0] = lerp(alvr.controller_position[0][0], desiredControllerPosition[0], lerpX30)
	alvr.controller_position[0][1] = lerp(alvr.controller_position[0][1], desiredControllerPosition[1], lerpX30)
	alvr.controller_position[0][2] = lerp(alvr.controller_position[0][2], desiredControllerPosition[2], lerpX30)
	
	#diagnostics.watch(alvr.controller_position[0][0])
	
	localLeftOffsetX = -0.04
	localLeftOffsetY = -0.15
	localLeftOffsetZ = 0.0
	
	if (keyboard.getPressed(handToggleKey)):
		handToggle = not handToggle
	
	if (keyboard.getKeyDown(handForwardKey)):
		localLeftOffsetZ += -0.2 #move hand forward 
	elif (keyboard.getKeyDown(handBackwardKey)):
		localLeftOffsetZ += 0.2 #move hand backward
	if (keyboard.getPressed(Key.V)):
		leftHandUp = not leftHandUp
	if (leftHandUp):
		localLeftOffsetY = 0.1
	
	if (not keyboard.getKeyDown(Key.LeftAlt)):
		if (handToggle or mouse.rightButton):
			desiredControllerPositionLeft = add(desiredControllerPosition, rotatevec( forwardOrientation, [localLeftOffsetX, localLeftOffsetY, localLeftOffsetZ,0] ) )
		else:
			desiredControllerPositionLeft = rotatevec( forwardOrientation, [-0.3, -0.2, -0.4, 0.0] )
			desiredControllerPositionLeft[0] += alvr.head_position[0]
			desiredControllerPositionLeft[1] += alvr.head_position[1]
			desiredControllerPositionLeft[2] += alvr.head_position[2]
	
	alvr.controller_position[1][0] = lerp(alvr.controller_position[1][0], desiredControllerPositionLeft[0], lerpX30)
	alvr.controller_position[1][1] = lerp(alvr.controller_position[1][1], desiredControllerPositionLeft[1], lerpX30)
	alvr.controller_position[1][2] = lerp(alvr.controller_position[1][2], desiredControllerPositionLeft[2], lerpX30)
	
	alvr.controller_orientation[1][0] = alvr.controller_orientation[0][0] 
	alvr.controller_orientation[1][1] = alvr.controller_orientation[0][1]
	alvr.controller_orientation[1][2] = alvr.controller_orientation[0][2] - math.radians(60)
	
	alvr.trigger[1] = keyboard.getKeyDown(triggerKey)

	alvr.buttons[0][systemId] = keyboard.getKeyDown(systemKey)
	
	alvr.buttons[0][menuId] = keyboard.getKeyDown(menuKey) or mouse.middleButton
	
	# Controller buttons
	
	trackpadClickNow = (not rightClick and (mouseBtnFwd or mouseBtnBack or touchX != 0))
	
	alvr.buttons[0][clickId] = trackpadClickNow
	alvr.buttons[0][touchId] = True
	
	triggerPulledNow = leftClick
	
	alvr.buttons[0][gripId] = keyboard.getKeyDown(gripKey)
		
	alvr.trigger[0] = triggerPulledNow
	
	executeTime = time.time() - timestamp
	diagnostics.watch(executeTime)