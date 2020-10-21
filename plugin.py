# Alarm System for Domoticz Plugin
#
# Author: Wizzard72
# Versions:
#   1.0.0: First release
#   1.0.1: Bug fix release
#   1.1.0: Bug fix release and reorder the Alarm Status Selector Switch levels, New Selector Switch for Open Section Timeout
#   1.1.1: Bug fix should fix "Issue: Rearming the zone doesn't seem to work #6"
#   1.1.2: Bug fix should fix "Issue: Sensor Active Time & Open Sections Timeout not saving settings #8"
#   1.2.0: Open Sections will show which device is cousing it
#   1.2.1: Bux fix for creating Open Section devices when plugin was already installed
#   1.3.0: Added fire devices
#
"""
<plugin key="Alarm" name="Alarm System for Domoticz" author="Wizzard72" version="1.3.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Alarm plugin</h2><br/>
        Current Version:    1.3.0: Added fire devices
        <br/>
        This plugin creates an Alarm System in Domoticz. It depends on the devices already available in Domoticz, such as PIR, Door, etc. sensors.<br/>
        <br/>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Add the Domoticz IP Address to the Settings Local Networks</li>
        </ul>
        <br/>
        Alarm zones:<br/>
        <ul style="list-style-type:square">
            <li>The first zone triggers the Security Panel</li>
            <li>The can be max 9 Alarm Zones</li>
            <li>Alarm zones are separated in Armed Home and Armed Away</li>
                <ul>
                    <li>Armed Home consists of devices (idx numbers) that can be triggered while you're at home (Door sensors, etc.)</li>
                    <li>Armed Away consists of all devices (idx numbers) that can be triggered when you're not home (PIR sensors)</li>
                    <li>In Armed Away mode it includes also the Armed Home sensors</li>
                </ul>
            <li>The deviceID (idx) that belongs to a zone are separated with a "," and a zone is separated with a ";"</li>
            <li>Both parameters must have the same amount of zones, but a zone can have different amount of devices in it. When a zone has no devices put in a "0" or the text "none".</li>
            <li>The active sensors met be activated longer than the setting "Interval in seconds"</li>
        </ul>
        <br/>
        Open Sections are detected and reported per zone in the Arming Status Selector Switch. After 50 seconds it's armed anyway.<br/>
        <br/>
        Exit and Entry Delay can be set through the Selector Switches. The values configured are applicable to all zones.<br/>
    </description>
    <params>
        <param field="Address" label="Domoticz IP Address" width="200px" required="true" default="192.168.x.x"/>
        <param field="Port" label="Domoticz Port Number" width="40px" required="true" default="8080"/>
        <param field="Username" label="Username" width="200px" required="true" default=""/>
        <param field="Password" label="Password" width="200px" required="true" default="" password="true"/>
        <param field="Mode1" label="Active devices to trigger Siren" width="300px">
            <options>
                <option label="Armed Home >= 1 / Armed Away = 1" value="1"  default="true" />
                <option label="Armed Home >= 1 / Armed Away >= 2" value="2"/>
                <option label="Armed Home >= 2 / Armed Away >= 1" value="3"/>
                <option label="Armed Home >= 2 / Armed Away >= 2" value="4"/>
            </options>
        </param>
        <param field="Mode2" label="Sensors in Zone Armed Home" width="600px" required="true" default="idx,idx,idx;idx,idx,idx"/>
        <param field="Mode3" label="Sensors in Zone Armed Away" width="600px" required="true" default="idx,idx,idx;idx,idx,idx"/>
        <param field="Mode4" label="Fire devices" width="600px" required="false" default="idx,idx,idx;idx,idx,idx"/>
        <param field="Mode5" label="Siren active for (s)" width="150" required="true" default="50"/>
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
import re
import requests
import urllib
from datetime import datetime
import time
import urllib.parse as parse
import base64
import urllib.parse as parse
import urllib.request as request
import base64
from datetime import datetime
from datetime import timedelta


class BasePlugin:
    ALARM_MAIN_UNIT = 1
    ALARM_ENTRY_DELAY = 2
    ALARM_EXIT_DELAY = 3
    ALARM_SENSOR_TIME = 5
    ALARM_OPEN_SECTION_TIMEOUT = 8
    ALARM_ARMING_MODE_UNIT = 10
    ALARM_ARMING_STATUS_UNIT = 20
    ALARM_PIR_Zone_UNIT = 30
    ALARM_OPEN_SECTION_DEVICE = 40
    ALARM_TRIGGERED_DEVICE = 50
    SecurityPanel = ""
    anybodyHome = ""
    entryDelay = 0
    exitDelay = 0
    secpassword = ""
    openSections = False
    amountofZones = 0
    sirenOn = False
    Matrix = ""
    MatrixRowTotal = 0
    TotalZones = 0
    ActivePIRSirenHome = 0
    ActivePIRSirenAway = 0
    SensorActiveTime = 0 #seconds
    OpenSectionArmAnyWay = 0
    OpenSectionTotal = {}
    ArmingStatusMode = {}
    versionCheck = False


    
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
        
        
        # check if version of domoticz is 2020.2 or higher
        try:
            if int(Parameters["DomoticzVersion"].split('.')[0]) < 2020:  # check domoticz major version
                Domoticz.Error(
                    "Domoticz version required by this plugin is 2020.2 (you are running version {}).".format(
                        Parameters["DomoticzVersion"]))
                Domoticz.Error("Plugin is therefore disabled")
            else:
                self.setVersionCheck(True)
                #self.versionCheck = True
        except Exception as err:
            Domoticz.Error("Domoticz version check returned an error: {}. Plugin is therefore disabled".format(err))
        if not self.versionCheck:
            return
        
        
        # create devices
        self.createDevices(self.TotalZones)


        # Create table
        # Nr | ZONE_Nr | Arm Home/Away| DeviceIdx | State | Changed | Time Changed |
        # 1    0         Arm Home       1000        Off     Normal    0
        # 1    0         Arm Home       1000        On      New       Time
        # 1    0         Arm Home       1000        On      Tripped   Time
        TotalRows = self.calculateMatixRows()
        self.MatrixRowTotal = TotalRows
        TotalColoms = 7
        self.createTheMatrix(TotalColoms, TotalRows)
        #Populate the Matrix with Armed Home Devices
        ZoneArmedHome = Parameters["Mode2"].split(";")
        zoneNr = 0
        for zone in ZoneArmedHome:
            devicesIdx = zone.split(",")
            for devices in devicesIdx:
                if str(devices.lower()) not in "none,0":
                    if self.doDeviceExist(devices) is True:
                        self.addToMatrix(TotalRows, zoneNr, "Armed Home", devices, "Off", "Normal", 0)
            zoneNr = zoneNr + 1
        
        #Populate the Matrix with Armed Away Devices
        zoneNr = 0
        ZoneArmedAway = Parameters["Mode3"].split(";")
        for zone in ZoneArmedAway:
            devicesIdx = zone.split(",")
            for devices in devicesIdx:
                if str(devices.lower()) not in "none,0":
                    if self.doDeviceExist(devices) is True:
                        self.addToMatrix(TotalRows, zoneNr, "Armed Away", devices, "Off", "Normal", 0)
            zoneNr = zoneNr + 1
        
        self.TotalZones = zoneNr
        
        #Populate the Matrix with Fire Devices
        zoneNr = 0
        ZoneFireDevices = Parameters["Mode4"].split(";")
        for zone in ZoneFireDevices:
            devicesIdx = zone.split(",")
            for devices in devicesIdx:
                if str(devices.lower()) not in "none,0":
                    if self.doDeviceExist(devices) is True:
                        self.addToMatrix(TotalRows, zoneNr, "Armed Home", devices, "Off", "Normal", 0)
            zoneNr = zoneNr + 1
        
        
        # create devices
        self.createDevices(self.TotalZones)
        
        #for zone in range(self.TotalZones):
        #    self.setZoneStatus(self.TotalZones, zone, "Normal")
        #    self.OpenSectionTotal[zone] = 0
            
        
        for x in range(TotalRows):
            Domoticz.Debug(strName+"Matrix: "+str(self.Matrix[x][0])+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+str(self.Matrix[x][3])+" | "+str(self.Matrix[x][4])+" | "+str(self.Matrix[x][5])+" | "+" | "+str(self.Matrix[x][5])+" | ")
        
        if int(Parameters["Mode1"]) == 1:
            self.ActivePIRSirenHome = 1
            self.ActivePIRSirenAway = 1
        elif int(Parameters["Mode1"]) == 2:
            self.ActivePIRSirenHome = 1
            self.ActivePIRSirenAway = 2
        elif int(Parameters["Mode1"]) == 3:
            self.ActivePIRSirenHome = 2
            self.ActivePIRSirenAway = 1
        elif int(Parameters["Mode1"]) == 4:
            self.ActivePIRSirenHome = 2
            self.ActivePIRSirenAway = 2
        
        for zone in range(self.TotalZones):
            self.ArmingStatusMode[zone] = 0
            openSectionDevice = self.ALARM_OPEN_SECTION_DEVICE + zone
            triggeredDevice = self.ALARM_TRIGGERED_DEVICE + zone
            UpdateDevice(openSectionDevice, 1, "None")
            UpdateDevice(triggeredDevice, 1, "None")

        self.entryDelay = Devices[self.ALARM_ENTRY_DELAY].nValue
        self.OpenSectionArmAnyWay = Devices[self.ALARM_OPEN_SECTION_TIMEOUT].nValue
        
        
        Domoticz.Heartbeat(5)
        self.secpassword = self.getsecpasspword()


    def onStop(self):
        strName = "onStop: "
        Domoticz.Debug(strName+"Plugin is stopping.")
        

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
        if self.versionCheck is True:
            Domoticz.Log("VersionCheck = TRUE")
        elif self.versionCheck is False:
            Domoticz.Log("VersionCheck = TRUE")
        else:
            Domoticz.Error("VersionCheck = ERROR")
        if self.versionCheck is True:
            strName = "onCommand: "
            Domoticz.Debug(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
            for zone in range(self.TotalZones):
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                if ArmingStatusUnit == Unit:
                    self.controlSiren(self.TotalZones)
            if self.ALARM_SENSOR_TIME == Unit:
                self.SensorActiveTime = Level + 20
                Domoticz.Debug(strName+"Sensor Active Time = "+str(self.SensorActiveTime))
                UpdateDevice(self.ALARM_SENSOR_TIME, Level, str(Level))
            if self.ALARM_ENTRY_DELAY == Unit:
                self.entryDelay = Level + 20 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            if self.ALARM_OPEN_SECTION_TIMEOUT == Unit: 
                self.entryDelay = Level + 20 #seconds
                Domoticz.Debug(strName+"Open Sections = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_OPEN_SECTION_TIMEOUT, Level, str(Level))
            if self.ALARM_EXIT_DELAY == Unit:
                self.exitDelay = Level + 20 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            for zone_nr in range(self.TotalZones):
                AlarmModeUnit = self.ALARM_ARMING_MODE_UNIT + zone_nr
                if AlarmModeUnit == Unit:
                    if Level == 0:
                        Domoticz.Log("Set Security Panel to Normal")
                        UpdateDevice(AlarmModeUnit, Level, str(Level))
                        openSectionDevice = self.ALARM_OPEN_SECTION_DEVICE + zone_nr
                        UpdateDevice(openSectionDevice, 1, "None")
                        self.alarmModeChange(zone_nr, Level)
                        self.mainAlarm()
                        if self.ALARM_ARMING_MODE_UNIT == Unit:
                            self.setSecurityState(0)
                    elif Level == 10:
                        Domoticz.Log("Set Security Panel to Armed Home")
                        UpdateDevice(AlarmModeUnit, Level, str(Level))
                        self.pollZoneDevices(self.MatrixRowTotal)
                        self.alarmModeChange(zone_nr, Level)
                        self.mainAlarm()
                        if self.ALARM_ARMING_MODE_UNIT == Unit:
                            self.setSecurityState(1)
                    elif Level == 20:
                        Domoticz.Log("Set Security Panel to Armed Away")
                        UpdateDevice(AlarmModeUnit, Level, str(Level))
                        self.pollZoneDevices(self.MatrixRowTotal)
                        self.alarmModeChange(zone_nr, Level)
                        self.mainAlarm()
                        if self.ALARM_ARMING_MODE_UNIT == Unit:
                            self.setSecurityState(2)
        else:
            Domoticz.Error("Check Configuration")
        
                
    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        strName = "onNotification: "
        Domoticz.Debug(strName+"called")
        Domoticz.Debug(strName+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        strName = "onDisconnect: "
        Domoticz.Debug(strName+"called")

    def onHeartbeat(self):
        if self.versionCheck is True:
            strName = "onHeartbeat: "
            Domoticz.Debug(strName+"called")
            self.SensorActiveTime = Devices[self.ALARM_SENSOR_TIME].nValue
            # Main alarm
            self.mainAlarm()
            # Siren
            #self.controlSiren(self.TotalZones)

            for x in range(self.MatrixRowTotal):
                Domoticz.Debug(strName+"Matrix: "+str(self.Matrix[x][0])+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+str(self.Matrix[x][3])+" | "+str(self.Matrix[x][4])+" | "+str(self.Matrix[x][5])+" | "+str(self.Matrix[x][6])+" | ")
        
            for zone in range(self.TotalZones):
                Domoticz.Debug(strName+"self.ArmingStatusMode["+str(zone)+"] = "+str(self.ArmingStatusMode[zone]))
        else:
            Domoticz.Error("Check Configuration")
         
    def setVersionCheck(self, value):
        strName = "setVersionCheck - "
        if self.versionCheck != value:
            self.versionCheck = value
            Domoticz.Log("Changed versionCheck to "+value)
        else:
            Domoticz.Log("VersionCheck is "+self.versionCheck)
        
        
    def pollZoneDevices(self, TotalRows):
        strName = "pollZoneDevices - "
        switchStatusIdx = ""
        for row in range(TotalRows):
            deviceIDX = self.Matrix[row][3]
            switchStatusIdx = self.getSwitchIDXStatus(deviceIDX)
            if switchStatusIdx == "On"  or switchStatusIdx == "Open" or switchStatusIdx == "Unlocked":
                if self.Matrix[row][4] not in "On,Normal":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "On", "New")
            elif switchStatusIdx == "Off" or switchStatusIdx == "Closed" or switchStatusIdx == "Locked":
                if self.Matrix[row][4] not in "Off":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off")
                    #if self.Matrix[row][2] == "Armed Away":
                    #   self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off", "Normal")
                    #else:
                    #    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off")
        
        for x in range(TotalRows):
            Domoticz.Debug(strName+"Matrix: "+str(self.Matrix[x][0])+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+str(self.Matrix[x][3])+" | "+str(self.Matrix[x][4])+" | "+str(self.Matrix[x][5])+" | "+str(self.Matrix[x][6])+" | ")
        
            
    def getSecurityState(self):
        strName = "getSecurityState - "
        APIjson = DomoticzAPI("type=command&param=getsecstatus")
        #/json.htm?type=command&param=getsecstatus
        try:
            nodes = APIjson
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        if nodes["secstatus"] == 0:
            Domoticz.Debug("Security State = Disarmed")
            self.SecurityPanel = "Disarmed"
        elif nodes["secstatus"] == 1:
            Domoticz.Debug("Security State = Arm Home")
            self.SecurityPanel = "Arm Home"
        elif nodes["secstatus"] == 2:
            Domoticz.Debug("Security State = Arm Away")
            self.SecurityPanel = "Arm Away"
        elif nodes["secstatus"] == 3:
            Domoticz.Debug("Security State = Unknown")
            self.SecurityPanel = "Unknown"
        
    def getsecpasspword(self):
        strName = "getsecpasspword - "
        APIjson = DomoticzAPI("type=settings")
        #type=command&param=getlightswitches
        try:
            nodes = APIjson
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        if nodes["SecPassword"] != "":
            secpassword = nodes["SecPassword"]
        return secpassword
    
    def setSecurityState(self, SecurityPanelState):
        strName = "setSecurityState - "
        #secpassword = self.getsecpasspword()
        if SecurityPanelState == 0 or SecurityPanelState == "Disarmed" or SecurityPanelState == "Normal":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=0&seccode="+self.secpassword)
        elif SecurityPanelState == 1 or SecurityPanelState == "Arm Home" or SecurityPanelState == "Armed Home":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=1&seccode="+self.secpassword)
        elif SecurityPanelState == 2 or SecurityPanelState == "Arm Away" or SecurityPanelState == "Armed Away":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=2&seccode="+self.secpassword)
        
                    
    def trippedSensor(self, TotalZones, TotalRows, AlarmMode, ZoneNr):
        strName = "trippedSensor - "
        # Check Sensor with state New
        if AlarmMode == "Disarmed":
            for row in range(TotalRows):
                #ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                if self.Matrix[row][5] == "New":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], self.Matrix[row][4], "Normal", 0)
                    #self.setAlarmArmingStatus("2trippedSensor", self.Matrix[row][1], "Normal")
            #self.setAlarmArmingStatus("2trippedSensor", self.Matrix[row][1], "Off")
        # Runs only when Armed Home or Armed Away
        elif AlarmMode == "Armed Home":
            trippedSensor = 0
            trippedZone = ""
            for row in range(TotalRows):
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                if self.Matrix[row][1] == ZoneNr:
                    if (self.Matrix[row][5] == "New" or self.Matrix[row][5] == "Tripped") and self.Matrix[row][2] == "Armed Home":
                        Domoticz.Log("Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                        if self.Matrix[row][3] not in Devices[self.ALARM_TRIGGERED_DEVICE+self.Matrix[row][1]].sValue:
                            self.setTriggeredDevice(self.Matrix[row][1], self.Matrix[row][3])
                        if self.ArmingStatusMode[self.Matrix[row][1]] != "Tripped":
                            if self.ArmingStatusMode[self.Matrix[row][1]] != "Alert":
                                self.setAlarmArmingStatus("1trippedSensor", self.Matrix[row][1], "Tripped")
                        #if self.Matrix[row][5] == "New":
                        sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                        self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                        self.setAlarmArmingStatus("2trippedSensor", self.Matrix[row][1], "Tripped")
                        trippedSensor = trippedSensor + 1
                        if trippedZone == "":
                            trippedZone = str(self.Matrix[row][1])
                        else:
                            trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])
                #else:
                    #self.setAlarmArmingStatus("2trippedSensor", self.Matrix[row][1], "Normal")
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log("Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
                    ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    if trippedZoneCheck >= self.ActivePIRSirenHome:
                        self.setAlarmArmingStatus("2trippedSensor", zone, "Alert")
                elif trippedZoneCheck == 0:
                    ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    try:
                        timeDiff = datetime.now() - datetime.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                    except TypeError:
                        timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                    timeDiffSeconds = timeDiff.seconds
                    if timeDiffSeconds >= (self.OpenSectionArmAnyWay):
                        self.setAlarmArmingStatus("5trippedSensor", zone, "Normal")
                #elif trippedZoneCheck == 0:
                #    if self.Matrix[row][6] == 0
                #        self.setAlarmArmingStatus("5trippedSensor", zone, "Normal")
        elif AlarmMode == "Armed Away": 
            trippedSensor = 0
            trippedZone = ""
            for row in range(TotalRows):
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                if self.Matrix[row][1] == ZoneNr:
                    if self.Matrix[row][5] == "New" or self.Matrix[row][5] == "Tripped":
                        Domoticz.Log("Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                        if self.Matrix[row][3] not in Devices[self.ALARM_TRIGGERED_DEVICE+self.Matrix[row][1]].sValue:
                            self.setTriggeredDevice(self.Matrix[row][1], self.Matrix[row][3])
                        if self.ArmingStatusMode[self.Matrix[row][1]] != "Tripped":
                            if self.ArmingStatusMode[self.Matrix[row][1]] != "Alert":
                                self.setAlarmArmingStatus("4trippedSensor", self.Matrix[row][1], "Tripped")
                        #if self.Matrix[row][5] == "New":
                        sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                        self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                        self.setAlarmArmingStatus("2trippedSensor", self.Matrix[row][1], "Tripped")
                        trippedSensor = trippedSensor + 1
                        if trippedZone == "":
                            trippedZone = str(self.Matrix[row][1])
                        else:
                            trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log("Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
                    ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    if trippedZoneCheck >= self.ActivePIRSirenAway:
                        self.setAlarmArmingStatus("5trippedSensor", zone, "Alert")
                elif trippedZoneCheck == 0:
                    ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    try:
                        timeDiff = datetime.now() - datetime.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                    except TypeError:
                        timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                    timeDiffSeconds = timeDiff.seconds
                    if timeDiffSeconds >= (self.OpenSectionArmAnyWay):
                        self.setAlarmArmingStatus("5trippedSensor", zone, "Normal")
                                
    def setTrippedSensorTimer(self, TotalRows, DeviceIdx, TimeChanged):
        strName = "setTrippedSensorTimer - "
        for row in range(TotalRows):
            #if self.Matrix[row][3] == DeviceIdx and self.Matrix[row][4] == "On" and self.Matrix[row][5] == "New":
            if self.Matrix[row][3] == DeviceIdx:
                if self.Matrix[row][5] == "New":
                    self.Matrix[row][5] = "Tripped"
                    self.Matrix[row][6] = TimeChanged
                    Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+self.Matrix[row][4]+" Changed = "+self.Matrix[row][5]+" Time Changed = "+str(TimeChanged))
                    #break
    
    def trippedSensorTimer(self, TotalRows):
        strName = "trippedSensorTimer"
        for row in range(TotalRows):
            if self.Matrix[row][5] == "Tripped":
                try:
                    timeDiff = datetime.now() - datetime.strptime(self.Matrix[row][6],'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(self.Matrix[row][6],'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= (self.SensorActiveTime + self.entryDelay):
                    self.Matrix[row][5] = "Normal"
                    self.Matrix[row][6] = 0
        
    def createTheMatrix(self, width, hight):
        strName = "createTheMatrix - "
        self.Matrix = [[0 for x in range(width)] for y in range(hight)] 
        # table:
        # ZONE_Nr | Arm Home/Away| DeviceIdx | State | Changed | Time Changed |
        # Matrix[0][0] = 1
        
    def calculateMatixRows(self):
        ZoneArmedHome = Parameters["Mode2"].split(";")
        ZoneArmedAway = Parameters["Mode3"].split(";")
        ZoneFireDevices = Parameters["Mode4"].split(";")
        countArmedHome = self.calculateAmountOfDevices(ZoneArmedHome)
        countArmedAway = self.calculateAmountOfDevices(ZoneArmedAway)
        countFireDevices = self.calculateAmountOfDevices(ZoneFireDevices)
        TotalRows = countArmedHome + countArmedAway + countFireDevices
        return TotalRows
        
    def calculateAmountOfDevices(self, AmountOfDevices):
        DevicesCount = 0
        for amount in AmountOfDevices:
            zoneDevices = amount.split(",")
            for amountDevices in zoneDevices:
                if str(amountDevices.lower()) not in "none,0":
                    if self.doDeviceExist(amountDevices) is True:
                        DevicesCount = DevicesCount + 1
        return DevicesCount
        
        
    def addToMatrix(self, TotalRows, ZoneNr, ArmMode, DeviceIdx, DeviceState, Changed, TimeChanged):
        strName = "addToMatrix - "
        # Find free row number
        LastRow = 0
        for row in range(TotalRows):
            if self.Matrix[row][0] == 0:
                LastRow = row
                #break
                
        # Add to Matrix
        NewRow = LastRow+1
        self.Matrix[LastRow][0] = NewRow
        self.Matrix[LastRow][1] = ZoneNr
        self.Matrix[LastRow][2] = ArmMode
        self.Matrix[LastRow][3] = DeviceIdx
        self.Matrix[LastRow][4] = DeviceState
        self.Matrix[LastRow][5] = Changed
        self.Matrix[LastRow][6] = TimeChanged
        Domoticz.Debug(strName+"Add row ("+str(NewRow)+"): ZoneNr = "+str(ZoneNr)+" ArmMode = "+ArmMode+" DeviceIdx = "+str(DeviceIdx)+" DeviceState = "+DeviceState+" Changed = "+Changed+" Time Changed = "+str(TimeChanged))
    
    def changeRowinMatrix(self, TotalRows, DeviceIdx, DeviceState, Changed=0, ChangedTime=9999):
        strName = "changeRowinMatrix - "
        for row in range(TotalRows):
            if self.Matrix[row][3] == DeviceIdx:
                self.Matrix[row][4] = DeviceState
                if Changed != 0:
                    self.Matrix[row][5] = Changed
                    #Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed)
                if ChangedTime != 9999:
                    self.Matrix[row][6] = ChangedTime
                    #Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed+" Changedtime = "+ChangedTime)
    
    
    def controlSiren(self, TotalZones):
        strName = "controlSiren - "
        countAlarm = 0
        for zone in range(TotalZones):
            if self.ArmingStatusMode[zone] == "Normal":
                self.deactivateSiren(self.TotalZones, zone)
            else:
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                AlarmModeUnit = self.ALARM_ARMING_MODE_UNIT+zone
                #timeDiff = 0
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                endSirenTimeSeconds = Devices[self.ALARM_ENTRY_DELAY].nValue + int(Parameters["Mode5"])
                if timeDiffSeconds >= Devices[self.ALARM_ENTRY_DELAY].nValue and timeDiffSeconds <= endSirenTimeSeconds: # EntryDelay
                    self.activateSiren(self.TotalZones, zone)
                    countAlarm = countAlarm + 1
                elif timeDiffSeconds < Devices[self.ALARM_ENTRY_DELAY].nValue:
                    countAlarm = countAlarm + 1
                elif timeDiffSeconds > endSirenTimeSeconds:
                    countAlarm = countAlarm + 0
                if countAlarm == 0:
                    AlarmModeUnit = self.ALARM_ARMING_MODE_UNIT + zone
                    if Devices[AlarmModeUnit].nValue == 10 or Devices[AlarmModeUnit].nValue == 20:
                        self.setAlarmArmingStatus("controlSiren", zone, "Normal")
                    else:
                        self.setAlarmArmingStatus("controlSiren", zone, "Off")
                    self.deactivateSiren(self.TotalZones, zone)
            
    
    def activateSiren(self, TotalZones, zoneNr):
        strName = "activateSiren - "
        ZoneAlerts = 0
        for zone in range(TotalZones):
            if self.ArmingStatusMode[zone] == "Alert":
                ZoneAlerts = ZoneAlerts + 1
        if ZoneAlerts > 0:
            if Devices[self.ALARM_MAIN_UNIT].sValue != "On":
                UpdateDevice(self.ALARM_MAIN_UNIT, 1, "On")
                Domoticz.Log("Turn ON Siren")
        
    def deactivateSiren(self, TotalZones, zoneNr):
        strName = "deactivateSiren - "
        ZoneAlerts = 0
        for zone in range(TotalZones):
            if self.ArmingStatusMode[zone] == "Alert":
                ZoneAlerts = ZoneAlerts + 1
        if ZoneAlerts == 0:
            if Devices[self.ALARM_MAIN_UNIT].sValue != "Off":
                UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
                Domoticz.Log("Turn OFF Siren")
        
    
    def mainAlarm(self):
        strName = "mainAlarm - "
        # Main Alarm script
        # Poll all sensors
        # Open Section - Exit Delay - Normal - Tripped - Alert
        if self.versionCheck is True:
            self.getSecurityState()
            self.pollZoneDevices(self.MatrixRowTotal)
            self.trippedSensorTimer(self.MatrixRowTotal)
            for zone in range(self.TotalZones):
                ArmingStatusUnit  = self.ALARM_ARMING_STATUS_UNIT + zone
                AlarmModeUnit = self.ALARM_ARMING_MODE_UNIT + zone
                # OFF
                if self.ArmingStatusMode[zone] == "Off":
                    self.controlSiren(self.TotalZones)
                    self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Disarmed", zone)
                # OPEN SECTIONS 
                elif self.ArmingStatusMode[zone] == "Open Sections":
                    try:
                        timeDiff = datetime.now() - datetime.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                    except TypeError:
                        timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                    timeDiffSeconds = timeDiff.seconds
                    if timeDiffSeconds >= self.OpenSectionArmAnyWay:
                        self.setAlarmArmingStatus("1-mainAlarm", zone, "Exit Delay")
                        self.OpenSectionTotal[zone] = 0
                # EXIT DELAY
                elif self.ArmingStatusMode[zone] == "Exit Delay":
                    AlarmModeUnit = self.ALARM_ARMING_MODE_UNIT + zone
                    # Exit Delay
                    try:
                        timeDiff = datetime.now() - datetime.strptime(Devices[AlarmModeUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                    except TypeError:
                        timeDiff = datetime.now() - datetime(*(time.strptime(Devices[AlarmModeUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                    timeDiffSeconds = timeDiff.seconds
                    if timeDiffSeconds >= self.exitDelay:
                        self.setAlarmArmingStatus("2-mainAlarm", zone, "Normal")
                # NORMAL
                elif self.ArmingStatusMode[zone] == "Normal":
                    # reset the open section text device
                    openSectionDevice = self.ALARM_OPEN_SECTION_DEVICE + zone
                    UpdateDevice(openSectionDevice, 1, "None")
                    triggeredDevice = self.ALARM_TRIGGERED_DEVICE + zone
                    UpdateDevice(triggeredDevice, 1, "None")
                    # Actual arm the building
                    if Devices[AlarmModeUnit].nValue == 0: # Disarmed
                        if self.ArmingStatusMode[zone] == "Normal":
                            self.setAlarmArmingStatus("3-mainAlarm", zone, "Off")
                        self.controlSiren(self.TotalZones)
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Disarmed", zone)
                    elif Devices[AlarmModeUnit].nValue == 10: # Armed Home
                        # Do the actual arming
                        self.controlSiren(self.TotalZones)
                        Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Home")
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Home", zone)
                    elif Devices[AlarmModeUnit].nValue == 20: # Armed Away
                        self.controlSiren(self.TotalZones)
                        Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Away")
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Away", zone)
                # TRIPPED
                elif self.ArmingStatusMode[zone] == "Tripped":
                    if Devices[AlarmModeUnit].nValue == 0: # Disarmed
                        if self.ArmingStatusMode[zone] == "Normal":
                            self.setAlarmArmingStatus("4-mainAlarm", zone, "Off")
                        self.controlSiren(self.TotalZones)
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Disarmed", zone)
                    elif Devices[AlarmModeUnit].nValue == 10: # Armed Home
                        # Do the actual arming
                        Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Home")
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Home", zone)
                    elif Devices[AlarmModeUnit].nValue == 20: # Armed Away
                        Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Away")
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Away", zone)
                # ALERT
                elif self.ArmingStatusMode[zone] == "Alert":
                    self.controlSiren(self.TotalZones)
        else:
            Domoticz.Error("Check Configuration")
               
            
    def alarmModeChange(self, zoneNr, newStatus):
        # Changes in the Alarm Mode will be handled here
        strName = "alarmModeChange - "
        ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + int(zoneNr)
        if newStatus == 0: # Normal
            # Reset Siren and Alarm Status
            self.setAlarmArmingStatus("alarmModeChange", zoneNr, "Off")
        elif newStatus == 10: # Armed Home
            # Check Exit Delay
            self.checkOpenSections(self.MatrixRowTotal, zoneNr, 10)
        elif newStatus == 20: # Armed Way
            self.checkOpenSections(self.MatrixRowTotal, zoneNr, 20)
            
            
    def setAlarmArmingStatus(self, Location, ZoneNr, ZoneMode):
        # This is the worker for alarmModeChange()
        ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + ZoneNr
        Domoticz.Debug("Location = "+Location)
        if ZoneMode == "Off" or ZoneMode == 0:
            if Devices[ArmingStatusUnit].sValue != "0":
                UpdateDevice(ArmingStatusUnit, 0, "0")
                self.setZoneStatus(self.TotalZones, ZoneNr, "Off")
                Domoticz.Log("Set Arming Status to Off")
        elif ZoneMode == "Open Sections" or ZoneMode == 10:
            if Devices[ArmingStatusUnit].sValue != "10":
                UpdateDevice(ArmingStatusUnit, 10, "10")
                self.setZoneStatus(self.TotalZones, ZoneNr, "Open Sections")
                Domoticz.Log("Set Arming Status to Open Sections")
        elif ZoneMode == "Exit Delay" or ZoneMode == 20:
            if Devices[ArmingStatusUnit].sValue != "20":
                UpdateDevice(ArmingStatusUnit, 20, "20")
                self.setZoneStatus(self.TotalZones, ZoneNr, "Exit Delay")
                Domoticz.Log("Set Arming Status to Exit Delay")
        elif ZoneMode == "Normal" or ZoneMode == 30:
            if Devices[ArmingStatusUnit].sValue != "30":
                UpdateDevice(ArmingStatusUnit, 30, "30")
                self.setZoneStatus(self.TotalZones, ZoneNr, "Normal")
                Domoticz.Log("Set Arming Status to Normal")
        elif ZoneMode == "Tripped" or ZoneMode == 40:
            if Devices[ArmingStatusUnit].sValue != "50":
                if Devices[ArmingStatusUnit].sValue != "40":
                    UpdateDevice(ArmingStatusUnit, 40, "40")
                    self.setZoneStatus(self.TotalZones, ZoneNr, "Tripped")
                    Domoticz.Log("Set Arming Status to Tripped")
        elif ZoneMode == "Alert" or ZoneMode == 50:
            if Devices[ArmingStatusUnit].sValue != "50":
                UpdateDevice(ArmingStatusUnit, 50, "50")
                self.setZoneStatus(self.TotalZones, ZoneNr, "Alert")
                Domoticz.Log("Set Arming Status to Alert")

    def setZoneStatus(self, TotalZones, ZoneNr, ZoneStatus):
        Domoticz.Debug("TotalZones = "+str(TotalZones)+" ZoneNr = "+str(ZoneNr)+" ZoneStatus = "+ZoneStatus)
        for zone in range(TotalZones):
            if zone == ZoneNr:
                self.ArmingStatusMode[zone] = ZoneStatus
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + zone
                break
            
    def checkOpenSections(self, TotalDevices, zoneNr, zoneMode):
        strName = "checkOpenSections - "
        if zoneMode == 0:
            zoneModeTxt = "Disarmed"
        elif zoneMode == 10:
            zoneModeTxt = "Armed Home"
        elif zoneMode == 20:
            zoneModeTxt = "Armed Away"
        countArmedHome = 0
        countArmedAway = 0
        for zone in range(self.TotalZones):
            self.OpenSectionTotal[zone] = 0
        for row in range(TotalDevices):
            if self.Matrix[row][1] == zoneNr:
                # Armed Home then only check Devices in Armed Home
                if zoneModeTxt == "Armed Home":
                    if self.Matrix[row][2] == "Armed Home":
                        if self.Matrix[row][4] == "On":
                            # found open section (device)
                            ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + zoneNr
                            self.setAlarmArmingStatus("checkOpenSections", zoneNr, "Open Sections")
                            self.setOpenSectionDevice(zoneNr, self.Matrix[row][3])
                            countArmedHome = countArmedHome + 1
                            self.OpenSectionTotal[zoneNr] = countArmedHome
                            #self.OpenSectionTotal[zoneNr] = self.OpenSectionTotal[zoneNr] + 1
                # Armed Away + Armed Home
                elif zoneModeTxt == "Armed Away":
                    if self.Matrix[row][4] == "On":
                        # found open section (device)
                        #ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + zoneNr
                        self.setAlarmArmingStatus("checkOpenSections", zoneNr, "Open Sections")
                        self.setOpenSectionDevice(zoneNr, self.Matrix[row][3])
                        countArmedAway = countArmedAway + 1
                        self.OpenSectionTotal[zoneNr] = countArmedAway
                        #self.OpenSectionTotal[zoneNr] = self.OpenSectionTotal[zoneNr] + 1
        #Moet nog aangepast worden:
        for zone in range(self.TotalZones):
            Domoticz.Log(strName+"Total count in zone "+str(zone)+" of Open Section Devices = "+str(self.OpenSectionTotal[zone]))
            if self.OpenSectionTotal[zone] == 0 and self.ArmingStatusMode[zone] != "Open Sections":
                # Exit Delay
                ArmingStatusUnit = self.ALARM_ARMING_STATUS_UNIT + int(zone)
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ArmingStatusUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= self.exitDelay:
                    self.setAlarmArmingStatus("checkOpenSections", zone, "Normal")
                elif timeDiffSeconds < self.exitDelay:
                    self.setAlarmArmingStatus("checkOpenSections", zone, "Exit Delay")

    
    def setOpenSectionDevice(self, zoneNr, idx):
        Domoticz.Log("Report OpenSections Device")
        openSectionDevice = self.ALARM_OPEN_SECTION_DEVICE + zoneNr
        openSectionDeviceName = self.getSwitchIDXName(idx)
        if Devices[openSectionDevice].sValue == "None":
            UpdateDevice(openSectionDevice, 1, openSectionDeviceName)
        else:
            openSectionDeviceNameTotal = Devices[openSectionDevice].sValue +","+ openSectionDeviceName
            UpdateDevice(openSectionDevice, 1, openSectionDeviceNameTotal)

    def setTriggeredDevice(self, zoneNr, idx):
        Domoticz.Log("Report Triggered Device")
        triggeredDevice = self.ALARM_TRIGGERED_DEVICE + zoneNr
        triggeredDeviceName = self.getSwitchIDXName(idx)+" (idx="+idx+")"
        if Devices[triggeredDevice].sValue == "None":
            UpdateDevice(triggeredDevice, 1, triggeredDeviceName)
            #Here straight to Alert for Fire devices
            ZoneFireDevices = Parameters["Mode4"].split(";")
            for zone in ZoneFireDevices:
                devicesIdx = zone.split(",")
                for devices in devicesIdx:
                    if str(devices.lower()) == idx:
                        #Found Fire Device turning on the Alert
                        self.setAlarmArmingStatus("setTriggeredDevice", zoneNr, "Alert")
        else:
            triggeredDeviceNameTotal = Devices[triggeredDevice].sValue +","+ triggeredDeviceName
            UpdateDevice(triggeredDevice, 1, triggeredDeviceNameTotal)
            
            
    def doDeviceExist(self, idx):
        strName = "doDeviceExist"
        statusdoDeviceExist = ""
        jsonQuery = "type=devices&rid="+idx
        #/json.htm?type=devices&rid=16
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
            Domoticz.Log("Device "+idx+" does exist!")
            statusdoDeviceExist = True
        except:
            nodes = []
            Domoticz.Error("Device "+idx+" NOT does exist!")
            statusdoDeviceExist = False
            self.setVersionCheck(False)
            #self.VersionCheck = False
        return statusdoDeviceExist
        
        
    def getSwitchIDXName(self, idx):
        strName = "getSwitchIDXLastUpdate"
        jsonQuery = "type=devices&rid="+idx
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        #Domoticz.Debug(strName+"APIjson = "+str(nodes))
        statusIdx = ""
        for node in nodes:
            statusIdx = str(node["Name"])
        return statusIdx
    
    def getSwitchIDXLastUpdate(self, idx):
        strName = "getSwitchIDXLastUpdate"
        jsonQuery = "type=devices&rid="+idx
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        #Domoticz.Debug(strName+"APIjson = "+str(nodes))
        statusIdx = ""
        for node in nodes:
            statusIdx = str(node["LastUpdate"])
        return statusIdx
    
    def getSwitchIDXStatus(self, idx):
        strName = "getSwitchIDXStatus"
        jsonQuery = "type=devices&rid="+idx
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        #Domoticz.Debug(strName+"APIjson = "+str(nodes))
        statusIdx = ""
        for node in nodes:
            statusIdx = str(node["Status"])
        return statusIdx
    
    def createDevices(self, TotalZones):
        strName = "createDevices - "
        if (self.ALARM_MAIN_UNIT not in Devices):
            Domoticz.Device(Name="SIREN",  Unit=self.ALARM_MAIN_UNIT, Used=1, TypeName="Switch", Image=13).Create()
            UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
            
        if (self.ALARM_ENTRY_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 second|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Description = "Entry Delay gives you a short time to disarm your Alarm System for Domoticz when entering your home."
            Domoticz.Device(Name="Entry Delay", Unit=self.ALARM_ENTRY_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
            UpdateDevice(self.ALARM_ENTRY_DELAY, 0, "0")
            
        if (self.ALARM_EXIT_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 seconds|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Description = "The Exit Delay setting gives you a short period of time to leave your home once you’ve armed Alarm System for Domoticz."
            Domoticz.Device(Name="Exit Delay", Unit=self.ALARM_EXIT_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
            UpdateDevice(self.ALARM_EXIT_DELAY, 0, "0")
        
        if (self.ALARM_SENSOR_TIME not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 seconds|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Description = "The time a triggered sensor is active in memory so we can track various sensors if they are triggered."
            Domoticz.Device(Name="Sensor Active Time", Unit=self.ALARM_SENSOR_TIME, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
            UpdateDevice(self.ALARM_SENSOR_TIME, 30, "30")
            
        if (self.ALARM_OPEN_SECTION_TIMEOUT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 second|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Description = "The timeout for open sections to proceed to the next step and arm the alarm anyway and correlate them."
            Domoticz.Device(Name="Open Sections Timeout", Unit=self.ALARM_OPEN_SECTION_TIMEOUT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
            UpdateDevice(self.ALARM_OPEN_SECTION_TIMEOUT, 30, "30")   
        
        
        Options = {"LevelActions": "||||",
                       "LevelNames": "Disarmed|Armed Home|Armed Away",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
        Description = "The Arming Mode options."
        found_device = False
        for zone_nr in range(self.TotalZones):
            for item in Devices:
                if zone_nr < 10:
                    removeCharacters = -20
                else:
                    removeCharacters = -21
                if Devices[item].Name[removeCharacters:] == "Arming Mode (Zone "+str(zone_nr)+")":
                        Domoticz.Log("Found device = "+"Arming Mode (Zone "+str(zone_nr)+")")
                        found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Arming_Mode()
                    Domoticz.Device(Name="Arming Mode (Zone "+str(zone_nr)+")", Unit=new_unit, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
       
        
        Options = {"LevelActions": "||||",
                       "LevelNames": "Off|Open Sections|Exit Delay|Normal|Tripped|Alert",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
        DescriptionArmingStatus = "The Arming Status options."
        #DescriptionOpenSectionsDevice = "List of Open Section Devices."
        found_device = False
        for zoneNr in range(TotalZones):
            for item in Devices:
                if zoneNr < 10:
                    removeCharacters = -22
                else:
                    removeCharacters = -23
                if Devices[item].Name[removeCharacters:] == "Arming Status (Zone "+str(zoneNr)+")":
                    Domoticz.Log("Found device = "+"Arming Status (Zone "+str(zoneNr)+")")
                    found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Arming_Status()
                    Domoticz.Device(Name="Arming Status (Zone "+str(zoneNr)+")", Unit=new_unit, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=DescriptionArmingStatus, Image=8).Create()
                            
        DescriptionOpenSectionsDevice = "List of Open Section Devices."
        found_device = False
        for zoneNr in range(TotalZones):
            for item in Devices:
                if zoneNr < 10:
                    removeCharacters = -20
                else:
                    removeCharacters = -21
                if Devices[item].Name[removeCharacters:] == "Open Sections zone "+str(zoneNr):
                    Domoticz.Log("Found device = "+"Open Sections zone "+str(zoneNr))
                    found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Open_Section_Device()
                    Domoticz.Device(Name="Open Sections zone "+str(zoneNr), Unit=new_unit, TypeName="Text", Used=1, Description=DescriptionOpenSectionsDevice, Image=8).Create()
        
        DescriptionTrippedDevice = "List of Tripped Devices."
        found_device = False
        for zoneNr in range(TotalZones):
            for item in Devices:
                if zoneNr < 10:
                    removeCharacters = -22
                else:
                    removeCharacters = -23
                if Devices[item].Name[removeCharacters:] == "Tripped Devices zone "+str(zoneNr):
                    Domoticz.Log("Found device = "+"Tripped Devices zone "+str(zoneNr))
                    found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Triggered_Device()
                    Domoticz.Device(Name="Tripped Devices zone "+str(zoneNr), Unit=new_unit, TypeName="Text", Used=1, Description=DescriptionTrippedDevice, Image=8).Create()
        
        
        
def DomoticzAPI(APICall):
    strName = "DomoticzAPI - "
    resultJson = None
    url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], Parameters["Port"], parse.quote(APICall, safe="&="))
    #Domoticz.Debug(strName+"Calling domoticz API: {}".format(url))
    try:
        req = request.Request(url)
        if Parameters["Username"] != "":
            #Domoticz.Debug(strName+"Add authentification for user {}".format(Parameters["Username"]))
            credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
            encoded_credentials = base64.b64encode(credentials.encode('ascii'))
            req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

        response = request.urlopen(req)
        #Domoticz.Debug(strName+"Response status = "+str(response.status))
        if response.status == 200:
            resultJson = json.loads(response.read().decode('utf-8'))
            if resultJson["status"] != "OK":
                Domoticz.Error(strName+"Domoticz API returned an error: status = {}".format(resultJson["status"]))
                resultJson = None
        else:
            Domoticz.Error(strName+"Domoticz API: http error = {}".format(response.status))
    except:
        Domoticz.Error(strName+"Error calling '{}'".format(url))
    return resultJson

        

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

def find_available_unit():
    for num in range(51,200):
        if num not in Devices:
            return num
    return None


def find_available_unit_Arming_Mode():
    for num in range(10,19):
        if num not in Devices:
            return num
    return None

def find_available_unit_Arming_Status():
    for num in range(20,29):
        if num not in Devices:
            return num
    return None

def find_available_unit_Open_Section_Device():
    for num in range(40,49):
        if num not in Devices:
            return num
    return None

def find_available_unit_Triggered_Device():
    for num in range(50,59):
        if num not in Devices:
            return num
    return None
