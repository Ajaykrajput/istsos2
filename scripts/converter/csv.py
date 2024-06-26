# -*- coding: utf-8 -*-
# ===============================================================================
#
# Authors: Massimiliano Cannata, Milan Antonovic
#
# Copyright (c) 2015 IST-SUPSI (www.supsi.ch/ist)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# ===============================================================================
"""

Usage example:

# File example: Calcaccia_A_1304160941.dat
# =====================================
# Identificazione: Calcaccia A	SN/TD: 739336/MTO-133	Firmware: FW1.14
# Valore minimo 0.123 mWS	Valore massimo 0.142 mWS	Valore medio 0.536 mWS	Pressure_Type="rel"	
# Ora	Data	Pressione [mWS]	Temperatura [°C]	Conducibilità [mS/cm]	Conta-impulsi [mm]	
# 09:50:00	26.03.2013	0.140	4.4		
# 10:00:00	26.03.2013	0.137	4.4		
# 10:10:00	26.03.2013	0.139	4.4		
# 10:20:00	26.03.2013	0.141	4.4		
# 10:30:00	26.03.2013	0.139	4.4		
# 10:40:00	26.03.2013	0.139	4.4		
# 10:50:00	26.03.2013	0.139	4.5		
# 11:00:00	26.03.2013	0.139	4.5	
# =====================================


from scripts.converter import csv

# Multi column date
importer = csv.CsvImporter('T_TRE', {
        "headrows": 3,
        "separator": "\t",
        "filenamedate": {
            "format": '%y%m%d%H%M',
            "remove": ['Calcaccia_A_','.dat']
        },
        "datetime": {
            "tz": '+01:00',
            "time": {
                "column": 0,
                "format": '%H:%M:%S'
            },
            "date": {
                "column": 1,
                "format": '%d.%m.%Y'
            }
        },
        "observations": [{
            "observedProperty": "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature",
            "column": 2
        }]
    },
    'http://localhost/istsos', 'pippo',
    "/home/milan/workspace/istsos/google-svn/trunk/test/scripts/data/in/csv", 'Calcaccia_A_*.dat',
    "/home/milan/workspace/istsos/google-svn/trunk/test/scripts/data/out",
    True
)
csv.execute()

# Single column date
importer = csv.CsvImporter('T_TRE', {
        "headrows": 0,
        "separator": "\t",
        "filenamedate": {
            "format": '%y%m%d%H%M',
            "remove": ['Calcaccia_A_','.dat']
        },
        "datetime": {
            "column": 1,
            "format": '%d.%m.%Y %H:%M:%S',
            "tz": '+01:00'
        },
        "observations": [{
            "observedProperty": "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature",
            "column": 3
        }]
    },
    'http://localhost/istsos', 'pippo',
    "istsos/test/scripts/data/in/csv", 'Calcaccia_A_*.dat',
    "istsos/test/scripts/data/out",
    True
)
csv.execute()


# File example: BR7_GW_____20210325000036.MIS
# =====================================
<STATION>BR7_GW____</STATION><SENSOR>0001</SENSOR><DATEFORMAT>YYYYMMDD</DATEFORMAT>
20201024;181000;9.997
20201024;182000;9.996
20201024;183000;9.996
<STATION>BR7_GW____</STATION><SENSOR>0002</SENSOR><DATEFORMAT>YYYYMMDD</DATEFORMAT>
20201024;181000;8.68
20201024;182000;8.70
20201024;183000;8.68
# =====================================

# Block interval enable / disable
importer = csv.CsvImporter('T_TRE', {
        "enabled_from": {
            "include": "<SENSOR>0001</SENSOR>"
        },
        "disabled_from": {
            "include": "<SENSOR>",
            "exclude": "<SENSOR>0001</SENSOR>"
        },
        skiplines: [
            'NO DATA AVAILABLE'
        ],
        "headrows": 0,
        "separator": ";",
        "filenamedate": {
            "format": '%Y%m%d%H%M%S',
            "remove": ['BR7_GW_____','.MIS']
        },
        "datetime": {
            "tz": '+01:00',
            "time": {
                "column": 1,
                "format": '%H%M%S'
            },
            "date": {
                "column": 2,
                "format": '%Y%m%d'
            }
        },
        "observations": [{
            "observedProperty": "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature",
            "column": 2
        }]
    },
    'http://localhost/istsos', 'pippo',
    "istsos/test/scripts/data/in/csv", 'BR7_GW_____20210325000036.MIS',
    "istsos/test/scripts/data/out",
    True
)
csv.execute()


"""

from scripts import raw2csv
from datetime import datetime
from datetime import timedelta
from pytz import timezone
import traceback
from types import FunctionType


class CsvImporter(raw2csv.Converter):
    
    def __init__(self, procedureName, config, url, service, inputDir, 
                 fileNamePattern, outputDir=None, qualityIndex=False, 
                 exceptionBehaviour={}, user=None, password=None, debug=False, 
                 csvlength=5000, filenamecheck=None, archivefolder = None, extra={}):
        
        self.config = config

        self.max_cols = 0

        if 'observations' in config:
            for obs in config['observations']:
                if 'column' in obs:
                    self.max_cols = max(self.max_cols, obs['column'])

        if 'enabled_from' in config:
            self.enabled = False
        else:
            self.enabled = None

        raw2csv.Converter.__init__(self,
            procedureName, url, service, inputDir, fileNamePattern, outputDir,
            qualityIndex, exceptionBehaviour, user, password, debug, csvlength,
            filenamecheck, archivefolder, extra)

    def parseDate(self, columns):
        
        if "column" in self.config["datetime"] and "format" in self.config["datetime"]:
            d = datetime.strptime(
                columns[self.config["datetime"]["column"]], 
                self.config["datetime"]["format"]
            )
        else:
            dt = "%s %s" % (
                columns[self.config["datetime"]['date']["column"]],
                columns[self.config["datetime"]['time']["column"]]
            )
            frm = "%s %s" % (
                self.config["datetime"]['date']["format"],
                self.config["datetime"]['time']["format"]
            )
            d = datetime.strptime(dt, frm)

        if "tz" in self.config["datetime"]:
            d = self.getDateTimeWithTimeZone(d, self.config["datetime"]["tz"])
        
        # if then function added, execute the function on datetime object
        if "then" in self.config["datetime"] and (
                isinstance(self.config["datetime"]["then"], FunctionType)):
            d = self.config["datetime"]["then"](d)
            
        return d
        

    def setEndPositionFromFilename(self, fileName):
        """
        Extract from file name the EndPosition Date, usefull with irregular 
        procedures like rain (tipping bucket) that can have no data when it's 
        not raining.
        
        In the config there shall be this type of configuration:
            
            "filenamedate": {
                "format": '%y%m%d%H%M',
                "tz": '+02:00',
                "remove": ['Calcaccia_A_','.dat']
            }
            
        """
        
        if self.fndf:
            dt = self.getDateFromFileName(fileName)
            self.setEndPosition(dt)
            
        """
        if "filenamedate" in self.config:
            
            dt = fileName;
            for rem in self.config["filenamedate"]["remove"]:
                dt = dt.replace(rem,'')
                
            dt = datetime.strptime(dt,self.config["filenamedate"]["format"])
            dt = dt.replace(tzinfo=timezone('UTC'))
            
            if "tz" in self.config["filenamedate"]:
                offset = self.config["filenamedate"]["tz"].split(":")
                dt = dt - timedelta(hours=int(offset[0]), minutes=int(offset[1]))'''
            
            self.setEndPosition(dt)
        """

    def parse(self, fileObj, fileName):
        # print "Filename: %s" % fileName
        cnt = 0
        for line in fileObj.readlines():
            cnt = cnt+1
            # Skipping header rows if present in configuration
            if "headrows" in self.config and cnt <= self.config['headrows']:
                # print("skipping headrows (%s/%s)" % (cnt, self.config['headrows']))
                continue

            elif "stopat" in self.config:
                if isinstance(self.config["stopat"], str) and (
                        line.find(self.config["stopat"])>=0):
                    # print("Breaking at line %s: %s" % (cnt, line))
                    break

            if "skiplines" in self.config:
                skipline = False
                for sl in self.config['skiplines']:
                    if sl in line:
                        skipline = True
                        break
                
                if skipline is True:
                    # print("Skipping at line %s, found '%s': %s" % (cnt, sl, line))
                    continue

            if self.enabled is not None and self.enabled is not True:

                if self.config['enabled_from']['include'] in line:
                    # print("Enabled at line %s, found '%s': %s" % (cnt, self.config['enabled_from']['include'], line))
                    self.enabled = True
                    continue

            elif self.enabled is not None and self.enabled is True:

                if (
                    self.config['disabled_from']['include'] in line
                    and self.config['disabled_from']['exclude'] not in line
                ):
                    self.enabled = False
                    continue

            if self.enabled is None or self.enabled is True:

                # Line splitting
                columns = line.split(self.config['separator'])

                if self.max_cols > 0 and len(columns) < (self.max_cols+1):
                    continue

                try:
                    date = self.parseDate(columns)
                    values = {}
                    for obs in self.config["observations"]:
                        if obs["column"] is None:
                            values[obs["observedProperty"]] = -999.9
                        else:
                            values[obs["observedProperty"]] = columns[obs["column"]]
                    self.addObservation(
                        raw2csv.Observation(date, values)
                    )
                    self.setEndPosition(date)

                except Exception as e:
                    print("%s [%s]:%s" % (fileName,cnt,line))
                    print(traceback.print_exc())
                    raise e
                
        self.setEndPositionFromFilename(fileName)
                

"""

Usage example:
    
# File example: Calcaccia_A_1304160941.dat
# =====================================
# Identificazione: Calcaccia A	SN/TD: 739336/MTO-133	Firmware: FW1.14
# Valore minimo 0.123 mWS	Valore massimo 0.142 mWS	Valore medio 0.536 mWS	Pressure_Type="rel"	
# Ora	Data	Pressione [mWS]	Temperatura [°C]	Conducibilità [mS/cm]	Conta-impulsi [mm]	
# 09:50:00	26.03.2013	0.140	4.4		
# 10:00:00	26.03.2013	0.137	4.4		
# 10:10:00	26.03.2013	0.139	4.4		
# 10:20:00	26.03.2013	0.141	4.4		
# 10:30:00	26.03.2013	0.139	4.4		
# 10:40:00	26.03.2013	0.139	4.4		
# 10:50:00	26.03.2013	0.139	4.5		
# 11:00:00	26.03.2013	0.139	4.5	
# =====================================

from scripts.converter import csv

# Multi column date
importer = csv.Offline1Importer('T_TRE', [{
        "observedProperty": "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature",
        "column": 2
    }],
    'http://localhost/istsos', 'pippo',
    "/home/milan/workspace/istsos/google-svn/trunk/test/scripts/data/in/csv", 'Calcaccia_A_*.dat',
    "/home/milan/workspace/istsos/google-svn/trunk/test/scripts/data/out",
    True
)
csv.execute()
"""

class Offline1Importer(CsvImporter):
    
    def __init__(self, procedureName, observations, url, service, inputDir, fileNamePattern, outputDir, debug):
        CsvImporter.__init__(self, procedureName, {
            "headrows": 3,
            "separator": "\t",
            "filenamedate": {
                "format": '%y%m%d%H%M',
                "remove": fileNamePattern.split("*")
            },
            "datetime": {
                "tz": '+01:00',
                "time": {
                    "column": 0,
                    "format": '%H:%M:%S'
                },
                "date": {
                    "column": 1,
                    "format": '%d.%m.%Y'
                }
            },
            "observations": observations
        }, url, service, inputDir, fileNamePattern, outputDir, debug)
            















