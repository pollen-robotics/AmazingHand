#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Only opens a freshly allocated PTY; never accesses a physical serial device."""
import math
import os
import pty
import select
import signal
import subprocess
import threading
import time
import unittest

import actionlib
import rospy
import roslaunch
import rostest
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from controller_manager_msgs.srv import ListControllers
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint

STEP = math.radians(300) / 1024
MIDDLE = [3, 0, -5, -8, -2, 5, -12, 0]
NAMES = [finger + "_" + axis + "_level"
         for finger in ("index", "middle", "ring", "thumb")
         for axis in ("flexion", "abduction")]


class ServoBus:
    def __init__(self, side):
        self.master, self.slave = pty.openpty()
        self.path = os.ttyname(self.slave)
        self.ids = list(range(1, 9)) if side == 1 else [15, 16, 13, 14, 11, 12, 17, 18]
        ordered = sorted(self.ids)
        self.registers = {}
        for sid in self.ids:
            regs = bytearray(80)
            raw = int(math.radians(MIDDLE[ordered.index(sid)]) / STEP + 511)
            regs[56:58] = raw.to_bytes(2, "big")
            self.registers[sid] = regs
        self.running = True
        self.corrupt = False
        self.error = None
        self.writes = []
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        buffer = bytearray()
        try:
            while self.running:
                if not select.select([self.master], [], [], 0.05)[0]:
                    continue
                buffer.extend(os.read(self.master, 4096))
                while len(buffer) >= 4 and len(buffer) >= buffer[3] + 4:
                    length = buffer[3] + 4
                    packet = bytes(buffer[:length])
                    del buffer[:length]
                    assert packet[:2] == b"\xff\xff"
                    assert sum(packet[2:]) & 255 == 255
                    sid, instruction = packet[2], packet[4]
                    params = packet[5:-1]
                    if instruction == 2:
                        address, size = params
                        reply = bytearray([255, 255, sid, size + 2, 0])
                        reply.extend(self.registers[sid][address:address+size])
                        reply.append((~sum(reply[2:])) & 255)
                        if self.corrupt:
                            reply[-1] ^= 1
                        os.write(self.master, reply)
                    elif instruction == 131:
                        assert sid == 254
                        address, size = params[:2]
                        for start in range(2, len(params), size + 1):
                            motor = params[start]
                            data = params[start+1:start+1+size]
                            self.registers[motor][address:address+size] = data
                            self.writes.append((motor, address, bytes(data)))
                            if address == 42:
                                self.registers[motor][56:58] = data
                    else:
                        raise AssertionError("Unexpected instruction")
        except Exception as error:
            self.error = error

    def close(self):
        self.running = False
        self.thread.join(2)
        os.close(self.master)
        os.close(self.slave)


class DriverIntegration(unittest.TestCase):
    def exercise(self, side, fault=False):
        bus = ServoBus(side)
        driver = None
        subscription = None
        states = []
        namespace = "/amazing_hand" if side == 1 else "/robot/left_hand"
        controller = "position_joint_trajectory_controller"
        try:
            # Exercise the actual launch file, including parameters and spawner.
            driver = subprocess.Popen([
                "roslaunch", "amazing_hand_ros", "amazing_hand.launch",
                "port:=" + bus.path, "side:=" + str(side),
                "middle_pos:=" + str(MIDDLE), "serial_timeout:=0.1",
            ] + ([] if side == 1 else ["namespace:=" + namespace]))
            rospy.wait_for_service(namespace + "/controller_manager/list_controllers", timeout=10)
            subscription = rospy.Subscriber(namespace + "/joint_states", JointState, states.append)
            client = actionlib.SimpleActionClient(
                namespace + "/" + controller + "/follow_joint_trajectory",
                FollowJointTrajectoryAction)
            self.assertTrue(client.wait_for_server(rospy.Duration(5)))
            list_controllers = rospy.ServiceProxy(
                namespace + "/controller_manager/list_controllers", ListControllers)
            self.assertEqual({c.name: c.state for c in list_controllers().controller},
                             {"joint_state_controller": "running", controller: "running"})
            topics = dict(rospy.get_published_topics())
            self.assertNotIn("/joint_states", topics)
            self.assertNotIn("/" + controller + "/state", topics)
            self.assertIn(namespace + "/robot_description", rospy.get_param_names())
            self.assertFalse(rospy.has_param("/robot_description"))
            # First target write must hold exact feedback, before torque is enabled.
            for sid in bus.ids:
                writes = [(addr, data) for motor, addr, data in bus.writes if motor == sid]
                self.assertEqual(writes[0][0], 42)
                self.assertEqual(writes[1:4], [(44, b"\0\0"), (46, (586).to_bytes(2, "big")), (40, b"\1")])
            target = [0.6, 0.2, 0.5, -0.2, 0.7, 0.1, 0.4, -0.1]
            goal = FollowJointTrajectoryGoal()
            goal.trajectory.joint_names = NAMES
            point = JointTrajectoryPoint()
            point.positions = target
            point.time_from_start = rospy.Duration(1.0)
            goal.trajectory.points = [point]
            client.send_goal(goal)
            self.assertTrue(client.wait_for_result(rospy.Duration(5)))
            self.assertEqual(client.get_result().error_code, 0)
            self.assertTrue(states)
            measured = dict(zip(states[-1].name, states[-1].position))
            for name, expected in zip(NAMES, target):
                self.assertAlmostEqual(measured[name], expected, delta=0.007)
            # Validate real wire targets, including left-hand ID/calibration permutation.
            for index, sid in enumerate(bus.ids):
                finger = index // 2
                difference = -45 + 135 * target[2*finger]
                total = 47 * target[2*finger+1]
                angle = (difference if index % 2 == 0 else -difference) + total
                angle += MIDDLE[sorted(bus.ids).index(sid)]
                expected = int(math.radians(angle) / STEP + 511)
                raw = int.from_bytes(bus.registers[sid][42:44], "big")
                self.assertLessEqual(abs(raw - expected), 1)
            if fault:
                bus.corrupt = True
                self.assertEqual(driver.wait(timeout=5), 1)
            else:
                driver.send_signal(signal.SIGINT)
                self.assertEqual(driver.wait(timeout=5), 0)
            time.sleep(0.1)
            for sid in bus.ids:
                self.assertEqual(bus.registers[sid][40], 0)
            self.assertIsNone(bus.error)
        finally:
            if subscription:
                subscription.unregister()
            if driver and driver.poll() is None:
                driver.send_signal(signal.SIGINT)
                try:
                    driver.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    driver.kill()
                    driver.wait()
            bus.close()

    def test_launch_servo_mapping(self):
        # Parse the real launch file without starting nodes or opening a device.
        # roslaunch eval converts numeric arg strings to integers automatically.
        launch = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                              "launch", "amazing_hand.launch")
        calibration = [35, -10, 30, -33, 30, -30, 30, -20]
        cases = [
            ([], 1, list(range(1, 9))),
            (["side:=1"], 1, list(range(1, 9))),
            (["side:=2"], 2, [15, 16, 13, 14, 11, 12, 17, 18]),
            (["side:=2", "servo_ids:=[1,2,3,4,5,6,7,8]"], 2, list(range(1, 9))),
        ]
        for namespace_args, namespace in [([], "/amazing_hand"),
                                          (["namespace:=robot/left_hand"], "/robot/left_hand")]:
            for args, side, ids in cases:
                config = roslaunch.config.ROSLaunchConfig()
                roslaunch.xmlloader.XmlLoader().load(
                    launch, config, argv=["middle_pos:=" + str(calibration)] + args + namespace_args,
                    verbose=False)
                private = namespace + "/amazing_hand/"
                self.assertEqual(config.params[private + "side"].value, side)
                self.assertEqual(config.params[private + "servo_ids"].value, ids)
                self.assertEqual(config.params[private + "middle_pos"].value, calibration)
                self.assertIn(namespace + "/robot_description", config.params)
                self.assertIn(namespace + "/position_joint_trajectory_controller/type", config.params)
                self.assertTrue(all(key.startswith(namespace + "/") for key in config.params))
                self.assertTrue(all(node.namespace == namespace + "/" for node in config.nodes))
                spawner = next(node for node in config.nodes if node.name == "controller_spawner")
                self.assertEqual(spawner.args,
                                 "joint_state_controller position_joint_trajectory_controller")

    def test_right(self):
        self.exercise(1)

    def test_left(self):
        self.exercise(2)

    def test_checksum_fault(self):
        self.exercise(1, fault=True)


if __name__ == "__main__":
    rospy.init_node("driver_integration_test")
    rostest.rosrun("amazing_hand_ros", "driver_integration", DriverIntegration)
