# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="Alarm" name="Alarm" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Unifi Presence Detection plugin</h2><br/>
        This plugin reads the Unifi Controller information such as the sensors on the Unifi Gateway. 
        Beside this it checks the presence of phone(s) and it is possible to add extra devices for example Geo Fencing.
        

    </description>
    <params>
        <param field="Mode1" label="Total amount of PIR zones:" width="75px">
            <options>
                <option label="1" value="1"  default="true" />
                <option label="2" value="2"/>
                <option label="3" value="3"/>
                <option label="4" value="4"/>
                <option label="5" value="5"/>
                <option label="6" value="6"/>
                <option label="7" value="7"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import json
from datetime import datetime
import time


class BasePlugin:
    ALARM_MAIN_UNIT = 0
    ALARM_ARMING_MODE_UNIT = 5
    ALARM_ARMING_STATUS_UNIT - 10
    ALARM_PIR_Zone_UNIT = 20
    
    # create devices
    if (self.ALARM_MAIN_UNIT not in Devices):
        Domoticz.Device(Name="ALARM",  Unit=self.ALARM_MAIN_UNIT, Used=1, TypeName="Switch").Create()
        UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
    
    if (self.ALARM_ARMING_MODE_UNIT not in Devices):
        Options = {"LevelActions": "||||",
                   "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                   "LevelOffHidden": "false",
                   "SelectorStyle": "0"}
        Domoticz.Device(Name="Arming Mode", Unit=self.ALARM_ARMING_MODE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
        Domoticz.Device(Name="Arming Mode",  Unit=self.ALARM_ARMING_MODE_UNIT, Used=1, TypeName="Switch").Create()
        UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 0, "Off")
    
    if (self.ALARM_ARMING_STATUS_UNIT not in Devices):
        Options = {"LevelActions": "||||",
                   "LevelNames": "Disarmed|Armed Home|Armed Away",
                   "LevelOffHidden": "false",
                   "SelectorStyle": "0"}
        Domoticz.Device(Name="Arming Status",  Unit=self.ALARM_ARMING_STATUS_UNIT, Used=1, TypeName="Switch").Create()
        UpdateDevice(self.ALARM_ARMING_STATUS_UNIT, 0, "Off")
    
    
    if (self.ALARM_PIR_Zone_UNIT not in Devices):
        Options = {"LevelActions": "||||",
                   "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                   "LevelOffHidden": "false",
                   "SelectorStyle": "0"}
        Domoticz.Device(Name="OverRide", Unit=self.UNIFI_OVERRIDE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "0")

    
    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        strName = "onStart: "
        Domoticz.Debug(strName+"called")
        if (Parameters["Mode6"] != "0"):
            Domoticz.Debugging(int(Parameters["Mode6"]))
        else:
            Domoticz.Debugging(0)
        
        # load custom images
        # reused the icons from iDetect - https://github.com/d-EScape/Domoticz_iDetect
        if "UnifiPresenceAnyone" not in Images: 
            Domoticz.Log(strName+"Add UnifiPresenceAnyone icons to Domoticz")
            Domoticz.Image("uanyone.zip").Create()
        
        if "UnifiPresenceOverride" not in Images: 
            Domoticz.Log(strName+"Add UnifiPresenceOverride icons to Domoticz")
            Domoticz.Image("uoverride.zip").Create()
        
        if "UnifiPresenceDevice" not in Images: 
            Domoticz.Log(strName+"Add UnifiPresenceDevice icons to Domoticz")
            Domoticz.Image("udevice.zip").Create()

        Domoticz.Log("Number of icons loaded = " + str(len(Images)))
        for item in Images:
            Domoticz.Log(strName+"Items = "+str(item))
            Domoticz.Log(strName+"Icon " + str(Images[item].ID) + " Name = " + Images[item].Name)
        
        # create devices
        if (self.UNIFI_WLAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="WLAN Counter",  Unit=self.UNIFI_WLAN_COUNTER_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_WLAN_COUNTER_UNIT, 0, "0")

        if (self.UNIFI_LAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="LAN Counter",  Unit=self.UNIFI_LAN_COUNTER_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_LAN_COUNTER_UNIT, 0, "0")
            
        if (self.UNIFI_ANYONE_HOME_UNIT not in Devices):
            Domoticz.Device(Name="AnyOne",  Unit=self.UNIFI_ANYONE_HOME_UNIT, Used=1, TypeName="Switch", Image=Images['UnifiPresenceAnyone'].ID).Create()
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")
            
        if (self.UNIFI_OVERRIDE_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="OverRide", Unit=self.UNIFI_OVERRIDE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "0")
        
        if (self.UNIFI_CPU_PERC_UNIT not in Devices):
            Domoticz.Device(Name="Gateway CPU Percentage",  Unit=self.UNIFI_CPU_PERC_UNIT, Used=1, TypeName="Percentage").Create()
            UpdateDevice(self.UNIFI_CPU_PERC_UNIT, 0, "0")
        
        if (self.UNIFI_MEM_PERC_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Mem Percentage",  Unit=self.UNIFI_MEM_PERC_UNIT, Used=1, TypeName="Percentage").Create()
            UpdateDevice(self.UNIFI_MEM_PERC_UNIT, 0, "0")
        
        if (self.UNIFI_BOARD_CPU_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Board (CPU) Temperature",  Unit=self.UNIFI_BOARD_CPU_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_BOARD_CPU_UNIT, 0, "0")
        
        if (self.UNIFI_BOARD_PHY_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Board (PHY) Temperature",  Unit=self.UNIFI_BOARD_PHY_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_BOARD_PHY_UNIT, 0, "0")
        
        if (self.UNIFI_CPU_UNIT not in Devices):
            Domoticz.Device(Name="Gateway CPU Temperature",  Unit=self.UNIFI_CPU_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_CPU_UNIT, 0, "0")
        
        if (self.UNIFI_PHY_UNIT not in Devices):
            Domoticz.Device(Name="Gateway PHY Temperature",  Unit=self.UNIFI_PHY_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_PHY_UNIT, 0, "0")
            
        if (self.UNIFI_UPTIME_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Uptime (hours)", Unit=self.UNIFI_UPTIME_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_UPTIME_UNIT, 0, "0.0")
        
        # create phone devices
        device_mac=Parameters["Mode2"].split(",")
        device_extra=Parameters["Mode3"].split(",")
        
        found_phone = False
        count_phone = 0
        for device in device_mac:
            device = device.strip()
            phone_name, mac_id = device.split("=")
            phone_name = phone_name.strip()
            mac_id = mac_id.strip().lower()
            try:
                for item in Devices:
                    if Devices[item].Name[8:] == phone_name:
                        Domoticz.Log(strName+"Found phone from configuration = "+device)
                        found_phone = True
                if found_phone == False:
                    new_unit = find_available_unit()
                    Domoticz.Device(Name=phone_name, Unit=new_unit, TypeName="Switch", Used=1, Image=Images['UnifiPresenceDevice'].ID).Create()
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")
            count_phone = count_phone + 1
        
        # Extra devices for Geofencing for example
        found_phone = False
        for ex_device in device_extra:
            ex_device = ex_device.strip()
            phone_name = ex_device
            try:
                for item in Devices:
                    if Devices[item].Name[8:] == phone_name:
                        Domoticz.Log(strName+"Found devices to monitor from configuration = "+device)
                        found_phone = True
                if found_phone == False:
                    new_unit = find_available_unit()
                    Domoticz.Device(Name=phone_name, Unit=new_unit, TypeName="Switch", Used=1, Image=Images['UnifiPresenceOverride'].ID).Create()
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")
            self.count_ex_device = self.count_ex_device + 1
        
        # calculate total devices
        extra_devices = 1 # Override device
        self.total_devices_count = count_phone + self.count_ex_device + extra_devices
        Domoticz.Debug(strName+"total_devices = "+str(self.total_devices_count))
        # Create table
        device_mac=Parameters["Mode2"].split(",")
        device_extra=Parameters["Mode3"].split(",")
        w, h = 6, self.total_devices_count;
        self.Matrix = [[0 for x in range(w)] for y in range(h)] 
        # table:
        # Phone_Name | MAC_ID | Unit_Number | State | Changed | Refresh
        # Matrix[0][0] = 1
        count = 1
        found_user = None
        self.Matrix[0][0] = "OverRide"            # Used for the OverRide Selector Switch
        self.Matrix[0][1] = "00:00:00:00:00:00"   # Used for the OverRide Selector Switch
        self.Matrix[0][2] = 255                   # Used for the OverRide Selector Switch
        self.Matrix[0][3] = "Off"                 # Used for the OverRide Selector Switch
        self.Matrix[0][4] = "No"                  # Used for the OverRide Selector Switch
        self.Matrix[0][5] = "No"                  # Used for the OverRide Selector Switch
        for device in device_mac:
            device = device.strip()
            Device_Name, Device_Mac = device.split("=")
            self.Matrix[count][0] = Device_Name 
            self.Matrix[count][1] = Device_Mac
            Device_Unit = None
            self.Matrix[count][3] = "Off"
            self.Matrix[count][4] = "No"
            self.Matrix[count][5] = "Yes"
            found_user = Device_Name
            for dv in Devices:
                # Find the unit number
                search_phone = Devices[dv].Name[8:]
                if Devices[dv].Name[8:] == found_user:
                    self.Matrix[count][2] = Devices[dv].Unit
                    continue
            Domoticz.Log(strName+"Phone Naam = "+self.Matrix[count][0]+" | "+str(self.Matrix[count][1])+" | "+str(self.Matrix[count][2])+" | "+self.Matrix[count][3]+" | "+self.Matrix[count][4])
            count = count + 1
        
        # Extra devices for Geofencing for example
        for ex_device in device_extra:
            self.Matrix[count][0] = ex_device.strip()
            self.Matrix[count][1] = "11:11:11:11:11:11"
            self.Matrix[count][3] = "Off"


    def onStop(self):
        strName = "onStop: "
        Domoticz.Debug(strName+"Pluggin is stopping.")
        

    def onConnect(self, Connection, Status, Description):
        strName = "onConnect: "
        Domoticz.Debug(strName+"called")
        Domoticz.Debug(strName+"Connection = "+str(Connection))
        Domoticz.Debug(strName+"Status = "+str(Status))
        Domoticz.Debug(strName+"Description = "+str(Description))

    def onMessage(self, Connection, Data):
        strName = "onMessage: "
        Domoticz.Debug(strName+"called")
        

    def onCommand(self, Unit, Command, Level, Hue):
        strName = "onCommand: "
        Domoticz.Log(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        
                
                
    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        strName = "onNotification: "
        Domoticz.Debug(strName+"called")
        Domoticz.Log(strName+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        strName = "onDisconnect: "
        Domoticz.Debug(strName+"called")

    def onHeartbeat(self):
        strName = "onHeartbeat: "
        Domoticz.Debug(strName+"called")

        

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def LogMessage(Message):
    strName = "LogMessage: "
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Debug(strName+"File written")

def DumpHTTPResponseToLog(httpResp, level=0):
    strName = "DumpHTTPResponseToLog: "
    if (level==0): Domoticz.Debug(strName+"HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(strName+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(strName+indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(strName+indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(strName+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")

def UpdateDevice(Unit, nValue, sValue, Image=None):
    strName = "UpdateDevice: "
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or ((Image != None) and (Image != Devices[Unit].Image)):
            if (Image != None) and (Image != Devices[Unit].Image):
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue), Image=Image)
                Domoticz.Log(strName+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
            else:
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Log(strName+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")

    # Generic helper functions
def DumpConfigToLog():
    strName = "DumpConfigToLog: "
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug(strName+"'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug(strName+"Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug(strName+"Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug(strName+"Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug(strName+"Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug(strName+"Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug(strName+"Device LastLevel: " + str(Devices[x].LastLevel))
    return
