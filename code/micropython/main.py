# ----------------------------------------------------------------------------
# main.py
#
# Main program
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-03-28, v1.0
# 2022-02-12, v1.1
# 2022-04-08, v1.2, a few improvements and fixes
# ----------------------------------------------------------------------------
import gc
import time
import random
import rbl2_robot
import rbl2_global as glb
import rbl2_config as cfg
from micropython import const

# pylint: disable=bad-whitespace
DIST_TOF_OBJ    = const(35)   # object if smaller than this distance
DIST_TOF_CLIFF  = const(150)  # cliff if larger than this distance
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
if __name__ == "__main__":
  # Initialize robot
  is_gui = "display" in cfg.DEVICES
  Robot = rbl2_robot.Robot(core=cfg.HW_CORE, use_gui=is_gui)
  Robot.autoupdate_gui = True
  only_sensors = False
  is_running = True

  # Wait for user to start robot, if display with button available
  if is_gui and cfg.DISPLAY_TYPE in [cfg.PIMORONI_PICO_DISPLAY]:
    glb.toLog("Press `A` to start robot ...")
    while True:
      if Robot.is_pressed_A:
        break  
      time.sleep_ms(25)
  
  # Main loop
  glb.toLog("Starting main loop (press `X` to shutdown)")
  try:
    while not Robot.state == glb.STATE_OFF and is_running:

      # Get distance sensor readings depending on sensor type and calculate
      # if obstacles and/or cliffs are detected ... 
      if Robot.distance_sensor_type == cfg.STY_EVOMINI:
        dLLo, dLHi, dRLo, dRHi = Robot.distances_mm
        objL = (dLLo > 0 and dLLo < 65) or (dLHi > 0 and dLHi < 80)
        objR = (dRLo > 0 and dRLo < 65) or (dRHi > 0 and dRHi < 80)
        objC = objL and objR
        clfL = dLLo > 120
        clfR = dRLo > 120
        free = not objL and not objR and not objC and not clfL and not clfR
        
      elif Robot.distance_sensor_type == cfg.STY_TOF:
        dL, dC, dR = Robot.distances_mm
        #print(dL, dC, dR)
        objL = (dL > 0 and dL < DIST_TOF_OBJ)
        objC = (dC > 0 and dC < DIST_TOF_OBJ)
        objR = (dR > 0 and dR < DIST_TOF_OBJ)
        clfL = dL > DIST_TOF_CLIFF
        clfR = dR > DIST_TOF_CLIFF
        free = not objL and not objR and not objC and not clfL and not clfR

      if only_sensors:
        # If only testing sensors, skip rest of main loop  
        continue   
          
      # Act on detected objects and/or cliffs    
      if free:
        if Robot.state is not glb.STATE_WALKING:
          Robot.move_forward()
          Robot.show_message("-")
      else:
        Robot.stop()
        while Robot.state is not glb.STATE_IDLE:
          Robot.sleep_ms(25)

        if clfL or clfR:
          if clfL and not clfR:
            Robot.turn(+1)
            Robot.show_message("Cliff_L__")
          elif not clfL and clfR:
            Robot.turn(-1)
            Robot.show_message("Cliff___R")
          elif clfL and clfR:
            Robot.move_backward()
            Robot.sleep_ms(2000)
            Robot.turn(1 if random.random() > 0.5 else -1)
            Robot.show_message("Cliff_L_R")
          Robot.sleep_ms(2000)

        elif objL or objC or objR :
          if objL and not objR:
            Robot.turn(+1)
            Robot.show_message("Objct_L__")
          elif not objL and objR:
            Robot.turn(-1)
            Robot.show_message("Objct___R")
          elif objC:
            Robot.move_backward()
            Robot.sleep_ms(1000)
            Robot.turn(1 if random.random() > 0.5 else -1)
            Robot.show_message("Objct__C_")
          Robot.sleep_ms(1000)

      # Sleep for a while and, if running only on one core, make sure that
      # the robot's hardware is updated
      Robot.sleep_ms(25)
      
      # Check if user pressed the X button
      is_running = not Robot.exit_requested

  except KeyboardInterrupt:
    pass

  # Clean up
  Robot.deinit()

# ----------------------------------------------------------------------------
