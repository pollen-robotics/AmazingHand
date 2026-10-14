// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <chrono>
#include <cstdint>
#include <string>
#include <vector>

namespace amazing_hand_ros {
using Bytes = std::vector<uint8_t>;
constexpr double kPi = 3.14159265358979323846;
constexpr double kStep = (300.0 * kPi / 180.0) / 1024.0;
Bytes packet(uint8_t id, uint8_t instruction, const Bytes& parameters);
Bytes parseStatus(const Bytes& data, uint8_t id, std::size_t size);
uint16_t positionRaw(double radians);
double positionRadians(uint16_t raw);
uint16_t speedRaw(double radians_per_second);
Bytes word(uint16_t value);

// Minimal protocol-v1/SCS0009 subset. Single-threaded bus ownership.
class Scs0009 {
 public:
  Scs0009(const std::string& port, int baudrate, double timeout);
  ~Scs0009();
  Scs0009(const Scs0009&) = delete;
  Scs0009& operator=(const Scs0009&) = delete;
  Bytes readRegister(uint8_t id, uint8_t address, uint8_t size);
  void syncWrite(const std::vector<int>& ids, uint8_t address,
                 const std::vector<Bytes>& values);
 private:
  using Clock = std::chrono::steady_clock;
  void wait(short events, Clock::time_point deadline);
  void send(const Bytes& data);
  uint8_t receive(Clock::time_point deadline);
  int fd_ = -1;
  double timeout_;
};
}  // namespace amazing_hand_ros
