#!/usr/bin/env python

#############################################################################
# Celestica
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import re
import os.path

try:
    from sonic_platform_base.thermal_base import ThermalBase
    from helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

IPMI_SENSOR_NETFN = "0x04"
IPMI_SS_READ_CMD = "0x2D {}"
IPMI_SS_THRESHOLD_CMD = "0x27 {}"
IPMI_SS_STATUS = "0x2B {}"
DEFUALT_LOWER_TRESHOLD = 0.0
HIGH_TRESHOLD_SET_KEY = "unc"
NULL_VAL = "N/A"


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    def __init__(self, thermal_index):
        ThermalBase.__init__(self)
        self._api_helper = APIHelper()
        self.index = thermal_index
        self.THERMAL_LIST = [
            ('TEMP_FAN_U52',        'Fan Tray Middle Temperature Sensor',           '0x00'),
            ('TEMP_FAN_U17',        'Fan Tray Right Temperature Sensor',            '0x01'),
            ('TEMP_SW_U52',         'Switchboard Left Inlet Temperature Sensor',    '0x02'),
            ('TEMP_SW_U16',         'Switchboard Right Inlet Temperature Sensor',   '0x03'),
            ('TEMP_BB_U3',          'Baseboard Temperature Sensor',                 '0x04'),
            ('TEMP_CPU',            'CPU Internal Temperature Sensor',              '0x05'),
            ('PSU1_Temp1',          'PSU1 Internal Temperature Sensor',             '0x34'),
            ('PSU1_Temp2',          'PSU1 Internal Temperature Sensor',             '0x35'),
            ('PSU2_Temp1',          'PSU2 Internal Temperature Sensor',             '0x3e'),
            ('PSU2_Temp2',          'PSU2 Internal Temperature Sensor',             '0x3f'),
            ('SW_U45_Temp',         'IR35215 Chip Temperature Sensor',              '0x4F'),
            ('SW_U72_Temp',         'IR35215 Chip Temperature Sensor',              '0x56'),
            ('SW_U87_Temp',         'IR35215 Chip Temperature Sensor',              '0x5D'),
            ('TEMP_SW_Internal',    'ASIC Internal Temperature Sensor',             '0x61')
        ]
        self.sensor_id = self.THERMAL_LIST[self.index][0]
        self.sensor_des = self.THERMAL_LIST[self.index][1]
        self.sensor_reading_addr = self.THERMAL_LIST[self.index][2]

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """
        temperature = NULL_VAL
        status, raw_ss_read = self._api_helper.ipmi_raw(
            IPMI_SENSOR_NETFN, IPMI_SS_READ_CMD.format(self.sensor_reading_addr))
        if status and len(raw_ss_read.split()) > 0:
            ss_read = raw_ss_read.split()[0]
            temperature = float(int(ss_read, 16))
        return temperature

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        high_threshold = NULL_VAL
        status, raw_up_thres_read = self._api_helper.ipmi_raw(
            IPMI_SENSOR_NETFN, IPMI_SS_THRESHOLD_CMD.format(self.sensor_reading_addr))
        if status and len(raw_up_thres_read.split()) > 6:
            ss_read = raw_up_thres_read.split()[4]
            high_threshold = float(int(ss_read, 16))
        return high_threshold

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal
        Returns:
            A float number, the low threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return NULL_VAL

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal
        Args : 
            temperature: A float number up to nearest thousandth of one degree Celsius, 
            e.g. 30.125
        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        status, ret_txt = self._api_helper.ipmi_set_ss_thres(
            self.sensor_id, HIGH_TRESHOLD_SET_KEY, temperature)
        return status

    def set_low_threshold(self, temperature):
        """
        Sets the low threshold temperature of thermal
        Args : 
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125
        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        return False

    ##############################################################
    ###################### Device methods ########################
    ##############################################################

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        return self.THERMAL_LIST[self.index][0]

    def get_presence(self):
        """
        Retrieves the presence of the device
        Returns:
            bool: True if device is present, False if not
        """
        return True if self.get_temperature() > 0 else False

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        return self.sensor_des

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return NULL_VAL

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        ss_status = False
        status, raw_ss_read = self._api_helper.ipmi_raw(
            IPMI_SENSOR_NETFN, IPMI_SS_STATUS.format(self.sensor_reading_addr))
        if status and len(raw_ss_read.split()) > 0:
            status_event_read = raw_ss_read.split()
            del status_event_read[0]
            ss_status = True if all(
                x == '00' for x in status_event_read) else False
        return ss_status
