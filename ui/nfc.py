from smartcard.System import readers
from smartcard.util import toHexString

class NFCReader:
    def __init__(self):
        self.readers = readers()
        self.reader = self.readers[0] if self.readers else None

    def list_readers(self):
        return [str(r) for r in self.readers]

    def read_card_uid(self):
        if not self.reader:
            return None, "No NFC reader found"
        try:
            connection = self.reader.createConnection()
            connection.connect()
            get_uid_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            response, sw1, sw2 = connection.transmit(get_uid_cmd)
            if sw1 == 0x90:
                return toHexString(response).replace(' ', ''), None
            return None, "Card not detected or unsupported"
        except Exception as e:
            return None, str(e) 