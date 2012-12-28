
class HexBuffer(object):

    def __init__(self,data,debug=None):
        self.data = data
        self.debug = debug
        self.length = len(data)
        self.index = 0 

    def __iter__(self):
        return self

    def reset(self):
        self.index = 0

    def remainder(self,f=""):
        start = self.index
        self.index = self.length
        if self.debug:
            self.debug(f,self.data[start:])    
        return self.data[start:]

    def peek(self,n=1):
        return self.data[self.index:self.index+(2*n)]

    def next(self,n=1,f=""):
        start = self.index
        end = start + (2 * n)
        if end > self.length:
            raise StopIteration()
        self.index = end
        if self.debug:
            self.debug(f,self.data[start:end])    
        return self.data[start:end]

    def nextInt(self,n=1,f=""):
        return int(self.next(n,f),16)

    def nextByte(self,n=1,f=""):
        return self.next(n,f).decode('hex')

    def nextArray(self,n=1,f=""):
        return [ self.next(1,"%s[%d]" % (f,i)) for i in range(n) ]
