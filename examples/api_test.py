#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
_
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

# ADAPT YOUR PATH HERE
sys.path.append('/home/dav/dvp/py/ebay')
import ebay_keys as ek

# OR ENABLE THIS DICT
# developer_key="..."
# application_key="..."
# certificate_key="..."
# auth_token=".........."

def pxml(my_object):
    return etree.tostring(my_object, pretty_print=True)

ews = EbayWebService(ek.developer_key,ek.application_key,ek.certificate_key,ek.auth_token)

# recc = ews.get('RecurringJob').recurringJobDetail
params={
# 'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
    'jobType': 'ActiveInventoryReport',
    # 'type_recurrence': 'time' or 'monthly' or 'weekly',
    'time': '00:00:20',
    'type_recurrence': 'monthly',
    'day': 'Day_Last',
    # 'type_recurrence': 'weekly',
    # 'day': 'Tuesday',
    # 'day': 'Sunday' up to 'Saturday or Day_1, Day_2 up to Day_Last
}

# recc = ews.create('RecurringJob', params);
# if recc != False:
    # print pxml(recc)
# recc = ews.delete('RecurringJob','5000338700')

reccget = ews.get('RecurringJob')
if reccget != False:
    print pxml(reccget)
    print 'head',[e.tag for e in reccget.getchildren()]
    for res in reccget:
        print 'data',[e for e in res.getchildren()]
else:
    print '    No job recurring'



