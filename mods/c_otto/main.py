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
import micropython

# ----------------------------------------------------------------------------
if __name__ == "__main__":
# Initialize robot
#  micropython.mem_info()
  Robot = rbl2_robot.Robot(core=cfg.HW_CORE)
  Robot.autoupdate_gui = True
#  micropython.mem_info()

  print("Press `A` for sensors only ...")
  trials = 80
  only_sensors = False 
  while trials > 0:
    if Robot.is_pressed_A:
      only_sensors = True
      break
    trials -= 1
    time.sleep_ms(25)
  if only_sensors:
    Robot.show_message("sensors-only")
    print ("Sensors  Only")
    Robot.no_servos(only_sensors)
  try:
    while not Robot.state == glb.STATE_OFF:
      dL, dC, dR = Robot.distances_mm
      if not only_sensors:
        objL = (dL < 80) or (dC < 80)
        objR = (dR < 80) or (dC < 80)
        clfL = (dL > 200) or (dC > 200)
        clfR = (dR > 200) or (dC > 200)
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
              Robot.show_message("Cliff_L__")
            elif not clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff___R")
            elif clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff__C_")
            Robot.sleep_ms(4000)

          elif objL or objR:
            if objL and not objR:
              Robot.turn(+1)
              Robot.show_message("Objct_L__")
            elif not objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct___R")
            elif objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct__C_")
            Robot.sleep_ms(2000)

      # Sleep for a while and, if running only on one core, make sure that
      # the robot's hardware is updated
      Robot.sleep_ms(50)

  except KeyboardInterrupt:
    # Clean up
    Robot.deinit()

# ----------------------------------------------------------------------------
