#!!!! Final version - I'm not maintaining this plugin anymore. Recently migrated to Home Assistant.

# Alarm System for Domoticz

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Siren.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Arming%20Mode%20Zone%200.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Arming%20Status%20Zone%200.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Entry%20Delay.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Exit%20Delay.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Open%20Sections%20Timeout.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Open%20Sections%20Zone%200.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Tripped%20Devices%20Zone%200.png)


## Versions

    1.0.0: First release
    1.0.1: Bug fix release
    1.1.0: Bug fix release and reorder the Alarm Status Selector Switch levels, New Selector Switch for Open Section Timeout
    1.1.1: Bug fix should fix "Issue: Rearming the zone doesn't seem to work #6"
    1.1.2: Bug fix should fix "Issue: Sensor Active Time & Open Sections Timeout not saving settings #8"
    1.2.0: Added Open Section Text Device
    1.2.1: Bug fix not creating Open Section Text Devices when updating an existing plugin
    1.3.0: Added fire devices, check if configured devices exists, text devices for Open Sections and Tripped devices
    1.3.1: Fire devices now active the alarm when alarm is disabled
    1.3.2: Thanks to Beastie971: Add support for PIR's with different options. Add support for disabling Alarm System with Security Panel

## Introduction
There was no real alarm system for Domoticz. Some scripts and blocky's are available, but they do not meet my expectations. 
So I created this plugin.

This plugin creates an Alarm System in Domoticz. It depends on the devices already available in your Domoticz setup, 
such as PIR, Door, other sensors.
    
## Introducing Alarm zones, etc.
- The first zone triggers the Security Panel
- The can be max 9 Alarm Zones.
- Alarm zones are separated in Armed Home and Armed Away:
- Armed Home consists of devices (idx numbers) that triggers the outside perimeter, such as:
  - front and/or back door sensor(s),
  - window sensor(s),
  - PIR sensor(s) in the garden, 
  - etc.
- Armed Away consists of all devices (idx numbers) that can be triggered when you're not home, such as:
  - PIR sensors indoors,
  - door sensor(s) indoor,
  - etc.
- If the Alarm is in Armed Away mode it includes also the Armed Home sensors.
- The deviceID (idx) that belongs to a zone are separated with a "," and a zone is separated with a ";"
- Both parameters must have the same amount of zones, but a zone can have different amount of devices in it. When a zone has no devices put in a "0" or the text "none".
- The active sensors device setting must be higer (in seconds) than the setting "Interval in seconds". So , if the active sensor device setting is for example 20s, it keeps the setting in memory active dor 20 seconds. If the Interval in seconds is for example 40s, then the triggerd sensors are never detected.
- Open Sections are detected and reported per zone in the Arming Status Selector Switch. Depending of the configured value of 
Selector Switch 'Open Sections Timeout' the alarm is armed anyway. Until the open sections are resolved, these sensors are not 
actively involved in the alarm detection process.
- Exit and Entry Delay can be set through the Selector Switches. They apply to each configured zone.

## Installation

The plugin is tested to works on a Raspberry Pi 3b.

### Pre Configuration Domoticz
#### Go to: Setup --> Settings:
* Enable Website Protection and create an user and set a password
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Website%20Protection.png)
* Add the Domoticz IP Address to the Settings Local Networks
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Local%20Networks.png)
#### Go to: Setup --> More Options --> Edit Users:
* Create an Alarm User        
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Alarm%20User.png)
* Set Devices allowed for Alarm User
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Alarm%20User%20Set%20Devices.png)

### Install plugin on Domoticz (only Linux is supported)
To install the plugin login to the Raspberry Pi (SSH / Putty).
  
        cd /home/<username>/domoticz/plugin
  
        git clone https://github.com/Wizzard72/Domoticz-Alarm
      
        sudo systemctl restart domoticz.service

Go to the hardware tab in Domoticz and select by field Type: Alarm System for Domoticz.
Fill in all fields:
| Field | Information|
| ----- | ---------- |
| Domoticz IP Address: | The internal IP address of your Domoticz Install. |
| Domoticz Port Number: | The port number of your Domoticz Install. |
| Username: | The plugin need access to the sensors.It reads them with JSON. You can create a separate  User for the plugin. |
| Password: | The password of the Username. |
| Active devices to trigger Siren:  | How many devices must be triggerd to set the alarm off. It's configurable for Armed Home and Armed Away and is applyable to all zones. |
| Zone Armed Home: | Devices (idx numbers) that trigger the Alarm when activated. If the Alarm is in Armed Home state, it only checks the devices for this zone. |
| Zone Armed Away: | Devices (idx numbers) that trigger the Alarm when activated. If the Alarm is in Armed Away state, it not only checks the devices for this zone, but also for the Armed Home Zone (Armed Away + Armed Home). |
| Fire alarm devices: | Devices (idx number) that trigger the Alarm when activated. If one of the fire devices is turned on the Alarm is turned on also. It's independed of the arming mode. |
| Siren active for (s): | Configure how long the siren is turned on. When the arming mode status is turned to Off, the siren is turned off aswel. |
| Debug: | Debug information. |

### Entry Delay
When system is armed (Armed Home or Armed Away) Entry Delay is used to set the time period necessary for you to approach the keypad and disarm the system once after you have been detected by the zone which you set as "entry zone". During this time the plugin will not trigger the alarm.

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Entry%20Delay.png)

### Exit Delay
The Exit Delay setting gives you a short period of time to leave your home once you’ve armed the Alarm.

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Exit%20Delay.png)

### Open Sections Timeout
The Open Sections Timeout is the amount of time the Alarm Arming Status keeps this status and after this period it's going to the next status. The Open Sections devices are not used until these open sections are closed. Then the device statussen are part of the alarm. 

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Open%20Sections%20Timeout.png)

### Sensor Active Time
The statussen of the devices are kept in memory. So for example a door is opened and closed that takes only 1 or 2 seconds. The Sensor Active Time enlarge this time. If a person opens a door and closed it but is not yet in reach of the motion sensor, then normally the plugin would not combine the 2 activities and thus would not sound the alarm. By extending the tripped sensor time it's more likely to detect this.

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Alarm/master/images/Sensor%20Active%20Time.png)

## Update
Update plugin to latest version:

        cd /home/<username>/domoticz/plugin
  
        git pull
      
        In Domoticz Hardware page: Disable the Alarm System for Domoticz plugin
        
        In Domoticz Hardware page: Enable the Alarm System for Domoticz plugin

