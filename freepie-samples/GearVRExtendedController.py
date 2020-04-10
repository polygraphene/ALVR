import math, time

# GearVR Extended Controller v0.9
#----------------------------------------------------------------------------
# INFO
#----------------------------------------------------------------------------
# This is controller script optimized for GearVR controller in HL:Alyx game. Use FreePIE to execute this script.
#
# *** Note: enable one-handed mode in SteamVR controller settings! Also disable application menu on trackpad center action
#
# * Rotate GearVR controller to move and rotate your hand
# * Swipe GearVR controller trackpad to extend your arm
# * Double-click trackpad 'Down' button to crouch
# * 'Back' button is mapped to controller 'Grip' for reloading weapon in HL:Alyx. Do not hold it too long - it will trigger system back action! 
# * Double-click 'Back' button to call System menu
# * Center trackpad button is 'Application Menu'. You shoud disable redundant action mapping in SteamVR controller settings
# 
# Look for SETTINGS below
#----------------------------------------------------------------------------
# Vector3D Math from https://github.com/gunny26/python-3d-math
#----------------------------------------------------------------------------
class Vector3D(object):
    """Vector in R³ with homogeneous part h"""

    def __init__(self, x, y, z, h=1):
        """
        3D coordinates given with x, y, z, homgeneous part is optinals, defaults to 1
        """
        self.__data = [x, y, z, h]
        self.x = self.__data[0]
        self.y = self.__data[1]
        self.z = self.__data[2]
        self.h = self.__data[3]

    @classmethod
    def from_list(cls, data):
        """create class from 4 item tuple"""
        return cls(data[0], data[1], data[2], data[3])

    def __eq__(self, other):
        """test equality"""
        return all((self[index] == other[index] for index in range(4)))

    def nearly_equal(self, other):
        """
        test nearly equality
        special for unittesting, to test if two floating point number are nearly
        equal, up to some degree of error
        """
        return all((abs(self[index] - other[index]) < 0.0001 for index in range(4)))

    def __getitem__(self, key):
        return self.__data[key]

    def __richcmp__(self, other, method):
        if method == 0: # < __lt__
            pass
        elif method == 2: # == __eq__
            return self.x == other.x and self.y == other.y and self.z == other.z and self.h == other.h
        elif method == 4: # > __gt__
            pass
        elif method == 1: # <= lower_equal
            pass
        elif method == 3: # != __ne__
            return self.x != other.x or self.y != other.y or self.z != other.z or self.h != other.h
        elif method == 5: # >= greater equal
            pass

    def __len__(self):
        """list interface"""
        return 4

    def __getitem__(self, key):
        """list interface"""
        return self.__data[key]

    def __setitem__(self, key, value):
        """list interface"""
        self.__data[key] = value

    def __repr__(self):
        """object representation"""
        return "Vector3D(%(x)f, %(y)f, %(z)f, %(h)f)" % self.__dict__

    def __str__(self):
        """string output"""
        return "[%(x)f, %(y)f, %(z)f, %(h)f]" % self.__dict__

    def __add__(self, other):
        """
        vector addition with another Vector class
        does not add up homogeneous part
        """
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z, self.h)

    def __iadd__(self, other):
        """
        vector addition with another Vector class implace
        does not add up homogeneous part
        """
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        """
        vector addition with another Vector class
        ignores homogeneous part
        """
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z, self.h)

    def __isub__(self, other):
        """
        vector addition with another Vector class implace
        ignores homogeneous part
        """
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, scalar):
        """
        multiplication with scalar
        ignores homogeneous part
        """
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar, self.h)

    def __imul__(self, scalar):
        """
        multiplication with scalar inplace
        ignores homogeneous part
        """
        self.x *= scalar
        self.y *= scalar
        self.z *= scalar
        return self

    def __div__(self, scalar):
        """
        division with scalar
        ignores homogeneous part
        """
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar, self.h)

    def __idiv__(self, scalar):
        """
        vector addition with another Vector class
        ignores homogeneous part
        """
        self.x /= scalar
        self.y /= scalar
        self.z /= scalar
        return self

    def length(self):
        """return length of vector"""
        return math.sqrt(self.x **2 + self.y ** 2 + self.z ** 2)

    def length_sqrd(self):
        """retrun length squared"""
        return self.x **2 + self.y ** 2 + self.z ** 2

    def dot(self, other):
        """
        homogeneous version, adds also h to dot product
        this version is used in matrix multiplication
        dot product of self and other vector
        dot product is the projection of one vector to another,
        for perpendicular vectors the dot prduct is zero
        for parallell vectors the dot product is the length of the other vector
        """
        dotproduct = self.x * other.x + self.y * other.y + self.z * other.z + self.h * other.h
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
        dotproduct = self.x * other.x + self.y * other.y + self.z * other.z
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
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
            self.h)

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
        return (self.x / self.z + shift_vec[0], self.y / self.z + shift_vec[1])

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
        factor = fov / (viewer_distance + self.z)
        x = self.x * factor + win_width / 2
        y = -self.y * factor + win_height / 2
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
		result = multiply(multiply(q, [self.x, self.y, self.z, 1]), conj(q))
		return Vector3D(result[0], result[1], result[2])
#----------------------------------------------------------------------------
#	Math Utility
#----------------------------------------------------------------------------

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
# SETTINGS
#----------------------------------------------------------------------------

# Arm pivot relative to your head
armLocalPosition = Vector3D(0.2, -0.2, -0.1)

# Hand is placed at the arm position + arm offset that you can control with trackpad. This is default arm offset
defaultArmX = 0.0
defaultArmY = 0.0
defaultArmZ = 0.4

# How low player can duck
crouchOffset = -0.8

# Enable this for head position displacement for correcting ARCore data
ARCoreCorrection = False

#----------------------------------------------------------------------------
#	Main Program
#----------------------------------------------------------------------------

global timestamp, rightControllerId, buttonsUpdateTime, lastTouchTime, isClick, downClick, backClick, isTouch, oldTouchX, oldTouchY, controllerOffsetX, controllerOffsetY, controllerOffsetZ, triggerPulled, clickHoldTime, downClickTime, backClickHoldTime, backClickTime, gripTriggerToggle, isCrouch, isSnappedAim

if starting:
	isClick = False
	timestamp = time.time()
	lastTouchTime = time.time()
	downClickTime = 0
	backClickTime = 0
	clickHoldTime = 0
	rightControllerId = 0
	oldTouchY = 0
	oldTouchX = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	isTouch = False
	downClick = False
	triggerPulled = False
	isCrouch = False
	gripTriggerToggle = False
	backClick = False
	isSnappedAim = False

deltaTime = time.time() - timestamp

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	# Get GearVR Input
	inputHeadPosition = Vector3D(alvr.input_head_position[0],alvr.input_head_position[1],alvr.input_head_position[2])
	if (isCrouch):
		inputHeadPosition.y = crouchOffset
	inputHeadRotation = Vector3D(alvr.input_head_orientation[0], alvr.input_head_orientation[1], alvr.input_head_orientation[2])
	inputControllerPosition = Vector3D(alvr.input_controller_position[0],alvr.input_controller_position[1],alvr.input_controller_position[2])
	inputControllerRotation = Vector3D(alvr.input_controller_orientation[0],alvr.input_controller_orientation[1],alvr.input_controller_orientation[2])
	controllerLocalPosition = inputControllerPosition - inputHeadPosition
	diagnostics.watch(controllerLocalPosition.x), diagnostics.watch(controllerLocalPosition.y),diagnostics.watch(controllerLocalPosition.z)
	
	# Get Controller Input
	wasTouched = isTouch
	isTouch = alvr.input_buttons[alvr.InputId("trackpad_touch")]
	isClickNow = alvr.input_buttons[alvr.InputId("trackpad_click")]
	touchX = alvr.input_trackpad[0]
	touchY = alvr.input_trackpad[1]
	deltaTouchX = 0
	deltaTouchY = 0
	if (isTouch):
		lastTouchTime = time.time()
		if (wasTouched):
			deltaTouchX = (touchX - oldTouchX)
			deltaTouchY = (touchY - oldTouchY)
		oldTouchX = touchX
		oldTouchY = touchY
	diagnostics.watch(isTouch), diagnostics.watch(touchX), diagnostics.watch(touchY)
	
	# Get Trackpad Down Click
	downClickDouble = False
	if (isClickNow):
		# prevents click from happening until double click time gap ended
		if (not isClick and clickHoldTime > 0.15 or alvr.input_trackpad[1] > -0.75): 
			isClick = True
		clickHoldTime += deltaTime
		if (not downClick and alvr.input_trackpad[1] < -0.75):
			if (time.time() - downClickTime < 0.3 ):
				downClickDouble = True
				isCrouch = not isCrouch
			downClickTime = time.time()
			downClick = True
	else:
		clickHoldTime = 0
		isClick = False
		downClick = False
	
	# Get Keyboard WASD
	keyboardX = (keyboard.getKeyDown(Key.D) * 1.0 - keyboard.getKeyDown(Key.A) * 1.0)
	keyboardY = (keyboard.getKeyDown(Key.W) * 1.0 - keyboard.getKeyDown(Key.S) * 1.0)
	#diagnostics.watch(keyboardX), diagnostics.watch(keyboardY)
	
	# Set Trackpad XY touch
	alvr.trackpad[rightControllerId][0] = touchX
	alvr.trackpad[rightControllerId][1] = touchY
	
	# Set Trackpad touch and click
	alvr.buttons[rightControllerId][alvr.Id("trackpad_touch")] = isTouch
	alvr.buttons[rightControllerId][alvr.Id("trackpad_click")] = isClick

	# Move virtual controller position by deltaTouch
	if ( isTouch ):
		controllerOffsetX += deltaTouchX * 0.25
		controllerOffsetZ += deltaTouchY * 0.50
	controllerOffsetX = clamp(controllerOffsetX, -0.3, 0.3)
	controllerOffsetY = clamp(controllerOffsetY, -0.3, 0.3)
	controllerOffsetZ = clamp(controllerOffsetZ,  0.0, 0.8)
	controllerLocalOffset = Vector3D(controllerOffsetX, controllerOffsetY, -controllerOffsetZ)
	
	# Clear controller position offset after some time of inactivity
	if (not isTouch and (time.time() - lastTouchTime) > 0.2):
		controllerOffsetX = lerp(controllerOffsetX, defaultArmX, 2.0 * deltaTime)
		controllerOffsetY = lerp(controllerOffsetY, defaultArmY, 2.0 * deltaTime)
		controllerOffsetZ = lerp(controllerOffsetZ, defaultArmZ, 2.0 * deltaTime)
	
	# Controller position and rotation override
	alvr.override_controller_orientation = True
	alvr.override_controller_position = True
	
	handPivotPosition = inputHeadPosition + armLocalPosition.rotateByEulerAngles(inputHeadRotation.x, inputHeadRotation.y, inputHeadRotation.z)
	handPosition = handPivotPosition + controllerLocalOffset.rotateByEulerAngles(inputControllerRotation.x, inputControllerRotation.y, inputControllerRotation.z)
	handLocalPosition = handPosition - inputHeadPosition
	#diagnostics.watch(controllerLocalX), diagnostics.watch(controllerLocalY),diagnostics.watch(controllerLocalZ)
	controllerRotation = inputControllerRotation

	alvr.controller_orientation[rightControllerId][0] = controllerRotation.x #lerp(alvr.controller_orientation[rightControllerId][0], controllerRotationX, deltaTime * 30)
	alvr.controller_orientation[rightControllerId][1] = controllerRotation.y #lerp(alvr.controller_orientation[rightControllerId][1], controllerRotationY, deltaTime * 30)
	alvr.controller_orientation[rightControllerId][2] = controllerRotation.z + math.radians(45) #lerp(alvr.controller_orientation[rightControllerId][2], controllerRotationZ, deltaTime * 30) #  + math.radians(45)
	
	t = deltaTime * 50
	alvr.controller_position[rightControllerId][0] = lerp(alvr.controller_position[rightControllerId][0], handPosition.x, t )
	alvr.controller_position[rightControllerId][1] = lerp(alvr.controller_position[rightControllerId][1], handPosition.y, t )
	alvr.controller_position[rightControllerId][2] = lerp(alvr.controller_position[rightControllerId][2], handPosition.z, t )
	
	alvr.override_head_position = True
	
	if (ARCoreCorrection):
		headToDisplayDistance = -0.25
	else:
		headToDisplayDistance = 0.0
	
	headPosition = inputHeadPosition - Vector3D(0,0,headToDisplayDistance).rotateByEulerAngles(inputHeadRotation.x, inputHeadRotation.y, inputHeadRotation.z)
	#diagnostics.watch(v[0]), diagnostics.watch(v[1]),diagnostics.watch(v[2])
	alvr.head_position[0] = headPosition.x
	alvr.head_position[1] = headPosition.y
	alvr.head_position[2] = headPosition.z
	
	# Hold touchpad down and pull the trigger to activate 'Grip' button
	triggerPulledNow = alvr.input_buttons[alvr.InputId("trigger")]
	
	triggerPulled = triggerPulledNow

	alvr.trigger[rightControllerId] = triggerPulled
	backClickNow = alvr.input_buttons[alvr.InputId("back")]
	if (backClickNow):
		backClickHoldTime += deltaTime
	else:
		backClickHoldTime = 0
		
	backClickDeltaTime = (time.time() - backClickTime) 
	backClickDouble = False
	if (backClickNow):
		if (not backClick):
			if (backClickDeltaTime < 0.5):
				backClickDouble = True
			
		backClickTime = time.time()
		backClick = True
	else:
		if (backClick and backClickHoldTime < 0.15):
			gripTriggerToggle = not gripTriggerToggle;
		backClick = False
	
	centerClick = False
	if (isClick and touchX > -0.3 and touchX < 0.3 and touchY > -0.3 and touchY < 0.3):
		#if (clickHoldTime > 0.2):
		centerClick = True
		isClick = False
		
	alvr.buttons[rightControllerId][alvr.Id("grip")] = backClick or keyboard.getKeyDown(Key.R)
	
	alvr.buttons[0][alvr.Id("system")] = backClickDouble
	#diagnostics.watch(systemButton)
	backClick = backClickNow
	if (centerClick):
		alvr.buttons[rightControllerId][alvr.Id("application_menu")] = True
	else:
		alvr.buttons[rightControllerId][alvr.Id("application_menu")] = False
	diagnostics.watch(gripTriggerToggle), diagnostics.watch(backClickDeltaTime), diagnostics.watch(backClick), diagnostics.watch(backClickHoldTime)
	diagnostics.watch(triggerPulled)