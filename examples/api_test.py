#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

import os, os.path
import sys
import uuid
# from datetime import date
from lxml import etree
from lxml import objectify

# ADAPT YOUR PATH HERE
sys.path.append('/home/dav/dvp/py/ebay/ebaypyt/lib')
from ebaypyt import EbayWebService


my_keys = {
"developer_key"   : "...",
"application_key" : "...",
"certificate_key" : "...",
"auth_token"      : ".........."
}

def pxml(my_object):
    return etree.tostring(recc, pretty_print=True)

ews = EbayWebService(my_keys['developer_key'],my_keys['application_key'],my_keys['certificate_key'],my_keys['auth_token'])

# recc = ews.get('RecurringJob').recurringJobDetail
vals={
# 'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
    'jobType': 'FeeSettlementReport',
    # 'type_recurrence': 'time' or 'monthly' or 'weekly',
    'type_recurrence': 'time',
    'time': 120
    # 'day': 'Sunday' up to 'Saturday or Day_1, Day_2 up to Day_last
}

recc = ews.create('RecurringJob', vals)
# recc = ews.delete('RecurringJob')
#
# print pxml(recc)
reccget = ews.get('RecurringJob').recurringJobDetail
print [e.tag for e in reccget.getchildren()]
print [e for e in reccget.getchildren()]

# job = ews.get('Job')
# print dav.getvar(recc, vars())
# print [e.tag for e in job.getchildren()]

