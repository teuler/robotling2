# Robotling 2

Robotling-2 is a small, simple 6-legged robot using the new Raspberry Pi micro controller [RP2040](https://www.raspberrypi.org/documentation/rp2040/getting-started/) as brain. To move around, it uses a simplified tripod walk that requires only three servo motors - inspired by a 20 year old book called ["Insectronics"](https://books.google.de/books/about/Insectronics.html?id=dYZ-67WxUWkC&redir_esc=y).

Except from the electronics and a few screws, it is fully 3D printed. Software is available for [MicroPython](https://github.com/teuler/robotling2/tree/main/code/micropython) and [MMBasic](https://github.com/teuler/robotling2/tree/main/code/mmbasic).

Check out the [Wiki](https://github.com/teuler/robotling2/wiki) for details and [video1](https://youtu.be/0tkTgc_Hvlo), [video2](https://youtu.be/2amrnnNkvMk).

[<img src="https://github.com/teuler/robotling2/blob/main/pictures/GIF3.gif" alt="Drawing" width="400"/>](https://github.com/teuler/robotling2/blob/main/pictures/GIF3.gif)[<img src="https://github.com/teuler/robotling2/blob/main/pictures/IMG_7990.png" alt="Drawing" width="400"/>](https://github.com/teuler/robotling2/blob/main/pictures/IMG_7990.png)

### Release Notes

* 2022-07-02
  - Code updates to account for the new [unified display API](https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules/picographics/README.md) in the MicroPython v1.19 firmware (beta) from Pimorono
* 2022-04-15
  - New version of the [driver](https://github.com/teuler/robotling2/blob/main/code/micropython/robotling_lib/sensors/pololu_tof_ranging_pio.py) for Pololu time-of-flight sensors w/ pulse width modulation. It uses the RP2040’s PIO (programmable I/O) interface instead of waiting for `time_pulse_us()`.
* 2022-04-08
  - [MicroPython demo code](https://github.com/teuler/robotling2/tree/main/code/micropython) updated:
     - Fixed small compatibility issues with MicroPython v1.18
     - Display distance measurements also for Pololu ToF sensors   
     - Add `"display"` as a "device" to the configuration to allow the robot to operate also w/o a PicoDisplay and to prepare the use of other types of displays.
     - [Servo calibration program](https://github.com/teuler/robotling2/blob/main/code/micropython/calibrate_servos.py) added. For instructions, see [here](https://github.com/teuler/robotling2/wiki/Demo#kalibrierung-der-beinstellung).
* 2022-02-12
  - New version of [MicroPython demo code](https://github.com/teuler/robotling2/tree/main/code/micropython). Changes:
     - More consistent with MMBasic demo
     - Support for 3-channel time-of-flight distance sensor array
     - More gracefully ending the program when `X` is pressed
     - Constants for sensor port pins
     - Robot can now backup to avoid an obstacle
  - All `.stl` files adjusted to print orientation; `.stl` file for Pololu tof sensors added
  - Wiki pages added: "[Mechanik](https://github.com/teuler/robotling2/wiki/Mechanik)", "[Aufbau und Hinweise zum Zusammenbau](https://github.com/teuler/robotling2/wiki/Aufbau-und-Hinweise-zum-Zusammenbau)", German version of "[Elektronik, Platine, und Teile](https://github.com/teuler/robotling2/wiki/Elektronik,-Platine,-und-Teile)", "[Erweiterungen & Modifikationen](https://github.com/teuler/robotling2/wiki/Erweiterungen-&-Modifikationen)", "[Sensoren](https://github.com/teuler/robotling2/wiki/Sensoren)"
  - Cleaned up and updated wiki pages for MicroPython and MMBasic
  - Added demo code loading instructions for both [MMBasic](https://github.com/teuler/robotling2/wiki/Running-the-robot-with-MMBasic) and [MicroPython](https://github.com/teuler/robotling2/wiki/Running-the-robot-with-MicroPython).
  - Completed parts list
* 2022-01-22
  - [Parts list](https://github.com/teuler/robotling2/wiki/Electronics,-PCB-and-parts#Electronics_Parts) added 
  - Information about the distance sensors added
* 2021-12-16
  - Slightly updated version of board added
* 2021-11-20
  - [MMBasic program explained (German)](https://github.com/teuler/robotling2/wiki/Kommentare-zum-MMBasic-Programm) added to Wiki.
* 2021-11-07
  - Code v1.xx written in [MMBasic](https://mmbasic.com/) added. It uses the Pico version (["PicoMite"](https://geoffg.net/picomite.html)) version of the MMBasic interpreter written Geoff Graham and Peter Mather (see [repository](https://github.com/UKTailwind/PicoMite)).
  - New [wiki page](https://github.com/teuler/robotling2/wiki/Running-the-robot-with-MMBasic) about running the robot under MMBasic.
  - New sensor head for Time-of-flight distance sensors by Pololu [#4064](https://www.pololu.com/product/4064/specs)
* 2021-04-25
  - "Arm" for distance sensor added (i.e. the [multi-pixel evo mini](https://www.terabee.com/shop/lidar-tof-range-finders/teraranger-evo-mini/))
  - Battery compartment modified such that it can also carry a [1000 mAh single-cell LiPo](https://www.exp-tech.de/zubehoer/batterien-akkus/lipo-akkus/5801/3.7v-1000mah-lithium-polymer-akku-mit-jst-ph-anschluss).
* 2021-04-10
  - PCB slightly updated
  - Video and new pictures added
* 2021-04-05
  - Fritzing file and BOM for board (v0.3) added
  - .STL files for 3D printed parts added
  - FreeCAD document added
  - Some code added (so far only walk demo w/o sensors)
* 2021-03-27 - Initial release
