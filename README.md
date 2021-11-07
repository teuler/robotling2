# Robotling 2

Robotling-2 is a small, simple 6-legged robot using the new Raspberry Pi microcontroller [RP2040](https://www.raspberrypi.org/documentation/rp2040/getting-started/) as brain. To move around, it uses a simplified tripod walk that requires only three servo motors - inspired by a 20 year old book called ["Insectronics"](https://www.amazon.com/Insectronics-Build-Walking-Robot-Robotics-ebook/dp/B000W10R32). 

Check out the [Wiki](https://github.com/teuler/robotling2/wiki) for details and [video1](https://youtu.be/0tkTgc_Hvlo), [video2](https://youtu.be/2amrnnNkvMk).

[<img src="https://github.com/teuler/robotling2/blob/main/pictures/GIF3.gif" alt="Drawing" width="400"/>](https://github.com/teuler/robotling2/blob/main/pictures/GIF3.gif)[<img src="https://github.com/teuler/robotling2/blob/main/pictures/IMG_7990.png" alt="Drawing" width="400"/>](https://github.com/teuler/robotling2/blob/main/pictures/IMG_7990.png)

### Release Notes

* 2021-11-07
  - Code v1.00 written in [MMBasic](https://mmbasic.com/) added. It uses the Pico version (["PicoMite"](https://geoffg.net/picomite.html)) version of the MMBasic interpreter written Geoff Graham and Peter Mather (see [repository](https://github.com/UKTailwind/PicoMite)).
  - New sensor head for Time-of-flight distance sensors by Pololu [#4064](https://www.pololu.com/product/4064/specs)
* 2021-04-25
  - "Arm" for distance sensor added (i.e. the [multi-pixel evo mini](https://www.terabee.com/shop/lidar-tof-range-finders/teraranger-evo-mini/))
  - Battery compartment modified such that it can also carry a [1000 mAh single-cell LiPo](https://www.exp-tech.de/zubehoer/batterien-akkus/lipo-akkus/5801/3.7v-1000mah-lithium-polymer-akku-mit-jst-ph-anschluss).
* 2021-04-10
  - PCB slighly updated
  - Video and new pictures added
* 2021-04-05
  - Fritzing file and BOM for board (v0.3) added
  - .STL files for 3D printed parts added
  - FreeCAD document added
  - Some code added (so far only walk demo w/o sensors)
* 2021-03-27 - Initial release
