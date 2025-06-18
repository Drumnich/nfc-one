from smartcard.System import readers

rlist = readers()
print("Readers:", rlist)
if not rlist:
    print("No NFC reader found")
    exit()

reader = rlist[0]
print("Using reader:", reader)
connection = reader.createConnection()
connection.connect()
get_uid_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
try:
    response, sw1, sw2 = connection.transmit(get_uid_cmd)
    print("Response:", response, "SW1:", sw1, "SW2:", sw2)
except Exception as e:
    print("Error reading card:", e) 