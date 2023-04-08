## Versions

### Stand-alone program versions

- `rbl2_v1_13_co2.bas`  
  Full version w/ CO2 sensor, ToF distance sensors, 240x240 display, and 4th servo. Sleeps until the CO2 concentration is above a certain limit. If it is, the robot wakes up and walks around.
- `rbl2_v1_12_tof_picodisplay.bas`  
  Version w/ ToF distance sensors, and 240x135 display (PicoDisplay). Walks around, avoiding obstacles and cliffs/edges.
- `rbl2_v1_11_basic`  
  Basic version (no sensors, no display). Walks in a square (sort of). Will run into obstacles or fall of the table!
  
### Program versions using `rbl_lib`

The current beta version of MMBasic (`PicoMiteV5.07.07b33.uf2` and higher; [download](https://geoffg.net/picomite.html)) implements `LIBRARY` commands, which allow to "extend" MMBasic with a set of functions (in form of another `.bas` program). Multiple libraries can be used and they occupy the flash slot #4. By moving all robot functions and subroutines (`R.xxx`) into a library, the programs become much shorter and common functions (now in the library) are much easier to maintain between programs. To demonstrate this, I converted the two of the demo programs such that they use a common library.

- `rbl2_v1_21_basic`, `rbl2_v1_22_tof_picodisplay.bas`  
  Library-enabled versions of the programs above. 
- `rbl_lib.bas`  
  Library with all robot-related functions, subroutines, constants, and variables.
- `rbl_servo_calibration.bas`  
  Interactive servo calibration program.

To use the new programs:
- Load library `rbl_lib.bas` onto the Pico using `xmodem r`, then:
     ```
     flash overwrite 3  ' Save original library code
     library delete     ' Delete previous libraries 
     library save       ' Save current code as library
     ```
- When saving as library, the code is stripped of all extra stuff (e.g. comments, white spaces etc.). To make a change to the original library code, use the copy in flash slot #3. Don't forget to save your main program before you load the library into the editor:
     ```
     flash overwrite 1  ' Save main program, if any, in slot #1
     flash load 3       ' Load original library code from slot #3
     edit               ' Make your changes
     flash overwrite 3  ' Save changed library code
     library delete     ' Delete previous libraries
     library save       ' Save current code as library
     ```   
     
