# amazing_hand_ros

A ROS 1 driver for AmazingHand with eight Feetech SCS0009 servos.
It uses ros_control to accept finger trajectories and publish measured finger states.

Each of the four fingers has two controls: **flexion** (bending) and
**abduction** (sideways motion). Commands use normalized levels rather than
motor angles or anatomical joint angles.

The driver is written in C++. You can use it without running the Python demo first.

## 1. Build the package

You need a Linux system with ROS 1, a catkin workspace, and `catkin_tools`.
Place the AmazingHand repository in the workspace's `src` directory, so this
package is located at `src/AmazingHand/amazing_hand_ros`.

Source your ROS 1 installation, then run the following from the workspace root:

```bash
# Use the setup file for your ROS 1 installation.
# Examples: /opt/ros/noetic/setup.bash or /opt/ros/one/setup.bash
source /path/to/ros1/setup.bash

rosdep install --from-paths src/AmazingHand/amazing_hand_ros --ignore-src -r -y
catkin build amazing_hand_ros
source devel/setup.bash
```

## 2. Prepare the hand and calibration

Connect the assembled hand to a compatible serial bus adapter and its external
power supply. Identify the adapter's device path, such as `/dev/ttyACM0`, and
make sure your user can read and write it. Stop any Python demo or other program
using that port before starting the driver.

The servos must already have unique IDs and a common baud rate (1,000,000 by
default). This driver does not configure servo IDs or EEPROM settings.

### If you have used PythonExample

Use the **calibrated values for your own hand** from `MiddlePos` in
`AmazingHand_Demo.py` as the `middle_pos` launch argument. Keep the values in
degrees and in ascending physical servo ID order.

Regardless of how you set up PythonExample, run this driver from a terminal
with your ROS 1 installation and catkin workspace sourced as shown above.

### If this is your first time using AmazingHand

Complete the hand's assembly, servo ID setup, and middle-position calibration
before launching the driver. See the upstream
[AmazingHand assembly guide](../docs/AmazingHand_Assembly.pdf) and
[PythonExample servo ID setup notes](../PythonExample/README.md).

The upstream
[middle-position calibration script](../PythonExample/AmazingHand_Hand_FingerMiddlePos.py)
is a helper for commanding one servo pair to chosen calibration angles.
It is **not automatic calibration**: set its serial port, servo IDs, and
`MiddlePos_1` / `MiddlePos_2` for the pair being calibrated, following the assembly
guide. The linked setup notes cover servo configuration, not Python installation.
Prepare a Python environment that can run the helper before using it. Running it
moves the selected motors.

Record the eight servo angles, in degrees, that correspond to the calibrated
middle pose. These become `middle_pos`. They are offsets from the servo's angle
origin, not raw encoder counts. In this driver's conversion, encoder count 511
is 0°, and one count is 300/1024°. Do not substitute another hand's calibration
or assume that all eight values are zero.

### Choose the servo mapping

| Launch setting | Index motors | Middle motors | Ring motors | Thumb motors | Order of `middle_pos` |
| --- | --- | --- | --- | --- | --- |
| `side:=1` (right, default) | 1, 2 | 3, 4 | 5, 6 | 7, 8 | IDs 1 through 8 |
| `side:=2` (left) | 15, 16 | 13, 14 | 11, 12 | 17, 18 | IDs 11 through 18 |

For a different mapping, set `servo_ids` in this order:
index motor 1, index motor 2, middle motor 1, middle motor 2, ring motor 1,
ring motor 2, thumb motor 1, thumb motor 2.

For example, a left hand whose motors use IDs 1 through 8 in that logical order
can use:

```text
side:=2 servo_ids:='[1,2,3,4,5,6,7,8]'
```

Even with a custom mapping, `middle_pos` is always ordered by **ascending physical
ID**, not by the order of `servo_ids`. The `side` argument selects the default ID
mapping; it does not reverse the abduction sign.

## 3. Start the driver

From a terminal with the workspace sourced, launch the driver with your
calibration. The numbers below illustrate the syntax; **replace them with your
hand's values**.

```bash
roslaunch amazing_hand_ros amazing_hand.launch \
  port:=/dev/ttyACM0 \
  middle_pos:='[3, 0, -5, -8, -2, 5, -12, 0]'
```

When launched at the ROS root namespace, all hand interfaces are placed under
`/amazing_hand` by default. Use the
`namespace` argument to choose a different namespace, for example:

```bash
roslaunch amazing_hand_ros amazing_hand.launch \
  namespace:=robot/left_hand side:=2 port:=/dev/ttyACM0 \
  middle_pos:='[3, 0, -5, -8, -2, 5, -12, 0]'
```

Replace the calibration values and port with those for that hand. With this
namespace, feedback is published on `/robot/left_hand/joint_states` and the action
is `/robot/left_hand/position_joint_trajectory_controller/follow_joint_trajectory`.
Update the topic and action names in the examples below accordingly.
`robot_description`, controller parameters, and controller_manager services are
also scoped to the selected namespace. The driver node is named `amazing_hand`,
so its private parameters are under `<namespace>/amazing_hand/`.
A relative `namespace` is resolved within any enclosing launch group; a leading
`/` makes it absolute. Joint names inside messages and the URDF are unchanged by
the namespace.

Add `side:=2` for the default left-hand mapping, or `servo_ids:=...` for a custom
mapping. `middle_pos` is required and has no default.

At startup, the driver reads all eight positions and checks their limits.
It then sets the measured encoder positions as hold targets, sets goal time to
zero and the configured motor speed, enables torque, and reads back the torque
enable registers. It does not command an open or closed pose automatically, but
enabling torque and subsequent position control can move the fingers. An initial
pose outside either the level or motor limits prevents startup, allowing a small
encoder-quantization margin; check calibration, ID mapping, and the starting pose.

The launch file starts the joint-state and trajectory controllers. In another
terminal, source the same workspace and inspect feedback:

```bash
source devel/setup.bash
rostopic echo -n 1 /amazing_hand/joint_states
```

Press Ctrl-C in the launch terminal to stop. By default, the driver sends a
torque-disable command on normal shutdown. This command has no acknowledgment;
delivery is not guaranteed if communication has failed.

## 4. Send a finger trajectory

Each finger exposes two joint names:

| Joint name | Command range | Meaning |
| --- | --- | --- |
| `<finger>_flexion_level` | 0 to 1 | Increasing values bend the finger |
| `<finger>_abduction_level` | -1 to 1 | Signed sideways motion; 0 is centered |

Replace `<finger>` with `index`, `middle`, `ring`, or `thumb`.
These values are **dimensionless levels, not radians**. Specify all eight joints;
partial-joint goals are disabled.

Save this example as `move_hand.py`. With the driver running, execute
`python3 move_hand.py` in a terminal with the workspace sourced.
**It commands all four fingers** to flexion 0.6 and centered abduction with a
three-second trajectory. Actual arrival depends on motor speed, load, and tracking
error. Allow more time for larger motions.

```python
#!/usr/bin/env python3
import actionlib
import rospy
from actionlib_msgs.msg import GoalStatus
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from trajectory_msgs.msg import JointTrajectoryPoint

rospy.init_node("hand_command")
client = actionlib.SimpleActionClient(
    "/amazing_hand/position_joint_trajectory_controller/follow_joint_trajectory",
    FollowJointTrajectoryAction,
)
if not client.wait_for_server(rospy.Duration(10.0)):
    raise RuntimeError("Hand trajectory controller is not available")

goal = FollowJointTrajectoryGoal()
goal.trajectory.joint_names = [
    finger + "_" + axis + "_level"
    for finger in ("index", "middle", "ring", "thumb")
    for axis in ("flexion", "abduction")
]
point = JointTrajectoryPoint()
point.positions = [0.6, 0.0] * 4
point.time_from_start = rospy.Duration(3.0)
goal.trajectory.points = [point]

client.send_goal(goal)
if not client.wait_for_result(rospy.Duration(10.0)):
    client.cancel_goal()
    raise RuntimeError("Timed out waiting for the hand trajectory")

result = client.get_result()
if client.get_state() != GoalStatus.SUCCEEDED:
    raise RuntimeError("Trajectory did not succeed: " + client.get_goal_status_text())
if result is None:
    raise RuntimeError("Controller returned no trajectory result")
if result.error_code != result.SUCCESSFUL:
    raise RuntimeError(
        "Trajectory failed: {} ({})".format(result.error_string, result.error_code)
    )
print("Trajectory completed")
```

Not every combination of flexion and abduction is reachable. In particular,
avoid combining full flexion with full sideways motion. The next section explains
the coordinate definition and motor limits.

## 5. Understand levels and reachable poses

AmazingHand uses two motors per finger in a parallel mechanism. This driver
represents their difference and sum as flexion and abduction levels; it does not
solve the mechanism's anatomical joint angles.

Let `a` and `b` be the two motor angles **in degrees after subtracting their
middle_pos offsets**:

```text
flexion_level   = ((a - b) / 2 + 45) / 135
abduction_level =  (a + b) / (2 * 47)

a = -45 + 135 * flexion_level + 47 * abduction_level
b =  45 - 135 * flexion_level + 47 * abduction_level
```

Useful reference poses for one finger:

| Pose | Motor angles (a, b) | Flexion | Abduction |
| --- | --- | --- | --- |
| Maximum extension in the level range | (-45°, +45°) | 0 | 0 |
| Open pose used by PythonExample's `OpenHand` | (-35°, +35°) | 10/135 ≈ 0.0741 | 0 |
| Calibrated middle pose | (0°, 0°) | 1/3 | 0 |
| Closed pose used by `CloseHand` | (+90°, -90°) | 1 | 0 |
| A sideways pose used by `SpreadHand` | (+4°, +90°) | 2/135 ≈ 0.0148 | +1 |

Flexion 0 includes poses more extended than the demo's `OpenHand`.
The sideways scale of 47° corresponds to half the motor-angle sum in the last row.
Positive abduction follows the motor-angle sum, so its physical direction depends
on the finger and hand; it does not universally mean "spread away from the middle
finger."

### Command limits and feedback

Commands are first clamped to the level ranges, then each calibrated motor angle
is clamped to `motor_min_deg` / `motor_max_deg` (default: -90° / +90°).

With the default motor limits, a pair of levels `f` (flexion, 0 to 1) and `s`
(abduction, -1 to 1) is within both motor limits exactly when:

```text
abs(-45 + 135*f) + abs(47*s) <= 90
```

This describes the software motor-angle limits, not a guarantee that the physical
mechanism can attain every such pose under load or without interference.

For example, `f=1, s=1` exceeds the motor limits. The driver warns when a command
is clamped. If the resulting pose violates the trajectory controller's tolerances,
the action fails rather than reporting successful arrival at the requested pose.

`/amazing_hand/joint_states` reports transformed **measured** positions without clamping, so
feedback can lie outside the command ranges. Its units are:

| Field | Units / behavior |
| --- | --- |
| Position | Dimensionless level |
| Velocity | Level/s, estimated from position differences |
| Effort | Always 0; not measured |
| Trajectory acceleration, if supplied | Level/s² |

The motor's goal-speed setting is programmed from `goal_speed` in rad/s; it is not
a measured or guaranteed speed. Trajectory timing sets the requested rate of
motion in level space. The URDF velocity limits are descriptive and are
not enforced as software velocity or acceleration limiters by this driver.

## 6. Configuration and ROS interfaces

The `namespace` argument controls launch name resolution; it is not a private
node parameter. The remaining arguments are loaded as private parameters of the
`amazing_hand` node, for example `/amazing_hand/amazing_hand/middle_pos` with the
default namespace. They are read at startup; restart the driver after changing
them.

| Argument | Default | Description |
| --- | --- | --- |
| `namespace` | `amazing_hand` | Namespace for all hand nodes, controllers, topics, and parameters |
| `middle_pos` | Required | Eight calibration angles in degrees, ascending physical ID order |
| `side` | `1` | Default ID mapping: 1 = right, 2 = left |
| `servo_ids` | Selected by `side` | Eight unique IDs from 0 to 253 in finger/motor order |
| `port` | `/dev/ttyACM0` | Serial device |
| `baudrate` | `1000000` | Host serial baud rate; must match the servos |
| `serial_timeout` | `0.05` | Timeout in seconds, separately for sending a packet and receiving its complete reply; greater than 0 and at most 5 |
| `control_rate` | `50` | Target read/update/write frequency in Hz; greater than 0 and at most 1000 |
| `goal_speed` | `3.0` | Requested motor speed setting in rad/s; must encode to a nonzero supported register value |
| `motor_min_deg` | `-90` | Lower motor-angle limit relative to calibration |
| `motor_max_deg` | `90` | Upper motor-angle limit relative to calibration |
| `disable_torque_on_shutdown` | `true` | Disable torque on normal shutdown |

Calibration values and motor limits must also keep every absolute motor target
within the encoder range (counts 0 through 1023).

Supported host baud rates are 1000000, 500000, 115200, 57600, 38400, and 19200.
Servos must respond to READ instructions. The driver does not change their
baud rate or response settings. It uses READ for feedback and broadcast
SyncWrite for commands, so it does not require acknowledgments for individual
write instructions.

The following names assume the default namespace at the ROS root:

| Interface | ROS name | Type / purpose |
| --- | --- | --- |
| Measured state | `/amazing_hand/joint_states` | `sensor_msgs/JointState` |
| Trajectory action | `/amazing_hand/position_joint_trajectory_controller/follow_joint_trajectory` | `control_msgs/FollowJointTrajectoryAction` |
| Trajectory topic | `/amazing_hand/position_joint_trajectory_controller/command` | `trajectory_msgs/JointTrajectory` |
| Controller feedback | `/amazing_hand/position_joint_trajectory_controller/state` | `control_msgs/JointTrajectoryControllerState` |
| Controller management | `/amazing_hand/controller_manager/*` | Load, start, stop, and inspect controllers |

Use the action interface when you need completion or failure feedback.
Controller rates and trajectory tolerances are set in
[config/controllers.yaml](config/controllers.yaml).

## 7. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Cannot open or lock the serial port | Device path, user permissions, and other programs using the port |
| Serial timeout | Hand power, adapter connection, servo IDs, baud rate, and READ response settings |
| Initial pose outside configured limits | `middle_pos` values and ordering, `servo_ids` mapping, and the hand's starting pose |
| Command saturation warning | The combined flexion/abduction target and configured motor limits |
| Trajectory tolerance failure | Reachable target, sufficient trajectory duration, motor speed, and controller tolerances |

During operation, communication errors, invalid replies, servo error flags, or
non-finite commands stop the control loop. The driver attempts to disable torque
and exits. Because the driver is a required node, its failure shuts down the
entire containing roslaunch, including other nodes if this launch is included in
a larger robot launch. It does not reconnect automatically.
A disconnected bus can prevent the torque-disable command from reaching the hand.

Position reads are sequential, while target positions are sent together using
SyncWrite. Communication errors include the operation and register address;
READ errors also identify the servo ID. Serial latency can reduce the actual
loop rate below `control_rate`; this is not a hard-real-time driver.

## 8. URDF and transmission details

The [URDF](urdf/amazing_hand.urdf.xacro) contains nine empty links, eight level
joints, and four transmissions. It has no visual or collision geometry.
The joints use the URDF `revolute` type to expose bounded coordinates, but their
values are levels: this model is not a geometric representation of the hand and
should not be used to infer physical link poses or collisions.

Each finger uses the standard
`transmission_interface/DifferentialTransmission` with:

| Parameter | Value |
| --- | --- |
| Actuator reductions | `[1, -1]` |
| Joint reductions | `[135*pi/180, 47*pi/180]` |
| Joint offsets | `[45/135, 0]` |

The driver loads these transmissions from the URDF for both feedback and command
conversion. Actuator positions entering the transmission are calibrated radians;
the driver subtracts `middle_pos` before feedback conversion and adds it back
after command conversion. No custom transmission plugin is required.

The hardware exposes `hardware_interface::PositionJointInterface`.
The launch file loads `joint_state_controller/JointStateController` and
`position_controllers/JointTrajectoryController`.

## 9. Test without a hand

From the workspace root:

```bash
source devel/setup.bash
catkin run_tests amazing_hand_ros
catkin_test_results build/amazing_hand_ros/test_results
```

Tests use generated pseudo-terminals, not physical serial devices. They cover
packet validation, unit conversion, URDF transmission conversion, serial timeouts,
both hand mappings, default and custom launch namespaces, trajectory execution,
state feedback, shutdown, and
communication-fault handling. These checks do not replace validation on hardware.

To inspect launch parameters without starting the driver:

```bash
roslaunch --dump-params amazing_hand_ros amazing_hand.launch \
  middle_pos:='[3,0,-5,-8,-2,5,-12,0]'
```

## License and protocol source

This package is licensed under [Apache-2.0](LICENSE). Its minimal SCS0009 protocol
implementation adapts position/speed conversion, READ, and SyncWrite from
[rustypot](https://github.com/pollen-robotics/rustypot).
See [NOTICE](NOTICE) for attribution and the source revision.
