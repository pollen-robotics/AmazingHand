"""Finger poses and command-line options shared by the hand motion demos."""
import argparse

JOINT_NAMES = [f"{finger}_{motion}_level"
               for finger in ("index", "middle", "ring", "thumb")
               for motion in ("flexion", "abduction")]


def options(argv):
    parser = argparse.ArgumentParser(description="Run one gesture sequence with the hand driver.")
    parser.add_argument("--side", type=int, choices=(1, 2), default=1,
                        help="match the driver's side (1 = right, 2 = left)")
    parser.add_argument("--namespace", default="/amazing_hand", help="hand driver namespace")
    return parser.parse_args(argv)


def poses(side):
    """Yield a gesture name, its duration in seconds, and four (flexion, abduction) pairs."""
    opened = (0.075, 0.0)
    closed = (1.0, 0.0)
    open_hand = [opened] * 4
    fist = [closed] * 4
    # Mirror sideways gestures in motor-sum coordinates on the left hand.
    sign = 1.0 if side == 1 else -1.0
    point = [opened, closed, closed, closed]
    victory = [(0.04, 0.53 * sign), (0.04, -0.53 * sign), closed, closed]

    yield "Open", 2.0, open_hand
    yield "Close", 2.0, fist
    for count in range(1, 5):
        yield "Open finger by finger", 1.5, open_hand[:count] + fist[count:]
    yield "Spread", 2.0, [(0.04, sign), opened, (0.04, -sign), (0.04, -sign)]
    yield "Bring fingers together", 3.2, [(0.11, -0.64 * sign), opened,
                                          (0.08, 0.74 * sign), (0.02, 0.91 * sign)]
    yield "Open", 1.8, open_hand
    yield "Point", 2.0, point
    for _ in range(3):
        yield "Wag index", 2.4, [(0.02, 0.74 * sign), closed, closed, closed]
        yield "Wag index", 2.4, [(0.02, -0.74 * sign), closed, closed, closed]
    yield "Open", 2.0, open_hand
    yield "OK", 1.5, [(0.70, 0.0), (0.33, 0.0), (0.19, 0.0), (0.53, 0.82 * sign)]
    yield "Open", 1.5, open_hand
    yield "Victory", 2.0, victory
    for _ in range(3):
        yield "Scissors", 1.5, [(0.075, -0.32 * sign), (0.075, 0.32 * sign), closed, closed]
        yield "Scissors", 1.5, victory
    yield "Open", 2.0, open_hand
    yield "Pinch", 2.0, [closed, closed, closed, (0.61, -0.80 * sign)]
    yield "Open", 2.0, open_hand
