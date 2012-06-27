#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Ebay-py is a library for Python to interact with the Ebay's Web Service API.

    Credits :
    Thanks to Wesley Hansen for eBay-LMS-API
    (https://github.com/...)
    from which I also inspired my library.
"""

__author__ = ""
__date__ = ""

import httplib
import simplejson
import os, os.path
import sys
import gzip
import uuid


from datetime import date, datetime
from lxml import etree
from lxml import objectify


def objectify_to_dict(xml_objectify, cast_fields=None, useless_key=None):
    '''
        :xml_objectify : an objectify object that represente an xml
        :cast_fields :dictionnary that can force the type of each value return
        :useless_key : if a parent key is in this list and if this parent key have
            for value a dictionnary with only one key.
            The parent key will be drop and only the child key will be visible in the response
    '''
    result = {}
    if not cast_fields: cast_fields = {}
    for key in xml_objectify.__dict__.keys():
        if cast_fields.get(key) == list:
            result[key] = []
            for element in xml_objectify.__dict__[key]:
                result[key].append(objectify_to_dict(element, cast_fields=cast_fields, useless_key=useless_key))
        elif hasattr(xml_objectify.__dict__[key], 'pyval'):
            if cast_fields.get(key):
                result[key] = cast_fields.get(key)(xml_objectify.__dict__[key].pyval)
            else:
                result[key] = xml_objectify.__dict__[key].pyval
        else:
            result[key] = objectify_to_dict(xml_objectify.__dict__[key], cast_fields=cast_fields, useless_key=useless_key)
    if useless_key and len(result) == 1 and result.keys()[0] in useless_key:
        return result[result.keys()[0]]
    return result


class EbayError(Exception):
     def __init__(self, objectify_value):
         self.error_id = objectify_value.errorMessage.error.errorId
         self.error_message = objectify_value.errorMessage.error.message

     def __str__(self):
         return repr(self.error_message)


class EbayObject(object):
    def __init__(self, connection, params):
        self.connection = connection
        self.get_uuid = uuid.uuid4

    def build_request(self, action, params=None):
        return ''

    def call(self, action, params=None):
        core_request = self.build_request(action, params=params)
        print core_request
        # import pdb; pdb.set_trace()

        return self.connection.send_request(action, core_request)


class RecurringJob(EbayObject):
    def __init__(self, connection, params=None):
        super(RecurringJob, self).__init__(connection, params)
        self.recurrency={}
        self.allowable_jobTypes = ('ActiveInventoryReport', 'FeeSettlementReport', 'SoldReport')

    def build_request(self, action, params):
        '''
        This function builds the request string for the specifies 'action' api call
        '''

        request  = ""

        if action == 'deleteRecurringJob' :
            request += '<recurringJobId>%s</recurringJobId>' %params

        elif action == 'getRecurringJobExecutionHistory' :
            request += """
                <jobStatus>Completed</jobStatus>
                <recurringJobId>%s</recurringJobId>
                <startTime>%s</startTime>
                <endTime>%s</endTime>
            """%(params['jobId'], params['startTime'], params['endTime'])

        elif action == 'createRecurringJob' :
            if params['jobType'] in self.allowable_jobTypes:
                request += """
                    <downloadJobType>%s</downloadJobType>
                    <UUID>%s</UUID>
                """%(params['jobType'], self.get_uuid())

            recurrency_type = params['recurrency'].get('type')

            if recurrency_type == 'frequency':
                request += '<frequencyInMinutes>%s</frequencyInMinutes>' % params['recurrency']['time']

            elif recurrency_type == 'daily':
                request += """
                    <dailyRecurrence>
                        <timeOfDay>%s</timeOfDay>
                    </dailyRecurrence>
                """% params['recurrency']['time']

            elif recurrency_type == 'weekly':
                request += """
                    <weeklyRecurrence>
                        <dayOfWeek>%s</dayOfWeek>
                        <timeOfDay>%s</timeOfDay>
                    </weeklyRecurrence>
                """%(params['recurrency']['day'], params['recurrency']['time'])

            elif recurrency_type == 'monthly':
                request += """
                    <monthlyRecurrence>
                        <dayOfMonth>%s</dayOfMonth>
                        <timeOfDay>%s</timeOfDay>
                    </monthlyRecurrence>
                """%(params['recurrency']['day'], params['recurrency']['time'])

        return request

    def get(self, filter=None):
        if filter == 'history':
            return self.call('getRecurringJobExecutionHistory')
        else:
            tree = self.call('getRecurringJobs')
            if 'recurringJobDetail' in [e.tag for e in tree.getchildren()]:
                # print etree.tostring(tree, pretty_print=True)
                return self.call('getRecurringJobs').recurringJobDetail
            else:
                return False

    def delete(self, ebay_id):
        return self.call('deleteRecurringJob', ebay_id)

    def _check_recurrence_element(self, type_recurrence, period, timeMonth=None ):
        '''
        Args:
            type_recurrence(string): time/monthly/weekly
            period(string): eg : 08:00:18 (if time), Day_2 (if monthly), Monday (if weekly)

        '''

        if type_recurrence == 'time':
            try:
                if timeMonth:
                    time_sent = period
                    result = datetime.strptime(time_sent, '%H:%M:%S')
                else:
                    # add '.1Z' suffix to get the required full format '%H:%M:%S.%fZ' with only '%H:%M:%S' given
                    time_sent = period+'.1Z'
                    result = datetime.strptime(time_sent, '%H:%M:%S.%fZ')
            except ValueError:
                raise Exception( ">>> Given time %s is not in HH:MM:SS time format" % (period ) )
            result = time_sent

        elif type_recurrence == 'monthly':
            # Calendar creation except 29th, 30th day of the month
            tmp = list(range(1,29,1))
            month_days = ['Day_'+str(my_int) for my_int in tmp]
            month_days.append('Day_Last') # the last day of month

            if period not in month_days:
                raise Exception( ">>> Given month day '%s' must be choosen in \n%s" % (period, month_days) )
            result = period

        elif type_recurrence == 'weekly':
            week_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            period = period.capitalize()
            if period not in week_days:
                raise Exception( ">>> Given week day '%s' must be choosen in \n%s" % (period, week_days) )
            result = period
        else:
            raise Exception( ">>> Recurrency type '%s' has no defined treatment. Allowables type are : 'time', 'dayOfMonth' and 'dayOfWeek'" % (type_recurrence) )

        return result

    def _get_recurrence_params(self, timeOf='00:00:00', type_recurrence=None, dayOf=None ):
        '''

        '''

        if not type_recurrence:
            if isinstance(timeOf, int):
                return {'type': 'frequency','time': timeOf}
            else:
                return {'type': 'daily','time': self._check_recurrence_element('time', timeOf) }

        elif type_recurrence and dayOf:
            if type_recurrence == 'weekly':
                import pdb; pdb.set_trace()
                return {
                    'type': 'weekly',
                    'day': self._check_recurrence_element('weekly', dayOf),
                    'time': self._check_recurrence_element('time', timeOf),
                    }

            elif type_recurrence == 'monthly':
                return {
                    'type': 'monthly',
                    'day': self._check_recurrence_element('monthly', dayOf),
                    'time': self._check_recurrence_element('time', timeOf, True), # monthly 'time' has a different format
                    }
        else:
            raise Exception( ">>> 'dayOf' argument is not defined" )

    def create(self, params):
        '''
        vals={'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
            'type_recurrence': 'time' or 'monthly' or 'weekly'
            'time': int (minutes) or HH:MM:SS (hour),
            'day': 'Sunday' up to 'Saturday or Day_1, Day_2 up to Day_last
        }
        '''
        type_recurrence, day = None, None
        # import pdb; pdb.set_trace()
        if self.type_recurrence:
            type_recurrence = self.type_recurrence
        if self.day:
            day = self.day

        params['recurrency'] = self._get_recurrence_params(self.time, type_recurrence, day)

        tree = self.call('createRecurringJob', params)

        # if tree != False and 'recurringJobId' in [e.tag for e in tree.getchildren()]:
        if 'recurringJobId' in [e.tag for e in tree.getchildren()]:
            print etree.tostring(tree, pretty_print=True)
            return tree.recurringJobId
        else:
            return False

class Job(EbayObject):
    def get(self, filter=None):
        return self.connection.send_request('getJobs', self._core_request)


class Connection():
    '''

    '''
    def __init__(self, developer_key, application_key, certificate_key, auth_token,
                                            site_host=None, file_host=None, site_id=None):

        if not site_host:
            site_host = 'webservices.ebay.com'
        if not file_host:
            file_host = 'storage.ebay.com'
        if not site_id:
            site_id = 100

        self.developer_key = developer_key
        self.application_key = application_key
        self.certificate_key = certificate_key
        self.auth_token = auth_token
        self.site_host = site_host
        self.file_host = file_host
        self.site_id = site_id


    def _generate_headers(self, action, site_location):
        '''
        Creates the base headers that every request needs
        '''
        headers={}
        headers['X-EBAY-SOA-SECURITY-TOKEN'] = self.auth_token
        headers['Content-Type'] = 'text/xml'
        headers['X-EBAY-SOA-SERVICE-NAME'] = site_location
        headers['X-EBAY-SOA-OPERATION-NAME'] = action

        return headers


    def _complete_request(self, action, core_request):
        '''
        This function complete the build of the request string for the specified 'action' api call
        '''

        prefix  = """
                <?xml version="1.0" encoding="utf-8"?>
                <%sRequest xmlns="http://www.ebay.com/marketplace/services">
                """ % action
        suffix  = '</%sRequest>' % action

        return prefix + core_request + suffix


    def send_request(self, action, core_request, type_location='site'):
        '''
        Connects to eBay server, and HTTPS POSTs the request with the given headers
        Returns the response xml or an error message where appropriate
        '''

        # debug = False

        if type_location == 'file':
            site_location = 'FileTransferService'
        else:
            site_location = 'BulkDataExchangeService'

        request = self._complete_request(action, core_request)
        print request
        headers = self._generate_headers(action, site_location)

        # if debug == True:
            # print ' req', request
            # return False
        # else:
        connection = httplib.HTTPSConnection( self.site_host )

        connection.request( "POST", '/'+site_location, request, headers )

        response = connection.getresponse()

        if response.status != 200:
            raise Exception( "Error %s sending request: %s" % (response.status, response.reason ) )

        web_service_response = response.read()
        connection.close()

        # remove the chain that produces a poor display in the xml tree during subsequent processing
        web_service_response = web_service_response.replace(' xmlns="http://www.ebay.com/marketplace/services"','')

        #transform xml response in objectify xml object
        result = objectify.fromstring(web_service_response)
        # print etree.tostring(result, pretty_print=True)

        # Reads the response. If call is a failure raise an error
        # If call is a success return lxml objectify tree
        if result.ack == "Failure":
            raise EbayError(result)
        return result


class EbayWebService():

    def __init__(self, developer_key, application_key, certificate_key, auth_token,
                                            site_host=None,file_host=None, site_id=None):

        self.connection = Connection(developer_key, application_key, certificate_key,
                                                        auth_token, site_host, file_host, site_id)

    def get(self, ebay_object_name, params=None):
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.get(params)

    def create(self, ebay_object_name, params):
        '''
        params={'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
            'type_recurrence': 'time' or 'monthly' or 'weekly'
            'time': int (minutes) or HH:MM:SS (hour),
            'day': 'Sunday' up to 'Saturday' or 'Day_1' up to 'Day_2' or 'Day_Last'
        }
        '''
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.create(params)

    def delete(self, ebay_object_name, ebay_id):
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.delete(ebay_id)

    # def update(self, ebay_object_name, id, vals):
        # ebay_object = eval(ebay_object_name)(self.connection)
        # return ebay_object.update(filter)

# CreateUploadJob
# UploadFile
# StartUploadJob
# GetJobStatus
# AbortJob
# GetJobs
# DownloadFile
# StartDownloadJob
# CreateRecurringJob
# GetRecurringJobs
# GetRecurringJobExecutionHistory
# DeleteRecurringJob
