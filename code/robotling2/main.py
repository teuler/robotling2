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
  do_exit = False
  counter = 0
  Robot = rbl2_robot.RobotBase(core=cfg.HW_CORE)

  try:
    try:
      while not do_exit:

        if counter == 20:
          Robot.move_forward()
        elif counter == 75:
          Robot.stop()
        elif counter == 100:
          Robot.turn(-1)
        elif counter == 250:
          Robot.stop()
        elif counter == 300:
          Robot.turn(+1)
        elif counter == 400:
          Robot.stop()
        elif counter == 420:
          Robot.power_down()
        counter += 1

        # Update GUI
        Robot.GUI.show_info(glb.STATE_STRS[Robot.state],
            "{0:.1f}".format(Robot.direction)
            if Robot.state is glb.STATE_TURNING else ""
          )

        # Sleep for a while and, if running only on one core, make sure that
        # the robot's hardware is updated
        do_exit = Robot.state == glb.STATE_OFF
        Robot.sleep_ms(50)

    except KeyboardInterrupt:
      pass
  finally:
    # Clean up
    Robot.deinit()

# ----------------------------------------------------------------------------
