#include <SCServo.h>

SCSCL sc;

// Side
int Side = 1; // replace "1" by "2" for left hand

//Speed 
// Right-hand hardware test: 6.9 rad/s completed a cycle; 7.0 rad/s failed.
int MaxSpeed = 1349; // 6.9 rad/s in servo counts per second
int CloseSpeed =750;

//Fingers middle poses 
int MiddlePos[8]={520,511,500,490,515,520,480,511}; // replace values by your calibration results


//Servo control
float Step = 0.293; // 300°/1024

void setup()
{
  Serial1.begin(1000000);
  //Serial.begin(115200);
  sc.pSerial = &Serial1;
  delay(1000);
}



void loop()
{
  
  OpenHand();delay(500);

  CloseHand();delay(3000);
  
  OpenHand_Progressive();delay(400);

  SpreadHand();delay(600);
  ClenchHand();delay(600);

  OpenHand();delay(200);

  Index_Pointing();delay(400);
  Nonono();delay(500);
 
  OpenHand();delay(300);

  Perfect();delay(800);

  OpenHand();delay(400);

  Victory();delay(1000);
  Scissors();delay(500);

  OpenHand();delay(400);

  Pinched(); delay(1000);

  Fuck();delay(800);

  

  
}



void OpenHand()
{
  Move_Index (-35, 35, MaxSpeed);
  Move_Middle (-35, 35, MaxSpeed);
  Move_Ring (-35, 35, MaxSpeed);
  Move_Thumb (-35, 35, MaxSpeed);

}

void CloseHand()
{
  Move_Index (90, -90, CloseSpeed);
  Move_Middle (90, -90, CloseSpeed);
  Move_Ring (90, -90, CloseSpeed);
  Move_Thumb (70, -70, CloseSpeed+200);
  
}

void OpenHand_Progressive()
{
  Move_Index (-35, 35, 1200); // Open Index
  delay(300);
  Move_Middle (-35, 35, 1200); // Open Middle
  delay(300);
  Move_Ring (-35, 35, 1200); // Open Ring
  delay(300);
  Move_Thumb (-35, 35, MaxSpeed); // Open Thumb 
}

void SpreadHand()
{
  if (Side==1) // Right Hand
  {
    Move_Index (4, 90, MaxSpeed);
    Move_Middle (-32, 32, MaxSpeed);
    Move_Ring (-90, -4, MaxSpeed);
    Move_Thumb (-90, -4, MaxSpeed);  
  } 
  else if (Side==2) // Left Hand
  {
    Move_Index (-60, 0, MaxSpeed);
    Move_Middle (-35, 35, MaxSpeed);
    Move_Ring (-4, 90, MaxSpeed);
    Move_Thumb (-4, 90, MaxSpeed);  
  }
}

void ClenchHand()
{
  if (Side==1) // Right Hand
  {
    Move_Index (-60, 0, MaxSpeed);
    Move_Middle (-35, 35, MaxSpeed);
    Move_Ring (0, 70, MaxSpeed);
    Move_Thumb (-4, 90, MaxSpeed);  
  }


  else if (Side==2) // Left Hand
  {
    Move_Index (0, 60, MaxSpeed);
    Move_Middle (-35, 35, MaxSpeed);
    Move_Ring (-70, 0, MaxSpeed);
    Move_Thumb (-90, -4, MaxSpeed);
  }
  
}



void Index_Pointing()
{
  Move_Index (-40, 40, MaxSpeed);
  Move_Middle (90, -90, MaxSpeed);
  Move_Ring (90, -90, MaxSpeed);
  Move_Thumb (90, -90, MaxSpeed);
}

void Nonono()
{
  Index_Pointing();
  for (int i=0;i<3;i++)
  {
    delay(300);
    Move_Index (-10, 80, MaxSpeed);
    delay(300);
    Move_Index (-80, 10, MaxSpeed);
  }
  Move_Index (-35, 35, MaxSpeed);
  delay(400);
}

void Perfect()
{
  if (Side==1) //Right Hand
  {
    Move_Index (50, -50, MaxSpeed);
    Move_Middle (0, -0, MaxSpeed);
    Move_Ring (-20, 20, MaxSpeed);
    Move_Thumb (65, 12, MaxSpeed);

  }
  else if (Side==2) // Left Hand
  {
    Move_Index (50, -50, MaxSpeed);
    Move_Middle (0, -0, MaxSpeed);
    Move_Ring (-20, 20, MaxSpeed);
    Move_Thumb (-12, -65, MaxSpeed);
  }
}

void Victory()
{
  if (Side==1) //Right Hand
  {
    Move_Index (-15, 65, MaxSpeed);
    Move_Middle (-65, 15, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (90, -90, MaxSpeed);

  }
  else if (Side==2) // Left Hand
  {
    Move_Index (-65, 15, MaxSpeed);
    Move_Middle (-15, 65, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (90, -90, MaxSpeed);
  }
}

void Pinched()
{
  if (Side==1) //Right Hand
  {
    Move_Index (90, -90, MaxSpeed);
    Move_Middle (90, -90, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (0, -75, MaxSpeed);

  }
  else if (Side==2) // Left Hand
  {
    Move_Index (90, -90, MaxSpeed);
    Move_Middle (90, -90, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (75, 0, MaxSpeed);
  }
}

void Scissors()
{
  Victory();
  if (Side==1) //Right
  {
    for (int i=0;i<3;i++)
    {
      delay(300);
      Move_Index (-50, 20, MaxSpeed);
      Move_Middle (-20, 50, MaxSpeed);
      
      delay(300);
      Move_Index (-15, 65, MaxSpeed);
      Move_Middle (-65, 15, MaxSpeed);
    }  

  }
  else if (Side==2) // Left Hand
  {
    for (int i=0;i<3;i++)
    {
      delay(300);
      Move_Index (-20, 50, MaxSpeed);
      Move_Middle (-50, 20, MaxSpeed);
      
      delay(300);
      Move_Index (-65, 15, MaxSpeed);
      Move_Middle (-15, 65, MaxSpeed);
    }
  }
}


void Fuck()
{
  if (Side==1) //Right Hand
  {
    Move_Index (90, -90, MaxSpeed);
    Move_Middle (-35, 35, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (0, -75, MaxSpeed);

  }
  else if (Side==2) // Left Hand
  {
    Move_Index (90, -90, MaxSpeed);
    Move_Middle (-35, 35, MaxSpeed);
    Move_Ring (90, -90, MaxSpeed);
    Move_Thumb (75, 5, MaxSpeed);
  }
}

void Move_Index (float Pos_1, float Pos_2, int Speed)
{
  sc.RegWritePos(1, MiddlePos[0]+Pos_1/Step, 0, Speed);sc.RegWritePos(2, MiddlePos[1]+Pos_2/Step, 0, Speed);sc.RegWriteAction();
}
void Move_Middle (float Pos_1, float Pos_2, int Speed)
{
  sc.RegWritePos(3, MiddlePos[2]+Pos_1/Step, 0, Speed);sc.RegWritePos(4, MiddlePos[3]+Pos_2/Step, 0, Speed);sc.RegWriteAction();
}
void Move_Ring (float Pos_1, float Pos_2, int Speed)
{
  sc.RegWritePos(5, MiddlePos[4]+Pos_1/Step, 0, Speed);sc.RegWritePos(6, MiddlePos[5]+Pos_2/Step, 0, Speed);sc.RegWriteAction();
}
void Move_Thumb (float Pos_1, float Pos_2, int Speed)
{
  sc.RegWritePos(7, MiddlePos[6]+Pos_1/Step, 0, Speed);sc.RegWritePos(8, MiddlePos[7]+Pos_2/Step, 0, Speed);sc.RegWriteAction();
}
  