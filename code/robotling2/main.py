# ----------------------------------------------------------------------------
# main.py
#
# Main program
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-03-28, v1.0
# ----------------------------------------------------------------------------
import gc
import time
import rbl2_robot
import rbl2_global as glb
import rbl2_config as cfg
from micropython import const

# ----------------------------------------------------------------------------
if __name__ == "__main__":
  # Initialize robot
  Robot = rbl2_robot.Robot(core=cfg.HW_CORE)
  Robot.autoupdate_gui = True
  only_sensors = False

  print("Press `A` for sensors only ...")
  trials = 80
  while trials > 0:
    if Robot.is_pressed_A:
      only_sensors = True
      break
    trials -= 1
    time.sleep_ms(25)
  if only_sensors:
    Robot.show_message("sensors-only")
  Robot.no_servos(only_sensors)

  try:
    while not Robot.state == glb.STATE_OFF:

      dLLo, dLHi, dRLo, dRHi = Robot.distances_mm

      if not only_sensors:
        objL = (dLLo > 0 and dLLo < 65) or (dLHi > 0 and dLHi < 80)
        objR = (dRLo > 0 and dRLo < 65) or (dRHi > 0 and dRHi < 80)
        clfL = dLLo > 120
        clfR = dRLo > 120
        free = not objL and not objR and not clfL and not clfR

        if free:
          if Robot.state is not glb.STATE_WALKING:
            Robot.move_forward()
            Robot.show_message("-")
        else:
          Robot.stop()
          while Robot.state is not glb.STATE_IDLE: Robot.sleep_ms(25)

          if clfL or clfR:
            if clfL and not clfR:
              Robot.turn(+1)
              Robot.show_message("Cliff_L_")
            elif not clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff__R")
            elif clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff_LR")
            Robot.sleep_ms(4000)

          elif objL or objR:
            if objL and not objR:
              Robot.turn(+1)
              Robot.show_message("Objct_L_")
            elif not objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct__R")
            elif objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct_LR")
            Robot.sleep_ms(2000)

      # Sleep for a while and, if running only on one core, make sure that
      # the robot's hardware is updated
      Robot.sleep_ms(50)

  except KeyboardInterrupt:
    # Clean up
    Robot.deinit()

# ----------------------------------------------------------------------------
