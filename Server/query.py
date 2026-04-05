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
# query function
###################################################################
def query(data, syslog_entries, ts):
    try:
        qparts = shlex.split(data.strip())
    except ValueError:
        response = "Invalid QUERY syntax."
        qparts = []

    if qparts:
        # Expected:
        # QUERY <IP_or_DNS>:<Port> <SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>
        if len(qparts) < 4:
            response = (
                "Correct Usage: QUERY <IP_or_DNS>:<Port> "
                "<SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>"
            )
        else:
            target = qparts[1]
            qtype = qparts[2].upper()
            qvalue = " ".join(qparts[3:]).strip()

            if not syslog_entries:
                response = "No indexed log entries to query."
            else:
                def fmt_entry(e: SyslogEntry) -> str:
                    ts = e.timestamp.strftime("%b %d %H:%M:%S")
                    
                    print(needle+"\n\n")
                    print(ts+"\n\n")

                    return f"{ts} {e.hostname} {e.daemon}: {e.message}"

                matches = []
                lines = []

                if qtype == "SEARCH_DATE":
                    needle = qvalue.lower()
                    for e in syslog_entries:
                        ts = e.timestamp.strftime("%b %d %H:%M:%S").lower()
                        print(f"DEBUG: Comparing '{needle}' to '{ts}'")
                        if needle in ts:
                            matches.append(e)
                    if matches:
                        lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for date '{qvalue}':"]

                        top_n = 10
                        bottom_n = 3
                        total = len(matches)

                        if total <= top_n + bottom_n:
                            
                            for i, e in enumerate(matches, 1):
                                lines.append(f"{i}. {fmt_entry(e)}")
                        else:
                            
                            for i, e in enumerate(matches[:top_n], 1):
                                lines.append(f"{i}. {fmt_entry(e)}")

                            lines.append("...")  # optional separator

                            
                            for i in range(total - bottom_n, total):
                                lines.append(f"{i+1}. {fmt_entry(matches[i])}")

                        response = "\n".join(lines)
                    else:
                        response = f"No matching entries found for date '{qvalue}'."

                elif qtype == "SEARCH_HOST":
                    for e in syslog_entries:
                        if e.hostname.lower() == qvalue.lower():
                            matches.append(e)
                    if matches:
                        lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for host '{qvalue}':"]

                        top_n = 10
                        bottom_n = 3
                        total = len(matches)

                        if total <= top_n + bottom_n:
                            
                            for i, e in enumerate(matches, 1):
                                lines.append(f"{i}. {fmt_entry(e)}")
                        else:
                            
                            for i, e in enumerate(matches[:top_n], 1):
                                lines.append(f"{i}. {fmt_entry(e)}")

                            lines.append("...")  # optional separator

                            
                            for i in range(total - bottom_n, total):
                                lines.append(f"{i+1}. {fmt_entry(matches[i])}")

                        response = "\n".join(lines)
                    else:
                        response = f"No matching entries found for host '{qvalue}'."

                elif qtype == "SEARCH_DAEMON":
                    for e in syslog_entries:
                        if e.daemon.lower() == qvalue.lower():
                            matches.append(e)
                    if matches:
                        lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for daemon '{qvalue}':"]

                        top_n = 10
                        bottom_n = 3
                        total = len(matches)

                        if total <= top_n + bottom_n:
                            
                            for i, e in enumerate(matches, 1):
                                lines.append(f"{i}. {fmt_entry(e)}")
                        else:
                            
                            for i, e in enumerate(matches[:top_n], 1):
                                lines.append(f"{i}. {fmt_entry(e)}")

                            lines.append("...")  # optional separator

                            
                            for i in range(total - bottom_n, total):
                                lines.append(f"{i+1}. {fmt_entry(matches[i])}")

                        response = "\n".join(lines)
                    else:
                        response = f"No matching entries found for daemon '{qvalue}'."

                elif qtype == "SEARCH_SEVERITY":
                    sev = qvalue.upper()
                    for e in syslog_entries:
                        if e.severity.upper() == sev:
                            matches.append(e)

                    if matches:
                        lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for severity '{sev}':"]

                        top_n = 10
                        bottom_n = 3
                        total = len(matches)

                        if total <= top_n + bottom_n:
                            
                            for i, e in enumerate(matches, 1):
                                lines.append(f"{i}. {fmt_entry(e)}")
                        else:
                            
                            for i, e in enumerate(matches[:top_n], 1):
                                lines.append(f"{i}. {fmt_entry(e)}")

                            lines.append("...")  # optional separator

                            
                            for i in range(total - bottom_n, total):
                                lines.append(f"{i+1}. {fmt_entry(matches[i])}")

                        response = "\n".join(lines)

                    else:
                        response = f"No matching entries found for severity '{sev}'."

                        #https://www.tiktok.com/@purrito152/video/7595372803818294558?lang=en

                elif qtype == "SEARCH_KEYWORD":
                    needle = qvalue.lower()
                    for e in syslog_entries:
                        if needle in e.message.lower():
                            matches.append(e)
                    if matches:
                        lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for keyword '{qvalue}':"]

                        top_n = 10
                        bottom_n = 3
                        total = len(matches)

                        if total <= top_n + bottom_n:
                            
                            for i, e in enumerate(matches, 1):
                                lines.append(f"{i}. {fmt_entry(e)}")
                        else:
                            
                            for i, e in enumerate(matches[:top_n], 1):
                                lines.append(f"{i}. {fmt_entry(e)}")

                            lines.append("...")  # optional separator

                            
                            for i in range(total - bottom_n, total):
                                lines.append(f"{i+1}. {fmt_entry(matches[i])}")

                        response = "\n".join(lines)
                    else:
                        response = f"No matching entries found for keyword '{qvalue}'."

                elif qtype == "COUNT_KEYWORD":
                    needle = qvalue.lower()
                    count = sum(1 for e in syslog_entries if needle in e.message.lower())
                    response = f"The keyword '{qvalue}' appears in {count} indexed log entr{'y' if count==1 else 'ies'}."

                else:
                    response = (
                        f"Unknown QUERY type: {qtype}. "
                        "Use SEARCH_DATE, SEARCH_HOST, SEARCH_DAEMON, SEARCH_SEVERITY, SEARCH_KEYWORD, or COUNT_KEYWORD."
                    )
                
                return response