
import optparse,sys 
from sms import SMSDeliver, SMSException
from chat import TTYReader,NotFound

def pairs(l):
    i = iter(l)
    while True:
        yield(i.next(),i.next())

class ATError(Exception):
    pass

class ModemReader(TTYReader):

    def user_setup(self):
        self.AT('E0')
        self.readlines()

    def sendAT(self,message,check_ok=True):
        self.readlines()
        if not message.startswith('AT'):
            message = 'AT' + message
        self.write(message + "\r\n")
        if check_ok:
            try:
                self.match(lambda l:l == "OK")
                f = lambda l:l and not l.startswith(('^',message))
                return filter(f,self.buffer)
            except(NotFound):
                raise ATError(message,self.buffer)

    def sendExtendedAT(self,message,data):
        self.readlines()
        if not message.startswith('AT'):
            message = 'AT' + message
        self.write(message + "\r")
        self.ready(1)
        self.write(data + "\x1a")
        print self.readlines()

    def AT(self,command,strip=True):
        lines = self.sendAT(command)
        if lines:
            result = lines[0]
            if strip and result.startswith('+'):
                return result.split(': ',1)[1]
            else:
                return result
        else:
            return None

class GSMModemReader(ModemReader):

    def user_setup(self):
        super(GSMModemReader,self).user_setup()
        self.pduMode()

    def getModel(self):
        mnfr = self.AT('+CGMI')
        model = self.AT('+CGMM')
        return "%s %s" % (mnfr.title(),model)

    def getIMEI(self):
        return self.AT('+CGSN')

    def getIMSI(self):
        return self.AT('+CIMI')

    def getMSISDN(self):
        return self.AT('+CNUM').split(",")[1].strip('"')
    
    def checkSMSSupport(self):
        service,mt,mo,bm = self.AT('+CSMS?').split()[1].split(",")
        if mt:
            return True
        else:
            return False

    def getMode(self):
        mode = self.AT("+CMGF?")
        return {"0":"PDU","1":"Text"}[mode]

    def textMode(self):
        self.sendAT("+CMGF=1")

    def pduMode(self):
        self.sendAT("+CMGF=0")

    def deleteSMS(self,n):
        try:
            self.pduMode()
            self.AT("AT+CMGD=%d" % n)
            return True
        except ATError:
            return False

    def getSMS(self,n,debug=None):
        try:
            self.pduMode()
            header,tpdu = self.sendAT('+CMGR=%d' % n)
            sms = SMSDeliver(debug)
            sms.parse(header,tpdu,n)
            return sms
        except (ATError,ValueError):
            return None

    def getSMSList(self,new=True,debug=None):
        sms_list = []
        if new:
            cmd = '+CMGL=0'
        else:
            cmd = '+CMGL=4'
        try:
            self.pduMode()
            for header,tpdu in pairs(self.sendAT(cmd)):
                try:
                    sms = SMSDeliver(debug)
                    sms.parse(header,tpdu)
                    sms_list.append(sms)
                except SMSException, e:
                    print >>sys.stdout, "Invalid SMS Message:" + header
            return sms_list
        except (ATError,ValueError):
            return None

if __name__ == '__main__':
    import code,optparse
    parser = optparse.OptionParser()
    parser.add_option("-d", "--device", help="Modem device to open")
    options,args = parser.parse_args()

    if options.device:
        modem = GSMModemReader(options.device)
        print
        print "Device:", modem.getModel()
        print "MSISDN:", modem.getMSISDN()
        print "IMSI:  ", modem.getIMSI()
        print "IMEI:  ", modem.getIMEI()
        print 
        code.interact(banner="Modem device configured as 'modem'\n",local=locals())
    else:
        parser.print_help()
