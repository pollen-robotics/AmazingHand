cmake_minimum_required(VERSION 3.16)
project(amazing_hand_driver LANGUAGES NONE)

if("$ENV{ROS_VERSION}" STREQUAL "1")
  message(STATUS "Skipping ROS 2 amazing_hand_driver in ROS 1")
  install(CODE "")  # Provide the install target expected by workspace builders.
  return()
endif()

enable_language(CXX)
find_package(ament_cmake REQUIRED)
find_package(feetech_driver REQUIRED)
find_package(transmission_interface REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(pluginlib REQUIRED)

add_library(amazing_hand_hardware_interface SHARED src/amazing_hand_hardware_interface.cpp)
target_compile_features(amazing_hand_hardware_interface PRIVATE cxx_std_20)
target_link_libraries(amazing_hand_hardware_interface PRIVATE feetech_driver::communication_protocol
  hardware_interface::hardware_interface transmission_interface::transmission_interface
  pluginlib::pluginlib rclcpp::rclcpp)
pluginlib_export_plugin_description_file(hardware_interface amazing_hand_hardware_interface.xml)
install(TARGETS amazing_hand_hardware_interface LIBRARY DESTINATION lib)

install(DIRECTORY config launch urdf DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/hand_description scripts/hand_rviz_config DESTINATION lib/${PROJECT_NAME})
install(FILES LICENSE ../README.md DESTINATION share/${PROJECT_NAME})
ament_package()
