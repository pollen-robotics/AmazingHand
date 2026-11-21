# SPDX-License-Identifier: Apache-2.0
"""Eight simulated SCS0009 servos on a freshly allocated pseudo-terminal."""
import math
import os
import pty
import select
import threading

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
