# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="Alarm" name="Alarm" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Alarm">
    <description>
        <h2>Alarm plugin</h2><br/>
        
        

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
        <param field="Mode2" label="Zone devices" width="600px" required="true" default="Zone1=idx,idc,idc;Zone2=idx,idx,idx"/>
        <param field="Mode4" label="Anybody Home Device" width="200px" required="true" default="Anybody Home Device"/>
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
    ALARM_ARMING_MODE_UNIT = 5
    ALARM_ARMING_STATUS_UNIT = 10
    ALARM_PIR_Zone_UNIT = 20
    SecurityPanel = ""
    anybodyHome = ""
    entryDelay = 0
    exitDelay = 0
    
    
    
    
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
        if (self.ALARM_MAIN_UNIT not in Devices):
            Domoticz.Log("TESTTTT")
            Domoticz.Device(Name="ALARM",  Unit=self.ALARM_MAIN_UNIT, Used=1, TypeName="Switch", Image=13).Create()
            UpdateDevice(self.ALARM_MAIN_UNIT, 0, "Off")
            
        if (self.ALARM_ENTRY_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0|10|20|30|40|50|60|70|80|90",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Entry Delay (s)", Unit=self.ALARM_ENTRY_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_ENTRY_DELAY, 0, "0")
            
        if (self.ALARM_EXIT_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0|10|20|30|40|50|60|70|80|90",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Exit Delay (s)", Unit=self.ALARM_EXIT_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_EXIT_DELAY, 0, "0")
    
        if (self.ALARM_ARMING_MODE_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Disarmed|Armed Home|Armed Away",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Arming Mode", Unit=self.ALARM_ARMING_MODE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=9).Create()
            UpdateDevice(self.ALARM_ARMING_MODE_UNIT, 0, "0")
    
        if (self.ALARM_ARMING_STATUS_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Normal|Arming|Tripped|Timed Out|Alert|Error",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Arming Status", Unit=self.ALARM_ARMING_STATUS_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=8).Create()
            UpdateDevice(self.ALARM_ARMING_STATUS_UNIT, 0, "0")

        # Create table
        w, h = 5, int(Parameters["Mode1"]);
        self.Matrix = [[0 for x in range(w)] for y in range(h)] 
        # table:
        # ZONE_Name | State | Changed | Time | Refresh
        # Matrix[0][0] = 1
        
        Domoticz.Heartbeat(int(Parameters["Mode5"]))
        secpassword = self.getsecpasspword()


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
            if Level == 0: # Override Off
                self.entryDelay = 0 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 10:
                self.entryDelay = 10 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 20:
                self.entryDelay = 20 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 30:
                self.entryDelay = 30 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 40:
                self.entryDelay = 40 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 50:
                self.entryDelay = 50 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 60:
                self.entryDelay = 60 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 70:
                self.entryDelay = 70 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 80:
                self.entryDelay = 80 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
            elif Level == 90:
                self.entryDelay = 90 #seconds
                Domoticz.Log(strName+"Entry Delay = "+str(self.entryDelay))
                UpdateDevice(self.ALARM_ENTRY_DELAY, 1, str(Level))
                
        if self.ALARM_EXIT_DELAY == Unit:
            if Level == 0:
                self.exitDelay = 0 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 10:
                self.entryDelay = 10 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 20:
                self.entryDelay = 20 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 30:
                self.entryDelay = 30 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 40:
                self.entryDelay = 40 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 50:
                self.entryDelay = 50 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 60:
                self.entryDelay = 60 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 70:
                self.entryDelay = 70 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 80:
                self.entryDelay = 80 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
            elif Level == 90:
                self.entryDelay = 90 #seconds
                Domoticz.Log(strName+"Exit Delay = "+str(self.exitDelay))
                UpdateDevice(self.ALARM_EXIT_DELAY, 1, str(Level))
        
                
                
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
        i = 0
        for node in nodes:
            self.Matrix[i][0] = node["Name"]
            Domoticz.Log(strName+"node = "+str(node))
            if node["Status"] == "On":
                Domoticz.Log(strName+node["Name"]+" is Activated (On)")
                zoneStatus = "On"
            elif node["Status"] == "Off":
                Domoticz.Log(strName+node["Name"]+" is Deactivated (Off)")
                zoneStatus = "Off"
            self.Matrix[i][1] = node["Name"]
            self.Matrix[i][2] = ""
            self.Matrix[i][3] = ""
            self.Matrix[i][4] = ""
            i = i + 1
        
        for count in range(int(Parameters["Mode1"])):
            Domoticz.Log(strName+"Alarm = "+self.Matrix[count][0]+" | "+str(self.Matrix[count][1])+" | "+str(self.Matrix[count][2])+" | "+self.Matrix[count][3]+" | "+self.Matrix[count][4])
        
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
                    self.setSecurityState(0)
                elif node["Status"] == "Off":
                    self.anybodyHome = "Off"
                    self.setSecurityState(2)
        

        
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
