## Versions

- `rbl2_v1_13_co2.bas`  
  Full version w/ CO2 sensor, ToF distance sensors, 240x240 display, and 4th servo. Sleeps until the CO2 concentration is above a certain limit. If it is, the robot wakes up and walks around.
- `rbl2_v1_12_tof_picodisplay.bas`  
  Version w/ ToF distance sensors, and 240x135 display (PicoDisplay). Walks around, avoiding obstacles and cliffs/edges.
- `rbl2_v1_11_basic`  
  Basic version (no sensors, no display). Walks in a square (sort of). Will run into obstacles or fall of the table!
  
The current beta version of MMBasic (`PicoMiteV5.07.07b33.uf2` and higher; [download](https://geoffg.net/picomite.html)) implements `LIBRARY` commands, which allow to "extend" MMBasic with a set of functions (in form of another `.bas` program). Multiple libraries can be used and they occupy the flash slot #4.
