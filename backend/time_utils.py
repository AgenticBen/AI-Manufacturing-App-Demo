"""Parse Postgres RFC3339 timestamps consistently on Python 3.9 and 3.12."""
from datetime import datetime
import re

def parse_time(value):
    text=value.replace('Z','+00:00')
    text=re.sub(r'\.([0-9]{1,5})(?=[+-]|$)',lambda m:'.'+m.group(1).ljust(6,'0'),text)
    return datetime.fromisoformat(text)
