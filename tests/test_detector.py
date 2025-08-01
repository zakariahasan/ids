from ids.core.detector import SynFloodDetector

class DummyPacket:
    def __init__(self, ip):
        self.ip = type('IP', (), {'src': ip})
        self.tcp = type('TCP', (), {'flags': '0x0002'})

def test_syn_flood():
    det = SynFloodDetector()
    pkt = DummyPacket('10.0.0.1')
    for _ in range(det.THRESHOLD + 1):
        alerts = det.inspect(pkt)
    assert alerts and "SYN flood" in alerts[0]