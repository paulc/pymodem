
import os,re,select,sys,termios,time

class NotFound(Exception):
    pass

class TTYReader(object):

    def __init__(self,device,speed=termios.B115200):
        self.device = device
        self.fd = os.open(device, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)
        self.buffer = []
        self.tty_setup(speed)
        self.user_setup()

    def tty_setup(self,speed):
        params = termios.tcgetattr(self.fd)
        params[0] = termios.IGNBRK
        params[1] = 0
        params[2] = (termios.CS8 | termios.CLOCAL | termios.CREAD)
        params[3] = 0
        params[4] = speed
        params[5] = speed
        termios.tcsetattr(self.fd, termios.TCSANOW, params)

    def user_setup(self):
        pass
        
    def write(self,data):
        os.write(self.fd,data)

    def ready(self,timeout=0):
        return select.select([self.fd],[],[],timeout)[0] == [self.fd]

    def interact(self,filter=lambda x:True):
        print "Connected: %s" % self.device
        while True:
            readable = select.select([0,self.fd],[],[])[0]
            if 0 in readable:
                data = sys.stdin.readline().rstrip()
                if data:
                    self.write(data + "\r\n")
            if self.fd in readable:
                data = self.readline()
                if data and filter(data):
                    print ">>>", data

    def read(self,n=1):
        return os.read(self.fd,n)

    def readline(self,timeout=1):
        data = ""
        while self.ready(timeout):
            data += os.read(self.fd,1)
            if data[-2:] == "\r\n":
                break
        return data[:-2]

    def match(self,f=None,timeout=2):
        self.buffer = []
        now = time.time() 
        #while self.ready(timeout) and (time.time() - now < timeout):
        while time.time() - now < timeout:
            line = self.readline()
            if line:
                if f(line):
                    return line
                else:
                    self.buffer.append(line)
        raise NotFound()
        
    def readlines(self,f=None):
        lines = []
        while self.ready():
            lines.append(self.readline())
        return filter(f,lines)

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-d", "--device", help="TTY device to open")
    parser.add_option("-b", "--speed", help="Speed (Default: 115200)")
    options,args = parser.parse_args()

    if options.speed:
        try:
            speed = termios.__dict__["B%s" % options.speed]
        except KeyError:
            print "ERROR: Invalid TTY speed - %s" % options.speed
            speeds = [ int(x[1:]) for x in dir(termios) if \
                            re.search('^B[0-9]*$',x) and int(x[1:]) > 0 ]
            speeds.sort()
            print "(Valid: %s)" % ",".join(map(str,speeds))
            sys.exit(0)
    else:
        speed = termios.B115200

    if options.device:
        tty = TTYReader(options.device,speed)
        print "Opening Device:", options.device
        tty.interact()
    else:
        parser.print_help()
