// SPDX-License-Identifier: Apache-2.0
// SCS0009 register conversions and protocol subset adapted from rustypot;
// see NOTICE for source revision and attribution.
#include <amazing_hand_ros/scs0009.h>
#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <stdexcept>
#include <sys/file.h>
#include <termios.h>
#include <unistd.h>

namespace amazing_hand_ros {
namespace {
void fail(const std::string& operation) {
  throw std::runtime_error(operation + ": " + std::strerror(errno));
}
uint8_t checksum(const Bytes& data, std::size_t end) {
  uint8_t sum = 0;
  for (std::size_t i = 2; i < end; ++i) sum += data[i];
  return static_cast<uint8_t>(~sum);
}
}
Bytes packet(uint8_t id, uint8_t instruction, const Bytes& parameters) {
  if (id > 254 || parameters.size() > 253) throw std::invalid_argument("Invalid packet size/ID");
  Bytes result{255, 255, id, static_cast<uint8_t>(parameters.size() + 2), instruction};
  result.insert(result.end(), parameters.begin(), parameters.end());
  result.push_back(checksum(result, result.size()));
  return result;
}
Bytes parseStatus(const Bytes& data, uint8_t id, std::size_t size) {
  if (data.size() != size + 6 || data[0] != 255 || data[1] != 255 ||
      data[2] != id || data[3] != size + 2)
    throw std::runtime_error("Malformed status packet for servo " + std::to_string(id));
  if (checksum(data, data.size() - 1) != data.back())
    throw std::runtime_error("Status checksum error for servo " + std::to_string(id));
  if (data[4] != 0)
    throw std::runtime_error("Servo " + std::to_string(id) + " error bits: " + std::to_string(data[4]));
  return Bytes(data.begin() + 5, data.end() - 1);
}
uint16_t positionRaw(double radians) {
  const double raw = radians / kStep + 511.0;
  if (!std::isfinite(raw) || raw < 0 || raw > 1023)
    throw std::invalid_argument("Position outside SCS0009 encoder range");
  return static_cast<uint16_t>(raw);  // rustypot truncates, rather than rounds
}
double positionRadians(uint16_t raw) {
  if (raw > 1023) throw std::runtime_error("Invalid SCS0009 position word");
  return (static_cast<int>(raw) - 511) * kStep;
}
uint16_t speedRaw(double speed) {
  const double raw = speed / kStep;
  if (!std::isfinite(raw) || raw < 1 || raw > 32767)
    throw std::invalid_argument("goal_speed must be positive and representable (zero means unlimited)");
  return static_cast<uint16_t>(raw);
}
Bytes word(uint16_t value) {
  return {static_cast<uint8_t>(value >> 8), static_cast<uint8_t>(value & 255)};
}
Scs0009::Scs0009(const std::string& port, int baudrate, double timeout) : timeout_(timeout) {
  if (!std::isfinite(timeout) || timeout <= 0 || timeout > 5)
    throw std::invalid_argument("serial_timeout must be in (0, 5] seconds");
  speed_t speed;
  switch (baudrate) {
    case 1000000: speed = B1000000; break;
    case 500000: speed = B500000; break;
    case 115200: speed = B115200; break;
    case 57600: speed = B57600; break;
    case 38400: speed = B38400; break;
    case 19200: speed = B19200; break;
    default: throw std::invalid_argument("Unsupported host baudrate");
  }
  fd_ = ::open(port.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK | O_CLOEXEC);
  if (fd_ < 0) fail("open " + port);
  try {
    if (flock(fd_, LOCK_EX | LOCK_NB) < 0) fail("lock serial port");
    termios config{};
    if (tcgetattr(fd_, &config) < 0) fail("tcgetattr");
    cfmakeraw(&config);
    config.c_cflag |= CLOCAL | CREAD;
    config.c_cflag &= ~(CSTOPB | PARENB | CRTSCTS);
    config.c_cc[VMIN] = 0;
    config.c_cc[VTIME] = 0;
    if (cfsetispeed(&config, speed) < 0 || cfsetospeed(&config, speed) < 0 ||
        tcsetattr(fd_, TCSANOW, &config) < 0) fail("configure serial port");
    if (tcflush(fd_, TCIOFLUSH) < 0) fail("tcflush");
  } catch (...) { ::close(fd_); fd_ = -1; throw; }
}
Scs0009::~Scs0009() { if (fd_ >= 0) ::close(fd_); }
void Scs0009::wait(short events, Clock::time_point deadline) {
  for (;;) {
    const auto left = std::chrono::duration<double, std::milli>(deadline - Clock::now()).count();
    if (left <= 0) throw std::runtime_error("Serial transaction timeout");
    pollfd descriptor{fd_, events, 0};
    const int result = ::poll(&descriptor, 1, static_cast<int>(std::ceil(left)));
    if (result < 0) { if (errno == EINTR) continue; fail("poll"); }
    if (result == 0) throw std::runtime_error("Serial transaction timeout");
    if (descriptor.revents & (POLLERR | POLLHUP | POLLNVAL))
      throw std::runtime_error("Serial device disconnected");
    if (descriptor.revents & events) return;
  }
}
void Scs0009::send(const Bytes& data) {
  const auto deadline = Clock::now() + std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(timeout_));
  std::size_t sent = 0;
  while (sent < data.size()) {
    wait(POLLOUT, deadline);
    const auto count = ::write(fd_, data.data() + sent, data.size() - sent);
    if (count < 0) {
      if (errno == EINTR || errno == EAGAIN) continue;
      fail("serial write");
    }
    sent += static_cast<std::size_t>(count);
  }
}
uint8_t Scs0009::receive(Clock::time_point deadline) {
  for (;;) {
    wait(POLLIN, deadline);
    uint8_t byte;
    const auto count = ::read(fd_, &byte, 1);
    if (count == 1) return byte;
    if (count < 0 && errno != EINTR && errno != EAGAIN) fail("serial read");
  }
}
Bytes Scs0009::readRegister(uint8_t id, uint8_t address, uint8_t size) {
  if (id > 253 || size == 0 || size > 250) throw std::invalid_argument("Invalid register read");
  try {
    // Discard late replies after previous transactions. No concurrent transactions.
    if (tcflush(fd_, TCIFLUSH) < 0) fail("flush receive buffer");
    send(packet(id, 2, {address, size}));
    const auto deadline = Clock::now() + std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(timeout_));
    unsigned header = 0;
    while (header < 2) header = receive(deadline) == 255 ? header + 1 : 0;
    Bytes data{255, 255};
    uint8_t sender = receive(deadline);
    while (sender == 255) sender = receive(deadline);
    data.push_back(sender);
    const auto length = receive(deadline);
    data.push_back(length);
    if (length < 2 || length > 252) throw std::runtime_error("Invalid status length");
    for (unsigned i = 0; i < length; ++i) data.push_back(receive(deadline));
    return parseStatus(data, id, size);
  } catch (const std::exception& e) {
    throw std::runtime_error("READ id=" + std::to_string(id) +
        " address=" + std::to_string(address) + " size=" + std::to_string(size) +
        ": " + e.what());
  }
}
void Scs0009::syncWrite(const std::vector<int>& ids, uint8_t address,
                       const std::vector<Bytes>& values) {
  if (ids.empty() || ids.size() != values.size() || values[0].empty() ||
      values[0].size() > 250) throw std::invalid_argument("Invalid sync write");
  Bytes params{address, static_cast<uint8_t>(values[0].size())};
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (ids[i] < 0 || ids[i] > 253 || values[i].size() != values[0].size())
      throw std::invalid_argument("Invalid sync write ID/width");
    params.push_back(static_cast<uint8_t>(ids[i]));
    params.insert(params.end(), values[i].begin(), values[i].end());
  }
  const auto data = packet(254, 0x83, params);
  try {
    send(data); // Broadcast sync-write has no status reply.
  } catch (const std::exception& e) {
    throw std::runtime_error("SYNC_WRITE address=" + std::to_string(address) +
        " count=" + std::to_string(ids.size()) + ": " + e.what());
  }
}
}  // namespace amazing_hand_ros
