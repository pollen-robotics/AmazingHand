import time
import numpy as np

from rustypot import Scs0009PyController

# Servo IDs and calibrated middle positions per finger
# Fill in MiddlePos_1 / MiddlePos_2 with the values you calibrated for each finger
FINGERS = {
    1: {"ID_1": 1, "ID_2": 2, "MiddlePos_1": -5, "MiddlePos_2": -3},
    2: {"ID_1": 3, "ID_2": 4, "MiddlePos_1": -5, "MiddlePos_2": -10},
    3: {"ID_1": 5, "ID_2": 6, "MiddlePos_1": 2, "MiddlePos_2": -4},
    4: {"ID_1": 7, "ID_2": 8, "MiddlePos_1": -10, "MiddlePos_2": 8},
}

c = Scs0009PyController(
    serial_port="COM3",
    baudrate=1000000,
    timeout=0.5,
)


def enable_torque(finger):
    data = FINGERS[finger]
    c.write_torque_enable(data["ID_1"], 1)
    c.write_torque_enable(data["ID_2"], 1)


def servo_in_middle(finger):
    data = FINGERS[finger]
    c.write_goal_speed(data["ID_1"], 6)
    c.write_goal_speed(data["ID_2"], 6)
    Pos_1 = np.deg2rad(data["MiddlePos_1"])
    Pos_2 = np.deg2rad(data["MiddlePos_2"])
    c.write_goal_position(data["ID_1"], Pos_1)
    c.write_goal_position(data["ID_2"], Pos_2)
    time.sleep(0.01)


def main():
    choice = input("Which finger? (1-4, or 'a' for all): ").strip().lower()

    if choice == "a":
        targets = [1, 2, 3, 4]
    elif choice in ("1", "2", "3", "4"):
        targets = [int(choice)]
    else:
        print("Invalid input.")
        return

    for finger in targets:
        enable_torque(finger)

    while True:
        for finger in targets:
            servo_in_middle(finger)
        time.sleep(3)


if __name__ == '__main__':
    main()
