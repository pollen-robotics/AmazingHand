cmake_minimum_required(VERSION 3.10)
project(amazing_hand_description)

if("$ENV{ROS_VERSION}" STREQUAL "2")
  find_package(ament_cmake REQUIRED)
  ament_package()
else() # if("$ENV{ROS_VERSION}" STREQUAL "2")
  find_package(catkin REQUIRED)
  catkin_package()
endif() # if("$ENV{ROS_VERSION}" STREQUAL "2")

install(DIRECTORY config meshes mjcf sdf urdf DESTINATION share/${PROJECT_NAME})
install(FILES LICENSE DESTINATION share/${PROJECT_NAME})
