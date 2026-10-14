// SPDX-License-Identifier: Apache-2.0
#include <amazing_hand_ros/scs0009.h>
#include <transmission_interface/differential_transmission_loader.h>
#include <transmission_interface/transmission_parser.h>
#include <urdf/model.h>
#include <gtest/gtest.h>
#include <cmath>
#include <cstdio>
#include <limits>
#include <thread>
#include <pty.h>
#include <unistd.h>

namespace ah = amazing_hand_ros;
TEST(Protocol, KnownPackets) {
  EXPECT_EQ((ah::Bytes{255,255,1,4,2,56,2,190}), ah::packet(1,2,{56,2}));
  EXPECT_EQ((ah::Bytes{255,255,254,10,131,30,2,11,0,0,12,10,20,31}),
            ah::packet(254,131,{30,2,11,0,0,12,10,20}));
  EXPECT_EQ((ah::Bytes{1,255}), ah::word(511));
}
TEST(Protocol, RejectsBadReplies) {
  const ah::Bytes good = ah::packet(1,0,{1,255});
  EXPECT_EQ((ah::Bytes{1,255}), ah::parseStatus(good,1,2));
  auto bad = good;
  bad.back() ^= 1;
  EXPECT_THROW(ah::parseStatus(bad,1,2), std::runtime_error);
  EXPECT_THROW(ah::parseStatus(good,2,2), std::runtime_error);
  EXPECT_THROW(ah::parseStatus(good,1,1), std::runtime_error);
  EXPECT_THROW(ah::parseStatus(ah::packet(1,4,{1,255}),1,2), std::runtime_error);
  EXPECT_THROW(ah::parseStatus({},1,2), std::runtime_error);
}
TEST(Conversion, RustypotReference) {
  EXPECT_EQ(511, ah::positionRaw(0));
  EXPECT_DOUBLE_EQ(0, ah::positionRadians(511));
  EXPECT_EQ(818, ah::positionRaw(90 * ah::kPi/180));
  EXPECT_EQ(203, ah::positionRaw(-90 * ah::kPi/180));
  EXPECT_EQ(586, ah::speedRaw(3));
  EXPECT_EQ(1368, ah::speedRaw(7));
  for (int degrees = -140; degrees <= 140; ++degrees)
    EXPECT_NEAR(degrees * ah::kPi/180, ah::positionRadians(ah::positionRaw(degrees * ah::kPi/180)), ah::kStep);
  EXPECT_THROW(ah::positionRaw(3), std::invalid_argument);
  EXPECT_THROW(ah::positionRaw(std::numeric_limits<double>::quiet_NaN()), std::invalid_argument);
  EXPECT_THROW(ah::speedRaw(0), std::invalid_argument);
  EXPECT_THROW(ah::positionRadians(1024), std::runtime_error);
}
TEST(Transmission, RealUrdfAndRoundTrip) {
  const std::string command = "xacro " PACKAGE_SOURCE_DIR "/urdf/amazing_hand.urdf.xacro";
  FILE* process = popen(command.c_str(), "r");
  ASSERT_NE(nullptr, process);
  std::string xml;
  char buffer[4096];
  while (fgets(buffer, sizeof(buffer), process)) xml += buffer;
  ASSERT_EQ(0, pclose(process));
  urdf::Model model;
  ASSERT_TRUE(model.initString(xml));
  EXPECT_EQ(8u, model.joints_.size());
  EXPECT_EQ(9u, model.links_.size());
  for (const auto& link : model.links_) {
    EXPECT_FALSE(link.second->visual);
    EXPECT_FALSE(link.second->collision);
  }
  std::vector<transmission_interface::TransmissionInfo> infos;
  ASSERT_TRUE(transmission_interface::TransmissionParser::parse(xml, infos));
  ASSERT_EQ(4u, infos.size());
  transmission_interface::DifferentialTransmissionLoader loader;
  for (const auto& info : infos) {
    auto transmission = loader.load(info);
    ASSERT_TRUE(transmission);
    double m1 = 0, m2 = 0, flex = 0, abd = 0;
    transmission_interface::ActuatorData actuator;
    transmission_interface::JointData joint;
    actuator.position = {&m1, &m2};
    joint.position = {&flex, &abd};
    for (const auto& pose : std::vector<std::vector<double>>{
             {-45,45,0,0}, {-35,35,10.0/135,0}, {90,-90,1,0}, {0,0,1.0/3,0},
             {4,90,(-43.0+45)/135,1}, {-90,-4,(-43.0+45)/135,-1},
             {72,-25,(48.5+45)/135,0.5}}) {
      m1 = pose[0]*ah::kPi/180;
      m2 = pose[1]*ah::kPi/180;
      transmission->actuatorToJointPosition(actuator,joint);
      EXPECT_NEAR(pose[2], flex, 1e-12);
      EXPECT_NEAR(pose[3], abd, 1e-12);
      m1 = m2 = 0;
      transmission->jointToActuatorPosition(joint,actuator);
      EXPECT_NEAR(pose[0]*ah::kPi/180, m1, 1e-12);
      EXPECT_NEAR(pose[1]*ah::kPi/180, m2, 1e-12);
    }
  }
}
TEST(Serial, PseudoTerminalReadWriteAndTimeout) {
  int master, slave;
  char name[128];
  ASSERT_EQ(0, openpty(&master, &slave, name, nullptr, nullptr));
  {
    ah::Scs0009 bus(name, 1000000, 0.1);
    ah::Bytes received;
    std::thread servo([&] {
      uint8_t data[8];
      std::size_t count = 0;
      while (count < sizeof(data)) {
        auto n = ::read(master, data + count, sizeof(data) - count);
        if (n <= 0) return;
        count += n;
      }
      received.assign(data, data + count);
      const auto reply = ah::packet(15,0,{1,255});
      // Fragmented status packets must also work.
      for (auto byte : reply) { (void)::write(master, &byte, 1); usleep(100); }
    });
    ah::Bytes result;
    try { result = bus.readRegister(15,56,2); }
    catch (...) { servo.join(); throw; }
    servo.join();
    EXPECT_EQ(ah::packet(15,2,{56,2}), received);
    EXPECT_EQ((ah::Bytes{1,255}), result);
    bus.syncWrite({15,16},42,{ah::word(511),ah::word(818)});
    ah::Bytes written(14);
    std::size_t count = 0;
    while (count < written.size()) {
      auto n = ::read(master, written.data()+count, written.size()-count);
      ASSERT_GT(n,0);
      count += n;
    }
    EXPECT_EQ(ah::packet(254,131,{42,2,15,1,255,16,3,50}),written);
    try {
      bus.readRegister(15,56,2);
      FAIL() << "Expected a timeout";
    } catch (const std::runtime_error& e) {
      EXPECT_NE(std::string::npos, std::string(e.what()).find("READ id=15 address=56 size=2"));
      EXPECT_NE(std::string::npos, std::string(e.what()).find("timeout"));
    }
  }
  ::close(master);
  ::close(slave);
}
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
