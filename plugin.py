# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="Alarm" name="Alarm" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Alarm plugin</h2><br/>
        This plugin creates a Alarm System in Domoticz. It depends on the devices already available in Domoticz.
        
        The first zone triggers the Security Panel.
        
        
        The parameter "Zone Armed Home" and "Zone Armed Away" are used to create one or more zones. The deviceID (idx) that belongs to a zone are separated with a "," and a zone is separated with a ";".
        Both parameters must have the same amount of zones, but a zone van have different amount of devices in it. When a zone has no devices put in a "0" or the text "none".
        Zone(s) are groups in Domoticz. Best is to Protect the groups.

    </description>
    <params>
        <param field="Address" label="Domoticz IP Address" width="200px" required="true" default="localhost"/>
        <param field="Port" label="Port" width="40px" required="true" default="8080"/>
        <param field="Username" label="Username" width="200px" required="true" default=""/>
        <param field="Password" label="Password" width="200px" required="true" default=""/>
        <param field="Mode1" label="Active devices to trigger Siren" width="250px">
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
    SensorActiveTime = 30 #seconds
    
    
    
    
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
        self.createDevices()


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
                if Level == 0:
                    self.deactivateSiren()
                elif Level == 40:
                    self.activateSiren()
        
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
                    Domoticz.Log(strName+"Set Security Panel to Normal")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(0)
                elif Level == 10:
                    Domoticz.Log(strName+"Set Security Panel to Armed Home")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(1)
                elif Level == 20:
                    Domoticz.Log(strName+"Set Security Panel to Armed Away")
                    UpdateDevice(zoneUnitNr, Level, str(Level))
                    self.alarmModeChange(zone_nr, Level)
                    if self.ALARM_ARMING_MODE_UNIT == Unit:
                        self.setSecurityState(2)
        
                
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
        self.mainAlarm()

        
        countAlarm = 0
        for zone in range(self.TotalZones):
            zoneNr = self.ALARM_ARMING_STATUS_UNIT+zone
            #timeDiff = 0
            if Devices[zoneNr].nValue == 40:
                try:
                    timeDiff = datetime.now() - datetime.strptime(Devices[zoneNr].LastUpdate,'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(Devices[zoneNr].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                endSirenTimeSeconds = Devices[self.ALARM_ENTRY_DELAY].nValue + int(Parameters["Mode4"])
                if timeDiffSeconds >= Devices[self.ALARM_ENTRY_DELAY].nValue and timeDiffSeconds <= endSirenTimeSeconds: # EntryDelay
                    self.activateSiren()
                    countAlarm = countAlarm + 1
                    Domoticz.Log(strName+"Turn ON Siren")
                else:
                    self.deactivateSiren()
                    if countAlarm >= 1:
                        countAlarm = countAlarm - 1
                    else:
                        countAlarm = 0
                    Domoticz.Log(strName+"Turn OFF Siren")
            elif Devices[zoneNr].nValue == 0:
                if Devices[self.ALARM_MAIN_UNIT].nValue == 1 and countAlarm == 0:
                    self.deactivateSiren()

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
            if switchStatusIdx == "On":
                if self.Matrix[row][4] not in "On,Normal":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "On", "New")
            elif switchStatusIdx == "Off":
                if self.Matrix[row][4] not in "Off":
                    self.changeRowinMatrix(TotalRows, self.Matrix[row][3], "Off", "Normal")
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
            #UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 0, "0")
        elif SecurityPanelState == 1 or SecurityPanelState == "Arm Home" or SecurityPanelState == "Armed Home":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=1&seccode="+self.secpassword)
            #UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 10, "10")
        elif SecurityPanelState == 2 or SecurityPanelState == "Arm Way" or SecurityPanelState == "Armed Away":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=2&seccode="+self.secpassword)
            #UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 20, "20")
        
    
    def alarmEnable(self):
        strName = "alarmEnable - "
        APIjson = DomoticzAPI("type=devices&filter=light&used=true&order=Name")
        #type=command&param=getlightswitches
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        for node in nodes:
            if node["Name"] == str(Parameters["Mode4"]):
                if node["Status"] == "On":
                    self.anybodyHome = "On"
                    #self.setSecurityState(0)
                elif node["Status"] == "Off":
                    self.anybodyHome = "Off"
                    #self.setSecurityState(2)
                    
    def trippedSensor(self, TotalZones, TotalRows, AlarmMode):
        strName = "trippedSensor - "
        # Check Sensor with state New
        # Runs only when Armed Home or Armed Away
        if AlarmMode == "Armed Home":
            trippedSensor = 0
            trippedZone = ""
            for row in range(TotalRows):
                zoneNrUnit = 0
                if self.Matrix[row][5] == "New" and self.Matrix[row][2] == "Armed Away":
                    Domoticz.Log(strName+"Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                    if Devices[zoneNrUnit].nValue < 20: # Tripped value
                        UpdateDevice(zoneNrUnit, 20, "20") # Tripped
                    sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                    self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                    trippedSensor = trippedSensor + 1
                    if trippedZone == "":
                        trippedZone = str(self.Matrix[row][1])
                    else:
                        trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])
            #trippedZoneCheck = trippedZone.count('0')
            #Domoticz.Log(strName+"Total tripped sensors for all zones = "+str(trippedZoneCheck))
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log(strName+"Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
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
                if self.Matrix[row][5] == "New":
                    Domoticz.Log(strName+"Found Tripped Sensor (idx = "+str(self.Matrix[row][3])+") in zone "+str(self.Matrix[row][1]))
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+self.Matrix[row][1]
                    if Devices[zoneNrUnit].nValue < 20: # Tripped value
                        UpdateDevice(zoneNrUnit, 20, "20") # Tripped
                    sensorTime = self.getSwitchIDXLastUpdate(self.Matrix[row][3])
                    self.setTrippedSensorTimer(self.MatrixRowTotal, self.Matrix[row][3], sensorTime)
                    trippedSensor = trippedSensor + 1
                    if trippedZone == "":
                        trippedZone = str(self.Matrix[row][1])
                    else:
                        trippedZone = str(trippedZone)+","+str(self.Matrix[row][1])
            #trippedZoneCheck = trippedZone.count('0')
            #Domoticz.Log(strName+"Total tripped sensors for all zones = "+str(trippedZoneCheck))
            for zone in range(TotalZones):
                trippedZoneCheck = trippedZone.count(str(zone))
                if trippedZoneCheck != 0:
                    Domoticz.Log(strName+"Total tripped sensors for zone "+str(zone)+" = "+str(trippedZoneCheck))
                if trippedZoneCheck >= self.ActivePIRSirenAway:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 40, "40") # Alert
                elif trippedZoneCheck == 0:
                    zoneNrUnit = self.ALARM_ARMING_STATUS_UNIT+zone
                    UpdateDevice(zoneNrUnit, 0, "0") # Normal
        
    def setTrippedSensorTimer(self, TotalRows, DeviceIdx, TimeChanged):
        strName = "setTrippedSensorTimer - "
        for row in range(TotalRows):
            if self.Matrix[row][3] == DeviceIdx and self.Matrix[row][4] == "Tripped" and self.Matrix[row][5] == "New":
                self.Matrix[row][5] = "Locked"
                self.Matrix[row][6] = TimeChanged
                Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed+" Time Changed = "+str(TimeChanged))
    
    
    def trippedSensorTimer(self, TotalRows):
        strName = "trippedSensorTimer"
        for row in range(TotalRows):
            if self.Matrix[row][4] == "Tripped" and self.Matrix[row][5] == "Locked":
                try:
                    timeDiff = datetime.now() - datetime.strptime(self.Matrix[row][6],'%Y-%m-%d %H:%M:%S')
                except TypeError:
                    timeDiff = datetime.now() - datetime(*(time.strptime(self.Matrix[row][3],'%Y-%m-%d %H:%M:%S')[0:6]))
                timeDiffSeconds = timeDiff.seconds
                if timeDiffSeconds >= self.SensorActiveTime:
                    self.Matrix[row][5] = "Normal"
                    self.Matrix[row][6] = 0
    
    def collectSensorData(self):
        strName = "collectSensorData - "
        jsonQuery = "type=scenes"
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        for x in nodes:
            Domoticz.Log(strName+""+x["Name"][:10])
            if x["Name"][:10] == "Alarm Zone":
                Domoticz.Log("Status = "+x["Status"])
                if x["Status"] == "On":
                    Domoticz.Log(strName+"All sensors are activated.")
                    if self.SecurityPanel == "Disarmed":
                        Domoticz.Log("But alarm is Disabled")
                    elif self.SecurityPanel == "Armed Home":
                        Domoticz.Log("Check if Armed Home sensors are triggered orthe Armed Away.")
                        if x["Name"][10:] != "Armed Home":
                            Domoticz.Log("The sensors are triggerd. SOUND THE SIREN")
                            self.sirenOn = True
                            self.activateSiren()
                    elif self.SecurityPanel == "Armed Away":
                        Domoticz.Log("But alarm is Armed Awat: SOUND THE SIREN")
                elif x["Status"] == "Off":
                    Domoticz.Log(strName+"All sensors are deactivated.")
                elif x["Status"] == "Mixed":
                    Domoticz.Log(strName+"Some sensors are activated.")
                    if self.SecurityPanel == "Disarmed":
                        Domoticz.Log("But alarm is Disabled")
                    elif self.SecurityPanel == "Armed Home":
                        Domoticz.Log("Check if Armed Home sensors are triggered orthe Armed Away.")
                        if x["Name"][10:] != "Armed Home":
                            Domoticz.Log("The sensors are triggerd. SOUND THE SIREN")
                            self.sirenOn = True
                            self.activateSiren()
        
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
    
    def changeRowinMatrix(self, TotalRows, DeviceIdx, DeviceState, Changed):
        strName = "changeRowinMatrix - "
        for row in range(TotalRows):
            if self.Matrix[row][3] == DeviceIdx:
                self.Matrix[row][4] = DeviceState
                self.Matrix[row][5] = Changed
                #self.Matrix[row][6] = TimeChanged
                Domoticz.Debug(strName+"Changed row "+str(row)+" to: DeviceState = "+DeviceState+" Changed = "+Changed)
    
    
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
            #if Devices[ZoneID].nValue == 0: # or Disarmed
            #    Domoticz.Log(strName+"Zone "+str(zone)+" is Disarmed")
            #el
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
        if newStatus == 0: # Normal
            # Reset Siren and Alarm Status
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            UpdateDevice(zoneNrUnit, 0, "0") # Normal
        elif newStatus == 10: # Armed Home
            # Use 
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            # check open sections
            self.checkOpenSections(zoneNr, 10)
            if self.openSections == True:
                Domoticz.Log(strName+"There are open sections")
            elif self.openSections == False:
                UpdateDevice(zoneNrUnit, 0, "0") # Normal
        elif newStatus == 20: # Armed Way
            # Use EntryDelay
            UpdateDevice(zoneNrUnit, 10, "10") # Arming
            # check open sections
            self.checkOpenSections(zoneNr, 20)
            if self.openSections == True:
                Domoticz.Log(strName+"There are open sections")
            elif self.openSections == False:
                UpdateDevice(zoneNrUnit, 0, "0") # Normal
        
    def checkOpenSections(self, zoneNr, zoneMode):
        strName = "checkOpenSections - "
        if zoneMode == 10: # Armed Home
            # We need to check Alarm Zone x - Armed Home for open sections
            # /json.htm?type=scenes if Status is Mixed we have open sections
            APIjson = DomoticzAPI("type=scenes")
            try:
                nodes = APIjson["result"]
            except:
                nodes = []
            Domoticz.Debug(strName+"APIjson = "+str(nodes))
            zoneName = "Alarm Zone "+str(zoneNr)+" - Armed Home"
            for node in nodes:
                if node["Name"] == zoneName:
                    if node["Status"] == "On":
                        OpenSectionDevice = self.deviceOpenSections(node["idx"], zoneName)
                        Domoticz.Log(strName+"Found open sections: "+OpenSectionDevice+". Please check open sections")
                        self.openSections = True
                    elif node["Status"] == "Mixed":
                        OpenSectionDevice = self.deviceOpenSections(node["idx"], zoneName)
                        Domoticz.Log(strName+"Found open sections: "+OpenSectionDevice+". Please check open sections")
                        self.openSections = True
                    elif node["Status"] == "Off":
                        Domoticz.Log(strName+"No open sections found. Safe to set the Alarm.")
                        self.openSections = False
        elif zoneMode == 20: # Armed Away
            Domoticz.Log(strName+"Armed Away")
    
    def deviceOpenSections(self, zoneIdx, zoneName):
        strName = "deviceOpenSections - "
        openSectionsDeviceName = "| "
        # /json.htm?type=command&param=getscenedevices&idx=number&isscene=true
        jsonQuery = "type=command&param=getscenedevices&idx="+zoneIdx+"&isscene=true"
        Domoticz.Debug(strName+"jsonQuery = "+jsonQuery)
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        # Find DevID en met DevID kan met: /json.htm?type=devices&rid=DevID de Status opgevraagd worden van device!
        for node in nodes:
            if self.getSwitchIDXStatus(node["DevID"]) == "On":
                openSectionsDeviceName = openSectionsDeviceName + node["Name"] + " | "
        return openSectionsDeviceName
    
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
    
    def createDevices(self):
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
                        Domoticz.Log(strName+"Found device = "+"Arming Mode (Zone "+str(zone_nr)+")")
                        found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Arming_Mode()
                    Domoticz.Device(Name="Arming Mode (Zone "+str(zone_nr)+")", Unit=new_unit, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
       
        
        Options = {"LevelActions": "||||",
                       "LevelNames": "Normal|Arming|Tripped|Exit Delay|Alert|Error",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
        Description = "The Arming Status options."
        found_device = False
        for zone_nr in range(self.TotalZones):
            for item in Devices:
                if zone_nr < 10:
                    removeCharacters = -22
                else:
                    removeCharacters = -23
                if Devices[item].Name[removeCharacters:] == "Arming Status (Zone "+str(zone_nr)+")":
                    Domoticz.Log(strName+"Found device = "+"Arming Status (Zone "+str(zone_nr)+")")
                    found_device = True
            if found_device == False:
                    new_unit = find_available_unit_Arming_Status()
                    Domoticz.Device(Name="Arming Status (Zone "+str(zone_nr)+")", Unit=new_unit, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=8).Create()
        
        #create zone groups and populate them
        # Armed Home Group
        zoneArmedHome = Parameters["Mode2"].split(";")
        zoneCountArmedHome = 0
        node_idx = ""
        #/json.htm?type=scenes
        jsonQuery = "type=scenes"
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        for zone in zoneArmedHome:
            #/json.htm?type=addscene&name=scenename&scenetype=1
            zoneGroupName = "Alarm Zone "+str(zoneCountArmedHome)+" - Armed Home"
            found_node = False
            for node in nodes:
                if node["Name"] == zoneGroupName:
                    # zone group exists and find its idx
                    found_node = True
                    node_idx = node["idx"]
            if found_node == False:
                # if zone group is not found create it and find its idx
                jsonQueryAddGroup = "type=addscene&name="+zoneGroupName+"&scenetype=1"
                DomoticzAPI(jsonQueryAddGroup)
                jsonQuery = "type=scenes"
                APIjson = DomoticzAPI(jsonQuery)
                try:
                    nodes = APIjson["result"]
                except:
                    nodes = []
                for node in nodes:
                    if node["Name"] == zoneGroupName:
                        node_idx=node["idx"]
            # Populate the zone groups with devices (idx)
            # /json.htm?type=command&param=getscenedevices&idx=number&isscene=true
            jsonQueryListDevices = "type=command&param=getscenedevices&idx="+str(node_idx)+"&isscene=true"
            APIjson = DomoticzAPI(jsonQueryListDevices)
            nodes_result = False
            try:
                nodes = APIjson["result"]
                nodes_result = True
            except:
                nodes = []
            if nodes_result == False:
                # No devices addes to the group
                #/json.htm?type=command&param=addscenedevice&idx=5&isscene=true&devidx=29&command=0&level=0&hue=0
                deviceAddGroup = zone.split(",")
                count = 1
                for addDevice in deviceAddGroup:
                    if node_idx != 0 or str(node_idx) != "none":
                        jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+str(node_idx)+"&isscene=true&devidx="+str(addDevice)+"&command=0&level=100&hue=0"
                        DomoticzAPI(jsonQueryAddDevicetoGroup)
            else:
                # Devices already belong to group, have to check if all are in them
                # Delete all devices from group
                #/json.htm?type=command&param=getscenedevices&idx=number&isscene=true
                jsonQueryListDevices = "type=command&param=getscenedevices&idx="+str(node_idx)+"&isscene=true"
                APIjson = DomoticzAPI(jsonQueryListDevices)
                nodes_result = False
                try:
                    test = APIjson["result"]
                except:
                    test = []
                for item in test:
                    Domoticz.Debug(strName+"item "+item["ID"])
                    jsonQueryDeleteDevices = "type=command&param=deletescenedevice&idx="+str(item["ID"])
                    Domoticz.Debug(strName+"json delete = "+jsonQueryDeleteDevices)
                    DomoticzAPI(jsonQueryDeleteDevices)
                # No devices addes to the group
                #/json.htm?type=command&param=addscenedevice&idx=5&isscene=true&devidx=29&command=0&level=0&hue=0
                deviceAddGroup = zone.split(",")
                count = 1
                for addDevice in deviceAddGroup:
                    if node_idx != 0 or str(node_idx) != "none":
                        jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+str(node_idx)+"&isscene=true&devidx="+str(addDevice)+"&command=0&level=100&hue=0"
                        DomoticzAPI(jsonQueryAddDevicetoGroup)
            zoneCountArmedHome = zoneCountArmedHome + 1        

        # Armed Away Group
        zoneArmedAway = Parameters["Mode3"].split(";")
        zoneCountArmedAway = 0
        node_idx = ""
        #/json.htm?type=scenes
        jsonQuery = "type=scenes"
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        for zone in zoneArmedAway:
            #/json.htm?type=addscene&name=scenename&scenetype=1
            zoneGroupName = "Alarm Zone "+str(zoneCountArmedAway)+" - Armed Away"
            found_node = False
            for node in nodes:
                if node["Name"] == zoneGroupName:
                    # zone group exists and find its idx
                    found_node = True
                    node_idx = node["idx"]
            if found_node == False:
                # if zone group is not found create it and find its idx
                jsonQueryAddGroup = "type=addscene&name="+zoneGroupName+"&scenetype=1"
                DomoticzAPI(jsonQueryAddGroup)
                jsonQuery = "type=scenes"
                APIjson = DomoticzAPI(jsonQuery)
                try:
                    nodes = APIjson["result"]
                except:
                    nodes = []
                for node in nodes:
                    if node["Name"] == zoneGroupName:
                        node_idx=node["idx"]
            # Populate the zone groups with devices (idx)
            # /json.htm?type=command&param=getscenedevices&idx=number&isscene=true
            jsonQueryListDevices = "type=command&param=getscenedevices&idx="+str(node_idx)+"&isscene=true"
            APIjson = DomoticzAPI(jsonQueryListDevices)
            nodes_result = False
            try:
                nodes = APIjson["result"]
                nodes_result = True
            except:
                nodes = []
            if nodes_result == False:
                # No devices addes to the group
                #/json.htm?type=command&param=addscenedevice&idx=5&isscene=true&devidx=29&command=0&level=0&hue=0
                deviceAddGroup = zone.split(",")
                count = 1
                for addDevice in deviceAddGroup:
                    if node_idx != 0 or str(node_idx) != "none":
                        jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+str(node_idx)+"&isscene=true&devidx="+str(addDevice)+"&command=0&level=100&hue=0"
                        DomoticzAPI(jsonQueryAddDevicetoGroup)
            else:
                # Devices already belong to group, have to check if all are in them
                # Delete all devices from group
                #/json.htm?type=command&param=getscenedevices&idx=number&isscene=true
                jsonQueryListDevices = "type=command&param=getscenedevices&idx="+str(node_idx)+"&isscene=true"
                APIjson = DomoticzAPI(jsonQueryListDevices)
                nodes_result = False
                try:
                    test = APIjson["result"]
                except:
                    test = []
                for item in test:
                    Domoticz.Debug(strName+"item "+item["ID"])
                    jsonQueryDeleteDevices = "type=command&param=deletescenedevice&idx="+str(item["ID"])
                    Domoticz.Debug(strName+"json delete = "+jsonQueryDeleteDevices)
                    DomoticzAPI(jsonQueryDeleteDevices)
                # No devices addes to the group
                #/json.htm?type=command&param=addscenedevice&idx=5&isscene=true&devidx=29&command=0&level=0&hue=0
                deviceAddGroup = zone.split(",")
                count = 1
                for addDevice in deviceAddGroup:
                    if node_idx != 0 or str(node_idx) != "none":
                        jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+str(node_idx)+"&isscene=true&devidx="+str(addDevice)+"&command=0&level=100&hue=0"
                        DomoticzAPI(jsonQueryAddDevicetoGroup)
            zoneCountArmedAway = zoneCountArmedAway + 1    
        
        # Armed Away Group
        #zoneArmedAway = Parameters["Mode3"].split(";")
        #zoneCountArmedAway =0
        #for zone in zoneArmedAway:
            #/json.htm?type=addscene&name=scenename&scenetype=1
       #    zoneGroupName = "Alarm Zone "+str(zone)+" - Armed Away"
        #    jsonQueryAddGroup = "type=addscene&name="+zoneGroupName+"&scenetype=1"
            #DomoticzAPI(jsonQueryAddGroup)
         #   Domoticz.Log(strName+"zoneArmedAway = "+str(zoneArmedAway))
          #  deviceAddGroup = zone.split(",")
           # count = 1
            #for addDevice in deviceAddGroup:
                #/json.htm?type=command&param=addscenedevice&idx=number&isscene=true&devidx=deviceindex&command=1&level=number&hue=number
             #   deviceIdx = ""
              #  jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+number+"&isscene=true&devidx="+deviceIdx+"&command=1&level=0&hue="+count
               # count = count + 1
            #zoneCountArmedAway = zoneCountArmedAway + 1
        
        #if zoneCountArmedHome == zoneCountArmedAway:
         #   self.amountofZones = zoneCount
          #  Domoticz.Log(strName+"Found "+str(self.amountofZones)+" zone(s).")
        #elif zoneCountArmedHome > zoneCountArmedAway:
         #   Domoticz.Error(strName+"Zone Armed Home has more zones than Zone Armed Away")
          #  Domoticz.Error(strName+"Add an empty zone in Zone Armed Away Parameter (;none)")
        #elif zoneCountArmedHome < zoneCountArmedAway:
         #   Domoticz.Error(strName+"Zone Armed Home has less zones than Zone Armed Away")
          #  Domoticz.Error(strName+"Add an empty zone in Zone Armed Home Parameter (;none)")
        
        
        
        
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
