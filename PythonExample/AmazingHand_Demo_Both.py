import time
import numpy as np

from rustypot import Scs0009PyController

#Side
# 1=> Right Hand // 2=> Left Hand


#Speed
MaxSpeed = 7
CloseSpeed = 3

#Fingers middle poses
MiddlePos_1 = [3, 0, -8, -13, 2, -5, -12, -5] #1eplace values by your calibration1esults
MiddlePos_2 = [3, -3, -1, -10, 5, 2, -7, 3] #1eplace values by your calibration1esults


c = Scs0009PyController(
        serial_port="COM5",
        baudrate=1000000,
        timeout=0.05,  #0.05
    )



def main():
    
    c.write_torque_enable(1, 1)    # (Lowest ID , #1 = On / 2 = Off / 3 = Free )  
    t0 = time.time()

    while True:
        t = time.time() - t0

        OpenHand()
        time.sleep(0.5)

        CloseHand()
        time.sleep(4)

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
        time.sleep(0.5)
        Scissors()
        time.sleep(0.5)

        OpenHand()
        time.sleep(0.4)

        Pinched()
        time.sleep(1.5)

        Fuck()
        time.sleep(0.8)



# 1 = Right Hand / 2 = Left Hand
def OpenHand():
        Move_Index (-35,35, MaxSpeed, 1)
        Move_Index (-35,35, MaxSpeed, 2)
        Move_Middle (-35,35, MaxSpeed, 1)
        Move_Middle (-35,35, MaxSpeed, 2)
        Move_Ring (-35,35, MaxSpeed, 1)
        Move_Ring (-35,35, MaxSpeed, 2)
        Move_Thumb (-35,35, MaxSpeed, 1)
        Move_Thumb (-35,35, MaxSpeed, 2) 
                
        
def CloseHand():
        Move_Index (90,-90, CloseSpeed, 1)
        Move_Index (90,-90, CloseSpeed, 2)
        Move_Middle (90,-90, CloseSpeed, 1)
        Move_Middle (90,-90, CloseSpeed, 2)
        Move_Ring (90,-90, CloseSpeed, 1)
        Move_Ring (90,-90, CloseSpeed, 2)
        Move_Thumb (90,-90, CloseSpeed+4, 1)  #Higher Speed to be sure thumb is passing under index
        Move_Thumb (90,-90, CloseSpeed+4, 2)  #Higher Speed to be sure thumb is passing under index



def OpenHand_Progressive():

        Move_Index (-35,35, MaxSpeed-2, 1)
        Move_Index (-35,35, MaxSpeed-2, 2)
        time.sleep(0.2)
        Move_Middle (-35,35, MaxSpeed-2, 1)
        Move_Middle (-35,35, MaxSpeed-2, 2)
        time.sleep(0.2)
        Move_Ring (-35,35, MaxSpeed-2, 1)
        Move_Ring (-35,35, MaxSpeed-2, 2)
        time.sleep(0.2)
        Move_Thumb (-35,35, MaxSpeed-2, 1)
        Move_Thumb (-35,35, MaxSpeed-2, 2)

        

def SpreadHand():  
        Move_Index (4, 90, MaxSpeed, 1)
        Move_Index (-90, 0, MaxSpeed, 2)
        Move_Middle (-32, 32, MaxSpeed, 1)
        Move_Middle (-32, 32, MaxSpeed, 2)
        Move_Ring (-90, -4, MaxSpeed, 1)
        Move_Ring (-4, 90, MaxSpeed, 2)
        Move_Thumb (-90, -4, MaxSpeed, 1)   
        Move_Thumb (-4, 90, MaxSpeed, 2)  

  
def ClenchHand(): 
        Move_Index (-60, 0, MaxSpeed, 1)
        Move_Index (0, 60, MaxSpeed, 2)
        Move_Middle (-35, 35, MaxSpeed, 1)
        Move_Middle (-35, 35, MaxSpeed, 2)
        Move_Ring (0, 70, MaxSpeed, 1)
        Move_Ring (-70, 0, MaxSpeed, 2)
        Move_Thumb (-4, 90, MaxSpeed, 1)       
        Move_Thumb (-90, -4, MaxSpeed, 2)
  

def Index_Pointing():
        Move_Index (-40, 40, MaxSpeed, 1)
        Move_Index (-40, 40, MaxSpeed, 2)
        Move_Middle (90, -90, MaxSpeed, 1)
        Move_Middle (90, -90, MaxSpeed, 2)
        Move_Ring (90, -90, MaxSpeed, 1)
        Move_Ring (90, -90, MaxSpeed, 2)
        Move_Thumb (90, -90, MaxSpeed, 1)     
        Move_Thumb (90, -90, MaxSpeed, 2)
  
def Nonono():
        Index_Pointing()
        for i in range(3) :
            time.sleep(0.2)
            Move_Index (-10, 80, MaxSpeed, 1)
            Move_Index (-10, 80, MaxSpeed, 2)
            time.sleep(0.2)
            Move_Index (-80, 10, MaxSpeed, 1)
            Move_Index (-80, 10, MaxSpeed, 2)
    
        Move_Index (-35, 35, MaxSpeed, 1)
        Move_Index (-35, 35, MaxSpeed, 2)
        time.sleep(0.4)
       
  
  
def Perfect():
        Move_Index (55, -55, MaxSpeed-3, 1)
        Move_Index (55, -55, MaxSpeed-3, 2)
        Move_Middle (0, -0, MaxSpeed, 1)
        Move_Middle (0, -0, MaxSpeed, 2)
        Move_Ring (-20, 20, MaxSpeed, 1)
        Move_Ring (-20, 20, MaxSpeed, 2)
        Move_Thumb (85, 10, MaxSpeed, 1)      
        Move_Thumb (-10, -85, MaxSpeed, 2)
  
def Victory():

        Move_Index (-15, 65, MaxSpeed, 1)
        Move_Index (-65, 15, MaxSpeed, 2)
        Move_Middle (-65, 15, MaxSpeed, 1)
        Move_Middle (-15, 65, MaxSpeed, 2)
        Move_Ring (90, -90, MaxSpeed, 1)
        Move_Ring (90, -90, MaxSpeed, 2)
        Move_Thumb (90, -90, MaxSpeed, 1)     
        Move_Thumb (90, -90, MaxSpeed, 2)


def Pinched():
        Move_Index (90, -90, MaxSpeed, 1)
        Move_Index (90, -90, MaxSpeed, 2)
        Move_Middle (90, -90, MaxSpeed, 1)
        Move_Middle (90, -90, MaxSpeed, 2)
        Move_Ring (90, -90, MaxSpeed, 1)
        Move_Ring (90, -90, MaxSpeed, 2)
        Move_Thumb (5, -75, MaxSpeed, 1)  
        Move_Thumb (75, -5, MaxSpeed, 2)

def Scissors():
 
    Victory() 
    for i in range(3):  
        time.sleep(0.2)
        Move_Index (-50, 20, MaxSpeed, 1)
        Move_Middle (-20, 50, MaxSpeed, 1)
        Move_Index (-20, 50, MaxSpeed, 2)
        Move_Middle (-50, 20, MaxSpeed, 2)
        
        time.sleep(0.2)
        Move_Index (-15, 65, MaxSpeed, 1)
        Move_Middle (-65, 15, MaxSpeed, 1)
        Move_Index (-65, 15, MaxSpeed, 2)
        Move_Middle (-15, 65, MaxSpeed, 2)
            

def Fuck():
        Move_Index (90, -90, MaxSpeed, 1)
        Move_Index (90, -90, MaxSpeed, 2)
        Move_Middle (-35, 35, MaxSpeed, 1)
        Move_Middle (-35, 35, MaxSpeed, 2)
        Move_Ring (90, -90, MaxSpeed, 1)
        Move_Ring (90, -90, MaxSpeed, 2)
        Move_Thumb (5, -75, MaxSpeed, 1)  
        Move_Thumb (75, -5, MaxSpeed, 2)


#Fingers

def Move_Index (Angle_1,Angle_2,Speed, Hand):
    if (Hand==1): #Right hand finger
        c.write_goal_speed(1, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(2, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_1[0]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_1[1]+Angle_2) 
        c.write_goal_position(1, Pos_1)
        c.write_goal_position(2, Pos_2)
        time.sleep(0.0002)

    if (Hand==2): #Left hand finger
        c.write_goal_speed(11, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(12, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_2[0]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_2[1]+Angle_2) 
        c.write_goal_position(11, Pos_1)
        c.write_goal_position(12, Pos_2)
        time.sleep(0.0002)

def Move_Middle(Angle_1,Angle_2,Speed, Hand):    
    if (Hand==1): #Right hand finger
        c.write_goal_speed(3, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(4, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_1[2]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_1[3]+Angle_2)
        c.write_goal_position(3, Pos_1)
        c.write_goal_position(4, Pos_2)
        time.sleep(0.0002)
    if (Hand==2): #Left hand finger
        c.write_goal_speed(13, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(14, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_2[2]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_2[3]+Angle_2)
        c.write_goal_position(13, Pos_1)
        c.write_goal_position(14, Pos_2)
        time.sleep(0.0002)

def Move_Ring(Angle_1,Angle_2,Speed, Hand):
    if (Hand==1): #Right hand finger    
        c.write_goal_speed(5, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(6, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_1[4]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_1[5]+Angle_2)
        c.write_goal_position(5, Pos_1)
        c.write_goal_position(6, Pos_2)
        time.sleep(0.0002)

    if (Hand==2): #Left hand finger
        c.write_goal_speed(15, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(16, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_2[4]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_2[5]+Angle_2)
        c.write_goal_position(15, Pos_1)
        c.write_goal_position(16, Pos_2)
        time.sleep(0.0002)

def Move_Thumb(Angle_1,Angle_2,Speed, Hand):
    if (Hand==1): #Right hand finger      
        c.write_goal_speed(7, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(8, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_1[6]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_1[7]+Angle_2)
        c.write_goal_position(7, Pos_1)
        c.write_goal_position(8, Pos_2)
        time.sleep(0.0002)

    if (Hand==2): #Left hand finger
        c.write_goal_speed(17, Speed)
        time.sleep(0.0002)
        c.write_goal_speed(18, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(MiddlePos_2[6]+Angle_1)
        Pos_2 = np.deg2rad(MiddlePos_2[7]+Angle_2)
        c.write_goal_position(17, Pos_1)
        c.write_goal_position(18, Pos_2)
        time.sleep(0.0002)

   

if __name__ == '__main__':
    main()



