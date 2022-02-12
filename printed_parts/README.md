
This folder contains the `.stl` files for all parts. The robot was desiged using [FreeCad](https://www.freecadweb.org/); the corresponding design files (different versions) are in the  `FreeCAD_files` subfolder.

### Notes:
- `bar.stl`, `bar_long.stl`, `bar_medium.stl` - only one of these is needed. They have different lengths, defining if the legs are parallel to each other (`bar`) or if the front and rear legs are angled slightly forwards and backwards, respectively (`bar_long`, `bar_medium`)
- `rear_bottom.stl`, `rear_bottom_lipo1000.stl` - only one of these is needed, depending on the battery holder. `rear_bottom` holds a 2x AAA battery cartridge (not recommended, because the batteries wear out quite quickly), `rear_bottom_lipo1000` a approx. 1Ah LiPo (e.g. like [this](https://eckstein-shop.de/LiPo-Akku-Lithium-Ion-Polymer-Batterie-37V-1200mAh-JST-PH-Connector)).
- `sensor_adapter_evo_mini_terabee.stl` - is needed to attached an [Evo Mini](https://www.terabee.com/shop/lidar-tof-range-finders/teraranger-evo-mini/) ranging sensor from Terabee.
- `sensor_adapter_tof_pololu.stl` - is needed to attach Pololu's time-of-flight distance sensors (for details, see [here](https://github.com/teuler/robotling2/wiki/Sensoren#time-of-flight-sensoren)).
- `foot_left.stl`, `foot_right.stl` - feet to be attached to the legs (preliminary, not needed)
