#!/usr/bin/env python3
"""parse_choice accepts a listed row or free text typed into the window list (regression: typed 'kestrel' was rejected)."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'../../profile/airootfs/usr/local/lib/kestrel'))
import taskbar_core as c
items=[(11,'Google - Google Chrome'),(12,'Kestrel - Google Chrome')]
checks=[(c.parse_choice('2. Kestrel - Google Chrome\n',items)==12,'row'),(c.parse_choice('kestrel',items)==12,'typed title'),
 (c.parse_choice('GOOGLE',items)==11,'case-insensitive'),(c.parse_choice('nothing',items) is None,'no match'),(c.parse_choice('',items) is None,'empty')]
bad=[n for ok,n in checks if not ok]
print('taskbar-core-test:',('FAILED '+str(bad)) if bad else 'all passed');sys.exit(1 if bad else 0)
