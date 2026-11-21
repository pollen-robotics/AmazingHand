# SPDX-License-Identifier: Apache-2.0
import math
import os
import signal
import subprocess
import time

import yaml
import pytest
import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint

from servo_bus import MIDDLE, NAMES, STEP, ServoBus


@pytest.mark.parametrize("side,hand,first_id", [(1, "right_hand", 1), (2, "left_hand", 11)])
def test_hardware_requires_explicit_calibration(side, hand, first_id, tmp_path):
    config = tmp_path / ".config" / "amazing_hand_ros"
    config.mkdir(parents=True)
    (config / (hand + ".yaml")).write_text(yaml.safe_dump(dict(enumerate(MIDDLE, first_id))))
    # Generate the hardware description only. A legacy file must never satisfy
    # the requirement to supply the connected hand's calibration.
    result = subprocess.run([
        "ros2", "run", "amazing_hand_driver", "hand_description",
        str(side), "", "[]", "50", "amazing_hand", "false", "/unused",
        "1000000", "0.05", "3", "-90", "90", "true",
    ], env=dict(os.environ, HOME=str(tmp_path)), capture_output=True, text=True)
    assert result.returncode != 0
    assert "explicit middle_pos" in result.stderr


@pytest.mark.parametrize("side,namespace", [(1, "amazing_hand"), (2, "robot/left_hand")])
def test_trajectory(side, namespace, tmp_path):
    bus = ServoBus(side)
    rclpy.init()
    node = rclpy.create_node("hand_test")
    feedback = {}
    node.create_subscription(JointState, f"/{namespace}/joint_states",
                             lambda msg: feedback.update(zip(msg.name, msg.position)), 10)
    client = ActionClient(node, FollowJointTrajectory,
                          f"/{namespace}/position_joint_trajectory_controller/follow_joint_trajectory")
    env = dict(os.environ, ROS_LOG_DIR=str(tmp_path))
    process = subprocess.Popen([
        "ros2", "launch", "amazing_hand_driver", "amazing_hand.launch.xml",
        "port:=" + bus.path, "serial_timeout:=0.15", "middle_pos:=" + str(MIDDLE),
        f"side:={side}", f"namespace:={namespace}",
    ], start_new_session=True, env=env)
    try:
        assert client.wait_for_server(timeout_sec=25)
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = NAMES
        target = [0.6, 0.2, 0.5, -0.2, 0.7, 0.1, 0.4, -0.1]
        point = JointTrajectoryPoint(positions=target)
        point.time_from_start.sec = 1
        goal.trajectory.points = [point]
        sent = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, sent, timeout_sec=5)
        assert sent.done() and sent.result().accepted
        result = sent.result().get_result_async()
        rclpy.spin_until_future_complete(node, result, timeout_sec=8)
        assert result.done() and result.result().result.error_code == 0
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            if all(abs(feedback.get(n, -2) - v) < 0.007 for n, v in zip(NAMES, target)):
                break
        assert [feedback[n] for n in NAMES] == pytest.approx(target, abs=0.007)
        for i, sid in enumerate(bus.ids):
            flex, abd = target[i//2*2:i//2*2+2]
            angle = (-45 + 135*flex) * (1 if i % 2 == 0 else -1) + 47*abd
            angle += MIDDLE[sorted(bus.ids).index(sid)]
            raw = int.from_bytes(bus.registers[sid][42:44], "big")
            assert abs(raw - int(math.radians(angle) / STEP + 511)) <= 1
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(12)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        node.destroy_node()
        rclpy.shutdown()
        bus.close()
    assert bus.error is None
    assert all(bus.registers[sid][40] == 0 for sid in bus.ids)
