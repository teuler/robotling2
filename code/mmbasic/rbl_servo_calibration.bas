' Robotling2 - Servo Calibration
' The MIT Licence (MIT)
' Copyright (c) 2021-2023 Thomas Euler
' 2023-04-07 - v1.00, Initial release
' 2023-04-08 - Now saves servo calibration values in a configuration file
' ----------------------------------------------------------------------------
Option Escape

' Some global constants
Const P_MAX_MS   = 2.2
Const P_MIN_MS   = 0.8
Const P_STEP1_MS = 0.05
Const P_STEP2_MS = 0.01

' Define some variables
Dim string sr$, sa$, key$
Dim integer iServo, saveAsFile = -1, i
Dim float p_ms, l_ms

' Default servo ranges
'Dim integer r_us(1,2) = (1400,1600, 1400,1600, 1400,1600)
Dim integer r_us(1,2)  =(890,1600, 1150,1800, 1775,2170)
Dim integer r_deg(1,2) = (-40, 40, -40, 40, -20, 20)

' Start interactive calibration
Print
Print "Interactive Robotling2 Servo Calibration"
Print "========================================"
Print " +   Increase by " +Str$(P_STEP1_MS, 0, 3) +" ms"
Print " -   Decrease by " +Str$(P_STEP1_MS, 0, 3) +" ms"
Print "p,P  Toggle precision (" +Str$(P_STEP1_MS, 0, 3) +" vs. ";
Print Str$(P_STEP2_MS, 0, 3) +")"
Print "s,S  Save value and goto next position/servo"
Print "ESC  Abort program"
Print
Print "Save calibration also as `rbl.cfg` on `A:` (y/n): ";
key$ = ""
Do
  key$ = UCase$(Inkey$)
  If Len(key$) > 0 And (key$ = "N" Or key$ = "Y") Then
    Print key$
    saveAsFile = key$ = "Y"
  EndIf
Loop Until saveAsFile >= 0
Print

' Left leg pair (M1)
Print "M1: Left leg pair:"
Print Str$(r_deg(0,0),3,0) +" deg (to the front):"
r_us(0,0) = Int(inquireNewPos(0, r_us(0,0)/1000) *1000)
Print Str$(r_deg(1,0),3,0) +" deg (to the back):"
r_us(1,0) = Int(inquireNewPos(0, r_us(1,0)/1000) *1000)

' Right leg pair (M2)
Print "M2: Right leg pair:"
Print Str$(r_deg(1,1),3,0) +" deg (to the front):"
r_us(1,1) = Int(inquireNewPos(1, r_us(1,1)/1000) *1000)
Print Str$(r_deg(0,1),3,0) +" deg (to the back):"
r_us(0,1) = Int(inquireNewPos(1, r_us(0,1)/1000) *1000)

' Center leg pair (M3)
Print "M3: Center leg pair:"
p_ms = (r_us(0,2) +(r_us(1,2) -r_us(0,2))/2) /1000
Print "   0 deg (all legs level):"
p_ms = inquireNewPos(2, p_ms)
Print "Lift (on the right side):"
l_ms = p_ms
l_ms = inquireNewPos(2, l_ms)
r_us(0,2) = Int(l_ms *1000)
r_us(1,2) = Int((p_ms +(p_ms -l_ms)) *1000)

' Print results as Basic code
Print
Print "Results as MMBasic code:"
Print "-----------------------"

sr$ = "Dim integer _serv_range_us(1,2)  = ("
sa$ = "Dim integer _serv_range_deg(1,2) = ("
For iServo=0 To 2
  sr$ = sr$ +Str$(r_us(0,iServo)) +"," +Str$(r_us(1,iServo))
  sa$ = sa$ +Str$(r_deg(0,iServo)) +"," +Str$(r_deg(1,iServo))
  If iServo < 2 Then
    sr$ = sr$ +", "
    sa$ = sa$ +", "
  Else
    sr$ = sr$ +")"
    sa$ = sa$ +")"
  EndIf
Next iServo
Print sr$
Print sa$
Print

If saveAsFile Then
' Save also as file
  Print "Save as file `rbl.cfg` to A: drive ..."
  Open "A:rbl.cfg" For output As #1
    For i=0 To 2
      Print #1, i;",";r_us(0,i);",";r_us(1,i);","; r_deg(0,i);",";r_deg(1,i)
    Next i
  Close #1
EndIf

_PWM_M123 0, 0, 0, 1
Print "Done."
End

' ----------------------------------------------------------------------------
Function inquireNewPos(iS, p) As Float
  ' Let user adjust a servo position of motor `iS`
  Local integer done = 0
  Local string ch$ = ""
  Local float s_ms = Choice(iS < 2, P_STEP1_MS, P_STEP2_MS)

  ' Goto starting position
  setServo iS, p

  ' Inquire ...
  Do While Not(done)
    ch$ = Inkey$
    If Len(ch$) > 0 Then
      Select Case ch$
        Case "+"
          p = Choice(p < P_MAX_MS, p +s_ms, P_MAX_MS)
        Case "-"
          p = Choice(p > P_MIN_MS, p -s_ms, P_MIN_MS)
        Case "s", "S"
          done = 1
        Case "p", "P"
          s_ms = Choice(s_ms = P_STEP1_MS, P_STEP2_MS, P_STEP1_MS)
        Case Chr$(27)
          _PWM_M123 0, 0, 0, 1
          Print
          Print "User aborted the program."
          End
     End Select
      If Not(done) Then
        setServo iS, p
      EndIf
    EndIf
  Loop
  Print
  inquireNewPos = p
End Function

Sub setServo(iS, p)
  Print "\&0d  -> p=" +Str$(p, 0, 3) +" ms";
  Select Case iS
    Case 0: _PWM_M123 p*10, 0, 0
    Case 1: _PWM_M123 0, p*10, 0
    Case 2: _PWM_M123 0, 0, p*10
  End Select
End Sub

' ----------------------------------------------------------------------------                                                                        