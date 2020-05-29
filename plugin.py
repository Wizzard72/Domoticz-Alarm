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


class BasePlugin:
    ALARM_MAIN_UNIT = 1
    ALARM_ARMING_MODE_UNIT = 5
    ALARM_ARMING_STATUS_UNIT = 10
    ALARM_PIR_Zone_UNIT = 20
    
    
    
    
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
        self.pollZoneDevices()
        
    def pollZoneDevices(self):
        #/json.htm?type=devices&rid=IDX
        APIjson = self.DomoticzAPI("type=devices&rid=20")
        try:
            nodes = APIjson["result"]
        except:
            nodes = []
        
    def DomoticzAPI(APICall):
        resultJson = None
        url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], Parameters["Port"], parse.quote(APICall, safe="&="))
        Domoticz.Debug("Calling domoticz API: {}".format(url))
        try:
            req = request.Request(url)
            if Parameters["Username"] != "":
                Domoticz.Debug("Add authentification for user {}".format(Parameters["Username"]))
                credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
                encoded_credentials = base64.b64encode(credentials.encode('ascii'))
                req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

            response = request.urlopen(req)
            if response.status == 200:
                resultJson = json.loads(response.read().decode('utf-8'))
                if resultJson["status"] != "OK":
                    Domoticz.Error("Domoticz API returned an error: status = {}".format(resultJson["status"]))
                    resultJson = None
            else:
                Domoticz.Error("Domoticz API: http error = {}".format(response.status))
        except:
            Domoticz.Error("Error calling '{}'".format(url))
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
