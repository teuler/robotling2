' Robotling2 - w/TOF +PicoDisplay
' The MIT Licence (MIT)
' Copyright (c) 2021-23 Thomas Euler
' 2021-11-07 - v0.15,  Initial release
' 2022-02-04 - v0.16,  CO2 sensor added
' 2022-09-27 - v0.17,  Changes towards CO2 sensing behaviour
' 2022-10-29 - v1.00,  CO2 bot's first release
' 2022-11-12 - v1.01,  resorting pins
' 2023-02-18 - v1.12,  small fixes, w/ToF sensors +PicoDisplay
' 2023-03-04 - v1.121, PWM assignment in one place; graceful exit on `Q`
' 2023-04-01 - v1.122, using new LIBRARY command
' ---------------------------------------------------------------------------
' Requirements:
'   `rbl_lib.bas` saved as library (new LIBRARY SAVE command)
'
' Assumed options:
'   OPTION COLOURCODE ON
'   OPTION DISPLAY 64, 80
'   OPTION AUTORUN ON
'   OPTION SYSTEM SPI GP18,GP19,GP20
'   OPTION LCDPANEL ST7789, RL, GP17,GP15,GP16,GP22
'
' Display
'   xxx
'
' Cables
'   M1 - left legs (front left servo)
'   M2 - right legs (front right servo)
'   M3 - centre legs (center servo)
'   A0 - left distance sensor out
'   A1 - centre distance sensor out
'   D0 - right distance sensor out
'   A2 -
'   5V - distance sensor common power
'   gd - distance sensor common ground
''
' ---------------------------------------------------------------------------
Print
R.Log 0, "Robotling2 - w/ToF +PicoDisplay"
R.Log 0, "-------------------------------"

' Start of main program
Dim integer n, ev = 0

' Initialize sensors
R.CreateSensor 0, R.A0, POLOLU_TOF_50, 3, USE_PULSIN
R.CreateSensor 1, R.A1, POLOLU_TOF_50, 3, USE_PULSIN
R.CreateSensor 2, R.D0, POLOLU_TOF_50, 3, USE_PULSIN

' Create GUI controls (if display is enabled)
R.Splash 3000
R.CreateGUI

' Start heartbeat, if RGB LED present
R.SetRGBLED C_READY, START_BEAT

' If PicoDisplay w/ buttons:
' Set key A to start and key X to stop robot
Dim integer abort_requested = 0
Sub StartProg
  R.running = 1
End Sub
Sub AbortProg
  R.Log INFO, "User pressed key A"
  abort_requested = 1
End Sub
R.OnKey R.KEY_A, "StartProg"
R.OnKey R.KEY_X, "AbortProg"
If R.DISPLAY = 2 Or R.DISPLAY = 0 Then StartProg

' Possible events
Const EV_NONE   = 0
Const EV_OBJ_R  = &B00000100
Const EV_OBJ_C  = &B00001000
Const EV_OBJ_L  = &B00010000
Const EV_OBJ    = &B00011100
Const EV_CLF_R  = &B00100000
Const EV_CLF_C  = &B01000000
Const EV_CLF_L  = &B10000000
Const EV_CLF    = &B11100000
Const EV_ANYOBS = &B11111100

' Wait for key A to start program
Do While Not(R.running): R.Spin 100: Loop

' Start moving
Do While R.running
  R.Spin 50

  ' Reset event variable
  ev = 0
  R.SetRGBLED C_READY

  ' Check if distance sensors detected something,
  ' i.e. obstacle and/or cliff
  ev = ev Or Choice(R.Sensor(0) < R.D_OBJECT, EV_OBJ_R, 0)
  ev = ev Or Choice(R.Sensor(0) > R.D_CLIFF, EV_CLF_R, 0)
  ev = ev Or Choice(R.Sensor(1) < R.D_OBJECT, EV_OBJ_C, 0)
  ev = ev Or Choice(R.Sensor(1) > R.D_CLIFF, EV_CLF_C, 0)
  ev = ev Or Choice(R.Sensor(2) < R.D_OBJECT, EV_OBJ_L, 0)
  ev = ev Or Choice(R.Sensor(2) > R.D_CLIFF, EV_CLF_L, 0)

  ' Respond to event
  If (ev And EV_ANYOBS) = 0 Then
    ' Nothing detected, just walk
    R.Move FORWARD, 50
  ElseIf ev And EV_CLF Then
    ' Some cliff detected
    R.SetRGBLED C_DETECT_CLIFF
    R.Move BACKWARD, 50
    R.Spin 2000
    R.Move Choice(Rnd() > 0.5, TURN_LEFT, TURN_RIGHT), 70
    R.Spin 2000
  ElseIf ev And EV_OBJ Then
    ' Some object detected
    R.SetRGBLED C_DETECT_OBJ
    If ev And EV_OBJ_R Then
      R.Move TURN_LEFT, 60
      R.Spin 1000 +Int(Rnd()*4000)
    ElseIf ev And EV_OBJ_L Then
      R.Move TURN_RIGHT, 60
      R.Spin 1000 +Int(Rnd()*4000)
    EndIf
  EndIf

  ' Check if still running
  R.running = R.running And Not(abort_requested)
Loop

' Shutting down
R.Stop
R.Spin 2000, END_OF_MOVE
R.Shutdown
R.Log NONE, "Done"

' ---------------------------------------------------------------------------                        
