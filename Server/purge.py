###################################################################
# libraries
###################################################################
from dataclasses import dataclass
from datetime import datetime
import socket
import threading
import re
import shlex


###################################################################
# dataclass initialization
###################################################################
@dataclass
class SyslogEntry:
    severity:str
    timestamp:datetime
    hostname:str
    daemon:str
    message:str

###################################################################
# purge function
###################################################################
def purge(syslog_entries):
    count = len(syslog_entries)
    if count == 0:
        response = f"Nothing to purge, {count} log entries in server."
    else:
        syslog_entries.clear()
        response = f"Server successfully purged, {count} log entries deleted."

    return response