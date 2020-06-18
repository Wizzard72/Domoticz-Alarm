# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="Alarm" name="Alarm" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Alarm plugin</h2><br/>
        This plugin creates an Alarm System in Domoticz. It depends on the devices already available in Domoticz, such as PIR, Door, etc. sensors.<br/>
        <br/>
        <h3>Configuration</h3><br/>
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
        </ul>
        <br/>
        Open Sections are detected and reported per zone in the Arming Status Selector Switch. After 50 seconds it's armed anyway.<br/>
        <br/>
        Exit and Entry Delay can be set through the Selector Switches. They are for all the zones configured<br/>
    </description>
    <params>
        <param field="Address" label="Domoticz IP Address" width="200px" required="true" default="localhost"/>
        <param field="Port" label="Port" width="40px" required="true" default="8080"/>
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
        <param field="Mode2" label="Zone Armed Home" width="600px" required="true" default="idx,idc,idc;idx,idx,idx"/>
        <param field="Mode3" label="Zone Armed Away" width="600px" required="true" default="idx,idc,idc;idx,idx,idx"/>
        <param field="Mode4" label="Siren active for (s)" width="150" required="true" default="50"/>
        <param field="Mode5" label="Interval in seconds" width="200px" required="true" default="15"/>
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
    ALARM_ARMING_MODE_UNIT = 10
    ALARM_ARMING_STATUS_UNIT = 20
    ALARM_PIR_Zone_UNIT = 30
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
        ZoneArmedHome = Parameters["Mode2"].split(";")
        zoneNr = 0
        for zone in ZoneArmedHome:
            devicesIdx = zone.split(",")
            for devices in devicesIdx:
                if str(devices.lower()) not in "none,0":
                    self.addToMatrix(TotalRows, zoneNr, "Armed Home", devices, "Off", "Normal", 0)
            zoneNr = zoneNr + 1
        zoneNr = 0
        ZoneArmedAway = Parameters["Mode3"].split(";")
        for zone in ZoneArmedAway:
            devicesIdx = zone.split(",")
            for devices in devicesIdx:
                if str(devices.lower()) not in "none,0":
                    self.addToMatrix(TotalRows, zoneNr, "Armed Away", devices, "Off", "Normal", 0)
            zoneNr = zoneNr + 1
        
        self.TotalZones = zoneNr
        
        # create devices
        self.createDevices(self.TotalZones)
        
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
        
        
        Domoticz.Heartbeat(int(Parameters["Mode5"]))
        self.secpassword = self.getsecpasspword()


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
        Domoticz.Debug(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        
        for zone in range(self.TotalZones):
            zoneNrUnitID = self.ALARM_ARMING_STATUS_UNIT+zone
            if zoneNrUnitID == Unit:
                self.controlSiren(self.TotalZones)
                #if Level == 0:
                #    self.deactivateSiren()
                #elif Level == 40:
                #    self.activateSiren()
        
        if self.ALARM_SENSOR_TIME == Unit:
            self.SensorActiveTime = Level
            Domoticz.Debug(strName+"Sensor Active Time = "+str(self.SensorActiveTime))
            UpdateDevice(self.ALARM_SENSOR_TIME, Level, str(Level))
        
        if self.ALARM_ENTRY_DELAY == Unit:
            if Level == 0:
                self.entryDelay = 0 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 10:
                self.entryDelay = 10 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 20:
                self.entryDelay = 20 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 30:
                self.entryDelay = 30 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 40:
                self.entryDelay = 40 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 50:
                self.entryDelay = 50 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 60:
                self.entryDelay = 60 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 70:
                self.entryDelay = 70 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 80:
                self.entryDelay = 80 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 90:
                self.entryDelay = 90 #seconds
                Domoticz.Debug(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
                
        if self.ALARM_EXIT_DELAY == Unit:
            if Level == 0:
                self.exitDelay = 0 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 10:
                self.exitDelay = 10 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 20:
                self.exitDelay = 20 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 30:
                self.exitDelay = 30 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 40:
                self.exitDelay = 40 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 50:
                self.exitDelay = 50 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 60:
                self.exitDelay = 60 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 70:
                self.exitDelay = 70 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 80:
                self.exitDelay = 80 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 90:
                self.exitDelay = 90 #seconds
                Domoticz.Debug(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
        
        for zone_nr in range(self.TotalZones):
            zoneUnitNr = self.ALARM_ARMING_MODE_UNIT + zone_nr
            if zoneUnitNr == Unit:
                if Level == 0:
                    Domoticz.Log("Set Security Panel to Normal")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(0)
                    self.mainAlarm()
                elif Level == 10:
                    Domoticz.Log("Set Security Panel to Armed Home")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(1)
                    self.mainAlarm()
                elif Level == 20:
                    Domoticz.Log("Set Security Panel to Armed Away")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(2)
                    self.mainAlarm()
        
                
    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        strName = "onNotification: "
        Domoticz.Debug(strName+"called")
        Domoticz.Debug(strName+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        strName = "onDisconnect: "
        Domoticz.Debug(strName+"called")

    def onHeartbeat(self):
        strName = "onHeartbeat: "
        Domoticz.Debug(strName+"called")
        # Main alarm
        self.mainAlarm()
        # Siren
        self.controlSiren(self.TotalZones)

        for x in range(self.MatrixRowTotal):
            Domoticz.Log(strName+"Matrix: "+str(self.Matrix[x][0])+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+str(self.Matrix[x][3])+" | "+str(self.Matrix[x][4])+" | "+str(self.Matrix[x][5])+" | "+str(self.Matrix[x][6])+" | ")
             
         
    def pollZoneDevices(self, TotalRows):
        strName = "pollZoneDevices - "
        APIjson = DomoticzAPI("type=scenes")
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        switchStatusIdx = ""
        for row in range(TotalRows):
            deviceIDX = self.Matrix[row][3]
            switchStatusIdx = self.getSwitchIDXStatus(deviceIDX)
            if switchStatusIdx in "On,Open" or switchStatusIdx == "Unlocked":
                if self.Matrix[row][4] not in "On,Normal":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "On", "New")
            elif switchStatusIdx in "Off,Closed" or switchStatusIdx == "Locked":
                if self.Matrix[row][4] not in "Off":
                    if self.Matrix[row][2] == "Armed Away":
                        self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off", "Normal")
                    else:
                        self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off")
        # reset Matrix for the zone
        #for row in range(self.MatrixRowTotal):
        #    Domoticz.Log("Reset Matrix so there are no false positives ("+self.Matrix[row][3]+" - Normal - 0)")
        #    self.changeRowinMatrix(self.MatrixRowTotal, self.Matrix[row][3], "Off", "Normal", 0)
        
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
        elif SecurityPanelState == 2 or SecurityPanelState == "Arm Way" or SecurityPanelState == "Armed Away":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=2&seccode="+self.secpassword)
        
                    
    def trippedSensor(self, TotalZones, TotalRows, AlarmMode):
        strName = "trippedSensor - "
        # Check Sensor with state New
        # Runs only when Armed Home or Armed Away
        if AlarmMode == "Armed Home":
            trippedSensor = 0
            trippedZone = ""
            for row in range(TotalRows):
                zoneNrUnit = 0
                if (self.Matrix[row][5] == "New" or self.Matrix[row][5] == "Tripped") and self.Matrix[row][2] == "Armed Home":
                    Domoticz.Log("Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                    if Devices[zoneNrUnit].nValue < 20: # Tripped value
                        UpdateDevice(zoneNrUnit, 20, "20") # Tripped
                    if self.Matrix[row][5] == "New":
                        sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                        self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                    trippedSensor = trippedSensor + 1
                    if trippedZone == "":
                        trippedZone = str(self.Matrix[row][1])
                    else:
                        trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])        
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log("Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
                if trippedZoneCheck >= self.ActivePIRSirenHome:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 40, "40") # Alert
                elif trippedZoneCheck == 0:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 0, "0") # Normal
        elif AlarmMode == "Armed Away": 
            trippedSensor = 0
            trippedZone = ""
            for row in range(TotalRows):
                zoneNrUnit = 0
                if self.Matrix[row][5] == "New" or self.Matrix[row][5] == "Tripped":
                    Domoticz.Log("Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                    if Devices[zoneNrUnit].nValue < 20: # Tripped value
                        UpdateDevice(zoneNrUnit, 20, "20") # Tripped
                    if self.Matrix[row][5] == "New":
                        sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                        self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                    trippedSensor = trippedSensor + 1
                    if trippedZone == "":
                        trippedZone = str(self.Matrix[row][1])
                    else:
                        trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log("Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
                if trippedZoneCheck >= self.ActivePIRSirenAway:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 40, "40") # Alert
                elif trippedZoneCheck == 0:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 0, "0") # Normal
        
    def setTrippedSensorTimer(self, TotalRows, DeviceIdx, TimeChanged):
        strName = "setTrippedSensorTimer - "
        for row in range(TotalRows):
            if self.Matrix[row][3] == DeviceIdx and self.Matrix[row][4] == "On" and self.Matrix[row][5] == "New":
                self.Matrix[row][5] = "Tripped"
                self.Matrix[row][6] = TimeChanged
                Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+self.Matrix[row][4]+" Changed = "+self.Matrix[row][5]+" Time Changed = "+str(TimeChanged))
    
    
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
        countArmedHome = self.calculateAmountOfDevices(ZoneArmedHome)
        countArmedAway = self.calculateAmountOfDevices(ZoneArmedAway)
        TotalRows = countArmedHome + countArmedAway
        return TotalRows
        
    def calculateAmountOfDevices(self, AmountOfDevices):
        DevicesCount = 0
        for amount in AmountOfDevices:
            zoneDevices = amount.split(",")
            for amountDevices in zoneDevices:
                if str(amountDevices.lower()) not in "none,0":
                    DevicesCount = DevicesCount + 1
        return DevicesCount
        
        
    def addToMatrix(self, TotalRows, ZoneNr, ArmMode, DeviceIdx, DeviceState, Changed, TimeChanged):
        strName = "addToMatrix - "
        # Find free row number
        LastRow = 0
        for row in range(TotalRows):
            if self.Matrix[row][0] == 0:
                LastRow = row
                break
                
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
    
    def changeRowinMatrix(self, TotalRows, DeviceIdx, DeviceState, Changed=0, ChangedTime=0):
        strName = "changeRowinMatrix - "
        for row in range(TotalRows):
            if self.Matrix[row][3] == DeviceIdx:
                self.Matrix[row][4] = DeviceState
                if Changed != 0:
                    self.Matrix[row][5] = Changed
                    #Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed)
                if ChangedTime != 0:
                    self.Matrix[row][6] = ChangedTime
                    #Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed+" Changedtime = "+ChangedTime)
    
    
    def controlSiren(self, TotalZones):
        countAlarm = 0
        for zone in range(TotalZones):
            zoneNr = self.ALARM_ARMING_STATUS_UNIT+zone
            #timeDiff = 0
            if Devices[zoneNr].nValue == 40: # Alert
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[zoneNr].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[zoneNr].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                endSirenTimeSeconds = Devices[self.ALARM_ENTRY_DELAY].nValue + int(Parameters["Mode4"])
                if timeDiffSeconds >= Devices[self.ALARM_ENTRY_DELAY].nValue and timeDiffSeconds <= endSirenTimeSeconds: # EntryDelay
                    self.activateSiren()
                    countAlarm = countAlarm + 1
                    Domoticz.Log("Turn ON Siren")
                else:
                    self.deactivateSiren()
                    if countAlarm >= 1:
                        countAlarm = countAlarm - 1
                    else:
                        countAlarm = 0
                    Domoticz.Log("Turn OFF Siren")
            elif Devices[zoneNr].nValue == 0:
                if Devices[self.ALARM_MAIN_UNIT].nValue == 1 and countAlarm == 0:
                    self.deactivateSiren()
    
    def activateSiren(self):
        strName = "activateSiren - "
        UpdateDevice(self.ALARM_MAIN_UNIT, 1, "On")
        
    def deactivateSiren(self):
        strName = "deactivateSiren - "
        UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
        
    def mainAlarm(self):
        strName = "mainAlarm - "
        # Main Alarm script
        # Poll all sensors
        self.getSecurityState()
        self.pollZoneDevices(self.MatrixRowTotal)
        self.trippedSensorTimer(self.MatrixRowTotal)
        
        # Alarm Mode
        for zone in range(self.TotalZones):
            ZoneID = self.ALARM_ARMING_MODE_UNIT + zone
            StatusID = self.ALARM_ARMING_STATUS_UNIT + zone
            # Exit Delay
            try:
                timeDiff = datetime.now() - datetime.strptime(Devices[ZoneID].LastUpdate,'%Y-%m-%d %H:%M:%S')
            except TypeError:
                timeDiff = datetime.now() - datetime(*(time.strptime(Devices[ZoneID].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
            timeDiffSeconds = timeDiff.seconds
            if Devices[StatusID].nValue == 50: # Open sections
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[StatusID].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[StatusID].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= 30: # 30 seconds after Open Section Notification enable alarm anyway
                    UpdateDevice(StatusID, 0, "0")
            else:
                if Devices[ZoneID].nValue == 10: # Armed Home
                    Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Home")
                    if timeDiffSeconds >= Devices[self.ALARM_EXIT_DELAY].nValue:
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Home")
                    else:
                        UpdateDevice(StatusID, 30, "30") # Normal
                elif Devices[ZoneID].nValue == 20: # Armed Away
                    Domoticz.Debug(strName+"Zone "+str(zone)+" is Armed Away")
                    if timeDiffSeconds >= Devices[self.ALARM_EXIT_DELAY].nValue:
                        self.trippedSensor(self.TotalZones, self.MatrixRowTotal, "Armed Away")
                    else:
                        UpdateDevice(StatusID, 30, "30") # Normal
            

            
    def alarmModeChange(self, zoneNr, newStatus):
        strName = "alarmModeChange - "
        zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT + int(zoneNr)
        StatusIDUnit = self.ALARM_ARMING_STATUS_UNIT + int(zoneNr)
        if newStatus == 0: # Normal
            # Reset Siren and Alarm Status
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            UpdateDevice(zoneNrUnit, 0, "0") # Normal
        elif newStatus == 10: # Armed Home
            # Use 
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            # check open sections
            self.checkOpenSections(self.MatrixRowTotal, zoneNr, 10)
            if Devices[StatusIDUnit].nValue == 50: # open sections
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[StatusIDUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[StatusIDUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= 50:
                    UpdateDevice(StatusIDUnit, 0, "0") # Normal
        elif newStatus == 20: # Armed Way
            # Use EntryDelay
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            # check open sections
            self.checkOpenSections(self.MatrixRowTotal, zoneNr, 20)
            if Devices[StatusIDUnit].nValue == 50: # open sections
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[StatusIDUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[StatusIDUnit].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= 50:
                    UpdateDevice(StatusIDUnit, 0, "0") # Normal

    def checkOpenSections(self, TotalDevices, zoneNr, zoneMode):
        strName = "checkOpenSections - "
        if zoneMode == 0:
            zoneModeTxt = "Disarmed"
        elif zoneMode == 10:
            zoneModeTxt = "Armed Home"
        elif zoneMode == 20:
            zoneModeTxt = "Armed Away"
        for row in range(TotalDevices):
            if self.Matrix[row][1] == zoneNr:
                # Armed Home then only check Devices in Armed Home
                Domoticz.Log("1JAAA HOOR")
                if zoneModeTxt == "Armed Home":
                    Domoticz.Log("2JAAA HOOR")
                    if self.Matrix[row][2] == "Armed Home":
                        Domoticz.Log("3JAAA HOOR")
                        if self.Matrix[row][4] == "On":
                            # found a device in zone to be armed
                            zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT + zoneNr
                            UpdateDevice(zoneNrUnit, 50, "50") # Open Sections
                            Domoticz.Log("4JAAA HOOR")
                # Armed Away + Armed Home
                elif zoneModeTxt == "Armed Away":
                    if self.Matrix[row][4] == "On":
                        # found a device in zone to be armed
                        zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT + zoneNr
                        UpdateDevice(zoneNrUnit, 50, "50") # Open Sections
                        Domoticz.Log("4JAAA HOOR")

    
    def getSwitchIDXLastUpdate(self, idx):
        strName = "getSwitchIDXLastUpdate"
        jsonQuery = "type=devices&rid="+idx
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
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
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
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
                       "LevelNames": "0 second|10 seconds|20 seconds|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Entry Delay", Unit=self.ALARM_ENTRY_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_ENTRY_DELAY, 0, "0")
            
        if (self.ALARM_EXIT_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 second|10 seconds|20 seconds|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Exit Delay", Unit=self.ALARM_EXIT_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_EXIT_DELAY, 0, "0")
        
        if (self.ALARM_SENSOR_TIME not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 second|10 seconds|20 seconds|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Sensor Active Time", Unit=self.ALARM_SENSOR_TIME, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_SENSOR_TIME, 30, "30")
        
        
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
                       "LevelNames": "Normal|Arming|Tripped|Exit Delay|Alert|Open Sections",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
        Description = "The Arming Status options."
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
                    Domoticz.Device(Name="Arming Status (Zone "+str(zoneNr)+")", Unit=new_unit, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=8).Create()
        
def DomoticzAPI(APICall):
    strName = "DomoticzAPI - "
    resultJson = None
    url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], Parameters["Port"], parse.quote(APICall, safe="&="))
    Domoticz.Debug(strName+"Calling domoticz API: {}".format(url))
    try:
        req = request.Request(url)
        if Parameters["Username"] != "":
            Domoticz.Debug(strName+"Add authentification for user {}".format(Parameters["Username"]))
            credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
            encoded_credentials = base64.b64encode(credentials.encode('ascii'))
            req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

        response = request.urlopen(req)
        Domoticz.Debug(strName+"Response status = "+str(response.status))
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
