' Robotling2 - basic
' The MIT Licence (MIT)
' Copyright (c) 2021-23 Thomas Euler
' 2021-11-07 - v0.15, Initial release
' 2022-02-04 - v0.16, CO2 sensor added
' 2022-09-27 - v0.17, Changes towards CO2 sensing behaviour
' 2022-10-29 - v1.00, CO2 bot's first release
' 2022-11-12 - v1.01, resorting pins
' 2023-02-18 - v1.11, small fixes, basic version (no display, no sensors)
' ---------------------------------------------------------------------------
' Assumed options:
'   OPTION COLOURCODE ON
'   OPTION DISPLAY 64, 80
'   OPTION CPUSPEED 133000
'   OPTION AUTORUN ON
'
' Display
'   None
' Cables
'   M1 - left legs (front left servo)
'   M2 - right legs (front right servo)
'   M3 - centre legs (center servo)
'   A0 -
'   A1 -
'   D0 -
'   A2 -
'   5V -
'   gd -
' ---------------------------------------------------------------------------
Option Base 0
Option Explicit

' Version information
Const R.Version      = 1.11
Const R.Name$        = "Robotling2"

' Sensor port pin definitions (robotling2 board)
Const R.TX           = 6     ' GP4  / COM2
Const R.RX           = 7     ' GP5
Const R.SDA          = 1     ' GP0  / I2C
Const R.SCL          = 2     ' GP1
Const R.A0           = 31    ' GP26 / ADC0
Const R.A1           = 32    ' GP27 / ADC1
Const R.A2           = 34    ' GP28 / ADC2
Const R.D0           = 5     ' GP3
Const R.D1           = 29    ' GP22

' Configuration (Robot)
Const R.SERVOS_ON    = 1     ' 0=Servos stay off (for testing purposes)
Const R.VERBOSE      = 1     ' 0=No logging to the console
Const R.DEBUG        = 0     ' 0=No debugging messages

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Initialize hardware
GoTo InitRobot

' Start of main program
RobotMain:
  Dim integer turns = 0, running = 1
  Dim integer dir = TURN_RIGHT

  ' Start moving
  R.Spin 500
  Do While running

    ' Walk straight
    R.Move FORWARD, 60
    R.Spin 4000

    ' Turn
    R.Move dir, 60
    R.Spin 5000

    ' Change direction of turn every 4 turns
    If turns Mod 4 = 0 Then
      dir = Choice(dir = TURN_LEFT, TURN_RIGHT, TURN_LEFT)
    EndIf
    Inc turns, 1
  Loop

  ' Shutting down
  R.Stop
  R.Spin 2000, END_OF_MOVE
  R.Shutdown
  R.Log NONE, "Done"
End

' ============================================================================
' From here on, internal stuff
'
InitRobot:
  ' Log related definitions
  Const NONE          = 0
  Const INFO          = 1
  Const ERR           = 2
  Dim R.MsgType$(2) length 5
  Data "", "Info", "Error"
  Read R.MsgType$()

  R.Log NONE, "Initializing ..."
  R.Log INFO, R.Name$ +" v" +Str$(R.Version, 1,2)

  ' Robot commands and command parameters
  Const STOP           = 0
  Const FORWARD        = 1
  Const TURN_LEFT      = 2
  Const TURN_RIGHT     = 3
  Const BACKWARD       = 4

  Const END_OF_MOVE    = 1

  ' Robot states
  Const RBOT_NONE      = 0
  Const RBOT_IDLE      = 1
  Const RBOT_WALK      = 2
  Const RBOT_BACKING   = 3
  Const RBOT_STOPPING  = 4
  Const RBOT_TURN_L    = 5
  Const RBOT_TURN_R    = 6
  Dim R.State$(6) length 9
  Data "None", "Idle", "Walking", "Backing"
  Data "Stopping", "LeftTurn", "RightTurn"
  Read R.State$()

  ' Robot control update parameters
  Const SPIN_STEP_MS   = 50

 ' Motor definitions and calibration
  Const SERV_STEP_MS   = 15
  Const SERV_MAX_VEL   = 100
  Const SERV_FREQ_HZ   = 100
  Dim integer _serv_range_us(1,2)  = (840,1640, 1040,1840, 1790,2190)
  Dim integer _serv_range_deg(1,2) = (-40, 40, -40, 40, -20, 20)

  ' Gait
  Const GAIT_I_STOP    = 0
  Const GAIT_I_WALK    = 1
  Const GAIT_I_TURN    = 1
  Dim integer _gait(4,4)
  Data   0,  0,  0, 600, -1 ' stop
  Data   0,  0, 10, 200,  2 ' walk
  Data  20, 20, 10, 400,  3
  Data  20, 20,-10, 200,  4
  Data -20,-20,-10, 400,  1
  Read _gait()

  ' Internal pins (Robotling2 board)
  Const R.M1  = 14 ' Servo motors
  Const R.M2  = 27
  Const R.M3  = 4
  Const R.LED = 15 ' Onboard LED

  ' Initialize hardware
  R.Init

  ' Move servos to neutral (stop) position
  R.MoveServos 0, 0,0,0
  R.Stop
  R.Spin 1000, END_OF_MOVE

  R.Log NONE, "Ready."
  GoTo RobotMain

' -----------------------------------------------------------------------------
Sub R.Init
  ' Prepare hardware
  Local integer i

  ' Control parameters
  Dim integer _state = RBOT_NONE, _newState = RBOT_NONE
  Dim integer _curMode = STOP, _curVel = 0
  Dim integer _gaitPtr = -1, _dir(2) = (1,1,1)

  ' Servo motors
  Dim integer _serv_dt(2), _serv_da(2), _serv_nSteps = 0
  Dim float _serv_curPos(1,2) = (0,0,0,0,0,0)
  Dim float _serv_trgPos(1,2) = (0,0,0,0,0,0)
  Dim float _serv_step(1,2) = (0,0,0,0,0,0)
  For i=0 To 2
    _serv_dt(i) = _serv_range_us(1,i) -_serv_range_us(0,i)
    _serv_da(i) = _serv_range_deg(1,i) -_serv_range_deg(0,i)
  Next i

  ' Onboard LED
  SetPin R.LED, DOUT

  ' Power up
  R.Power 1

  ' Timers to keep servo motors moving and robot walking
  SetTick SERV_STEP_MS, _cb_moveServos, 1
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub R.Power(state)
  ' Power robot up or down
  Static integer _curr_state = 0
  If state = _curr_state Then Exit Sub
  If state = 0 Then
    ' Servos off
    R.ServoPower 0
    _curr_state = 0
  Else
    ' Servos on, robot in neutral, if requested
    R.ServoPower 1
    _curr_state = 1
  EndIf
End Sub

' ---------------------------------------------------------------------------
' Robot movement commands
'
Sub R.Move(mode, vel)
  ' Let the robot walk (FORWARD, TURN_LEFT, etc.) at 'vel' percent speed
  If mode = _curMode Then Exit Sub
  _curMode = mode
  _curVel = Max(Min(SERV_MAX_VEL-10, vel), 0)
  Select Case mode
    Case FORWARD
      R.Log INFO, "Move forward (" +Str$(_curVel, 3) +"%)"
      _newState = RBOT_WALK
    Case BACKWARD
      R.Log INFO, "Move backward (" +Str$(_curVel, 3) +"%)"
      _newState = RBOT_BACKING
    Case TURN_LEFT
      R.Log INFO, "Turn left"
      _newState = RBOT_TURN_L
    Case TURN_RIGHT
      R.Log INFO, "Turn right"
      _newState = RBOT_TURN_R
    Case STOP
      R.Stop
    Case Else
      R.Log ERR, "Unknown mode"
      _newState = RBOT_NONE
  End Select
End Sub

Sub R.Stop
  ' Stop the robot
  If _state <> RBOT_IDLE Then
    R.Log INFO, "Stop"
    _curVel = 0
    _newState = RBOT_STOPPING
  EndIf
End Sub

Sub R.Shutdown
  ' Switch off servor motors, RGB LED etc.
  Local integer i
  For i=1 To 5
    PWM i, OFF
  Next i
End Sub

Function R.Mode()
  R.Mode = _curMode
End Function

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Servo motor commands
'
Sub R.ServoPower(state)
  ' Switch servos on/off
  If R.SERVOS_ON = 0 Then Exit Sub
  If state Then
    SetPin R.M1, PWM5A
    SetPin R.M2, PWM2B
    SetPin R.M3, PWM1A
  Else
    PWM 5, OFF
    PWM 2, OFF
    PWM 1, OFF
  EndIf
End Sub

Sub R.MoveServos(dt_ms, a1_deg, a2_deg, a3_deg)
  ' Move servo motors within `dt_ms` to `ax_deg`
  Local integer i, n, a(2)=(a1_deg, a2_deg, a3_deg)
  n = Int(Max(0, dt_ms) /SERV_STEP_MS +1)
  For i=0 To 2
    a(i) = Min(Max(a(i), _serv_range_deg(0,i)), _serv_range_deg(1,i))
    _serv_trgPos(0,i) = a(i)
    _serv_trgPos(1,i) = _Angle2Duty(i, a(i))
    _serv_step(0,i) = (a(i) -_serv_curPos(0,i))/n
    _serv_step(1,i) = (_serv_trgPos(1,i) -_serv_curPos(1,i))/n
    If n = 1 Then
      _serv_curPos(0,i) = a(i)
      _serv_curPos(1,i) = _serv_trgPos(1,i)
    EndIf
    'Print i, _serv_curPos(0,i), a(i), _serv_trgPos(1,i), _serv_step(1,i), n
  Next i
  If n = 1 And R.SERVOS_ON Then
    PWM 5, SERV_FREQ_HZ, _serv_trgPos(1,0)
    PWM 2, SERV_FREQ_HZ,,_serv_trgPos(1,1)
    PWM 1, SERV_FREQ_HZ, _serv_trgPos(1,2)
    _serv_nSteps = 0
  Else
    _serv_nSteps = n
  EndIf
End Sub

Function R.isMoving() As integer
  ' Return 1 if servo motors are still moving
  R.isMoving = _serv_nSteps > 0
End Function

' -----------------------------------------------------------------------------
' LED-related
'
Sub R.SetLED(state)
  Pin(R.LED) = state > 0
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Other commands
'
Sub R.Spin(tout_ms, untilMoveDone)
  ' Wait for maximally `tout_ms' or until condition
  '
  Local integer t, t0=Timer, n=Max(0, tout_ms) /SPIN_STEP_MS
  Do
    ' Update stuff (e.g. gait)
    t = Timer
    _cb_gait
    If untilMoveDone = 1 And _serv_nSteps = 0 Then Exit Sub

    ' Pause for the rest of the time slot
    t = Timer -t
    If R.DEBUG And t > SPIN_STEP_MS Then
      Print "Spin too long", t
    Else
      Pause Max(1, SPIN_STEP_MS -t)
    EndIf
    Inc n, -1
  Loop Until (n = 0) Or ((Timer -t0) > tout_ms)
End Sub

Sub R.Log(type, msg$)
  ' Log a message
  If Not(R.VERBOSE) Then Exit Sub
  Local integer i = Min(Max(0, type), Bound(R.MsgType$()))
  Print R.MsgType$(i),"|" +msg$
End Sub

' --------------------------------------------------------------------------
' Internal methods
'
Sub _cb_moveServos
  ' Keeps the servos updated (Timer 1)
  If _serv_nSteps > 0 And R.SERVOS_ON Then
    Local integer i
    For i=0 To 2
      _serv_curPos(0,i) = _serv_curPos(0,i) +_serv_step(0,i)
      _serv_curPos(1,i) = _serv_curPos(1,i) +_serv_step(1,i)
    Next i
    PWM 5, SERV_FREQ_HZ, _serv_curPos(1,0)
    PWM 2, SERV_FREQ_HZ,,_serv_curPos(1,1)
    PWM 1, SERV_FREQ_HZ, _serv_curPos(1,2)
    _serv_nSteps = _serv_nSteps -1
    If _serv_nSteps = 0 Then
      PWM 5, SERV_FREQ_HZ, _serv_trgPos(1,0)
      PWM 2, SERV_FREQ_HZ,,_serv_trgPos(1,1)
      PWM 1, SERV_FREQ_HZ, _serv_trgPos(1,2)
      For i=0 To 2
        _serv_curPos(0,i) = _serv_trgPos(0,i)
        _serv_curPos(1,i) = _serv_trgPos(1,i)
      Next i
    EndIf
  EndIf
End Sub

Sub _cb_gait
  ' Keeps gait updated and robot walking (Timer 2)
  Local integer i, a0,a1, dt
  R.SetLED 1
  If _newState = RBOT_STOPPING Then
    ' Stop robot immediately
    i = GAIT_I_STOP
    R.MoveServos _gait(3,i), _gait(0,i), _gait(1,i), _gait(2,i)
    _gaitPtr = _gait(4,i)
    _state = RBOT_STOPPING
    _newState = RBOT_NONE
    R.Log NONE, "Stopping ..."
  Else
    If _serv_nSteps = 0 Then
      ' Servo move has ended
      If _state = RBOT_STOPPING Then
        ' Robot has stopped
        _state = RBOT_IDLE
        R.Log NONE, "Idle."
      Else
        dt = Int(_gait(3,i) *(SERV_MAX_VEL -_curVel)/100)
        If _newState = RBOT_NONE Then
          ' No new state requested
          If _gaitPtr >= 0 Then
            ' If gait ongoing, start next servo move
            i = _gaitPtr
            a0 = _gait(0,i) *_dir(0)
            a1 = _gait(1,i) *_dir(1)
            R.MoveServos dt, a0, a1, _gait(2,i)
            _gaitPtr = _gait(4,i)
          EndIf
        ElseIf _newState <> RBOT_IDLE Then
          ' A new state was requested ...
          Math set 1, _dir()
          If _newState = RBOT_TURN_L Then
            i = GAIT_I_TURN
            _dir(0) = -1
          ElseIf _newState = RBOT_TURN_R Then
            i = GAIT_I_TURN
            _dir(1) = -1
          Else
            i = GAIT_I_WALK
            If _newState = RBOT_BACKING Then
              Math set -1, _dir()
            EndIf
          EndIf
          a0 = _gait(0,i) *_dir(0)
          a1 = _gait(1,i) *_dir(1)
          R.MoveServos dt, a0, a1, _gait(2,i)
          _gaitPtr = _gait(4,i)
          _state = _newState
          _newState = RBOT_NONE
          R.Log INFO, "New state ->" +R.State$(_state)
        EndIf
      Else
        R.Log ERR, "Should not happen"
      EndIf
    EndIf
  EndIf
  R.SetLED 0
End Sub

Function _Angle2Duty(i, a_deg) As float
  ' Converts angle (deg) into duty cycle (%) for servo motor i
  Local float a, r, t
  a = Min(Max(a_deg, _serv_range_deg(0,i)), _serv_range_deg(1,i))
  r = (a -_serv_range_deg(0,i)) /Abs(_serv_da(i))
  t = _serv_range_us(0,i) +_serv_dt(i) *r
  _Angle2Duty = t /SERV_FREQ_HZ
End Function

' ---------------------------------------------------------------------------                   
