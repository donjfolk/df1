# DF1 #

Allen Bradley DF1 protocol implementation in Python for SLC Devices (May Work for Other things?).

### How to use ###
```

import df1

oServer = TcpMaster(server="10.250.1.100", port=44818, src=0x0, dst=0x1, timeout_in_sec=2.0)
print oServer.poll(F15:0', 1)
print oServer.poll(F15:0', 3)
print oServer.poll('I:1/0', 16)
```
