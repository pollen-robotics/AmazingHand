cmake_minimum_required(VERSION 3.16)
project(amazing_hand_description LANGUAGES NONE)

if("$ENV{ROS_VERSION}" STREQUAL "1")
  message(STATUS "Skipping ROS 2 amazing_hand_description in ROS 1")
  install(CODE "")  # Provide the install target expected by workspace builders.
  return()
endif()

find_package(ament_cmake REQUIRED)
install(DIRECTORY config meshes mjcf sdf urdf DESTINATION share/${PROJECT_NAME})
install(FILES LICENSE ../README.md DESTINATION share/${PROJECT_NAME})
ament_package()
