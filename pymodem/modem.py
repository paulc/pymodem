
import re,optparse,sys 
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

    def sendAT(self,message,timeout=2,check_ok=True):
        self.readlines()
        if not message.startswith('AT'):
            message = 'AT' + message
        self.write(message + "\r\n")
        if check_ok:
            try:
                self.match(lambda l:l == "OK",timeout=timeout)
                return filter(None,self.buffer)
            except(NotFound):
                raise ATError(message,filter(None,self.buffer))

    def sendExtendedAT(self,message,data,timeout=2,check_ok=True):
        self.readlines()
        if not message.startswith('AT'):
            message = 'AT' + message
        self.write(message + "\r")
        self.ready(1)
        self.write(data + "\x1a")
        if check_ok:
            try:
                self.match(lambda l:l == "OK",timeout=timeout)
                return filter(None,self.buffer)
            except(NotFound):
                raise ATError(message,filter(None,self.buffer))

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
    
    def getMode(self):
        mode = self.AT("+CMGF?")
        return {"0":"PDU","1":"Text"}[mode]

    def textMode(self):
        self.sendAT("+CMGF=1")

    def pduMode(self):
        self.sendAT("+CMGF=0")

    def checkSMSSupport(self):
        try:
            service,mt,mo,bm = re.search('(\d,\d,\d,\d)',self.AT('+CSMS?')).group().split(",")
            if mt:
                return True
            else:
                return False
        except Exception:
            return False

    def sendSMS(self,number,message):
        if len(message) > 160:
            raise ValueError("SMS message too long")
        self.textMode()
        return self.sendExtendedAT('+CMGS="%s"' % number,message,timeout=10)[0]

    def deleteSMS(self,n):
        try:
            self.pduMode()
            self.AT("AT+CMGD=%d" % n)
            return True
        except ATError:
            return False

    def getSMS(self,n,debug=None):
        self.pduMode()
        header,tpdu = self.sendAT('+CMGR=%d' % n)
        sms = SMSDeliver(debug)
        sms.parse(header,tpdu,n)
        return sms

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
