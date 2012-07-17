#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

import sys

# from datetime import date
from lxml import etree
from lxml import objectify

# ADAPT YOUR PATH HERE
sys.path.append('/home/dav/dvp/py/ebay/ebaypyt/lib')
from ebaypyt import EbayWebService

# ADAPT YOUR PATH HERE AND CREATE 'ebay_keys.py' file ...
sys.path.append('/home/dav/dvp/py/ebay')
import ebay_keys as ek

# ... OR ENABLE THIS DICT
# developer_key="..."
# application_key="..."
# certificate_key="..."
# auth_token=".........."

def pxml(my_object):
    return etree.tostring(my_object, pretty_print=True)

ews = EbayWebService(ek.developer_key,ek.application_key,ek.certificate_key,ek.auth_token)


# uncomment each block to test them

#  *********       ------------       *********
print '\n\n        ------- Recurring Job getting -------  '
# Display defined recurring jobs if exists
mget = ews.get('RecurringJob')
if mget != False:
    print '   >>> recurring jobs:', mget
else:
    print '   >>> No recurring jobs'


#  *********       ------------       *********
print '\n\n        ------- Recurring Job creation -------  '
params={
# 'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
    'jobType': 'SoldReport',
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
    # print '   >>> recurring jobs created:', recc
# else:
    # print '   >>> No created recurring jobs'


#  *********       ------------       *********
# print '\n\n        ------- Recurring Job deletion -------  '
# Give a valid value
# recc = ews.delete('RecurringJob','5000133101')
# if recc != False:
    # print '   >>> recurring jobs deleted:', recc
# else:
    # print '   >>> No deleting recurring jobs'


#  *********       ------------       *********
print '\n\n        ------- Jobs getting informations -------  '
params = {
    'jobStatus': 'Completed',
    # 'jobType': 'ActiveInventoryReport',
}

# jobs = ews.get('Job', params)
# if jobs != False:
    # print '  response:', jobs
    #Jobs ar returned in xml format
    # print pxml(jobs)
    # print 'head',[e.tag for e in jobs.getchildren()]
    # import pdb; pdb.set_trace()
    # for res in jobs:
        # print 'data',[e for e in res.getchildren()]
# else:
    # print '    No jobs'





#  *********       ------------       *********
print '\n\n        ------- Download job file-------  '

params = {
    'taskReferenceId': '5045798294',
    'fileReferenceId': '5042581944',
}
# file_downloaded_datas = ews.download('Job', params)
#
# #display the 500th first and the 500 last
# print file_downloaded_datas[:500], '\n\n...\n\n'
# print file_downloaded_datas[-500:]
#
# print 'api_test ebaypyt ended'






#  *********       ------------       *********
print '\n\n        ------- Product getting informations ------- '
#
# params = {
    # 'ItemID': '260874940015',
    # 'DetailLevel': 'ItemReturnAttributes',
# }

# product = ews.get('Product', params)
# if product != False:
    # print '\n\n  response:', product[0]
# else:
    # print '\n\n   No product'
