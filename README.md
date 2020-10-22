# Alarm System for Domoticz
Versions:

    1.0.0: First release
    1.0.1: Bug fix release
    1.1.0: Bug fix release and reorder the Alarm Status Selector Switch levels, New Selector Switch for Open Section Timeout
    1.1.1: Bug fix should fix "Issue: Rearming the zone doesn't seem to work #6"
    1.1.2: Bug fix should fix "Issue: Sensor Active Time & Open Sections Timeout not saving settings #8"
    1.2.0: Added Open Section Text Device
    1.2.1: Bug fix not creating Open Section Text Devices when updating an existing plugin
    1.3.0: Added fire devices, check if configured devices exists, text devices for Open Sections and Tripped devices

There was no real alarm system for Domoticz. Some scripts and blocky's are available, but they do not meet my expectations. 
So I created this plugin.

This plugin creates an Alarm System in Domoticz. It depends on the devices already available in your Domoticz setup, 
such as PIR, Door, other sensors.
        
## Configuration
### Go to: Setup --> Settings:
* Enable Website Protection and create an user and set a password
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Website%20Protection.png)
* Add the Domoticz IP Address to the Settings Local Networks
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Local%20Networks.png)
### Go to: Setup --> More Options --> Edit Users:
* Create an Alarm User
![ble_tag(https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Website%20Protection.png)
* Set Devices allowed for Alarm User
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Alarm%20User%20Set%20Devices.png)
        
## Alarm zones:
    * The first zone triggers the Security Panel
    * The can be max 9 Alarm Zones.
    * Alarm zones are separated in Armed Home and Armed Away:
    * Armed Home consists of devices (idx numbers) that triggers the outside perimeter, such as:
        * frond and/or back door sensor(s),
        * window sensor(s),
        * PIR sensor(s) in the garden, 
        * etc.
    * Armed Away consists of all devices (idx numbers) that can be triggered when you're not home, such as:
        * PIR sensors indoors,
        * door sensor(s) indoor,
        * etc.
    * If the Alarm is in Armed Away mode it includes also the Armed Home sensors.
    * The deviceID (idx) that belongs to a zone are separated with a "," and a zone is separated with a ";"
    * Both parameters must have the same amount of zones, but a zone can have different amount of devices in it. 
      When a zone has no devices put in a "0" or the text "none".
    * The active sensors device setting must be higer (in seconds) than the setting "Interval in seconds".
      So , if the active sensor device setting is for example 20s, it keeps the setting in memory active dor 20 seconds. If
      the Interval in seconds is for example 40s, then the triggerd sensors are never detected.
        
Open Sections are detected and reported per zone in the Arming Status Selector Switch. Depending of the configured value of 
Selector Switch 'Open Sections Timeout' the alarm is armed anyway. Until the open sections are resolved, these sensors are not 
actively involved in the alarm detection process.
        
Exit and Entry Delay can be set through the Selector Switches. They apply to each configured zone.

The plugin is tested to works on a Raspberry Pi 3b.

To install the plugin login to the Raspberry Pi (SSH / Putty).
  
        cd /home/<username>/domoticz/plugin
  
        git clone https://github.com/Wizzard72/Domoticz-Alarm
      
        sudo systemctl restart domoticz.service

Go to the hardware tab in Domoticz and select by field Type: Alarm System for Domoticz.
Fill in all fields:
    * Domoticz IP Address:              The internal IP address of your Domoticz Install.
    * Domoticz Port Number:             The port number of your Domoticz Install.
    * Username:                         The plugin need access to the sensors.It reads them with JSON. You can create a 
                                        separate  User for the plugin.
    * Password:                         The password of the Username.
    * Active devices to trigger Siren:  How many devices must be triggerd to set the alarm off. It's configurable for
                                        Armed Home and Armed Away and is applyable to all zones.
    * Zone Armed Home:                  Devices (idx numbers) that trigger the Alarm when activated. If the Alarm is in Armed
                                        Home state, it only checks the devices for this zone.
    * Zone Armed Away:                  Devices (idx numbers) that trigger the Alarm when activated. If the Alarm is in Armed
                                        Away state, it not only checks the devices for this zone, but also for the Armed Home
                                        Zone (Armed Away + Armed Home).
    * Siren active for (s):             Configure how long the siren is turned on. When the arming mode status is turned to Off,
                                        the siren is turned off aswel.
    * Poll Interval in seconds:         This settings controls how often the sensors are checked.
    * Debug:                            Debug information



Update plugin to latest version:

        cd /home/<username>/domoticz/plugin
  
        git pull
      
        In Domoticz Hardware page: Disable the Alarm System for Domoticz plugin
        
        In Domoticz Hardware page: Enable the Alarm System for Domoticz plugin


![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Alarm%20User.png)
