
GSM_03_38_ALPHABET = [ 
    u'@', u'\xa3', u'$', u'\xa5', u'\xe8', u'\xe9', u'\xf9',
    u'\xec', u'\xf2', u'\xc7', u'\n', u'\xd8', u'\xf8', u'',
    u'\xc5', u'\xe5', u'\u0394', u'_', u'\u03a6', u'\u0393',
    u'\u039b', u'\u03a9', u'\u03a0', u'\u03a8', u'\u03a3',
    u'\u0398', u'\u039e', u'\x1b', u'\xc6', u'\xe6', u'\xdf',
    u'\xc9', u' ', u'!', u'"', u'#', u'\u20ac', u'%', u'&', u"'",
    u'(', u')', u'*', u'+', u',', u'-', u'.', u'/', u'0', u'1',
    u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9', u':', u';',
    u'<', u'=', u'>', u'?', u'\xa1', u'A', u'B', u'C', u'D',
    u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N',
    u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X',
    u'Y', u'Z', u'\xc4', u'\xd6', u'\xd1', u'\xdc', u'\xa7',
    u'\xbf', u'a', u'b', u'c', u'd', u'e', u'f', u'g', u'h',
    u'i', u'j', u'k', u'l', u'm', u'n', u'o', u'p', u'q', u'r',
    u's', u't', u'u', u'v', u'w', u'x', u'y', u'z', u'\xe4',
    u'\xf6', u'\xf1', u'\xfc', u'\xe0'
]

GSM_03_38_ESCAPE = 27 

GSM_03_38_EXTENSION = {
    10: u'\x0c', 20: u'^', 40: u'{', 41: u'}', 47: u'\\', 
    60: u'[', 61: u'~', 62: u']', 64: u'|', 101: u'\xa4'
}

def decode_septets(text):
    shift = 0
    prev = 0
    bytes = []
    encoded = []
    escape = False
    for i in range(0,len(text),2):
        current = int(text[i:i+2],16)
        byte = ((current << shift) + (prev >> (8 - shift))) & 0x7f
        bytes.append(byte)
        shift = (shift + 1) % 7
        if shift == 0:
            bytes.append((current >> 1) & 0x7f)
        prev = current
    for b in bytes:
        if b == GSM_03_38_ESCAPE:
            escape = True
        else:
            if escape:
                encoded.append(GSM_03_38_EXTENSION.get(b,u' '))
                escape = False
            else:
                encoded.append(GSM_03_38_ALPHABET[b])
    return u"".join(encoded)

if __name__ == '__main__':

    while True:
        text = raw_input("GSM.03.38 Text >>> ")
        print decode_septets(text)

