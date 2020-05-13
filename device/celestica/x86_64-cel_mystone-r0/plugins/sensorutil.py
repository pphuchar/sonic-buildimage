#!/usr/bin/env python

__author__ = 'Wirut G.<wgetbumr@celestica.com>'
__license__ = "GPL"
__version__ = "0.2.0"
__status__ = "Development"

import requests


class SensorUtil():
    """Platform-specific SensorUtil class"""

    def __init__(self):
        self.sensor_url = "http://240.1.1.1:8080/api/sys/sensors"
        self.sys_fruid_url = "http://240.1.1.1:8080/api/sys/fruid/sys"
        self.sensor_info_list = None

    def request_data(self):
        # Reqest data from BMC if not exist.
        if self.sensor_info_list is None:
            sensor_data_req = requests.get(self.sensor_url)
            sensor_json = sensor_data_req.json()
            self.sensor_info_list = sensor_json.get('Information')
            sys_fruid_req = requests.get(self.sys_fruid_url)
            sys_fruid_json = sys_fruid_req.json()
            self.sys_fruid_list = sys_fruid_json.get('Information')
        return self.sensor_info_list

    def input_type_selector(self, unit):
        # Set input type.
        return {
            "C": "temperature",
            "V": "voltage",
            "RPM": "RPM",
            "A": "amp",
            "W": "power"
        }.get(unit, unit)

    def input_name_selector(self, sensor_name, input_name):

        self.sensor_name = {
            "syscpld-i2c-0-0d": "TEMPERATURE",
            "dps1100-i2c-24-58": "PSU1",
            "dps1100-i2c-25-59": "PSU2",
            "fancpld-i2c-8-0d": "FAN"
        }.get(sensor_name, sensor_name)

        if 'dps1100' in sensor_name:
            input_name = {
                "fan1": self.sensor_name + "_FAN",
                "iin": self.sensor_name + "_CURR_I",
                "iout1": self.sensor_name + "_CURR_O",
                "pin": self.sensor_name + "_POWER_I",
                "pout1": self.sensor_name + "_POWER_O",
                "temp1": self.sensor_name + "_TEMP1",
                "temp2": self.sensor_name + "_TEMP2",
                "vin": self.sensor_name + "_VOL_I",
                "vout1": self.sensor_name + "_VOL_O"
            }.get(input_name, input_name)

        elif 'tmp75' in sensor_name:
            input_name = {
                "tmp75-i2c-7-4d": "FTB_INLET_RIGHT",
                "tmp75-i2c-7-4c": "FTB_INLET_LEFT",
                "tmp75-i2c-7-4b": "FTB_SWITCH_OUTLET",
                "tmp75-i2c-7-4a": "BTF_SWITCH_OUTLET",
                "tmp75-i2c-39-48": "BTF_INLET_RIGHT",
                "tmp75-i2c-39-49": "BTF_INLET_LEFT"
            }.get(sensor_name, input_name)
            if self.get_sys_airflow() == "FTOB" and sensor_name == "tmp75-i2c-7-4d":
                input_name = "INLET_TEMP"

            if self.get_sys_airflow() == "BTOF" and sensor_name == "tmp75-i2c-39-48":
                input_name = "INLET_TEMP"

            self.sensor_name = "TEMPERATURE"

        elif 'fancpld' in sensor_name:
            raw_fan_input = input_name.split()
            input_name = raw_fan_input[0] + \
                raw_fan_input[1] + "_" + raw_fan_input[2]

        elif 'ir35' in sensor_name or 'ir38' in sensor_name:
            sensor_name_raw = sensor_name.split("-")
            sensor_name = sensor_name_raw[0]
            self.sensor_name = sensor_name.upper()

        return input_name.replace(" ", "_").upper()

    def get_num_sensors(self):
        """
            Get the number of sensors
            :return: int num_sensors
        """

        num_sensors = 0
        try:
            # Request and validate sensor's information
            self.sensor_info_list = self.request_data()

            # Get number of sensors.
            num_sensors = len(self.sensor_info_list)
        except:
            print "Error: Unable to access sensor information"
            return 0

        return num_sensors

    def get_sensor_input_num(self, index):
        """
            Get the number of the input items of the specified sensor
            :return: int input_num
        """

        input_num = 0
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()

            # Get sensor's input number.
            sensor_data = self.sensor_info_list[index-1]
            input_num = len(sensor_data.keys())-2
        except:
            print "Error: Unable to access sensor information"
            return 0

        return input_num

    def get_sensor_name(self, index):
        """
            Get the device name of the specified sensor.
            for example "coretemp-isa-0000"
            :return: str sensor_name
        """

        sensor_name = "N/A"
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()

            # Get sensor's name.
            sensor_data = self.sensor_info_list[index-1]
            sensor_name = sensor_data.get('name')

        except:
            return "N/A"

        return sensor_name

    def get_sensor_input_name(self, sensor_index, input_index):
        """
            Get the input item name of the specified input item of the
            specified sensor index, for example "Physical id 0"
            :return: str sensor_input_name
        """

        sensor_input_name = "N/A"
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()
            sensor_data = self.sensor_info_list[sensor_index-1].copy()

            # Remove none input key.
            del sensor_data["name"]
            del sensor_data["Adapter"]

            # Get sensor's input name.
            sensor_data_key = sensor_data.keys()
            sensor_input_name = sensor_data_key[input_index-1]
        except:
            return "N/A"

        return sensor_input_name

    def get_sensor_input_type(self, sensor_index, input_index):
        """
            Get the item type of the specified input item of the specified sensor index,
            The return value should among  "valtage","temperature"
            :return: str sensor_input_type
        """

        sensor_input_type = "N/A"
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()
            sensor_data = self.sensor_info_list[sensor_index-1].copy()

            # Remove none input key.
            del sensor_data["name"]
            del sensor_data["Adapter"]

            # Get sensor's input type name.
            sensor_data_key = sensor_data.keys()
            sensor_input_raw = sensor_data.get(sensor_data_key[input_index-1])
            sensor_data_str = sensor_input_raw.split()
            sensor_input_type = self.input_type_selector(sensor_data_str[1])
        except:
            return "N/A"

        return sensor_input_type

    def get_sensor_input_value(self, sensor_index, input_index):
        """
            Get the current value of the input item, the unit is "V" or "C"
            :return: float sensor_input_value
        """

        sensor_input_value = 0
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()
            sensor_data = self.sensor_info_list[sensor_index-1].copy()

            # Remove none input key.
            del sensor_data["name"]
            del sensor_data["Adapter"]

            # Get sensor's input value.
            sensor_data_key = sensor_data.keys()
            sensor_input_raw = sensor_data.get(sensor_data_key[input_index-1])
            sensor_data_str = sensor_input_raw.split()
            sensor_input_value = float(
                sensor_data_str[0]) if sensor_data_str[0] != "N/A" else 0
        except:
            print "Error: Unable to access sensor information"
            return 0

        return sensor_input_value

    def get_sensor_input_low_threshold(self, sensor_index, input_index):
        """
            Get the low threshold of the value,
            the status of this item is not ok if the current value<low_threshold
            :return: float sensor_input_low_threshold
        """

        sensor_input_low_threshold = 0
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()
            sensor_data = self.sensor_info_list[sensor_index-1].copy()

            # Remove none input key.
            del sensor_data["name"]
            del sensor_data["Adapter"]

            # Get sensor's input low threshold.
            sensor_data_key = sensor_data.keys()
            sensor_input_raw = sensor_data.get(sensor_data_key[input_index-1])
            sensor_data_str = sensor_input_raw.split()
            indices = [i for i, s in enumerate(
                sensor_data_str) if 'min' in s or 'low' in s]
            l_thres = float(
                sensor_data_str[indices[0] + 2]) if len(indices) != 0 else 0
            unit = sensor_data_str[indices[0] +
                                   3] if len(indices) != 0 else None
            if unit is not None and len(unit) > 1:
                sensor_input_low_threshold = l_thres * \
                    1000 if str(unit[0]).lower() == 'k' else l_thres
        except:
            print "Error: Unable to access sensor information"
            return 0

        return sensor_input_low_threshold

    def get_sensor_input_high_threshold(self, sensor_index, input_index):
        """
            Get the high threshold of the value,
            the status of this item is not ok if the current value > high_threshold
            :return: float sensor_input_high_threshold
        """

        sensor_input_high_threshold = 0
        try:
            # Request and validate sensor's information.
            self.sensor_info_list = self.request_data()
            sensor_data = self.sensor_info_list[sensor_index-1].copy()

            # Remove none input key.
            del sensor_data["name"]
            del sensor_data["Adapter"]

            # Get sensor's input high threshold.
            sensor_data_key = sensor_data.keys()
            sensor_input_raw = sensor_data.get(sensor_data_key[input_index-1])
            sensor_data_str = sensor_input_raw.split()
            indices = [i for i, s in enumerate(
                sensor_data_str) if 'max' in s or 'high' in s]
            h_thres = float(
                sensor_data_str[indices[0] + 2]) if len(indices) != 0 else 0
            unit = sensor_data_str[indices[0] +
                                   3] if len(indices) != 0 else None
            if unit is not None and len(unit) > 1:
                sensor_input_high_threshold = h_thres * \
                    1000 if str(unit[0]).lower() == 'k' else h_thres

        except:
            print "Error: Unable to access sensor information"
            return 0

        return sensor_input_high_threshold

    def get_sys_airflow(self):
        sys_air_flow = "Unknown"
        sys_pn_data = [
            v.split(":") for v in self.sys_fruid_list if "Product Part Number" in v]

        if len(sys_pn_data) == 0:
            return sys_air_flow

        sys_pn = sys_pn_data[0][1]
        if "R1241-F0001" in sys_pn:
            sys_air_flow = "FTOB"
        elif"R1241-F0002" in sys_pn:
            sys_air_flow = "BTOF"

        return sys_air_flow

    def get_all(self):

        all_sensor_dict = dict()

        # Request sensor's information.
        self.sensor_info_list = self.request_data()
        for sensor_data in self.sensor_info_list:
            sensor_info = sensor_data.copy()

            # Remove none unuse key.
            del sensor_info["name"]
            del sensor_info["Adapter"]

            # Set sensor data.
            sensor_dict = dict()

            for k, v in sensor_info.items():
                sensor_i_dict = dict()
                sensor_data_str = v.split()
                indices_h = [i for i, s in enumerate(
                    sensor_data_str) if 'max' in s or 'high' in s]
                indices_l = [i for i, s in enumerate(
                    sensor_data_str) if 'min' in s or 'low' in s]
                h_thres = float(
                    sensor_data_str[indices_h[0] + 2]) if len(indices_h) != 0 else 0
                l_thres = float(
                    sensor_data_str[indices_l[0] + 2]) if len(indices_l) != 0 else 0
                thres_unit = sensor_data_str[-1]

                sensor_i_dict["Type"] = self.input_type_selector(
                    sensor_data_str[1])
                sensor_i_dict["Value"] = float(
                    sensor_data_str[0]) if sensor_data_str[0] != "N/A" else 0
                sensor_i_dict["HighThd"] = h_thres * \
                    1000 if str(thres_unit[0]).lower() == 'k' else h_thres
                sensor_i_dict["LowThd"] = l_thres * \
                    1000 if str(thres_unit[0]).lower() == 'k' else l_thres

                k = self.input_name_selector(sensor_data.get('name'), k)
                sensor_dict[k] = sensor_i_dict

            if all_sensor_dict.get(self.sensor_name) is None:
                all_sensor_dict[self.sensor_name] = dict()

            all_sensor_dict[self.sensor_name].update(sensor_dict)

        sensor_dict = dict()
        sensor_dict["Sys_AirFlow"] = self.get_sys_airflow()
        all_sensor_dict["TEMPERATURE"].update(sensor_dict)

        return all_sensor_dict
