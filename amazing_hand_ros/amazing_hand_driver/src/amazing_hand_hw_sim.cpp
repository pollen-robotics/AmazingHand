// SPDX-License-Identifier: Apache-2.0
#include <gazebo_ros_control/default_robot_hw_sim.h>

namespace amazing_hand_driver {
// Gazebo Classic needs the link joints driven explicitly. Read their mimic
// factors from the same URDF used by robot_state_publisher.
class HandHWSim : public gazebo_ros_control::DefaultRobotHWSim {
  struct Mimic {
    gazebo::physics::JointPtr source, target;
    double multiplier, offset;
  };
  std::vector<Mimic> mimics_;

 public:
  bool initSim(const std::string& ns, ros::NodeHandle nh, gazebo::physics::ModelPtr model,
               const urdf::Model* urdf,
               std::vector<transmission_interface::TransmissionInfo> transmissions) override {
    if (!DefaultRobotHWSim::initSim(ns, nh, model, urdf, transmissions)) return false;
    for (const auto& entry : urdf->joints_) {
      const auto& mimic = entry.second->mimic;
      if (!mimic) continue;
      auto target = model->GetJoint(entry.first);
      auto source = model->GetJoint(mimic->joint_name);
      if (!source || !target) {
        ROS_ERROR_STREAM("Missing Gazebo mimic joint for " << entry.first);
        return false;
      }
      // This hinge is positioned kinematically. Explicit ODE damping on the
      // low-inertia CAD links can otherwise destabilize the model.
      target->SetDamping(0, 0.0);
      mimics_.push_back({source, target, mimic->multiplier, mimic->offset});
    }
    return true;
  }

  void writeSim(ros::Time time, ros::Duration period) override {
    DefaultRobotHWSim::writeSim(time, period);
    for (const auto& m : mimics_)
      m.target->SetPosition(0, m.source->Position(0) * m.multiplier + m.offset, false);
  }
};
}  // namespace amazing_hand_driver
PLUGINLIB_EXPORT_CLASS(amazing_hand_driver::HandHWSim, gazebo_ros_control::RobotHWSim)
