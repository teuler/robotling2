### TODOs
- Show time-of-flight sensor readings on the display
- Add splash screen
- Solve multitasking issue: In `rbl2_config.py` it is possible to set `HW_CORE = const(1)` (**experimental**) to direct the main background task to the RP2040's second core (core 1). The idea of this is to balance the workload between the cores. However, this option currently does not work for long; a few seconds after the robot starts to move, it freezes. 

### Issues
- The current MicroPython firmware (v1.18) for the Pico seems to crash from time to time; it is still responsible but shows nonsense errors (`NotImplementedError: opcode`). In this case, a reset helps.
