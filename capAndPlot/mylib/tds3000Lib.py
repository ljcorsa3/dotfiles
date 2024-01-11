import socket
import urllib
import urllib.request

class tdsControl:
    """Class for controlling a tds3000B scope."""
    tdsIP = "0.0.0.0"
    tdsPort = 0
    socket = 0
    selectedMeasurement = ""
    selectedChannel = 0

    def __init__(self, address, port):
        self.tdsIP = address
        self.tdsPort = port

    def queryValue(self):
        """After selecting a channel and measurement type you can
        query the scope to get the value."""
        return self.sendHTTPCmd("MEASUrement:IMMed:VALue?")

    def selectChannel(self, channel):
        """Select channel for measuring.  (1 is first channel)"""
        self.sendHTTPCmd("MEASUrement:IMMed:SOURCE1 CH" + str(channel))
        actualChannel = self.sendHTTPCmd("MEASUrement:IMMed:SOURCE1?")
        actualChannel = actualChannel[2:3]
        self.selectedChannel = int(actualChannel)

    def selectMeasurement(self, measurement):
        """Options for measurement are:
        {AMPlitude|AREa|BURst|CARea|CMEan|CRMs|DELay|FALL|FREQuency
        |HIGH|LOW|MAXimum|MEAN|MINImum|NDUty|NEDGECount|NOVershoot
        |NPULSECount|NWIdth|PEDGECount|PDUty
        |PERIod|PHAse|PK2Pk|POVershoot|PPULSECount|PWIdth|RISe|RMS}.  
        Input is not case sensitive."""
        self.sendHTTPCmd("MEASUrement:IMMed:TYPe " + measurement)
        actualType = self.sendHTTPCmd("MEASUrement:IMMed:TYPe?")
        self.selectedMeasurement = actualType.lower()

    def queryVoltage(self):
        if self.selectedMeasurement != "mean":
            self.selectMeasurement("mean")
        if self.selectedChannel != 1:
            self.selectChannel(1)
        return float(self.queryValue())

    def sendHTTPCmd(self, cmdStr):
        """
        Send a command mnemonic string to the TDS 3000B using HTTP.  The
        input is expected to be a command mnemonic (no response).
        """

        url = "http://" + self.tdsIP + ":" + str(self.tdsPort) + "/Comm.html";
        values = {"COMMAND" : cmdStr, "gpibsend" : "Send", "name" : "" }
        data = urllib.parse.urlencode(values).encode('ascii')
        req = urllib.request.Request(url, data)
        rsp = urllib.request.urlopen(req)
        content = rsp.read(742).decode('ascii')
        content = content.lower()
        startIndex = content.find("<textarea readonly wrap=\"on\" cols=\"60\" rows=\"10\" name=\"name\">");
        if startIndex >= 0:
            startIndex += len("<textarea readonly wrap=\"on\" cols=\"60\" rows=\"10\" name=\"name\">")
            content = content[startIndex:len(content)]
            endIndex = content.find("</textarea>")
            content = content[0:endIndex]
        else:
            content = ""
        return content


