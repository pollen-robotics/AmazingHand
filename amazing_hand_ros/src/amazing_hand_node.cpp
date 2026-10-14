// SPDX-License-Identifier: Apache-2.0
#include <amazing_hand_ros/scs0009.h>
#include <controller_manager/controller_manager.h>
#include <hardware_interface/robot_hw.h>
#include <hardware_interface/joint_command_interface.h>
#include <transmission_interface/differential_transmission_loader.h>
#include <transmission_interface/transmission_parser.h>
#include <urdf/model.h>
#include <ros/ros.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <memory>
#include <set>
#include <stdexcept>

namespace ah = amazing_hand_ros;
namespace ti = transmission_interface;
namespace {
void require(bool condition, const std::string& message) {
  if (!condition) throw std::runtime_error(message);
}
const std::array<std::string, 4> fingers{{"index", "middle", "ring", "thumb"}};

class Hand : public hardware_interface::RobotHW {
 public:
  explicit Hand(ros::NodeHandle& nh) {
    ros::NodeHandle pnh("~");
    int side, baud;
    double timeout, speed;
    std::string port, description;
    pnh.param("side", side, 1);
    require(side == 1 || side == 2, "side must be 1 (right) or 2 (left)");
    ids_ = side == 1 ? std::vector<int>{1,2,3,4,5,6,7,8} : std::vector<int>{15,16,13,14,11,12,17,18};
    pnh.getParam("servo_ids", ids_);
    require(ids_.size() == 8 && std::set<int>(ids_.begin(), ids_.end()).size() == 8,
            "servo_ids must contain eight unique IDs in logical finger/motor order");
    for (int id : ids_) require(id >= 0 && id <= 253, "servo ID outside [0,253]");
    std::vector<double> middle;
    require(pnh.getParam("middle_pos", middle) && middle.size() == 8,
            "middle_pos must contain eight calibration angles in degrees, in ascending physical ID order");
    auto sorted_ids = ids_;
    std::sort(sorted_ids.begin(), sorted_ids.end());
    pnh.param("motor_min_deg", motor_min_, -90.0);
    pnh.param("motor_max_deg", motor_max_, 90.0);
    require(std::isfinite(motor_min_) && std::isfinite(motor_max_) && motor_min_ < motor_max_,
            "Invalid calibrated motor limits");
    motor_min_ *= ah::kPi / 180;
    motor_max_ *= ah::kPi / 180;
    for (std::size_t i = 0; i < 8; ++i) {
      offset_[i] = middle[std::find(sorted_ids.begin(), sorted_ids.end(), ids_[i]) - sorted_ids.begin()] * ah::kPi / 180;
      require(std::isfinite(offset_[i]), "Non-finite middle_pos");
      ah::positionRaw(offset_[i] + motor_min_);
      ah::positionRaw(offset_[i] + motor_max_);
    }
    require(nh.getParam("robot_description", description), "Missing robot_description");
    urdf::Model model;
    require(model.initString(description), "Invalid URDF");
    std::vector<ti::TransmissionInfo> info;
    require(ti::TransmissionParser::parse(description, info) && info.size() == 4,
            "Expected four differential transmissions");
    ti::DifferentialTransmissionLoader loader;
    for (std::size_t finger = 0; finger < 4; ++finger) {
      const auto name = fingers[finger] + "_transmission";
      const auto it = std::find_if(info.begin(), info.end(), [&](const ti::TransmissionInfo& t) { return t.name_ == name; });
      require(it != info.end() && it->type_ == "transmission_interface/DifferentialTransmission",
              "Missing differential transmission " + name);
      require(it->joints_.size() == 2 && it->actuators_.size() == 2, "Invalid transmission dimensions");
      transmission_[finger] = loader.load(*it);
      require(static_cast<bool>(transmission_[finger]), "Failed to load " + name);
      for (std::size_t axis = 0; axis < 2; ++axis) {
        const std::size_t i = 2 * finger + axis;
        const auto joint_name = fingers[finger] + (axis == 0 ? "_flexion_level" : "_abduction_level");
        const auto joint = model.getJoint(joint_name);
        require(joint && joint->limits, "Missing joint limits for " + joint_name);
        // Data order follows DifferentialTransmission roles, independently of XML order.
        const auto jt = std::find_if(it->joints_.begin(), it->joints_.end(),
            [&](const ti::JointInfo& j) { return j.name_ == joint_name; });
        require(jt != it->joints_.end() && jt->role_ == (axis == 0 ? "joint1" : "joint2"),
                "Unexpected joint role for " + joint_name);
        const auto actuator_name = fingers[finger] + "_motor_" + std::to_string(axis + 1);
        const auto at = std::find_if(it->actuators_.begin(), it->actuators_.end(),
            [&](const ti::ActuatorInfo& a) { return a.name_ == actuator_name; });
        require(at != it->actuators_.end(), "Missing actuator " + actuator_name);
        TiXmlDocument actuator_xml;
        actuator_xml.Parse(at->xml_element_.c_str());
        const auto role = actuator_xml.RootElement()->FirstChildElement("role");
        require(role && role->GetText() && std::string(role->GetText()) == "actuator" + std::to_string(axis + 1),
                "Unexpected actuator role");
        lower_[i] = joint->limits->lower;
        upper_[i] = joint->limits->upper;
        require(lower_[i] == (axis == 0 ? 0.0 : -1.0) && upper_[i] == 1.0,
                "Level joint limits must be [0,1] or [-1,1]");
        state_interface_.registerHandle(hardware_interface::JointStateHandle(
            joint_name, &position_[i], &velocity_[i], &effort_[i]));
        command_interface_.registerHandle(hardware_interface::JointHandle(
            state_interface_.getHandle(joint_name), &command_[i]));
        actuator_state_[finger].position.push_back(&motor_position_[i]);
        actuator_command_[finger].position.push_back(&motor_command_[i]);
        joint_state_[finger].position.push_back(&position_[i]);
        joint_command_[finger].position.push_back(&limited_command_[i]);
      }
    }
    registerInterface(&state_interface_);
    registerInterface(&command_interface_);
    pnh.param<std::string>("port", port, "/dev/ttyACM0");
    pnh.param("baudrate", baud, 1000000);
    pnh.param("serial_timeout", timeout, 0.05);
    pnh.param("goal_speed", speed, 3.0);
    pnh.param("disable_torque_on_shutdown", disable_on_shutdown_, true);
    const auto raw_speed = ah::speedRaw(speed);
    bus_.reset(new ah::Scs0009(port, baud, timeout));
    // Read every motor before sending anything that can move it.
    readState(0);
    for (std::size_t i = 0; i < 8; ++i) {
      require(position_[i] >= lower_[i] - 0.005 && position_[i] <= upper_[i] + 0.005 &&
              motor_position_[i] >= motor_min_ - ah::kStep && motor_position_[i] <= motor_max_ + ah::kStep,
              "Initial pose outside configured limits; check middle_pos and starting pose");
    }
    command_ = position_;
    // Preserve exact measured encoder words for the initial hold target.
    bus_->syncWrite(ids_, 42, initial_position_words_);
    bus_->syncWrite(ids_, 44, std::vector<ah::Bytes>(8, ah::word(0)));
    bus_->syncWrite(ids_, 46, std::vector<ah::Bytes>(8, ah::word(raw_speed)));
    try {
      bus_->syncWrite(ids_, 40, std::vector<ah::Bytes>(8, ah::Bytes{1}));
      for (int id : ids_)
        require(bus_->readRegister(id, 40, 1)[0] == 1, "Torque enable readback failed");
    } catch (...) {
      try { bus_->syncWrite(ids_, 40, std::vector<ah::Bytes>(8, ah::Bytes{0})); } catch (...) {}
      throw;
    }
    ROS_INFO("AmazingHand ready: eight level joints, measured-position hold initialized");
  }
  ~Hand() { stop(false); }
  void stop(bool fault) noexcept {
    if (!bus_ || stopped_) return;
    stopped_ = true;
    if (fault || disable_on_shutdown_) {
      try { bus_->syncWrite(ids_, 40, std::vector<ah::Bytes>(8, ah::Bytes{0})); }
      catch (const std::exception& e) { ROS_ERROR("Torque disable failed: %s", e.what()); }
    }
  }
  void readState(double dt) {
    std::array<double, 8> measured;
    std::vector<ah::Bytes> words;
    for (std::size_t i = 0; i < 8; ++i) {
      const auto data = bus_->readRegister(ids_[i], 56, 2);
      measured[i] = ah::positionRadians((static_cast<uint16_t>(data[0]) << 8) | data[1]) - offset_[i];
      words.push_back(data);
    }
    // Commit only complete samples; a failed read never reaches controller_manager.
    const auto previous = position_;
    motor_position_ = measured;
    for (std::size_t i = 0; i < 4; ++i)
      transmission_[i]->actuatorToJointPosition(actuator_state_[i], joint_state_[i]);
    for (std::size_t i = 0; i < 8; ++i)
      velocity_[i] = dt > 0 ? (position_[i] - previous[i]) / dt : 0;
    initial_position_words_ = words;
  }
  void writeCommand() {
    bool saturated = false;
    for (std::size_t i = 0; i < 8; ++i) {
      require(std::isfinite(command_[i]), "Non-finite joint command");
      limited_command_[i] = std::max(lower_[i], std::min(upper_[i], command_[i]));
      saturated |= limited_command_[i] != command_[i];
    }
    for (std::size_t i = 0; i < 4; ++i)
      transmission_[i]->jointToActuatorPosition(joint_command_[i], actuator_command_[i]);
    std::vector<ah::Bytes> words;
    for (std::size_t i = 0; i < 8; ++i) {
      require(std::isfinite(motor_command_[i]), "Non-finite motor command");
      const auto limited = std::max(motor_min_, std::min(motor_max_, motor_command_[i]));
      saturated |= std::abs(limited - motor_command_[i]) > 1e-9;
      words.push_back(ah::word(ah::positionRaw(limited + offset_[i])));
    }
    if (saturated) ROS_WARN_THROTTLE(1, "Command saturated at level or motor limits; requested pose may be unreachable");
    bus_->syncWrite(ids_, 42, words);
  }
 private:
  hardware_interface::JointStateInterface state_interface_;
  hardware_interface::PositionJointInterface command_interface_;
  std::array<double, 8> position_{}, velocity_{}, effort_{}, command_{}, limited_command_{};
  std::array<double, 8> motor_position_{}, motor_command_{}, offset_{}, lower_{}, upper_{};
  std::array<ti::TransmissionSharedPtr, 4> transmission_;
  std::array<ti::ActuatorData, 4> actuator_state_, actuator_command_;
  std::array<ti::JointData, 4> joint_state_, joint_command_;
  std::vector<int> ids_;
  std::vector<ah::Bytes> initial_position_words_;
  std::unique_ptr<ah::Scs0009> bus_;
  double motor_min_, motor_max_;
  bool disable_on_shutdown_ = true, stopped_ = false;
};
}
int main(int argc, char** argv) {
  ros::init(argc, argv, "amazing_hand");
  ros::NodeHandle nh, pnh("~");
  try {
    double frequency;
    pnh.param("control_rate", frequency, 50.0);
    require(std::isfinite(frequency) && frequency > 0 && frequency <= 1000, "Invalid control_rate");
    Hand hand(nh);
    controller_manager::ControllerManager manager(&hand, nh);
    ros::AsyncSpinner spinner(1);
    spinner.start();
    ros::WallRate rate(frequency);
    auto previous = ros::SteadyTime::now();
    try {
      while (ros::ok()) {
        const auto now = ros::SteadyTime::now();
        const double dt = (now - previous).toSec();
        previous = now;
        hand.readState(dt);
        manager.update(ros::Time::now(), ros::Duration(dt));
        hand.writeCommand();
        rate.sleep();
      }
    } catch (...) { hand.stop(true); throw; }
    spinner.stop();
  } catch (const std::exception& e) {
    ROS_FATAL("AmazingHand stopped: %s", e.what());
    return 1;
  }
  return 0;
}
