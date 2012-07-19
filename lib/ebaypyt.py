#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   ebaypyt                                                                   #
#                                                                             #
#   Copyright (C) 2012 Akretion Sébastien BEAU <sebastien.beau@akretion.com>  #
#                               David BEAL <david.beal@akretion.com>          #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
"""
    Ebay-py is a library for Python to interact with the Ebay's Web Service APIS.

    Credits :
    Thanks to Wesley Hansen for eBay-LMS-APIS
    (https://github.com/wrhansen/eBay-LMS-APIS)
    from which I also inspired my library.
"""

__author__ = "Sébastien BEAU / David BEAL"
__date__ = "2012-07-17"

import httplib
import uuid
import zipfile
import tempfile
from datetime import date, datetime, timedelta
from lxml import etree
from lxml import objectify

ALLOWABLE_JOB_TYPES = ('ActiveInventoryReport', 'SoldReport')
# Documentation define another report but api alerts "JobType 'FeeSettlementReport' is unsupported"
ALLOWABLE_JOB_STATUS = ('Aborted', 'Completed', 'Created', 'Failed', 'InProcess', 'Scheduled')

APIS = {'api': {'host': 'api.ebay.com', 'location': 'ws/api.dll'} ,
    'web': {'host': 'webservices.ebay.com', 'location': 'BulkDataExchangeService'} ,
    'file': {'host': 'storage.ebay.com', 'location': 'FileTransferService'} ,
    }

SUCCESS_TAG = {'api':'Ack', 'web': 'ack', 'file': 'ack'}

APIS_COMPATIBILITY_LEVEL = 781

ZULU_STRING = 'T00:00:00Z'

HISTORIC_DAYS_MAX = 27

def objectify_to_dict(xml_objectify, cast_fields=None, useless_key=None):
    '''
        :params xml_objectify objectity: an objectify object that represente an xml
        :params cast_fields dict: dictionnary that can force the type of each value return
        :params useless_key list: if a parent key is in this list and if this parent key have
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
                if cast_fields[key] == str :
                    result[key] = cast_fields.get(key)(xml_objectify.__dict__[key].text)
                else:
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
         return repr(self.error_message) + ', Error number:' + repr(self.error_id)


class EbayObject(object):
    """ Generic object for ebay access """
    def __init__(self, connection, params):
        self.connection = connection
        self.unique_execution_ID = uuid.uuid4()
        # self.params = params

    def _update_params_value(self, key, new_value):
        """
        Modify self.params dict
        :param str key: self.params key
        :param str new_value: value to insert in self.params if key exists
        :rtype: None
        :return: None
        """
        value = self.params.get(key, None)
        if value:
            self.params[key] = new_value

    def build_xml_tag(self, tag, mandatory=False, allowables=None, default=None):
        """
        Build a complete xml tag : <my_tag>my_value</my_tag>
        :param str tag: xml tag
        :param boolean mandatory: indicate if tag must be generate
        :param list allowables: list of allowed values
        :param str default: default value if not exist in self.params
        :rtype: str
        :return: xml completed tag
        """
        value = self.params.get(tag, None)
        if mandatory == True and not value:
            if default:
                value = default
            else:
                raise Exception("Missing '%s' tag. It is a mandatory tag for this xml api call, please add it to provided parameters" % tag)
        if value:
            if allowables and value not in allowables:
                raise Exception("'%s' is not correct : use one of these values %s" % \
                                                                        (value, str(allowables)))
            return '\n\t<%s>%s</%s>' % (tag, value, tag)
        else:
            return ''

    def build_request(self, action, params=None):
        """
        This function builds the request string for the specifies 'action' api call
        USE IT in each child class
        :param str action: action name request
        :param dict params: parameters needed to build specific request
        :rtype: str
        :return: body of the request
        """
        return ''

    def call(self, action, api, params=None):
        """
        Generics processing for all chidren object
        USE IT in each child class
        :param str action: processing type to execute
        :param dict params: parameters used to build xml request
        :rtype: str
        :return: specfic xml string used to build request
        """
        core_request = self.build_request(action, params=params)
        return self.connection.web_service_processing(action, core_request, api=api)

    def download(self, params):
        print "'download' method should be only used with 'Job' object "

    def create(self, params):
        print "'create' method should be only used with 'RecurringJob' object "

    def get(self, web_service_request, api, xml_tag, params=None):
        """
        method to access informations about object with web service
        :param str web_service_request: request name
        :param str api: api type used by this api call service
        :param str xml_tag: xml response's tag inside is the main useful information
        :rtype: dict
        :return: web service response in a dictionary
        """
        tree = self.call(web_service_request, api, params=params)

        if xml_tag in [e.tag for e in tree.getchildren()]:
            xml_dict = objectify_to_dict(tree, {xml_tag: list})
            return xml_dict[xml_tag]
        else:
            return False


class RecurringJob(EbayObject):
    """ Tasks management of recurring/cron tasks defined with ebay """
    def __init__(self, connection, params=None):
        super(RecurringJob, self).__init__(connection, params)
        self.recurrency={}

    def build_request(self, action, params):
        ''' see EbayObject.build_request() docstring '''

        request  = ""
        self.params = params

        if action == 'deleteRecurringJob' :
            request += """
    <recurringJobId>%s</recurringJobId>""" %params

        elif action == 'createRecurringJob' :
            request += """
    <UUID>%s</UUID>""" % self.unique_execution_ID
            request += self.build_xml_tag('jobType', allowables=ALLOWABLE_JOB_TYPES)

            recurrency_type = params['recurrency'].get('type')

            if recurrency_type == 'frequency':
                request += '''
    <frequencyInMinutes>%s</frequencyInMinutes>''' % params['recurrency']['time']

            elif recurrency_type == 'daily':
                request += """
    <dailyRecurrence>
        <timeOfDay>%s</timeOfDay>
    </dailyRecurrence>"""% params['recurrency']['time']

            elif recurrency_type == 'weekly':
                request += """
    <weeklyRecurrence>
        <dayOfWeek>%s</dayOfWeek>
        <timeOfDay>%s</timeOfDay>
    </weeklyRecurrence>"""%(params['recurrency']['day'], params['recurrency']['time'])

            elif recurrency_type == 'monthly':
                request += """
    <monthlyRecurrence>
        <dayOfMonth>%s</dayOfMonth>
        <timeOfDay>%s</timeOfDay>
    </monthlyRecurrence>"""%(params['recurrency']['day'], params['recurrency']['time'])

        return request

    def get(self, filter=None):
        response = super(RecurringJob, self).get('getRecurringJobs', 'web', 'recurringJobDetail')
        if response != False:
            response = response[0]
        return response

    def delete(self, ebay_id):
        return self.call('deleteRecurringJob', 'web', ebay_id)

    def _check_recurrence_element(self, type_recurrence, period, timeMonth=None ):
        """
        Complete parameters provided and valid them
        :param str type_recurrence: time/monthly/weekly
        :param str period: eg : 08:00:18 (if time), Day_2 (if monthly), Monday (if weekly)
        :param boolean timeMonth: define monthly time with a different format than others
        :rtype: str
        :return: valid datas to build web services strings
        """

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
            raise Exception( ">>> Recurrency type '%s' has no defined processing. Allowables type are : 'time', 'dayOfMonth' and 'dayOfWeek'" % (type_recurrence) )

        return result

    def _get_recurrence_params(self, timeOf='00:00:00', type_recurrence=None, dayOf=None ):
        """

        :param str timeOf: minutes or hour/minute/second
        :param str type_recurrence: None/Weekly/Monthly
        :rtype: dict
        :return: well formed elements to build xml reccuring job request
        """

        if not type_recurrence:
            if isinstance(timeOf, int):
                return {'type': 'frequency','time': timeOf}
            else:
                return {'type': 'daily','time': self._check_recurrence_element('time', timeOf) }

        elif type_recurrence and dayOf:
            if type_recurrence == 'weekly':
                return {
                    'type': 'weekly',
                    'day': self._check_recurrence_element('weekly', dayOf),
                    'time': self._check_recurrence_element('time', timeOf),
                    }

            elif type_recurrence == 'monthly':
                return {
                    'type': 'monthly',
                    'day': self._check_recurrence_element('monthly', dayOf),
                    # monthly 'time' has a different format
                    'time': self._check_recurrence_element('time', timeOf, True),
                    }
        else:
            raise Exception( ">>> 'dayOf' argument is not defined" )

    def create(self, params):
        """
        RecurringJob creation
        :param dict params: example
            vals={'jobType': 'ActiveInventoryReport' / 'SoldReport',
                'type_recurrence': 'time' or 'monthly' or 'weekly'
                'time': int (minutes) or HH:MM:SS (hour),
                'day': 'Sunday' up to 'Saturday or Day_1, Day_2 up to Day_last
            }
        :rtype: str
        :return: RecurringJob number
        """
        type_recurrence, day = None, None

        if params.get('type_recurrence'):
            type_recurrence = params.get('type_recurrence')
        if params.get('day'):
            day = params.get('day')

        params['recurrency'] = self._get_recurrence_params(params.get('time'), type_recurrence, day)

        tree = self.call('createRecurringJob', 'web', params)

        if 'recurringJobId' in [e.tag for e in tree.getchildren()]:
            return tree.recurringJobId.text
        else:
            return False

class Job(EbayObject):
    """ Accessing 'jobs' defined in RecurringJob class """
    def __init__(self, connection, params=None):
        super(Job, self).__init__(connection, params)

    def build_request(self, action, params):
        """ see EbayObject.build_request() docstring """
        request  = ""
        self.params = params

        if action == 'downloadFile':
            request += self.build_xml_tag('taskReferenceId', mandatory=True)
            request += self.build_xml_tag('fileReferenceId', mandatory=True)

        elif action == 'getJobs':
            request += self.build_xml_tag('jobType', allowables=ALLOWABLE_JOB_TYPES)
            request += self.build_xml_tag('jobStatus', allowables=ALLOWABLE_JOB_STATUS)

            param_key = 'creationTimeFrom'

            # check params[param_key]
            new_value = self.params.get(param_key)
            if not new_value:
                new_value, self.params[param_key] = str(HISTORIC_DAYS_MAX), str(HISTORIC_DAYS_MAX)
            else:
                new_value = str(new_value)
            if new_value.isdigit() and int(new_value) > 0 and int(new_value) <= HISTORIC_DAYS_MAX:
                new_value = int(new_value)
            else:
                raise Exception("parameter '%s' = %s is not valid a number of days (between 1 and %s). Please modify it" % \
                                                    (param_key, new_value, HISTORIC_DAYS_MAX))

            # transform number of days in datetime UTC
            new_value = (date.today() + \
                timedelta(-int(self.params[param_key]))).isoformat() + ZULU_STRING
            self.params[param_key] = new_value

            request += self.build_xml_tag(param_key)

        return request

    def download(self, params):
        """
        Download file report
        :param dict params: {'taskReferenceId': '5...', 'fileReferenceId': '5...'}
        :rtype: str
        :return: xml string
        """
        return self.call('downloadFile', 'file', params)

    def get(self, params=None):
        return super(Job, self).get('getJobs', 'web', 'jobProfile', params)


class Product(EbayObject):
    """
    Trading Api use : only GetItem for now
    """

    def __init__(self, connection, params=None):
        super(Product, self).__init__(connection, params)

    # def message_except(self, attr):
        # return ">>> Missing %s key to build xml request " % (attr)

    def build_request(self, action, params):
        """ see EbayObject.build_request() docstring """

        request = ""
        self.params = params

        if action == 'GetItem':
            request += self.build_xml_tag('ItemID', True)
            # mandatory_attr = 'ItemID'
            # if not params.get(mandatory_attr) :
                # raise Exception( self.message_except(mandatory_attr) )

            # for attr in [mandatory_attr, 'DetailLevel']:
                # if params.get(attr) :
                    # request += '\n\t<%(attr)s>%(attr_id)s</%(attr)s>' % \
                                                            # {'attr': attr, 'attr_id': params[attr]}

            request += '''
    <RequesterCredentials>
        <eBayAuthToken>%s</eBayAuthToken>
    </RequesterCredentials>
    <WarningLevel>High</WarningLevel>''' % self.connection.auth_token

        return request

    def get(self, params=None):
        """
        GetItem implementation
        :param dict params: {'ItemID': '123456789...', 'DetailLevel': 'ItemReturnAttributes'}
        :rtype: dict
        :return: informations about the product
        """
        return super(Product, self).get('GetItem', 'api', 'Item', params)


class Communication():
    """ Generic class to :
        - Final request preparation
        - sending request
        - decoding web service response
    """
    def __init__(self, developer_key, application_key, certificate_key, auth_token,
                                                        site_id=None, compatibility=None):
        if not site_id:
            site_id = 0
        if not compatibility:
            compatibility = 781

        self.developer_key = developer_key
        self.application_key = application_key
        self.certificate_key = certificate_key
        self.auth_token = auth_token
        self.site_id = site_id
        self.compatibility = compatibility


    def _generate_headers(self, action, service_location, api):
        """
        Creates headers to each request
        :param str action: processing type to execute
        :param str service_location: web service location
        :param str api: api type used by this api call service
        :rtype: dict
        :return: dictionnay with all the header keys
        """

        headers={}
        headers['Content-Type'] = 'text/xml'

        if api == 'api':
            headers['X-EBAY-API-COMPATIBILITY-LEVEL'] = APIS_COMPATIBILITY_LEVEL
            headers['X-EBAY-API-DEV-NAME'] = self.developer_key
            headers['X-EBAY-API-APP-NAME'] = self.application_key
            headers['X-EBAY-API-CERT-NAME'] = self.certificate_key
            headers['X-EBAY-API-SITEID'] = self.site_id
            headers['X-EBAY-API-CALL-NAME'] = action
        else:
            headers['X-EBAY-SOA-SECURITY-TOKEN'] = self.auth_token
            headers['X-EBAY-SOA-SERVICE-NAME'] = service_location
            headers['X-EBAY-SOA-OPERATION-NAME'] = action

        return headers


    def _complete_request(self, action, core_request, api):
        """
        This function complete the build of the request string for the specified 'action' api call
        :param str action: processing type to execute
        :param str core_request: body of the request
        :param str api: api type used by this api call service
        :rtype: str
        :return: xml well formed request string
        """
        # LMS APIS
        self.xlmns = 'http://www.ebay.com/marketplace/services'

        # Trading APIS case
        if api == 'api':
            self.xlmns = 'urn:ebay:apis:eBLBaseComponents'

        prefix  = '<?xml version="1.0" encoding="utf-8"?>\n<%sRequest xmlns="%s">' % (action, self.xlmns)
        suffix  = '\n</%sRequest>' % action

        return prefix + core_request + suffix


    def _parse_download(self):
        """
        Parses the response string returned by the eBay server and extract xml response the information
        into two parts: the xml response part and zipfile part
        :rtype: str
        :return: xml string
        """

        start_xml = self.web_service_response.find( '<?xml')
        end_xml = self.web_service_response.find( '--MIME', start_xml)

        self.xml_response_download = self.web_service_response[start_xml:end_xml]

        #Find boundary string
        boundary = self.web_service_response.splitlines()[0]

        #Find the ending boundary index
        find = self.web_service_response.find( "Content-ID:" )

        find = self.web_service_response.find( '\r\n', find )

        #Find start of middle boundary
        middle_boundary = self.web_service_response.find( boundary, find )

        #XML response from downloadFile
        response = self.web_service_response[find:middle_boundary].strip()
        #Find next boundary
        find = self.web_service_response.find( "Content-ID:", middle_boundary )
        find = self.web_service_response.find( '\r\n', find )
        find_end = self.web_service_response.find( boundary, find )

        #Extract the compressed data
        binary_datas = self.web_service_response[find:find_end]

        temp=tempfile.TemporaryFile('w+b', -1, '.zip')
        temp.write(binary_datas)
        temp.seek(0)
        my_file = zipfile.ZipFile(temp, 'r')

        datas = ''
        for name in my_file.namelist():
            datas = my_file.read(name).strip()

        return datas


    def web_service_processing(self, action, core_request, api):
        """
        Connects to eBay server, and HTTPS POSTs the request with the given headers
        :param str action: processing type to execute
        :param str core_request: body of the request
        :rtype: objectify or xml
        :return: xml string if 'downloadFile' action or lxml.objectify xml response
        """

        request = self._complete_request(action, core_request, api)

        headers = self._generate_headers(action, APIS[api]['location'], api)

        connection = httplib.HTTPSConnection(APIS[api]['host'])

        connection.request( "POST", '/'+APIS[api]['location'], request, headers )
        response = connection.getresponse()

        if response.status != 200:
            raise Exception( "Error %s sending request: %s" % (response.status, response.reason ) )

        self.web_service_response = response.read()
        connection.close()

        # remove the chain that produces a poor display in the xml tree during subsequent processing
        self.web_service_response = self.web_service_response.replace(' xmlns="'+ self.xlmns +'"','')

        if api != 'file':
            #transform xml response in objectify xml object
            result = objectify.fromstring(self.web_service_response)

            # Reads the response. If call is a failure raise an error
            # If call is a success return lxml objectify tree
            if (result.__dict__[SUCCESS_TAG[api]] == "Failure"):
                raise EbayError(result)
        else:
            # if self.web_service_response contains download datas file
            result = self._parse_download()
            xml_objectify = objectify.fromstring(self.xml_response_download)

            if xml_objectify.__dict__[SUCCESS_TAG[api]] == "Failure":
                raise EbayError(xml_objectify)

        return result


class EbayWebService():

    def __init__(self, developer_key, application_key, certificate_key, auth_token
                                                                            , site_id=None):

        self.connection = Communication(developer_key, application_key, certificate_key,
                                                        auth_token, site_id)

    def get(self, ebay_object_name, params=None):
        return eval(ebay_object_name)(self.connection).get(params)

    def download(self, ebay_object_name, params=None):
        return eval(ebay_object_name)(self.connection).download(params)

    def create(self, ebay_object_name, params):
        return eval(ebay_object_name)(self.connection).create(params)

    def delete(self, ebay_object_name, ebay_id):
        return eval(ebay_object_name)(self.connection).delete(ebay_id)

    # def search(self, ebay_object_name, params=None):
        # return eval(ebay_object_name)(self.connection).search(params)

    # def update(self, ebay_object_name, id, vals):
        # return eval(ebay_object_name)(self.connection).update(filter)


