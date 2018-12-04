"""
RFXrcv-E python plugin for Domoticz
Author: plasticfist,
        adapted from the Smart Virtual Thermostat plugin by Logread, and
        https://github.com/domoticz/domoticz/blob/development/plugins/examples/HTTP.py
        https://github.com/domoticz/domoticz/blob/development/plugins/examples/DenonMarantz.py
Notes:  This works with an OLD RFXrcv-E device (see picture)
        I do not know if it will work with newer RFXrcv-E devices (smaller RFXLAN?)

TODO:
- implement initialization of device
  Commands
# reference: My original C implementation
#
->  F0 2C   Set variable length mode
<-  2C      ACK

->  F0 20   Version request
<-  4D 50   VersionL Master: 50

->  F0 2A   Enable all RF
<-  2A      ACK?

# reference: https://forums.homeseer.com/forum/3rd-party-developer-area/general-developer-discussion/mcs/xap/xap-library/26151-xapmcsrf-w800-rfxcom-xap-node
#
->  F0 29   Init command- 32 bit mode (W800 compatible)
<-  29      ACK

# reference: http://forum.micasaverde.com/index.php?topic=4991.150
->  F0 30   reset   (resets the RFXCOM and enable only X10 and AC)
->  F0 30   reset

# reference: "RF receiver details.pdf" (RFXCOM.COM/downloads way back machine 2008)

9. Hex Initialization commands.

9.1. 310MHz X10 only receiver
    F020 = return software version
    F021 = RFXCOM HS plug-in mode
    F025 = toggle baud rate
    F029 = receive X10, security and Oregon temp, output is 32 bits
    F02A = enable all possible receiving modes
    F02C = variable length mode receiving.
    F02F = disable receiving of X10 and security RF in modes 21, 29 and 2C
    F040 = disable this X10 receiver. Other receiver is in Visonic mode.
    F041 = receive variable length mode receiving. Other receiver is in Visonic mode.

9.2. 433.92MHz receiver
    F020 = return software version
    F021 = RFXCOM HS plug-in mode
    F024 = receive ARC-Tech codes
    F025 = toggle baud rate
    F028 = disable receiving of HomeEasy RF
    F029 = receive X10, security, ARC-Tech output is 32 bits
    F02A = enable all possible receiving modes
    F02C = variable length mode receiving.
    F02D = disable receiving of ARC-Tech RF in modes 21, 29 to 2C
    F02E = disable receiving of Ikea-Koppla RF (special receiver)
    F02F = disable receiving of X10 and security RF in modes 21, 29 to 2C
    F040 = disable this X10 receiver. Other receiver is in Visonic mode.
    F041 = variable length mode receiving. The other receiver is in Visonic mode.
    F042 = used in Visonic receiver to clear auxiliary contacts
    F043 = disable receiving of Oregon RF
    F044 = disable receiving of ATI Remote Wonder RF
    F045 = disable Visonic receiving
Copyright 2008, RFXCOM RF Receivers version 19.2 page 4 / 11

10. Variable length mode packet
The first byte of the packet in variable length mode doesn’t belong to the RF data received. The bits 6-0 of the first byte contain the packet length in hex of the RF data received.
Important: The most significant bit 7 of the first byte indicates if the packet is received by the Master receiver (bit7=0) or by the Slave receiver (bit7=1)

11. How received RF data is handled.
    On reception of an initialize command the receiver will respond with a byte equal to the second byte. E.g. if a hex init command “F029” is received, the receiver responds with “29”. On disable RF commands the receiver will respond with the mode set.
    Only valid RF and X10 packets are send to the RS232 port in “F029” 32 bits mode. This mode is also compatible with the W800RF32 receiver.
    In ARC mode only ARC-Tech RF packets are received and transmitted in variable length packets with ARC-Tech native format to the RS232 interface.
    In the modes 21, 29 and 2C the received ARC-Tech RF packets are converted to X10 format.
    In the mode 21 and 29 only the temperature field from the received Oregon packets is translated to RFXSensor format.
    The ATI Remote Wonder commands are send to the RS232 in native format. In mode 29 there are 12 bits added to the packet to have 32 bits.
    Note: a disabled receiver doesn’t respond on a software version request and doesn’t respond with an ACK to the set disable command.
Copyright 2008, RFXCOM RF Receivers version 19.2 page 5 / 11

12. Example of received data packets for an A1-off cmd
(all data is in hex format)
    Version request to receiver => F020
    4D185330 version of Master & optional Slave receiver.
    Master = version 18, Slave = version 30
    Init cmd to receiver => F024 (433.92MHz receiver only)
    24 ACK received
    140004 Housecode=C Group= 1 Unit= 1 Command: OFF received
    Init cmd to receiver => F029
    29 ACK received 609F20DF A1-Off received
    Init cmd to receiver => F02A
    2A ACK received 609F20DF A1-Off received
    Init cmd to receiver => F02C
    2C 20609F20DF
    A0609F20DF
    ACK received
    A1-Off received by a Master receiver
    20H=32 decimal bits received
    A1-Off received by a Slave receiver
    Bit7 on=slave receiver + 20H=32 decimal bits received
    Disable KAKU RF => F02D (433.92MHz receiver only)
    2C ACK received (ACK=current mode F02C)
    Disable X10 RF => F02F (433.92MHz receiver only)
    2C ACK received (ACK=current mode)

Version:    0.0.1: alpha
"""
"""
<plugin key="RFXrcv-E" name="RFXrcv-E" version="0.0.1" author="plasticfist" wikilink="https://www.domoticz.com/wiki/Plugins/RFXrcv-E.html" externallink="https://github.com/plasticfist/RFXrcv-E.git">
    <description>
        <h2>RFXrcv-E - www.rfxcom.com</h2><br/>
        Easily implement RFXrcv-E in Domoticz<br/>
        <h3>Set-up and Configuration</h3><br/>
        See domoticz wiki above.<br/>
    </description>
    <params>
        <param field="Address" label="RFXrcv-E IP Address" width="200px" required="true" default="192.168.0.9"/>
        <param field="Port" label="Port" width="40px" required="true" default="10001"/>
        <param field="Mode2" label="Create All?" width="200px">
            <options>
                <option label="Yes - Create all sensors, even when they can'tbe decoded" value="Yes"  default="true"/>
                <option label="No - Ignore unsupported sensors" value="No" />
            </options>
        </param>
        <param field="Mode1" label="Logging Level" width="200px">
            <options>
                <option label="Normal" value="Normal"  default="true"/>
                <option label="Verbose" value="Verbose"/>
                <option label="Debug - Python Only" value="2"/>
                <option label="Debug - Basic" value="62"/>
                <option label="Debug - Basic+Messages" value="126"/>
                <option label="Debug - Connections Only" value="16"/>
                <option label="Debug - Connections+Queue" value="144"/>
                <option label="Debug - All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import json
import urllib.parse as parse
import urllib.request as request
from datetime import datetime, timedelta
import time
import base64
import itertools
from collections import namedtuple

class BasePlugin:

    def __init__(self):
        self.debug = False
#        self.ActiveSensors = {}
#        self.InTempSensors = []

        tcpConn = None
#        self.disconnectCount= 0
#        Parameters["Version"]= 0.0.1
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        # setup the appropriate logging level
        try:
            debuglevel = int(Parameters["Mode1"])
        except ValueError:
            debuglevel = 0
            self.loglevel = Parameters["Mode1"]
        if debuglevel != 0:
            self.debug = True
            Domoticz.Debugging(debuglevel)
            DumpConfigToLog(DevId='')
            self.loglevel = "Verbose"
        else:
            self.debug = False
            Domoticz.Debugging(0)

        if Parameters["Mode2"]=='Yes':
            Domoticz.Log("RFXrcv-E create all devices seen.")

        self.tcpConn = Domoticz.Connection(Name="RFXrcv-EConn", Transport="TCP/IP", Protocol="None", Address=Parameters["Address"], Port=Parameters["Port"])
        self.tcpConn.Connect()
        self.pollPeriod = 16 #  6 * int(Parameters["Mode1"])
        self.pollCount = self.pollPeriod - 1
        Domoticz.Heartbeat(25)
        return

    def onStop(self):
        Domoticz.Debug("onStop called")
        Domoticz.Debugging(0)

    def onConnect(self, Connection, Status, Description):

        Domoticz.Debug("onConnect called")
        if (Status == 0):
            Domoticz.Debug("Connected successfully.")
        else:
            Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

        # list of commands to initialize device
        commandStep= 0
        Command = namedtuple('Command',['name','cmd'])
        initializeCommands= [Command(name='VersionRequest',cmd=b'\xF0\x20'),
                             Command(name='SetVariableLengthMode',cmd=b'\xF0\x2C'),
                             Command(name='EnableAllRF',cmd=b'\xF0\x2A')
                            ]

        # stagger the device initialization commands, to enable init and ACK to occur
        # A simple fire and forget (consume ACKs) will do
        # Note: and we seem to need a small delay, after connect
        d= 0
        for c in initializeCommands:
            Domoticz.Debug("InitializeDevice command: {}".format(initializeCommands[d].name))
            self.tcpConn.Send(initializeCommands[d].cmd, Delay=(d+1)*5)
            d += 1
        return

    def onMessage(self, Connection, Data):
        Domoticz.Debug('onMessage called - Received: '+Data.hex())

# prefer to use my own copy of the buffer
# TODO: this ought to accumulate, and process.  Rarely some packets come in two pieces..
        procData= bytearray(Data)

# process the incoming Data stream
        if len(procData)>0:

            # expecting ACKs 0x2C 0x2A, and periodic 0x50s (from where I don't know)
            if len(procData)<4:
                Domoticz.Debug('Consuming ACKs and spurious coms {0:02X}'.format(procData[0]))
                procData= procData[1:]

            # Prefer to process full sensor data packets
            elif processPacket(procData):
                procData= procData[10:]

            # if not check for version info packet
            #
            elif procData[0]==0x4D and procData[2]==0x53:
                Domoticz.Log("RFXCOM- RFReceiver Version- Master:{:02x} Slave:{:02x}".format(procData[1],procData[3]))
                procData= procData[4:]

            # I've seen it in reverse order too (odd?)
            elif procData[0]==0x53 and procData[2]==0x4D:
                Domoticz.Log("RFXCOM- RFReceiver Version- Master:{:02x} Slave:{:02x}".format(procData[3],procData[1]))
                procData= procData[4:]

        return

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug("onCommand called for Unit {}: Command '{}', Level: {}".format(Unit, Command, Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("****onDisconnect called")

    def onHeartbeat(self):
        now = datetime.now()
        Domoticz.Debug("onHeartbeat called {}".format(now))

        if (self.tcpConn != None and (self.tcpConn.Connecting() or self.tcpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            Domoticz.Log("****onHeartbeat called, Connection failure, re-connecting")
            if (self.tcpConn == None):
                self.tcpConn = Domoticz.Connection(Name="RFXrcv-EConn", Transport="TCP/IP", Protocol="None", Address=Parameters["Address"], Port=Parameters["Port"])
                self.tcpConn.Connect()

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

def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


#
#
# will redo this later (FIX), for now recognize one sensor only
#
# Oregon Scientific sensors
#
# Sensor    Code
# THGR122NX A2D    # *****I own this sensor (w/sticker 11A15), it is the correct code!
# BTHR918   5A5D
# BTHR968   5D60
# PCR800    2914
# PSR01
# RGR918    2A1D    rain gauge
# RGR968    2D10    rain gauge
# RTGR328NA
# THC268
# THGN123N  1D20
# THGN801   F824
# THGR122NX 1D20    *** own this, and it is sending 1A2D
# THGR228N  1A2D
# THGR268
# THGR810   F824
# THGR810(1)    F8B4
# THGR918   1A3D
# THN132N   EC40
# THR238NF  EC40
# THR268
# THWR288A  EA4C
# THWR288A-JD
# THWR800   C844
# UVN800    D874
# UVR128    EC70
# WGR800(2) 1994
# WGR800(3) 1984
# WGR918    3A0D
# STR918    3A0D
#
# 1. This is the temperature/RH sensor that originally shipped with the WMR100 – it was integrated with the anemometer.
# 2. The original anemometer which included a temperature/RH sensor.
# 3. The newer anemometer with no temperature/RH sensor.
#

# Generic helper functions
#------------------------------------------------------------
#
# Is there an RFXrcv-E packet starting at this point in buffer?
# Note: There might be more than one in the buffer together
# example Oregon Scientific packet:  1a2d40e4701660043e9e
#
# min length = 2
#
def processPacket(procData):

    sensorTypeId= (procData[0]<<8)|procData[1]
    sensorID2Name = {
        0x1A2D:'THGR122NX/THGN123N/THGN122N/THGR228N/THGR238/THGR268',
        0x1D20:'THGR122NX',
        0x5A5D:'BTHR918',
        0x5A6D:'BTHR918N/BTHR968',
        0x5D60:'BTHR968',
        0x2914:'PCR800',
        0x2A19:'PCR800',
        0x2A1D:'RGR126/RGR682/RGR918',
        0x2D10:'RGR968',
        0x1D20:'THGN123N',
        0xF824:'THGN801',
        0xF824:'THGR810',
        0xF8B4:'THGR810(1)',
        0x1A3D:'THGR918/THGRN228NX/THGN500',
        0xEC40:'THN132N/THR238NF',
        0xEC40:'THR238NF',
        0xEA4C:'THC238/THN132N/THWR288A/THR122N/THN122N/AW129/AW131/THWR288A',
        0xC844:'THWR800',
        0xD874:'UVN800',
        0xEC70:'UVR128',
        0x1994:'WGR800(2)',
        0x1984:'WGR800(3)',
        0x3A0D:'WGR918/STR918',
        0x0A4D:'Oregon-THR128/Oregon-THR138/Oregon-THC138',
        0xCA48:'THWR800',
        0xFA28:'THWR800',
        0xCA2C:'THGR328N',
        0xFAB8:'WTGR800',
        0x1A99:'WTGR800',
        0x1A89:'WGR800',
        0xEA7C:'UVN128/UV138',
        0xDA78:'UVN800',
        0xEAC0:'OWL CM113'
    }

    sensorName= sensorID2Name.get(sensorTypeId,"Unknown")
    if sensorName=='Unknown':
        # F007TH is identified by first byte, checksum will help eliminate false positives
        if procData[0]==0x8A:  # should be
            sensorName= 'F007TH'
            sensorTypeId = procData[0]<<8
        else:
            return False

# recognized sensor type
    Domoticz.Log('Packet ID {0:04X} - sensor {1} (len={2})'.format(sensorTypeId, sensorName,len(procData)))
    Domoticz.Log('Received: '+procData.hex())

# Create recognized devices, even if they can't be decoded
# just to show they are out there (and we should support them)
    channel= 0
    rollingCode=0
    sV=''
    BatteryLevel= 255
    DeviceTypeName= 'Custom'
    DeviceName= "{}-unsupported".format(sensorName)
    temperature= 0
    humidity= 0
    hs= 0
    humidityText = {
        0: "NORM",
        1: "COMF",
        2: "*DRY",
        3: "*WET"
    }
    bs= 0
    BatteryStatus= "OK"
    BatteryLevel= 100

    if sensorName=='F007TH':

        DeviceTypeName= "Temp+Hum"

        binary= ""
        for i in range(0, len(procData)):
            binary = binary + "{0:08b} ".format(procData[i])
        Domoticz.Log("binaryO: {}".format(binary))

        # for some reason the bytes are coming in reversed, flip them back
        binary= ""
        for i in range(0, len(procData)):
            procData[i] = reverse8Bits(procData[i])

        # data is arriving with the preamble_pattern[2] = {0x01, 0x45}; // 12 bits
        # on the front, (reference: ambient_weather.c)
        # to byte align, leave 0x45 (expected id) and find temp/hum data where we expect
        # need to shift entire message by two bits to the left
        for t in range(0, len(procData)):
            procData[t] &= 0b00111111
            procData[t] <<= 2
            if t<len(procData)-1:
                procData[t] |= ((procData[t+1]&0b11000000)>>6)

        binary= ""
        for i in range(0, len(procData)):
            binary = binary + "{0:08b} ".format(procData[i])
        Domoticz.Log("binaryR: {}".format(binary))

        if len(procData)<6:
            Domoticz.Debug('partial F007TH packet, aborting...')
            return False

        # is this a F007TH packet?
        Domoticz.Log("F007TH Code: {:02x}".format(procData[0]))
        if procData[0]!=0x45:
            Domoticz.Debug('not a F007TH packet, aborting...')
            return False

        # verify Checksum
        expected = procData[5];
        calculated = lfsr_digest8(procData, 5, 0x98, 0x3e) ^ 0x64;
        # Domoticz.Log('Expected: {0:02x} Calculated: {1:02x}'.format(expected, calculated))
        if expected != calculated:
            Domoticz.Log('Checksum error in Ambient Weather message. Expected: {0:02x} Calculated: {1:02x}'.format(expected, calculated))
        #    return False;

        rollingCode = procData[1]

        # battery status -  0 OK, 1 low
        # TODO: Verify (we need a low but not dead AAA to check this)
        bs = procData[2]&0x80

        # channel
        channel= ((procData[2]>>4) & 0b00000111)+1

        # humidity
        # humidity bits
        humidity = procData[4]

        # temperature bits (before reverse)
        temperature =  (procData[2] & 0b00001111) << 8
        temperature |= (procData[3] & 0b11111111)
        temperature /= 10
        temperature -= 40

        # Domotics expects Celsius
        # This sensor only reports in Fahrenheit
        # need to convert to Celsius
        temperature = (temperature-32)* (5/9)

# only decodes the Oregon Scientific THGR122NX, currently
    elif sensorTypeId==0x1A2D:

    # Must have enough packet to decode
    # should be 10, but we can get data from 8
        if len(procData)<9:
            Domoticz.Debug('partial packet, aborting...')
            return False;

    # calc nibble checksum
        sum= 0
        for b in range(8):
            sum += (procData[b]&0x0f)+(procData[b]>>4)
        sum -= 0x0a;

    # checksum verify
        if sum!=procData[8]:
            Domoticz.Debug('***Checksum failed')
            return False

        DeviceTypeName= "Temp+Hum"

# channel
        if procData[2]&0x10:
            channel = 1
        elif procData[2]&0x20:
            channel = 2
        elif procData[2]&0x40:
            channel = 3
        else:
            channel = -1

# rollingCode
        rollingCode= procData[3]

# battery status -  0 OK, 1 low
        bs = procData[4]&0x04

# temperature, BCD encoded Celsius with a fixed dec place
        t0 = float(procData[5]>>4)    # digit 1
        t1 = float(procData[5]&0x0F)  # digit 2
        t2 = float(procData[4]>>4)    # 1st digit right of decimal
        temperature = t0*10.0+t1+t2*0.1

# negative temp?
# docs seem to be wrong?
# I own the THGR122NX, and here is what works
        if (procData[6]&0x08)!=0:
            temperature = -temperature

# always report in Celsius, to see Fahrenheit, see
# Domoticz: Setup->Settings->Meters/Counters

# humidity
        h1= float(procData[7]&0x0F)
        h2= float(procData[6]>>4)
        humidity= h1*10.0+h2

# humidity status
        hs= procData[7]>>6

# set values for all sensors
    if bs!=0:
        BatteryStatus= "Low"
        BatteryLevel= 5

    humidityStatus= humidityText.get(hs, "Invalid")
    shortSensorName= sensorName.split("/")[0]
    DeviceName= "{}-{}".format(shortSensorName, channel)
    sV= "{0:.1f};{1};{2}".format(temperature, humidity, hs)
    Domoticz.Log("{} channel={} rollingCode={:02x} temperature= {} degrees Humidity={}% humidityStatus={} BatteryStatus={} sValue={}".format(sensorName, channel, rollingCode, temperature, humidity, humidityStatus, BatteryStatus, sV))
    DevId= "{0}{1:04X}{2:1X}{3:02X}".format(Parameters["HardwareID"], sensorTypeId, channel, rollingCode)

    TimedOut= 0
    UpdateDevice(DeviceName, DeviceTypeName, DevId, sV, TimedOut, BatteryLevel)
    return True

# def AmbientWeatherChecksum(l, buf):
#     mask = 0x7C;
#     checksum = 0x64;
#
#     for byteCnt in range(8)
#         int bitCnt;
#         data = buff[byteCnt]
#
#         for bitCnt in range(8)
#
#             # Rotate mask right
#             bit = mask & 1
#             mask = (mask >> 1 ) | (mask << 7)
#             if bit:
#                 mask ^= 0x18
#
#             # XOR mask into checksum if data bit is 1
#             if data & 0x80 :
#                 checksum ^= mask
#             data <<= 1
#         }
#     }
#     return checksum

def UpdateDevice(DeviceName, DeviceTypeName, DevId, sValue, TimedOut, BatteryLevel):
# update device, if it exists already
    found= False
    for Unit in Devices:
        if Devices[Unit].DeviceID==DevId:
            found= True
            break

# found a new device
    if found:
        Devices[Unit].Update(nValue=0, sValue=sValue, TimedOut=TimedOut, BatteryLevel=BatteryLevel)
        Domoticz.Debug("Update DevId='{}' with '{}'".format(DevId, sValue))
    else:
        nextDeviceUnit= len(Devices)+1 # if Devices else 0
        Domoticz.Log("Creating new Device {} - {}".format(nextDeviceUnit, DevId))
        newDevice = Domoticz.Device(DeviceName, Unit=nextDeviceUnit, TypeName=DeviceTypeName, Used=0, DeviceID=DevId)
        newDevice.Create()
        DumpConfigToLog(DevId='')

def DumpConfigToLog(DevId):
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")

    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device DeviceID: '" + str(Devices[x].DeviceID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def reverse8Bits(a):
    b= a&1
    for i in range(7):
        a >>= 1
        b <<= 1
        b |= a&1
    return b

# references:
# https://eclecticmusingsofachaoticmind.wordpress.com/2015/01/21/home-automation-temperature-sensors/
# https://github.com/merbanan/rtl_433/blob/master/src/devices/ambient_weather.c
# The check is an LFSR Digest-8, gen 0x98, key 0x3e, init 0x64
def lfsr_digest8(message, bytes, gen, key):
    sum = 0
    for k in range(0, bytes):
        data = message[k]
        for i in range (7,-1, -1):
            # fprintf(stderr, "key is %02x\n", key);
            # XOR key into sum if data bit is set
            if (data >> i) & 1:
                sum ^= key

            # roll the key right (actually the lsb is dropped here)
            # and apply the gen (needs to include the dropped lsb as msb)
            if key & 1:
                key = (key >> 1) ^ gen
            else:
                key = (key >> 1)
    return sum
