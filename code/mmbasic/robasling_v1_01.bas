' Robotling2
' The MIT Licence (MIT)
' Copyright (c) 2021 Thomas Euler
' 2021-11-07 - v1.00, Initial release
' 2021-11-12 - v1.01, small changes (gait)
'
' ---------------------------------------------------------------------------
' Assumed options:
'   OPTION COLOURCODE ON
'   OPTION DISPLAY 64, 80
'   OPTION CPUSPEED 133000
' With PicoDisplay:
'   OPTION SYSTEM SPI GP18,GP19,GP20
'   OPTION LCDPANEL ST7789_135, RLANDSCAPE, GP16,GP22,GP17
'   OPTION GUI CONTROLS 10
' ---------------------------------------------------------------------------
Option Base 0
Option Explicit

' Sensor port pin definitions (robotling2 board)
Const R.TX        = 6  ' COM2
Const R.RX        = 7  '
Const R.SDA       = 1  ' I2C
Const R.SCL       = 2
Const R.A0        = 31 ' ADC0
Const R.A1        = 32 ' ADC1
Const R.A2        = 34 ' ADC2
Const R.D0        = 5

' Configuration
Const R.SERVOS_ON = 1  ' 0=Servos stay off (for testing purposes)
Const R.DISPLAY   = 1  ' 0=PicoDisplay not used
Const R.VERBOSE   = 0  ' 0=No logging to the console

Const R.D_CLIFF   = 20 ' Distance threshold (cm) for cliff
Const R.D_OBJECT  = 5  ' Distance threshold (cm) for obstacle
Const R.D_MAX     = 30 ' Max. displayed distance (cm)

' Initialize hardware
GoTo InitRobot

' Start of main program
RobotMain:
  Dim integer n, running = 0, ev = 0

  ' Initialize sensors
  R.CreateSensor 0, R.TX, POLOLU_TOF_50, 3, USE_PULSIN
  R.CreateSensor 1, R.RX, POLOLU_TOF_50, 3, USE_PULSIN
  R.CreateSensor 2, R.D0, POLOLU_TOF_50, 3, USE_PULSIN

  ' Create GUI controls (if display is enabled)
  R.Splash 2000
  R.CreateGUI

  ' Start heartbeat
  R.SetRGBLED C_READY, START_BEAT

  ' Set key A to start and key X to stop robot
  Dim integer abort_requested = 0
  Sub StartProg
    running = 1
  End Sub
  Sub AbortProg
    R.Log INFO, "User pressed key A"
    abort_requested = 1
  End Sub
  R.OnKey R.KEY_A, "StartProg"
  R.OnKey R.KEY_X, "AbortProg"

  ' Possible events
  Const EV_NONE   = 0
  Const EV_OBJ_R  = &B000001
  Const EV_OBJ_C  = &B000010
  Const EV_OBJ_L  = &B000100
  Const EV_OBJ    = &B000111
  Const EV_CLF_R  = &B001000
  Const EV_CLF_C  = &B010000
  Const EV_CLF_L  = &B100000
  Const EV_CLF    = &B111000

  ' Wait for key A to start program
  Do While Not(running): R.Spin 100: Loop

  ' Start moving
  Do While running
    R.Spin 100

    ' Check for object and/or cliff
    ev = 0
    ev = ev Or Choice(R.Sensor(2) < R.D_OBJECT, EV_OBJ_R, 0)
    ev = ev Or Choice(R.Sensor(2) > R.D_CLIFF, EV_CLF_R, 0)
    ev = ev Or Choice(R.Sensor(1) < R.D_OBJECT, EV_OBJ_C, 0)
    ev = ev Or Choice(R.Sensor(1) > R.D_CLIFF, EV_CLF_C, 0)
    ev = ev Or Choice(R.Sensor(0) < R.D_OBJECT, EV_OBJ_L, 0)
    ev = ev Or Choice(R.Sensor(0) > R.D_CLIFF, EV_CLF_L, 0)

    ' Respond to event
    If ev = 0 Then
      ' Nothing detected, just walk ahead
      R.SetRGBLED C_READY
      R.Move FORWARD, 200
    ElseIf ev And EV_CLF Then
      ' Some cliff detected
      R.SetRGBLED C_DETECT_CLIFF
      R.Move BACKWARD, 100
      R.Spin 2000
      R.Move Choice(Rnd() > 0.5, TURN_LEFT, TURN_RIGHT), 100
      R.Spin 2000
    ElseIf ev And EV_OBJ Then
      ' Some object detected
      R.SetRGBLED C_DETECT_OBJ
      If ev And EV_OBJ_R Then
        R.Move TURN_LEFT, 150
        R.Spin 2000
      ElseIf ev And EV_OBJ_L Then
        R.Move TURN_RIGHT, 150
        R.Spin 2000
      EndIf
    EndIf

    ' Check if still running
    running = Not(abort_requested)
  Loop

  ' Shutting down
  R.Stop
  R.Spin 2000, END_OF_MOVE
  R.Shutdown
  Print "Done"
End

' ---------------------------------------------------------------------------
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

  ' Version information
  Const R.Version      = 1.01
  Const R.Name$        = "Robotling2"
  R.Log INFO, R.Name$ +" v" +Str$(R.Version, 1,2)

  ' Robot commands and command parameters
  Const STOP           = 0
  Const FORWARD        = 1
  Const TURN_LEFT      = 2
  Const TURN_RIGHT     = 3
  Const BACKWARD       = 4

  Const END_OF_MOVE    = 1
  Const START_BEAT     = 1
  Const STOP_BEAT      = 2
  Const USE_PULSIN     = 1

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

  ' Colors
  Const C_READY        = RGB(8,64,0)
  Const C_OK           = RGB(96,255,0)
  Const C_WARN         = RGB(ORANGE)
  Const C_DETECT_CLIFF = RGB(RED)
  Const C_DETECT_OBJ   = RGB(ORANGE)

  ' Robot control parameters
  Const SPIN_STEP_MS   = 50
  Const RGBLED_STEPS   = 8

  ' Sensor definitions
  Const MAX_SENSORS    = 3
  Const MAX_ISR_PULSE  = 3
  Const MAX_AV_STEPS   = 5
  Const SHARP_IR_15    = 1 ' GP2Y0AF15X, 1.5-15 cm, analog
  Const POLOLU_TOF_50  = 2 ' #4064, 1-50 cm, pulse-width

  ' Motor definitions and calibration
  Const SERV_STEP_MS   = 15
  Const SERV_MAX_VEL   = 250
  Const SERV_FREQ_HZ   = 100
  Dim integer _serv_range_us(1,2)  = (1090, 1910, 1020, 1820, 1210, 1645)
  Dim integer _serv_range_deg(1,2) = (-40, 40, -40, 40, -20, 20)

  ' Gait
  Const GAIT_I_STOP    = 0
  Const GAIT_I_WALK    = 1
  Const GAIT_I_TURN    = 1
  Dim integer _gait(4,5)
  Data   0,  0,  0, 600, -1 ' stop
  Data   0,  0, 10, 200,  2 ' walk
  Data  20, 20, 10, 400,  3
  Data  20, 20,-10, 200,  4
  Data -20,-20,-10, 400,  5
  Data -20,-20, 10, 200,  2
  Read _gait()

  ' Internal pins (Robotling2 board)
  Const R.M1    = 14 ' Servo motors
  Const R.M2    = 27
  Const R.M3    = 4
  Const R.LED   = 15 ' Onboard LED

  ' PicoDisplay-related definitions
  Dim integer _is_gui_ready = 0
  Dim integer _keyPins(3) = (16,17,19,20)
  Dim string _keyFuncs$(3) = ("","","","")
  Const R.KEY_A = 0
  Const R.KEY_B = 1
  Const R.KEY_X = 2
  Const R.KEY_Y = 3

  ' Initialize hardware
  R.Init

  ' Move servos to neutral (stop) position
  R.MoveServos 0, 0,0,0
  R.Stop
  R.Spin 1000, END_OF_MOVE
  R.Log NONE, "Ready."
  GoTo RobotMain

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub R.Init
  ' Prepare hardware
  Local integer i

  ' Control parameters
  Dim integer _state = RBOT_NONE, _newState = RBOT_NONE
  Dim integer _curMode = STOP, _curVel = 0
  Dim integer _gaitPtr = -1, _dir(2) = (1,1,1)

  ' Sensors
  Dim _sensors(MAX_SENSORS-1, 7), R.Sensor(MAX_SENSORS-1)
  For i=0 To MAX_SENSORS-1
    _sensors(i,0) = NONE ' Type
    _sensors(i,1) = -1   ' Pin
    _sensors(i,2) = 0    ' unused
    _sensors(i,3) = -1   ' ISR, if any
    _sensors(i,4) = 1    ' no averaging
    _sensors(i,5) = 0    ' index in raw data ring buffer
    _sensors(i,6) = 0    ' sensor mode
    R.Sensor(i)   = 0    ' last value
  Next i
  Dim _ISRPulse(MAX_ISR_PULSE-1, 3)
  For i=0 To MAX_ISR_PULSE-1
    _ISRPulse(i,0) = -1  ' Pin
    _ISRPulse(i,1) = 0   ' time when pin went high
    _ISRPulse(i,2) = 0   ' Length of last pulse in ms
  Next i
  Math set -1, _ISRPulse()
  Dim integer _nISRPulse = 0
  Dim float _sensRaw(MAX_SENSORS-1, MAX_AV_STEPS-1)
  Math set 0, _sensRaw()

  ' Servo motors
  Dim integer _serv_dt(2), _serv_da(2), _serv_nSteps = 0
  Dim float _serv_curPos(1,2) = (0,0,0,0,0,0)
  Dim float _serv_trgPos(1,2) = (0,0,0,0,0,0)
  Dim float _serv_step(1,2) = (0,0,0,0,0,0)
  For i=0 To 2
    _serv_dt(i) = _serv_range_us(1,i) -_serv_range_us(0,i)
    _serv_da(i) = _serv_range_deg(1,i) -_serv_range_deg(0,i)
  Next i
  If R.SERVOS_ON Then
    SetPin R.M1, PWM5A
    SetPin R.M2, PWM2B
    SetPin R.M3, PWM1A
  EndIf

  ' Onboard LED
  SetPin R.LED, DOUT

  ' Pico Display related
  If R.DISPLAY = 1 Then
    Dim _gui_t_sens, _gui_t_bat
    Dim integer _rgbLED_i = 0, _rgbLED_n = 1, _rgbLED_col = 0
    SetPin 9, PWM3A
    SetPin 10, PWM3B
    SetPin 11, PWM4A
  EndIf
  R.SetRGBLED 0

  ' Timers to keep servo motors moving and robot walking
  SetTick SERV_STEP_MS, _cb_moveServos, 1
End Sub

' ---------------------------------------------------------------------------
' Robot movement commands
'
Sub R.Move(mode, vel)
  ' Let the robot walk (FORWARD, TURN_LEFT, etc.) at 'vel' percent speed
  _curVel = Max(Min(SERV_MAX_VEL, vel), 0)
  If mode = _curMode Then Exit Sub
  _curMode = mode
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
  If R.DISPLAY Then
    CLS
  EndIf
End Sub

Function R.Mode()
  R.Mode = _curMode
End Function
' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Sensor commands
'
Sub R.CreateSensor(i, pin, type, nAv, mode)
  ' Initialize sensor # `i` of `type` connected to `pin`.
  ' `nAv` : >1 sliding average
  ' `mode`: depends on sensor
  '         SHARP_IR_15   : mode ignored
  '         POLOLU_TOF_50 : 0=use interrupts, 1=use Pulsin
  If i < 0 Or i >= MAX_SENSORS Then
    R.Log ERR, "Sensor index out of range"
    Exit Sub
  EndIf
  Local string s$ = ""
  Local integer n = Min(Max(1, nAv), MAX_AV_STEPS)
  _sensors(i,0) = type
  _sensors(i,1) = pin
  _sensors(i,4) = n
  _sensors(i,6) = mode
  Select Case type
    Case NONE
      SetPin pin, OFF
    Case SHARP_IR_15
      SetPin pin, AIN
      s$ = "Sharp IR analog"
    Case POLOLU_TOF_50
      If mode = 1 Then
        SetPin pin, DIN
      Else
        If _nISRPulse >=  MAX_ISR_PULSE Then
          R.Log ERR, "All pulse ISRs used"
          Exit Sub
        Else
          _ISRPulse(_nISRPulse,0) = pin
          _sensors(i,3) = _nISRPulse
          Select Case _nISRPulse
            Case 0: SetPin pin, INTB, _cb_Pulse0
            Case 1: SetPin pin, INTB, _cb_Pulse1
            Case 2: SetPin pin, INTB, _cb_Pulse2
          End Select
          _nISRPulse = _nISRPulse +1
        EndIf
      EndIf
      s$ = "Pololu ToF PW"
    Case Else
      R.Log Err, "Invalid sensor type"
      Exit Sub
  End Select
  If Len(s$) > 0 Then
    s$ = "Sensor #" +Str$(i) +s$ +" at " +Str$(pin)
    s$ = s$ +Choice(n > 1, " (mean of " +Str$(n) +")", "")
    R.Log INFO, s$
  EndIf
End Sub

Function R.Dist_cm(i)
  ' Return measured distance in cm, if sensor # `i` is ranging sensor
  If i >= 0 And i < MAX_SENSORS Then
    Local float x,raw
    If _sensors(i,0) = SHARP_IR_15 Then
      ' TODO: Check calculation
      x = 4095 *Pin(_sensors(i,1))/3.3
      R.Dist_cm = 1.325 +20.436*Exp(-0.00218*x) +24.613 *Exp(-0.0642*x)
      Exit Function
    ElseIf _sensors(i,0) = POLOLU_TOF_50 Then
      If _sensors(i,6) = 1 Then
        raw = Pulsin(_sensors(i,1), 5000, 5000)/1000
      Else
        raw = _ISRPulse(_sensors(i,3),2)
      EndIf
      x = Choice(raw < 1.01 Or raw >= 2.0, -1, Min(50, Max(0.5, 75 *(raw -1))))
      'Print Str$(x,6,2),, raw
      If _sensors(i,4) = 1 Then
        R.Dist_cm = x
      Else
        Local float buf(MAX_AV_STEPS-1)
        If x > 0 Then
          Local integer j = _sensors(i,5)
          _sensRaw(i,j) = x
          _sensors(i,5) = Choice(j < _sensors(i,4)-1, j+1, 0)
        EndIf
        Math SLICE _sensRaw(), i,, buf()
        R.Dist_cm = Math(SUM buf()) /_sensors(i,4)
      EndIf
      Exit Function
    EndIf
  EndIf
  R.Dist_cm = -1
End Function

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' PicoDisplay related commands
'
Sub R.SetLED(state)
  Pin(R.LED) = state > 0
End Sub

Sub R.SetRGBLED(rgb, mode)
  ' Set PicoDisplay LED to `rgb` w/ 8 bit per channel
  ' `mode`: 0=just set color, 1=restart pulsing, 2=stop pulsing
  If R.DISPLAY Then
    _rgbLED_col = rgb
    If mode = 0 Then Exit Sub
    _rgbLED_n = Choice(mode = 1, RGBLED_STEPS, 0)
    _rgbLED_i = -_rgbLED_n
    _cb_updateRGBLED
  EndIf
End Sub

Sub R.Splash(t_ms)
  ' Splash screen
  If R.DISPLAY Then
    Local integer x1,y1, fh, c = RGB(white)
    fh = MM.Info(FONTHEIGHT) +5
    x1 = Int(MM.HRes/2 -1) +2*fh
    y1 = Int(MM.VRes/2 -1)
    CLS
    Text x1,y1, R.Name$, LMD, 2,1, c
    Text x1-fh,y1, "v" +Str$(R.Version, 1,2), LMD, 2,1, c
    Text x1-fh*2,y1, "MMBasic", LMD, 2,1, c
    Text x1-fh*3,y1, "v" +Str$(MM.Ver, 1,4), LMD, 2,1, c
    Pause t_ms
  EndIf
End Sub

Sub R.CreateGUI()
  ' Create GUI controls
  If Not(R.DISPLAY) Then Exit Sub
  Local integer dx,dy,x1,y1,x2, gp, fc,bc, val, col, iS, jS
  Local integer yc, fh

  ' Initialize
  gp = 4
  dx = 100
  dy = Int(MM.VRes/3 -1) -2*gp
  x1 = 0
  x2 = x1+dx+3*gp
  y1 = gp
  bc = RGB(white)
  fc = RGB(gray)
  fh = MM.Info(FONTHEIGHT) +5

  ' Clear screen and set font
  CLS
  Font #2, 1

  ' Create GUI controls
  y1 = y1 +gp
  GUI BARGAUGE #1, x1,y1, dx,dy, fc,bc, 0,R.D_MAX
  GUI CAPTION #2, "n/a", x2,y1+dy, CBD
  y1 = y1 +dy +gp
  GUI BARGAUGE #3, x1,y1, dx,dy, ,, 0,R.D_MAX
  GUI CAPTION #4, "n/a", x2,y1+dy, CBD
  y1 = y1 +dy +gp
  GUI BARGAUGE #5, x1,y1, dx,dy, ,, 0,R.D_MAX
  GUI CAPTION #6, "n/a", x2,y1+dy, CBD
  x1 = MM.HRes -1
  y1 = 1
  GUI Caption #7, "Bat ---- mV", x1,y1, LTD
  _is_gui_ready = 1
End Sub

Sub R.UpdateGUI()
  ' Update GUI controls
  If Not(R.DISPLAY) Then Exit Sub
  Local integer i, val, col
  Local t
  t = Timer
  If t -_gui_t_sens > 100 Then
    For i=0 To 2
      val = R.Sensor(i)
      col = Choice(val > R.D_CLIFF Or val < R.D_OBJECT, C_WARN, C_OK)
      GUI BCOLOUR col, i*2+1
      CtrlVal(i*2 +1) = R.D_MAX -val
      CtrlVal(i*2 +2) = Str$(val, 3,0)
    Next i
    _gui_t_sens = t
  EndIf
  If t -_gui_t_bat > 2000 Then
    CtrlVal(7) = "Bat " +Str$(Pin(44)*3, 1,2) +" mV"
    _gui_t_bat = t
  EndIf
End Sub

Sub R.OnKey(key, cb$)
  ' Allow user to defined interrupt routines for switches
  If R.DISPLAY And key >= 0 And key < 4 Then
    _keyFuncs$(key) = cb$
    Select Case key
      Case R.KEY_A: SetPin _keyPins(key), INTL, _cb_keyA, PULLUP
      Case R.KEY_B: SetPin _keyPins(key), INTL, _cb_keyB, PULLUP
      Case R.KEY_X: SetPin _keyPins(key), INTL, _cb_keyX, PULLUP
      Case R.KEY_Y: SetPin _keyPins(key), INTL, _cb_keyY, PULLUP
    End Select
  EndIf
End Sub

Sub _cb_keyA
  If Len(_keyFuncs$(R.KEY_A)) > 0 Then Call (_keyFuncs$(R.KEY_A))
End Sub

Sub _cb_keyB
  If Len(_keyFuncs$(R.KEY_B)) > 0 Then Call (_keyFuncs$(R.KEY_B))
End Sub

Sub _cb_keyX
  If Len(_keyFuncs$(R.KEY_X)) > 0 Then Call (_keyFuncs$(R.KEY_X))
End Sub

Sub _cb_keyY
  If Len(_keyFuncs$(R.KEY_Y)) > 0 Then Call (_keyFuncs$(R.KEY_Y))
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Servo motor commands
'
Sub R.MoveServos(dt_ms, a1_deg, a2_deg, a3_deg)
  ' Move servo motors within `dt_ms` to `ax_deg`
  Local integer i, n, a(2) = (a1_deg, a2_deg, a3_deg)
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

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Other commands
'
Sub R.Spin(tout_ms, untilMoveDone)
  ' Wait for maximally `tout_ms' or until condition
  Local integer i,j, t,t0, dt, n = Max(0, tout_ms) /SPIN_STEP_MS
  t0 = Timer
  If R.DISPLAY And _is_gui_ready Then R.UpdateGUI
  Do
    t = Timer
    _cb_updateRGBLED
    _cb_updateSensors
    _cb_gait
    If untilMoveDone = 1 And _serv_nSteps = 0 Then Exit Sub
    t = Timer -t
    If t > SPIN_STEP_MS Then
      Print "Spin too long"
    Else
      Pause Max(1, SPIN_STEP_MS -t)
    EndIf
    n = n -1
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
' ISRs to measure the length of pulses w/o having to wait for the result
' (other than with PULSIN)
Sub _cb_pulse0
  If Pin(_ISRPulse(0,0)) Then _ISRPulse(0,1) = Timer: Exit Sub
  _ISRPulse(0,2) = Timer -_ISRPulse(0,1)
End Sub

Sub _cb_pulse1[B
  If Pin(_ISRPulse(1,0)) Then _ISRPulse(1,1) = Timer: Exit Sub
  _ISRPulse(1,2) = Timer -_ISRPulse(1,1)
End Sub

Sub _cb_pulse2
  If Pin(_ISRPulse(2,0)) Then _ISRPulse(2,1) = Timer: Exit Sub
  _ISRPulse(2,2) = Timer -_ISRPulse(2,1)
End Sub

Sub _cb_updateSensors
  ' Update sensor data -> _sensors(i,2)
  Local integer j
  For j=0 To MAX_SENSORS-1
    If _sensors(j,0) <> NONE Then R.Sensor(j) = R.Dist_cm(j)
  Next j
End Sub

Sub _cb_updateRGBLED
  ' Keep LED pulsing
  Local integer r,g,b
  r = Int(100*(_rgbLED_col >> 16)/255)
  g = Int(100*((_rgbLED_col And &H00FF00) >> 8)/255)
  b = Int(100*(_rgbLED_col And &HFF)/255)
  If _rgbLED_n > 0 Then
    Local float f = Abs(_rgbLED_i)/_rgbLED_n
    r = Int(r*f)
    g = Int(g*f)
    b = Int(b*f)
    If Sgn(_rgbLED_i) < 0 Then
      _rgbLED_i = Choice(Abs(_rgbLED_i) > 0, _rgbLED_i+1, 1)
    Else
      _rgbLED_i = Choice(_rgbLED_i < _rgbLED_n, _rgbLED_i+1, -(_rgbLED_n-1))
    EndIf
  EndIf
  PWM 3, 1000, 100-r, 100-g
  PWM 4, 1000, 100-b,
End Sub

Sub _cb_moveServos
  ' Keeps the servos updated (Timer 1)
  If _serv_nSteps > 0 And R.SERVOS_ON Then
    Local integer i
    For i=0 To 2
      _serv_curPos(0,i) = _serv_curPos(0,i) +_serv_step(0,i)
      _serv_curPos(1,i) = _serv_curPos(1,i) +_serv_step(1,i)
      'Print _serv_curPos(1,i)
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
  Local integer i, a0,a1, v
  Local float vel = 1/Max(1, (_curVel/100))
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
        If _newState = RBOT_NONE Then
          ' No new state requested
          If _gaitPtr >= 0 Then
            ' If gait ongoing, start next servo move
            i = _gaitPtr
            a0 = _gait(0,i) *_dir(0)
            a1 = _gait(1,i) *_dir(1)
            R.MoveServos _gait(3,i)*vel, a0, a1, _gait(2,i)
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
          v = _gait(3,i)
          a0 = _gait(0,i) *_dir(0)
          a1 = _gait(1,i) *_dir(1)
          R.MoveServos v*vel, a0, a1, _gait(2,i)
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
  'Print "#", _state, _newState, i, _gaitPtr, _serv_nSteps
End Sub

Function _Angle2Duty(i, a_deg) As float
  ' Converts angle (deg) into duty cycle (%) for servo motor i
  Local float a, r, t
  a = Min(Max(a_deg, _serv_range_deg(0,i)), _serv_range_deg(1,i))
  r = (a -_serv_range_deg(0,i)) /Abs(_serv_da(i))
  t = _serv_range_us(0,i) +_serv_dt(i) *r
  _Angle2Duty = t /SERV_FREQ_HZ
End Function

' ---------------------------------------------------------------------------                                 