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
' ---------------------------------------------------------------------------
' Assumed options:
'   OPTION COLOURCODE ON
'   OPTION DISPLAY 64, 80
'   OPTION CPUSPEED 133000
'   OPTION SYSTEM SPI GP18,GP19,GP20
'   OPTION LCDPANEL ST7789, RL, GP17,GP15,GP16,GP22
'   OPTION AUTORUN ON
'
' Display
'   xxx
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
' ---------------------------------------------------------------------------
Option Base 0
Option Explicit

' Version information
Const R.Version      = 1.121
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
Const R.DISP_ORIENT  = 1     ' 1=Rotate text, 0=As is
Const R.VERBOSE      = 1     ' 0=No logging to the console
Const R.DEBUG        = 0     ' 0=No debugging messages

Const R.D_CLIFF      = 20    ' Distance threshold (cm) for cliff
Const R.D_OBJECT     = 5     ' Distance threshold (cm) for obstacle
Const R.D_MAX        = 30    ' Max. displayed distance (cm)

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Initialize hardware
GoTo InitRobot

' Start of main program
RobotMain:
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
  Const C_READY        = RGB(96,255,0)
  Const C_OK           = RGB(96,255,0)
  Const C_WARN         = RGB(ORANGE)
  Const C_DETECT_CLIFF = RGB(RED)
  Const C_DETECT_OBJ   = RGB(ORANGE)
  Const C_TXT          = RGB(White)
  Const C_TXT_LO       = RGB(Gray)
  Const C_BKG          = RGB(Black)
  Const C_HEART        = RGB(Green)

  ' Robot control update parameters
  Const SPIN_STEP_MS   = 50
  Const RGBLED_STEPS   = 8
  Const GUI_RF_SENS_MS = 200
  Const GUI_RF_BATT_MS = 15000
  Const GUI_BKGL_MAX   = 100

  ' Sensor definitions
  Const MAX_SENSORS    = 3
  Const MAX_ISR_PULSE  = 3
  Const MAX_AV_STEPS   = 5
  Const SHARP_IR_15    = 1 ' GP2Y0AF15X, 1.5-15 cm, analog
  Const POLOLU_TOF_50  = 2 ' #4064, 1-50 cm, pulse-width

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
  ' Note: If you change the pins were, make sure you also change the
  ' respective PWM channels in `_PWM_M123` and `_SetPin_M123` at the very
  ' end of the program
  Const R.M1  = 14 ' Servo motor 1 (PWM5A)
  Const R.M2  = 27 ' Servo motor 2 (PWM2B)
  Const R.M3  = 4  ' Servo motor 3 (PWM1A)
  Const R.LED = 15 ' Onboard LED

  ' Determine display type, if any
  Const R.DISPLAY = R.GetDisplayType()

  ' PicoDisplay-related definitions
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

' -----------------------------------------------------------------------------
Sub R.Init
  ' Prepare hardware
  Local integer i

  ' Control parameters
  Dim integer _state = RBOT_NONE, _newState = RBOT_NONE
  Dim integer _curMode = STOP, _curVel = 0
  Dim integer _gaitPtr = -1, _dir(2) = (1,1,1)
  Dim integer R.running = 1

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

  ' Onboard LED
  SetPin R.LED, DOUT

  ' Display related
  Dim _gui_t_sens, _gui_t_bat
  Dim integer _is_gui_ready = 0, _gui_refresh = 1
  Dim integer _rgbLED_i = 0, _rgbLED_n = 0, _rgbLED_col = 0
  Select Case R.DISPLAY
    Case 1 ' 240x135 w/RGB LED and buttons
      _rgbLED_n = 1
      SetPin 9, PWM3A
      SetPin 10, PWM3B
      SetPin 11, PWM4A
    Case 2 '240x240
      _rgbLED_n = 0
  End Select
  R.SetRGBLED 0

  ' Power up
  R.Power 1

  ' Timers to keep servo motors moving and robot walking
  SetTick SERV_STEP_MS, _cb_moveServos, 1
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Function R.GetDisplayType()
  ' Try detecting the display (within limits)
  R.GetDisplayType = 0
  If MM.Info(LCDPANEL) = "ST7789" Then
    If MM.VRes*MM.HRes = 57600 Then
      ' Pimoroni 240x240 1.3" display
      R.GetDisplayType = 2
      R.Log INFO, "Pimoroni 240x240 1.3'' display"

    ElseIf MM.VRes*MM.HRes = 32400 Then
      ' Pimoroni 240x135 pico display pack (1)
      R.GetDisplayType = 1
      R.Log INFO "Pimoroni Pico display pack (240x135)"
    EndIf
  EndIf
  If R.GetDisplayType = 0 Then
    R.Log INFO, "No display detected"
  EndIf
End Function

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub R.Power(state)
  ' Power robot up or down
  Static integer _curr_state = 0
  If state = _curr_state Then Exit Sub
  If state = 0 Then
    ' Screen off, servos off
    Backlight 0
    R.ServoPower 0
    _curr_state = 0
  Else
    ' Screen on, servos on, robot in neutral, if requested
    Backlight GUI_BKGL_MAX
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
  R.ServoPower 0
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

' -----------------------------------------------------------------------------
' Display-related commands
'
Sub _text x%,y%, s$, c,bc, f%, ctr
  Local string a$ = Choice(ctr, "CT", "LT")
  Local integer _x = x%, _y = y%, _f = Choice(f% = 0, 3, f%)
  Local integer _fc = Choice(c = 0, C_TXT, c)
  Local integer _bc = Choice(bc = 0, C_BKG, bc)
  Text _x,_y, s$, a$,_f,, _fc,_bc
End Sub

Sub R.Splash(t_ms)
  ' Splash screen
  If R.DISPLAY = 0 Then Exit Sub
  Local integer x1,y1, fh
  Local string s$
  CLS
  Font #2, 1
  fh = MM.Info(FONTHEIGHT) +2
  x1 = Int(MM.HRes/2 -1)
  y1 = Int(MM.VRes/2 -1) -2*fh
  _text x1,y1, R.Name$, ,,2,1
  s$ = "v" +Str$(R.Version, 1,2)
  _text x1,y1+fh, s$, ,,2,1
  _text x1,y1+fh*2, "MMBasic", ,,2,1
  _text x1,y1+fh*3, "v" +Str$(MM.Ver, 1,4), ,,2,1
  Pause t_ms
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub R.CreateGUI()
  ' Create GUI
  ' (Define GUI elements here, if any; currently unused)
  If R.DISPLAY = 0 Then Exit Sub
  CLS
  Font #2, 1
  _is_gui_ready = 1
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub R.UpdateGUI(t_on_s)
  ' Update GUI controls; if `t_on_s` > 0 then update the GUI for that time
  ' span also when robot is sleeping
  If R.DISPLAY = 0 Or _is_gui_ready = 0 Then Exit Sub

  Local integer x=2, y=2, dx=Int(MM.HRes/3), dy=24, gp=16, x1=76
  Local integer col, i, val, w, dx2, dy2=dy*2+gp
  Local string s$
  Local t = Timer

  ' Status line
  If t -_gui_t_bat > GUI_RF_BATT_MS Then
    y = MM.VRes -22
    s$ = Str$(Pin(44)*3, 1,1) +"V "
    _text x,y, s$,,,2
    _gui_t_bat = t
  EndIf

  ' Distance sensor info
  If t -_gui_t_sens > GUI_RF_SENS_MS Then
    y = MM.VRes -50
    dx2 = dx -36
    For i=0 To 2
      val = R.Sensor(i)
      col = Choice(val > R.D_CLIFF Or val < R.D_OBJECT, C_WARN, C_OK)
      w = Max(1, Min(dx2 *val/R.D_MAX, dx2))
      _text x,y, Str$(val, 2,0),C_TXT,,2
      Box x+32,y,dx2,22,,C_TXT_LO,C_BKG
      Box x+32,y,w,22,,C_TXT_LO,col
      Inc x, dx
    Next i
    _gui_t_sens = t
  EndIf
End Sub

' -----------------------------------------------------------------------------
' LED-related
'
Sub R.SetLED(state)
  Pin(R.LED) = state > 0
End Sub

Sub R.SetRGBLED(rgb, mode)
  ' Set LED color, with `mode` being 0=just set color, 1=restart pulsing,
  ' 2=stop pulsing
  If R.DISPLAY = 0 Then Exit Sub
  _rgbLED_col = rgb
  If mode = 0 Then Exit Sub
  _rgbLED_n = Choice(mode = 1, RGBLED_STEPS, 0)
  _rgbLED_i = -_rgbLED_n
  _cb_updateRGBLED
End Sub

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
' Key-related routines (Pimoroni Pico display pack only)
'
Sub R.OnKey(key, cb$)
  ' Allow user to defined interrupt routines for switches
  If R.DISPLAY = 1 And key >= 0 And key < 4 Then
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
Sub R.ServoPower(state)
  ' Switch servos on/off
  If R.SERVOS_ON = 0 Then Exit Sub
  If state Then
    _SetPin_M123
  Else
    _PWM_M123 0,0,0, 1
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
    _PWM_M123 _serv_trgPos(1,0), _serv_trgPos(1,1), _serv_trgPos(1,2)
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
  '
  Local integer t, t0=Timer, n=Max(0, tout_ms) /SPIN_STEP_MS
  Do
    ' Update sensors, LEDs, gait, and GUI - depending on if the robot
    ' is sleeping
    t = Timer
    _cb_updateSensors
    _cb_updateRGBLED
    _cb_gait
    If R.running And UCase$(Inkey$) = "Q" Then
      ' Key `q` was pressed, shutdown robot ...
      R.running = 0
      n = 1
      R.Log INFO, "`Q` pressed, waiting for move to end ..."
    EndIf
    If untilMoveDone = 1 And _serv_nSteps = 0 Then Exit Sub
    R.UpdateGUI

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
' ISRs to measure the length of pulses w/o having to wait for the result
' (other than with PULSIN)
Sub _cb_pulse0
  If Pin(_ISRPulse(0,0)) Then _ISRPulse(0,1) = Timer: Exit Sub
  _ISRPulse(0,2) = Timer -_ISRPulse(0,1)
End Sub

Sub _cb_pulse1
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
  If R.DISPLAY = 0 Or _rgbLED_n = 0 Then Exit Sub
  Local integer r,g,b
  r = _rgbLED_col >> 16
  g = (_rgbLED_col And &H00FF00) >> 8
  b = _rgbLED_col And &HFF
  If R.DISPLAY = 2 Then
    ' Draw LED on screen
    Static t = Timer, state = 0
    If Timer -t > 400 Then
      Local col = RGB(r,g,b)
      Circle 224,228, 8, 1,1, C_TXT, Choice(state, col, C_BKG)
      state = Not state
      t = Timer
    EndIf
  ElseIf R.DISPLAY = 1 Then
    ' Manipulate built-in RGB LED
    r = Int(100*r/255)
    g = Int(100*g/255)
    b = Int(100*b/255)
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
    PWM 4, 1000, 100-b
  EndIf
End Sub

Sub _cb_moveServos
  ' Keeps the servos updated (Timer 1)
  If _serv_nSteps > 0 And R.SERVOS_ON Then
    Local integer i
    For i=0 To 2
      _serv_curPos(0,i) = _serv_curPos(0,i) +_serv_step(0,i)
      _serv_curPos(1,i) = _serv_curPos(1,i) +_serv_step(1,i)
    Next i
    _PWM_M123 _serv_curPos(1,0), _serv_curPos(1,1), _serv_curPos(1,2)
    _serv_nSteps = _serv_nSteps -1
    If _serv_nSteps = 0 Then
      _PWM_M123 _serv_trgPos(1,0), _serv_trgPos(1,1), _serv_trgPos(1,2)
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

' - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Sub _SetPin_M123
  SetPin R.M1, PWM5A
  SetPin R.M2, PWM2B
  SetPin R.M3, PWM1A
End Sub

Sub _PWM_M123 p0, p1, p2, off
  ' Set PWM for all walk servos or switch off (`off` == 1)
  If off Then
    PWM 5, OFF
    PWM 2, OFF
    PWM 1, OFF
  Else
    PWM 5, SERV_FREQ_HZ, p0
    PWM 2, SERV_FREQ_HZ,,p1
    PWM 1, SERV_FREQ_HZ, p2
  EndIf
End Sub

' ---------------------------------------------------------------------------                   
