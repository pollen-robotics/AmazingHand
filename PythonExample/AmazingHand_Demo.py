import time
import numpy as np

from rustypot import Scs0009PyController

#Side
Side = 1 # 1=> Right Hand // 2=> Left Hand


#Speed
MaxSpeed = 7
CloseSpeed = 3

#Fingers middle poses
MiddlePos = [3, 0, -5, -8, -2, 5, -12, 0] # replace values by your calibration results

c = Scs0009PyController(
        serial_port="COM11",
        baudrate=1000000,
        timeout=0.5,
    )

def sid(i):
    # logical ID: 1..8
    # right hand: 1..8
    # left hand: 11..18
    return i + 10 if Side == 2 else i

def main():
    
    c.write_torque_enable(1, 1)  #1 = On / 2 = Off / 3 = Free
    t0 = time.time()

    while True:
        t = time.time() - t0

        OpenHand()
        time.sleep(0.5)

        CloseHand()
        time.sleep(3)

        OpenHand_Progressive()
        time.sleep(0.5)

        SpreadHand()
        time.sleep(0.6)
        ClenchHand()
        time.sleep(0.6)

        OpenHand()
        time.sleep(0.2)

        Index_Pointing()
        time.sleep(0.4)
        Nonono()
        time.sleep(0.5)
        
        OpenHand()
        time.sleep(0.3)

        Perfect()
        time.sleep(0.8)

        OpenHand()
        time.sleep(0.4)

        Victory()
        time.sleep(1)
        Scissors()
        time.sleep(0.5)

        OpenHand()
        time.sleep(0.4)

        Pinched()
        time.sleep(1)

        Fuck()
        time.sleep(0.8)


        #trials

        #c.sync_write_raw_goal_position([1,2], [50,50])
        #time.sleep(1)

        #a=c.read_present_position(1)
        #b=c.read_present_position(2)
        #a=np.rad2deg(a)
        #b=np.rad2deg(b)
        #print(f'{a} {b}')
        #time.sleep(0.001)



def OpenHand():
    Move_Index (-35,35, MaxSpeed)
    Move_Middle (-35,35, MaxSpeed)
    Move_Ring (-35,35, MaxSpeed)
    Move_Thumb (-35,35, MaxSpeed)

def CloseHand():
    Move_Index (90,-90, CloseSpeed)
    Move_Middle (90,-90, CloseSpeed)
    Move_Ring (90,-90, CloseSpeed)
    Move_Thumb (90,-90, CloseSpeed+1)

def OpenHand_Progressive():
    Move_Index (-35,35, MaxSpeed-2)
    time.sleep(0.2)
    Move_Middle (-35,35, MaxSpeed-2)
    time.sleep(0.2)
    Move_Ring (-35,35, MaxSpeed-2)
    time.sleep(0.2)
    Move_Thumb (-35,35, MaxSpeed-2)

def SpreadHand():
    if (Side==1): # Right Hand
        Move_Index (4, 90, MaxSpeed)
        Move_Middle (-32, 32, MaxSpeed)
        Move_Ring (-90, -4, MaxSpeed)
        Move_Thumb (-90, -4, MaxSpeed)  
  
    if (Side==2): # Left Hand
        Move_Index (-60, 0, MaxSpeed)
        Move_Middle (-35, 35, MaxSpeed)
        Move_Ring (-4, 90, MaxSpeed)
        Move_Thumb (-4, 90, MaxSpeed)  
  
def ClenchHand():
    if (Side==1): # Right Hand
        Move_Index (-60, 0, MaxSpeed)
        Move_Middle (-35, 35, MaxSpeed)
        Move_Ring (0, 70, MaxSpeed)
        Move_Thumb (-4, 90, MaxSpeed)  
  
    if (Side==2): # Left Hand
        Move_Index (0, 60, MaxSpeed)
        Move_Middle (-35, 35, MaxSpeed)
        Move_Ring (-70, 0, MaxSpeed)
        Move_Thumb (-90, -4, MaxSpeed)
  
def Index_Pointing():
    Move_Index (-40, 40, MaxSpeed)
    Move_Middle (90, -90, MaxSpeed)
    Move_Ring (90, -90, MaxSpeed)
    Move_Thumb (90, -90, MaxSpeed)
  
def Nonono():
  Index_Pointing()
  for i in range(3) :
        time.sleep(0.2)
        Move_Index (-10, 80, MaxSpeed)
        time.sleep(0.2)
        Move_Index (-80, 10, MaxSpeed)
  
  Move_Index (-35, 35, MaxSpeed)
  time.sleep(0.4)
  
def Perfect():
  if (Side==1): #Right Hand
        Move_Index (50, -50, MaxSpeed)
        Move_Middle (0, -0, MaxSpeed)
        Move_Ring (-20, 20, MaxSpeed)
        Move_Thumb (65, 12, MaxSpeed)

  
  if (Side==2): #Left Hand
        Move_Index (50, -50, MaxSpeed)
        Move_Middle (0, -0, MaxSpeed)
        Move_Ring (-20, 20, MaxSpeed)
        Move_Thumb (-12, -65, MaxSpeed)
  
def Victory():
  if (Side==1): #Right Hand 
        Move_Index (-15, 65, MaxSpeed)
        Move_Middle (-65, 15, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (90, -90, MaxSpeed)

  
  if (Side==2): #Left Hand
        Move_Index (-65, 15, MaxSpeed)
        Move_Middle (-15, 65, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (90, -90, MaxSpeed)
  
def Pinched():
  if (Side==1): #Right Hand
        Move_Index (90, -90, MaxSpeed)
        Move_Middle (90, -90, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (0, -75, MaxSpeed)

  if (Side==2): #Left Hand
        Move_Index (90, -90, MaxSpeed)
        Move_Middle (90, -90, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (75, 5, MaxSpeed)

def Scissors():
  Victory();
  if (Side==1): #Right Hand
        for i in range(3):  
            time.sleep(0.2)
            Move_Index (-50, 20, MaxSpeed)
            Move_Middle (-20, 50, MaxSpeed)
            
            time.sleep(0.2)
            Move_Index (-15, 65, MaxSpeed)
            Move_Middle (-65, 15, MaxSpeed)
    

  if (Side==2): #Left Hand
        for i in range(3):
            time.sleep(0.2)
            Move_Index (-20, 50, MaxSpeed)
            Move_Middle (-50, 20, MaxSpeed)
            
            time.sleep(0.2)
            Move_Index (-65, 15, MaxSpeed)
            Move_Middle (-15, 65, MaxSpeed)

def Fuck():

  if (Side==1): #Right Hand
        Move_Index (90, -90, MaxSpeed)
        Move_Middle (-35, 35, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (0, -75, MaxSpeed)

  if (Side==2): #Left Hand
        Move_Index (90, -90, MaxSpeed)
        Move_Middle (-35, 35, MaxSpeed)
        Move_Ring (90, -90, MaxSpeed)
        Move_Thumb (75, 0, MaxSpeed)
  
def Move_Index(Angle_1, Angle_2, Speed):
    c.write_goal_speed(sid(1), Speed)
    time.sleep(0.0002)
    c.write_goal_speed(sid(2), Speed)
    time.sleep(0.0002)
    Pos_1 = np.deg2rad(MiddlePos[0] + Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[1] + Angle_2)
    c.write_goal_position(sid(1), Pos_1)
    c.write_goal_position(sid(2), Pos_2)
    time.sleep(0.005)

def Move_Middle(Angle_1,Angle_2,Speed):    
    c.write_goal_speed(sid(3), Speed)
    time.sleep(0.0002)
    c.write_goal_speed(sid(4), Speed)
    time.sleep(0.0002)
    Pos_1 = np.deg2rad(MiddlePos[2]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[3]+Angle_2)
    c.write_goal_position(sid(3), Pos_1)
    c.write_goal_position(sid(4), Pos_2)
    time.sleep(0.005)

def Move_Ring(Angle_1,Angle_2,Speed):    
    c.write_goal_speed(sid(5), Speed)
    time.sleep(0.0002)
    c.write_goal_speed(sid(6), Speed)
    time.sleep(0.0002)
    Pos_1 = np.deg2rad(MiddlePos[4]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[5]+Angle_2)
    c.write_goal_position(sid(5), Pos_1)
    c.write_goal_position(sid(6), Pos_2)
    time.sleep(0.005)

def Move_Thumb(Angle_1,Angle_2,Speed):    
    c.write_goal_speed(sid(7), Speed)
    time.sleep(0.0002)
    c.write_goal_speed(sid(8), Speed)
    time.sleep(0.0002)
    Pos_1 = np.deg2rad(MiddlePos[6]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[7]+Angle_2)
    c.write_goal_position(sid(7), Pos_1)
    c.write_goal_position(sid(8), Pos_2)
    time.sleep(0.005)


if __name__ == '__main__':
    main()



