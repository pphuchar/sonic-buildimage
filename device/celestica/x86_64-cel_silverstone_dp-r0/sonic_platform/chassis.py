#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

try:
    import sys
    import re
    import os
    import subprocess
    import time
    import json
    from sonic_platform_base.chassis_base import ChassisBase
    from helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_FAN_TRAY = 7
NUM_FAN = 2
NUM_PSU = 2
NUM_THERMAL = 14
NUM_SFP = 30
NUM_COMPONENT = 5

QSFP_PORT_START = 1
QSFP_PORT_END = 24
OSFP_PORT_START = 25
OSFP_PORT_END = 30

IPMI_OEM_NETFN = "0x3A"
IPMI_GET_REBOOT_CAUSE = "0x03 0x00 0x01 0x06"
TLV_EEPROM_I2C_BUS = 0
TLV_EEPROM_I2C_ADDR = 56
PORT_INFO_PATH = "/sys/devices/platform/cls-xcvr"
PATH_INT_SYSFS = "{0}/{1}/interrupt"
PATH_INTMASK_SYSFS = "{0}/{1}/interrupt_mask"
PATH_PRS_SYSFS = "{0}/{1}/qsfp_modprsL"


class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        ChassisBase.__init__(self)
        self._api_helper = APIHelper()
        self.sfp_module_initialized = False
        self.__initialize_components()
        self.__initialize_eeprom()

        if not self._api_helper.is_host():
            self.__initialize_psu()
            self.__initialize_fan()
            self.__initialize_thermals()
            self.__initialize_interrupts()

    def __initialize_sfp(self):
        from sonic_platform.sfp import Sfp
        for index in range(0, NUM_SFP):
            sfp = Sfp(index)
            self._sfp_list.append(sfp)
        self.sfp_module_initialized = True

    def __initialize_psu(self):
        from sonic_platform.psu import Psu
        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)

    def __initialize_fan(self):
        from sonic_platform.fan import Fan
        for fant_index in range(0, NUM_FAN_TRAY):
            for fan_index in range(0, NUM_FAN):
                fan = Fan(fant_index, fan_index)
                self._fan_list.append(fan)

    def __initialize_thermals(self):
        from sonic_platform.thermal import Thermal
        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

    def __initialize_eeprom(self):
        from sonic_platform.eeprom import Eeprom
        self._eeprom = Eeprom(TLV_EEPROM_I2C_BUS, TLV_EEPROM_I2C_ADDR)

    def __initialize_components(self):
        from sonic_platform.component import Component
        for index in range(0, NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    def __initialize_interrupts(self):
        # Initial Interrup MASK for QSFP, QSFPDD
        sfp_info_obj = {}
        for index in range(NUM_SFP):
            port_num = index+1
            if port_num in range(QSFP_PORT_START, QSFP_PORT_END+1):
                port_name = "QSFP{}".format(
                    str(port_num - QSFP_PORT_START + 1))
            elif port_num in range(OSFP_PORT_START, OSFP_PORT_END+1):
                port_name = "QSFPDD{}".format(
                    str(port_num - OSFP_PORT_START + 1))

            sfp_info_obj[index] = {}
            sfp_info_obj[index]['intmask_sysfs'] = PATH_INTMASK_SYSFS.format(
                PORT_INFO_PATH, port_name)
            sfp_info_obj[index]['int_sysfs'] = PATH_INT_SYSFS.format(
                PORT_INFO_PATH, port_name)
            sfp_info_obj[index]['prs_sysfs'] = PATH_PRS_SYSFS.format(
                PORT_INFO_PATH, port_name)

            self._api_helper.write_hex_value(
                sfp_info_obj[index]["intmask_sysfs"], 255)

        self.sfp_info_obj = sfp_info_obj

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis
        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.get_mac()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis
        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.get_serial()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.get_eeprom()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """

        status, raw_cause = self._api_helper.ipmi_raw(
            IPMI_OEM_NETFN, IPMI_GET_REBOOT_CAUSE)
        hx_cause = raw_cause.split()[0] if status and len(
            raw_cause.split()) > 0 else 00
        reboot_cause = {
            "00": self.REBOOT_CAUSE_HARDWARE_OTHER,
            "11": self.REBOOT_CAUSE_POWER_LOSS,
            "22": self.REBOOT_CAUSE_NON_HARDWARE,
            "33": self.REBOOT_CAUSE_HARDWARE_OTHER,
            "44": self.REBOOT_CAUSE_NON_HARDWARE,
            "55": self.REBOOT_CAUSE_NON_HARDWARE,
            "66": self.REBOOT_CAUSE_WATCHDOG,
            "77": self.REBOOT_CAUSE_NON_HARDWARE
        }.get(hx_cause, self.REBOOT_CAUSE_HARDWARE_OTHER)

        description = {
            "00": "Unknown reason",
            "11": "The last reset is Power on reset",
            "22": "The last reset is soft-set CPU warm reset",
            "33": "The last reset is soft-set CPU cold reset",
            "44": "The last reset is CPU warm reset",
            "55": "The last reset is CPU cold reset",
            "66": "The last reset is watchdog reset",
            "77": "The last reset is power cycle reset"
        }.get(hx_cause, "Unknown reason")

        return (reboot_cause, description)

    ##############################################################
    ######################## SFP methods #########################
    ##############################################################

    def get_num_sfps(self):
        """
        Retrieves the number of sfps available on this chassis
        Returns:
            An integer, the number of sfps available on this chassis
        """
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        return len(self._sfp_list)

    def get_all_sfps(self):
        """
        Retrieves all sfps available on this chassis
        Returns:
            A list of objects derived from SfpBase representing all sfps
            available on this chassis
        """
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        return self._sfp_list

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of a physical port in a chassis,
            starting from 1.
            For example, 1 for Ethernet0, 2 for Ethernet4 and so on.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        try:
            # The index will start from 1
            sfp = self._sfp_list[index-1]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (1-{})\n".format(
                             index, len(self._sfp_list)))
        return sfp

    ##############################################################
    ####################### Other methods ########################
    ##############################################################

    def get_watchdog(self):
        """
        Retreives hardware watchdog device on this chassis
        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device
        """
        if self._watchdog is None:
            from sonic_platform.watchdog import Watchdog
            self._watchdog = Watchdog()

        return self._watchdog

    ##############################################################
    ###################### Device methods ########################
    ##############################################################

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return self._api_helper.hwsku

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        return self._eeprom.get_pn()

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return self.get_serial_number()

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

    ##############################################################
    ###################### Event methods ########################
    ##############################################################
    def __clear_interrupt(self, port_idx):
        int_path = self.sfp_info_obj[port_idx]["int_sysfs"]
        self._api_helper.write_hex_value(int_path, 255)
        time.sleep(0.5)
        self._api_helper.write_hex_value(int_path, 0)
        return self._api_helper.read_txt_file(int_path)

    def __check_devices_status(self, port_idx):
        prs_path = self.sfp_info_obj[port_idx]["prs_sysfs"]
        return self._api_helper.read_txt_file(prs_path)

    def __compare_event_object(self, interrup_devices):
        devices = {}
        event_obj = {}
        for port_idx in interrup_devices:
            devices[port_idx] = 1 - \
                int(self.__check_devices_status(port_idx))
            self.__clear_interrupt(port_idx)

        if len(devices):
            event_obj['sfp'] = devices

        return json.dumps(event_obj)

    def __check_all_interrupt_event(self):
        interrupt_device = {}
        for i in range(NUM_SFP):
            int_sysfs = self.sfp_info_obj[i]["int_sysfs"]
            if self._api_helper.read_txt_file(int_sysfs) != '0x00':
                interrupt_device[i] = 1
        return interrupt_device

    def get_change_event(self, timeout=0):
        if timeout == 0:
            flag_change = True
            while flag_change:
                interrup_device = self.__check_all_interrupt_event()
                if len(interrup_device):
                    flag_change = False
                else:
                    time.sleep(0.5)
            return (True, self.__compare_event_object(interrup_device))
        else:
            device_list_change = {}
            while timeout:
                interrup_device = self.__check_all_interrupt_event()
                time.sleep(1)
                timeout -= 1
            device_list_change = self.__compare_event_object(interrup_device)
            return (True, device_list_change)
