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

from datetime import date
from lxml import etree
from lxml import objectify

sys.path.append('/home/dav/dvp/py/lib')
import dav


class EbayError(Exception):
     def __init__(self, objectify_value):
         self.error_id = objectify_value.errorMessage.error.errorId
         self.error_message = objectify_value.errorMessage.error.message

     def __str__(self):
         return repr(self.error_message)


class EbayObject(object):
    def __init__(self, connection):
        # print self
        self.connection = connection
        self._core_request = ''
        self.uuid = uuid.uuid4()
        self.allowable_jobTypes = ('ActiveInventoryReport', 'FeeSettlementReport', 'SoldReport')

class RecurringJob(EbayObject):
    def __init__(self,connection):
        super(RecurringJob, self).__init__(connection)
        self.recurrency={}
        self.jobId = ''

    def _modify_core_request(self, action ):
        '''
        This function builds the request string for the specifies 'action' api call
        '''

        request  = self._core_request

        if action == 'deleteRecurringJob' :
            request += '<recurringJobId>%s</recurringJobId>\r\n' % self.jobId

        if action == 'getRecurringJobExecutionHistory' :
            request += '<jobStatus>Completed</jobStatus>\r\n'
            request += '<recurringJobId>%s</recurringJobId>\r\n' % self.jobId
            request += '<startTime>%s</startTime>\r\n' % startTime
            request += '<endTime>%s</endTime>\r\n' % endTime

        if action == 'createRecurringJob' :
            if self.jobType in self.allowable_jobTypes:
                request += '\t<downloadJobType>%s</downloadJobType>\r\n' % self.jobType
                request += '\t<UUID>%s</UUID>\r\n' % self.uuid

            if self.recurrency.get('type',{}) == 'frequency':
                request += '\t<frequencyInMinutes>%s</frequencyInMinutes>\r\n' % self.recurrency['time']

            if self.recurrency.get('type',{}) == 'daily':
                request += '\t<dailyRecurrence>\r\n'
                request += '\t\t<timeOfDay>%s</timeOfDay>\r\n' % self.recurrency['time']
                request += '\t</dailyRecurrence>\r\n'

            if self.recurrency.get('type',{}) == 'weekly':
                request += '\t<weeklyRecurrence>\r\n'
                request += '\t\t<dayOfWeek>%s</dayOfWeek>\r\n' % self.recurrency['day']
                request += '\t\t<timeOfDay>%s</timeOfDay>\r\n' % self.recurrency['time']
                request += '\t</weeklyRecurrence>\r\n'

            if self.recurrency.get('type',{}) == 'monthly':
                request += '\t<monthlyRecurrence>\r\n'
                request += '\t\t<dayOfMonth>%s</dayOfMonth>\r\n' % self.recurrency['day']
                request += '\t\t<timeOfDay>%s</timeOfDay>\r\n' % self.recurrency['time']
                request += '\t</monthlyRecurrence>\r\n'

        self._core_request = request

    def get(self, filter=None):
        if filter == 'history':
            return self.connection.send_request('getRecurringJobExecutionHistory', self._core_request)
        else:
            return self.connection.send_request('getRecurringJobs', self._core_request)

    def delete(self, id):
        self._modify_core_request('deleteRecurringJob')


    def _check_recurrence_element( self, type_recurrence, period, timeMonth=None ):
        '''
        Args:
            type_recurrence(string): time/monthly/weekly
            period(string): eg : 08:00:18 (if time), Day_2 (if monthly), Monday (if weekly)

        '''

        if type_recurrence == 'time':
            try:
                if timeMonth:
                    time_sent = period
                    result = time.strptime(time_sent, '%H:%M:%S')
                else:
                    # add '.1Z' suffix to get the required full format '%H:%M:%S.%fZ' with only '%H:%M:%S' given
                    time_sent = period+'.1Z'
                    result = time.strptime(time_sent, '%H:%M:%S.%fZ')
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

        # frequency and recurrency are incompatible
        self.frequency = None
        return result

    def _set_recurrence( self, timeOf='00:00:00', type_recurrence=None, dayOf=None ):
        '''

        '''
        self.recurrency={}

        if not type_recurrence:
            if isinstance(timeOf, int):
                self.recurrency = {'type': 'frequency','time': timeOf}
            else:
                self.recurrency = {'type': 'daily','time': self._check_recurrence_element('time', timeOf) }

        elif type_recurrence and dayOf:
            if type_recurrence == 'weekly':
                self.recurrency = {'type': 'weekly','day': self._check_recurrence_element('weekly', dayOf) }
                self.recurrency['time'] = self._check_recurrence_element('time', timeOf)

            if type_recurrence == 'monthly':
                self.recurrency = {'type': 'monthly','day': self._check_recurrence_element('monthly', dayOf) }
                self.recurrency['time'] = self._check_recurrence_element('time', timeOf, True) # monthly 'time' has a different format

        else:
            raise Exception( ">>> 'dayOf' argument is not defined" )

    def create(self, vals):
        '''
        vals={'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
            'type_recurrence': 'time' or 'monthly' or 'weekly'
            'time': int (minutes) or HH:MM:SS (hour),
            'day': 'Sunday' up to 'Saturday or Day_1, Day_2 up to Day_last
        }
        '''
        if vals['jobType']:
            self.jobType = vals['jobType']
        type_recurrence, day = None, None

        # type_recurrence = vals.get('type_recurrence',None)
        # day = vals.get('day',None)

        self._set_recurrence(vals['time'], type_recurrence, day)

        self._modify_core_request('createRecurringJob')


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


    def _generate_headers(self, auth_token, action, site_location):
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

        prefix  = '<?xml version="1.0" encoding="utf-8"?>\r\n'
        prefix += '<%sRequest xmlns="http://www.ebay.com/marketplace/services">\r\n' % action
        suffix  = '</%sRequest>\r\n' % action

        return prefix + core_request + suffix


    def send_request(self, action, core_request, type_location='site'):
        '''
        Connects to eBay server, and HTTPS POSTs the request with the given headers
        Returns the response xml or an error message where appropriate
        '''

        if type_location == 'file':
            site_location = 'FileTransferService'
        else:
            site_location = 'BulkDataExchangeService'

        request = self._complete_request(action, core_request)
        headers = self._generate_headers(self.auth_token, action, site_location)

        connection = httplib.HTTPSConnection( self.site_host )

        dav.ecrire("POST/" + site_location, 'pyt')
        dav.ecrire('  req' + str(type(request))+str(request), 'pyt')
        dav.ecrire('  head' + str(headers), 'pyt')

        connection.request( "POST", '/'+site_location, request, headers )
        # print '\nreq', request

        response = connection.getresponse()

        if response.status != 200:
            raise Exception( "Error %s sending request: %s" % (response.status, response.reason ) )

        web_service_response = response.read()
        connection.close()

        # remove the chain that produces a poor display in the xml tree during subsequent processing
        web_service_response = web_service_response.replace(' xmlns="http://www.ebay.com/marketplace/services"','')
        #transform xml response in objectify xml object
        result = objectify.fromstring(web_service_response)

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

    def get(self, ebay_object_name, filter=None):
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.get(filter)

    def create(self, ebay_object_name, vals):
        '''
        vals={'jobType': 'ActiveInventoryReport' / 'FeeSettlementReport' / 'SoldReport',
            'type_recurrence': 'time' or 'monthly' or 'weekly'
            'time': int (minutes) or HH:MM:SS (hour),
            'day': 'Sunday' up to 'Saturday' or 'Day_1' up to 'Day_2' or 'Day_Last'
        }
        '''
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.create(vals)

    def delete(self, ebay_object_name, job_id):
        ebay_object = eval(ebay_object_name)(self.connection)
        return ebay_object.delete(id)


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

