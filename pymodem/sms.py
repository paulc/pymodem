
# AT+CMGF=1 (Text Mode)
# AT+CNUM (Phone Num)
# AT+CMGL=4 /"All" (List SMS)
# AT+CMGR=n (Get SMS)

from datetime import datetime

from hexbuffer import HexBuffer
from gsm_03_38 import decode_septets

def decode_number(bytes):
    number = []
    for pair in bytes:
        number.append(pair[1])
        number.append(pair[0])
    if number[-1].lower() == 'f':
        number.pop()
    return u"".join(number)

def decode_timestamp(bytes):
    timestamp = []
    for pair in bytes:
        timestamp.append(int(pair[1]+pair[0]))
    tz = timestamp.pop()
    timestamp[0] += 2000
    return datetime(*timestamp)

def get_bits(data,offset,bits=1):
    mask = ((1 << bits) - 1) << offset
    return (data & mask) >> offset 

def binary(n,count=16,reverse=0):
    bits = [str((n >> y) & 1) for y in range(count-1, -1, -1)]
    if reverse:
        bits.reverse()
    return "".join(bits)

def truncate(s,n,suffix=u"..."):
    if len(s) > n:
        return s[:n-len(suffix)]+suffix
    else:
        return s

class SMSException(Exception):
    pass

class SMSDeliver(object):
        
    def __init__(self,debug=None):
        self.status = 0
        self.index = 0
        self.address = u""
        self.SCtype = 0
        self.SCplan = 0
        self.SCnumber = u""
        self.PDUtype = 0
        self.OAtype = 0
        self.OAplan = 0
        self.OAnumber = u""
        self.ProtocolID = 0
        self.DataCoding = None
        self.TS = 0
        self.UD = ""
        self.decoded = u""
        self.debug = debug

    def parse(self,header,tpdu,index=0):
        self.parseHeader(header,index)
        self.parseTPDU(tpdu)

    def parseHeader(self,header,index=0):
        (cmd,status) = header.split(None,1)
        if cmd == "+CMGL:":
            (index,message_status,address_text,tpdu_length) = status.split(",")
        elif cmd == "+CMGR:":
            (message_status,address_text,tpdu_length) = status.split(",")
        else:
            raise SMSException("Invalid Message: %s" % cmd)
        self.index = int(index)
        self.status = int(message_status)
        self.address = address_text

    def parseSCAddress(self,buffer):
        length = buffer.nextInt(f="SCA Length")
        type = buffer.nextInt(f='SCA Type')
        self.SCtype = (type >> 4) & 7
        self.SCplan = type & 15
        if self.SCtype == 5:
            self.SCnumber = decode_septets(buffer.next(length-1,f='SCA'))
        elif self.SCtype == 1:
            self.SCnumber = "+" + decode_number(buffer.nextArray(length-1,f='SCA'))
        else:
            self.SCnumber = decode_number(buffer.nextArray(length-1,f='SCA'))

    def parsePDU(self,buffer):
        self.PDUtype = buffer.nextInt(f='PDU Type')
            
    def parseOA(self,buffer):
        length = sum(divmod(buffer.nextInt(f='OA Length'),2))
        type = buffer.nextInt(f='OA Type')
        self.OAtype = (type >> 4) & 7
        self.OAplan = type & 15
        if self.OAtype == 5:
            self.OAnumber = decode_septets(buffer.next(length,f='OA'))
        elif self.OAtype == 1:
            self.OAnumber = "+" + decode_number(buffer.nextArray(length,f='OA'))
        else:
            self.OAnumber = decode_number(buffer.nextArray(length,f='OA'))

    def parseProtocol(self,buffer):
        self.ProtocolID = buffer.nextInt(f='Protocol')
        dcs = buffer.nextInt(f='Protocol')
        coding_group = get_bits(dcs,6,2)
        if coding_group == 0:
            self.DataCoding = dict(
                message_class = get_bits(dcs,0,2),
                alphabet = get_bits(dcs,2,2),
                use_message_class = get_bits(dcs,4,1),
                compressed = get_bits(dcs,5,1)
            )
        elif coding_group == 2:
            # Message Waiting Indication
            raise SMSException("Unsupported DCS - Message Waiting Indication")
        else:
            # Reserved
            raise SMSException("Unsupported DCS - Reserved")
           
    def parseTS(self,buffer):
        self.TS = decode_timestamp(buffer.nextArray(7,f='TS'))
        
    def parseUD(self,buffer):
        length = buffer.nextInt(f='UD Length')
        self.UD = buffer.remainder(f='UD')
        alphabet = self.DataCoding['alphabet']
        if alphabet == 0:
            self.decoded = decode_septets(self.UD)
        elif alphabet == 1:
            self.decoded = self.UD.decode('hex')
        elif alphabet == 2:
            self.decoded = unicode(self.UD.decode('hex'),'utf-16be')
        else:
            raise SMSException("Unsupported Alphabet - Reserved")
        
    def parseTPDU(self,tpdu):
        if self.debug:
            self.debug("TPDU",tpdu)
        buffer = HexBuffer(tpdu,debug=self.debug)
        try:
            # PDU Type
            self.parseSCAddress(buffer)
            self.parsePDU(buffer)
            self.parseOA(buffer)
            self.parseProtocol(buffer)
            self.parseTS(buffer)
            self.parseUD(buffer)
        except StopIteration, ValueError:
            raise SMSException("Invalid Message")

    def __str__(self):
        return '<<SMSDeliver: %s,"%s","%s">>' % (self.index,self.OAnumber.encode('utf8'),truncate(self.decoded,40).encode('utf8'))

    def dump(self):

        properties = [ 'index', 'status', 'address', 'SCtype', 'SCplan', 'SCnumber',
                       'PDUtype', 'OAtype', 'OAplan', 'OAnumber', 'ProtocolID', 
                       'DataCoding', 'TS', 'UD', 'decoded' ]

        print "SMSDeliver"
        print "=========="
        print 

        for x in properties:
            if x not in [ 'UD' ]:
                print " %12s : %s" % (x,self.__dict__.get(x,""))

        print 

if __name__ == '__main__':

    import optparse,sys
    parser = optparse.OptionParser()
    parser.add_option("--debug",action='store_true')
    options,args = parser.parse_args()

    def log_data(field,data):
        print "++ %s: %s" % (field,data)

    while True:
        try:
            tpdu = raw_input('SMS Deliver TPDU >>> ')
            if tpdu == "":
                sys.exit()
            sms = SMSDeliver()
            if options.debug:
                sms.debug = log_data
            sms.parseTPDU(tpdu)
            sms.dump()
        except SMSException, e:
            print "** ERROR: SMSException:", e

