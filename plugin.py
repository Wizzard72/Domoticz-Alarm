# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="Alarm" name="Alarm" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Alarm plugin</h2><br/>
        This plugin creates a Alarm System in Domoticz. It depends on the devices already available in Domoticz.
        
        
        The parameter "Zone Armed Home" and "Zone Armed Away" are used to create one or more zones. The deviceID (idx) that belongs to a zone are separated with a "," and a zone is separated with a ";".
        Both parameters must have the same amount of zones, but a zone van have different amount of devices in it. When a zone has no devices put in a "0" or the text "none".
        Zone(s) are groups in Domoticz. Best is to Protect the groups.

    </description>
    <params>
        <param field="Address" label="Domoticz IP Address" width="200px" required="true" default="localhost"/>
        <param field="Port" label="Port" width="40px" required="true" default="8080"/>
        <param field="Username" label="Username" width="200px" required="false" default=""/>
        <param field="Password" label="Password" width="200px" required="false" default=""/>
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
        <param field="Mode2" label="Zone Armed Home" width="600px" required="true" default="idx,idc,idc;idx,idx,idx"/>
        <param field="Mode3" label="Zone Armed Away" width="600px" required="true" default="idx,idc,idc;idx,idx,idx"/>
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
        w, h = 5, int(Parameters["Mode1"]);
        self.Matrix = [[0 for x in range(w)] for y in range(h)] 
        # table:
        # ZONE_Name | State | Changed | Time | Refresh
        # Matrix[0][0] = 1
        
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
        Domoticz.Log(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        
        if self.ALARM_ENTRY_DELAY == Unit:
            if Level == 0:
                self.entryDelay = 0 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 10:
                self.entryDelay = 10 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 20:
                self.entryDelay = 20 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 30:
                self.entryDelay = 30 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 40:
                self.entryDelay = 40 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 50:
                self.entryDelay = 50 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 60:
                self.entryDelay = 60 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 70:
                self.entryDelay = 70 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 80:
                self.entryDelay = 80 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
            elif Level == 90:
                self.entryDelay = 90 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, Level, str(Level))
                
        if self.ALARM_EXIT_DELAY == Unit:
            if Level == 0:
                self.exitDelay = 0 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 10:
                self.exitDelay = 10 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 20:
                self.exitDelay = 20 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 30:
                self.exitDelay = 30 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 40:
                self.exitDelay = 40 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 50:
                self.exitDelay = 50 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 60:
                self.exitDelay = 60 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 70:
                self.exitDelay = 70 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 80:
                self.exitDelay = 80 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
            elif Level == 90:
                self.exitDelay = 90 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, Level, str(Level))
        
        if self.ALARM_ARMING_MODE_UNIT == Unit:
            if Level == 0:
                Domoticz.Log(strName+"Set Security Panel to Normal")
                UpdateDevice(self.ALARM_ARMING_MODE_UNIT, Level, str(Level))
                self.setSecurityState(0)
            elif Level == 10:
                Domoticz.Log(strName+"Set Security Panel to Armed Home")
                UpdateDevice(self.ALARM_ARMING_MODE_UNIT, Level, str(Level))
                self.setSecurityState(1)
            elif Level == 20:
                Domoticz.Log(strName+"Set Security Panel to Armed Away")
                UpdateDevice(self.ALARM_ARMING_MODE_UNIT, Level, str(Level))
                self.setSecurityState(2)
        
        
        for zone_nr in range(int(Parameters["Mode1"])):
            switchAlarmModeUnit = 10 + zone_nr
            if switchAlarmModeUnit == Unit:
                if Level == 0:
                    self.alarmModeChange(self, zone_nr, Level)
                elif Level == 10:
                    self.alarmModeChange(self, zone_nr, Level)
                elif Level == 20:
                    self.alarmModeChange(self, zone_nr, Level)
                
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
        self.pollZoneDevices()
        self.getSecurityState()
        self.alarmEnable()
        
    def pollZoneDevices(self):
        strName = "pollZoneDevices - "
        APIjson = DomoticzAPI("type=scenes")
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        #i = 0
        #for node in nodes:
        #    self.Matrix[i][0] = node["Name"]
        #    Domoticz.Log(strName+"node = "+str(node))
        #    if node["Status"] == "On":
        #        Domoticz.Log(strName+node["Name"]+" is Activated (On)")
        #        zoneStatus = "On"
        #    elif node["Status"] == "Off":
        #        Domoticz.Log(strName+node["Name"]+" is Deactivated (Off)")
        #        zoneStatus = "Off"
        #    self.Matrix[i][1] = node["Name"]
        #    self.Matrix[i][2] = ""
        #    self.Matrix[i][3] = ""
        #    self.Matrix[i][4] = ""
        #    i = i + 1
        
        #for count in range(int(Parameters["Mode1"])):
        #    Domoticz.Log(strName+"Alarm = "+self.Matrix[count][0]+" | "+str(self.Matrix[count][1])+" | "+str(self.Matrix[count][2])+" | "+self.Matrix[count][3]+" | "+self.Matrix[count][4])
        
        #for i in nodes:
        #    Domoticz.Log("APIjson = "+nodes[i])
            
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
            Domoticz.Log("Security State = Disarmed")
            self.SecurityPanel = "Disarmed"
        elif nodes["secstatus"] == 1:
            Domoticz.Log("Security State = Arm Home")
            self.SecurityPanel = "Arm Home"
        elif nodes["secstatus"] == 2:
            Domoticz.Log("Security State = Arm Away")
            self.SecurityPanel = "Arm Away"
        elif nodes["secstatus"] == 3:
            Domoticz.Log("Security State = Unknown")
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
            UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 0, "0")
        elif SecurityPanelState == 1 or SecurityPanelState == "Arm Home" or SecurityPanelState == "Armed Home":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=1&seccode="+self.secpassword)
            UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 10, "10")
        elif SecurityPanelState == 2 or SecurityPanelState == "Arm Way" or SecurityPanelState == "Armed Away":
            DomoticzAPI("type=command&param=setsecstatus&secstatus=2&seccode="+self.secpassword)
            UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 20, "20")
        
    
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
                    
    def trippedSensor(self):
        strName = "trippedSensor - "
        
        
    def createTheMatrix(self, width, hight):
        strName = "createTheMatrix - "
        
    def mainAlarm(self):
        strName = "mainAlarm - "
        for count in range(int(Parameters["Mode 1"])):
            Domoticz.Log("")
            
    def alarmModeChange(self, zoneNr, newStatus):
        strName = "alarmModeChange"
        zoneNrUnit = self.ALARM_ARMING_MODE_UNIT + zoneNr
        if newStatus == 0: # Normal
            # Reset Siren and Alarm Status
            UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
            UpdateDevice(zoneNrUnit, 0, "Off")
        elif newStatus == 10: # Armed Home
            # Use 
            UpdateDevice(zoneNrUnit, 10, "Arming")
            # check open sections
            self.checkOpenSections(zoneNr, 10)
            UpdateDevice(zoneNrUnit, 0, "Normal")
        elif newStatus == 20: # Armed Way
            # Use EntryDelay
            UpdateDevice(zoneNrUnit, 10, "Arming")
            # check open sections
            self.checkOpenSections(zoneNr, 20)
            UpdateDevice(zoneNrUnit, 0, "Normal")
        
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
            zoneName = "Alarm Zone "+zoneNr+" - Armed Home"
            for node in nodes:
                if node["Name"] == zoneName:
                    if node["Status"] == "On":
                        OpenSectionDevice = deviceOpenSections(node["idx"], zoneName)
                        Domoticz.Log(strName+"Found open sections: "+OpenSectionDevice+". Please check open sections")
                        self.openSections = True
                    elif node["Status"] == "Mixed":
                        OpenSectionDevice = deviceOpenSections(node["idx"], zoneName)
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
        APIjson = DomoticzAPI(jsonQuery)
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        Domoticz.Debug(strName+"APIjson = "+str(nodes))
        for node in nodes:
            if node["Status"] == "On":
                openSectionsDeviceName = openSectionsDeviceName + node["Name"] + " | "
        return openSectionsDeviceName
    
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
        for zone_nr in range(int(Parameters["Mode1"])):
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
                       "LevelNames": "Normal|Arming|Tripped|Timed Out|Alert|Error",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
        Description = "The Arming Status options."
        found_device = False
        for zone_nr in range(int(Parameters["Mode1"])):
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
                    jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+str(node_idx)+"&isscene=true&devidx="+str(addDevice)+"&command=0&level=0&hue=0"
                    DomoticzAPI(jsonQueryAddDevicetoGroup)
            else:
                # Devices already belong to group, have to check if all are in them
                # Delete all devices from group
                #/json.htm?type=command&param=getscenedevices&idx=number&isscene=true
                jsonQueryListDevices = "type=command&param=getscenedevices&idx="+str(node_idx)+"&isscene=true"
                APIjson = DomoticzAPI(jsonQueryListDevices)
                nodes_result = False
                try:
                    nodes = APIjson["result"]
                except:
                    nodes = []
                for idem in nodes:
                    jsonQueryDeleteDevices = "type=command&param=deletescenedevice&idx="+idem["idx"]
                    DomoticzAPI(jsonQueryListDevices)
                    
            #Domoticz.Log(strName+"zoneArmedHome = "+zoneArmedHome)
            #deviceAddGroup = zone.split(",")
            #count = 1
            #for addDevice in deviceAddGroup:
                #/json.htm?type=command&param=addscenedevice&idx=number&isscene=true&devidx=deviceindex&command=1&level=number&hue=number
                #deviceIdx = ""
                #jsonQueryAddDevicetoGroup = "type=command&param=addscenedevice&idx="+number+"&isscene=true&devidx="+deviceIdx+"&command=1&level=0&hue="+count
                #count = count + 1
            #zoneCountArmedHome = zoneCountArmedHome + 1
        
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
    Domoticz.Log(strName+"Calling domoticz API: {}".format(url))
    try:
        req = request.Request(url)
        if Parameters["Username"] != "":
            Domoticz.Log(strName+"Add authentification for user {}".format(Parameters["Username"]))
            credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
            encoded_credentials = base64.b64encode(credentials.encode('ascii'))
            req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

        response = request.urlopen(req)
        Domoticz.Log(strName+"Response status = "+str(response.status))
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
