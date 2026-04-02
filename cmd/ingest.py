import os
import re


def ingest(filepath):
    # code gets filepath
    
    if filepath:
    # if file found
        print("file found!") 
    # code access filepath
        parsed_entries = []
        pattern = re.compile(
            r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
            r'(?P<host>\S+)\s+(?P<service>[^\[:]+)(?:\[(?P<pid>\d+)\])?:\s(?P<message>.*)$'
        )

########################################################################################################################

        debug = True  

        if debug:
            class _DebugList(list):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._printed_last = False

                def append(self, item):
                    super().append(item)
                    n = super().__len__()
                    if n <= 5:
                        print(f"syslog entry {n}: {item}")

                def __len__(self):
                    n = super().__len__()
                    if n > 0 and not self._printed_last:
                        print(f"last syslog entry: {self[-1]}")
                        self._printed_last = True
                    return n

            parsed_entries = _DebugList(parsed_entries)

########################################################################################################################


        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m = pattern.match(line)
                if m:
                    parsed_entries.append(m.groupdict())

        print(f"parsed {len(parsed_entries)} syslog entries")
    
    else:
        print("file not found!")
        return
    # if file missing

def main():

        ingest("SVR1_server_auth_syslog.txt")


if __name__ == "__main__":
    main()