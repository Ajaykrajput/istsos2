# istSOS Istituto Scienze della Terra Sensor Observation Service
# Copyright (C) 2010 Massimiliano Cannata
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


import psycopg2 # @TODO the right library
import psycopg2.extras
import os, sys

import sosConfig
from istSOS import sosDatabase
from istSOS import sosException
import mx.DateTime.ISO
import isodate as iso
from datetime import timedelta
import copy, pytz


from datetime import datetime

'''
import logging
logPath = "/var/log/istsos/"
log = logging.getLogger('ist_logger')
hdlr = logging.FileHandler(logPath+'ist_logger.log')
#formatter = logging.Formatter('%(asctime)s [%(levelname)s] > %(message)s')
formatter = logging.Formatter('%(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.INFO)
'''

#----- VIRTUAL PROCESS LOADING -----
try:
    sys.path.append(sosConfig.virtual_processes_folder)
except:
    pass

class VirtualProcess():
    def __init__(self,filter,pgdb):
        self.filter = copy.deepcopy(filter)
        self.pgdb = pgdb
        self.ob_inputs = {}
        self.inputs = {}
        self.aggregate_function = filter.aggregate_function
        self.aggregate_interval = filter.aggregate_interval
        
    
    def setInput(self,val,name):
        "set generic input of generic type"
        self.inputs[name] = val
        
    def setSOSobservationVar(self,proc,prop,samplingTime=False):
        "method for setting a procedure observation input"
        self.filter.procedure = [proc]
        if type(prop)==type([]):
            self.filter.observedProperty = prop
        else:
            self.filter.observedProperty = [prop]
        
        #raise sosException.SOSException(3,"filter: %s" % self.filter.observedProperty)
        
        #CRETE OBSERVATION OBJECT
        #=================================================
        ob = observation()
        
        #BUILD BASE INFOS FOR REQUIRED PROCEDURE
        #=================================================
        sqlSel = "SELECT DISTINCT"
        sqlSel += " id_prc, name_prc, name_oty, stime_prc, etime_prc, time_res_prc, name_tru"
        sqlFrom = "FROM %s.procedures, %s.proc_obs p, %s.observed_properties, " %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
        sqlFrom += " %s.uoms, %s.time_res_unit, %s.obs_type" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
        sqlWhere = "WHERE id_prc=p.id_prc_fk AND id_opr_fk=id_opr AND id_uom=id_uom_fk AND id_tru=id_tru_fk AND id_oty=id_oty_fk"
        sqlWhere += " AND name_prc='%s'" %(self.filter.procedure[0])
        """
        properties = [ "name_opr='%s'" % op for op in self.filter.observedProperty ]
        sqlWhere += " AND ( %s )" %(" OR ".join(properties))
        raise sosException.SOSException(3,"l-SQL: %s - %s"%(sqlSel + " " + sqlFrom + " " + sqlWhere,"e"))
        """
        try:
            o = self.pgdb.select(sqlSel + " " + sqlFrom + " " + sqlWhere)[0]
        except Exception as e:
            raise sosException.SOSException(3,"SQL: %s - %s"%(sqlSel + " " + sqlFrom + " " + sqlWhere,e))    
        
        ob.baseInfo(self.pgdb,o)
        
        #GET DATA FROM PROCEDURE ACCORDING TO THE FILTERS
        #=================================================
        ob.setData(self.pgdb,o,self.filter)
        
        if samplingTime==False:
            return ob.data
        else:
            return (ob.data,ob.samplingTime)
        
    def setGenericObservationVar(self,data,name):
        "method for setting generic data observation"
        if not type(data)==type([]):
            if not ( type(data[0])==type([]) and len(data[0]==2) ):
                raise sosException.SOSException(3,"setGenericVar argument not appripriate")        
        self.ob_input[name] = data
    
    def setDischargeCurves(self,hqFile):
        "method for setting h-q tranformation tables/curves"       
        #set requested period
        #================================================
        hqFile = sosConfig.virtual_HQ_folder + "/" + hqFile
        tp=[]
        if self.filter.eventTime == None:
            tp = [None,None]
        else:
            for t in self.filter.eventTime:
                if len(t) == 2:
                    if t[0].find('+')==-1:
                        t[0] += "+00:00"
                    if t[1].find('+')==-1:
                        t[1] += "+00:00"    
                    tp.append(iso.parse_datetime(t[0]))
                    tp.append(iso.parse_datetime(t[1]))
                if len(t)==1:
                    if t[0].find('+')==-1:
                        t[0] += "+00:00"
                    tp.append(iso.parse_datetime(t[0]))
        period = (min(tp),max(tp))
        #get required parameters
        #==================================================
        hq_fh = open(hqFile,'r')
        lines = hq_fh.readlines()
        #read header
        hqs = {'from':[],'to':[],'low':[],'up': [],'A':[],'B':[],'C':[],'K':[]}
        head = lines[0].strip().split("|")
        try:
            fromt = head.index('from')  #from time
            tot = head.index('to')      #to time
            low = head.index('low_val') #if value is bigger than
            up = head.index('up_val')   #and is lower than
            A = head.index('A')         #use this A
            B = head.index('B')         #use this B
            C = head.index('C')         #use this C
            K = head.index('K')         #use this K
        except Exception as e:
            raise sosException.SOSException(3,"setDischargeCurves: FILE %s ,%s error in header.\n %s" %(hqFile,head,e))
        
        #get equations
        if not period[0] == None:
            for l in range(1,len(lines)):
                line = lines[l].split("|")
                if iso.parse_datetime(line[1]) > period[0] or iso.parse_datetime(line[0]) <= period[1]:
                    hqs['from'].append(iso.parse_datetime(line[fromt]))
                    hqs['to'].append(iso.parse_datetime(line[tot]))
                    hqs['low'].append(float(line[low]))
                    hqs['up'].append(float(line[up]))
                    hqs['A'].append(float(line[A]))
                    hqs['B'].append(float(line[B]))
                    hqs['C'].append(float(line[C]))
                    hqs['K'].append(float(line[K]))
        else:
            for l in [-1,-2]:
                try:
                    line = lines[l].split("|")
                    hqs['from'].append(iso.parse_datetime(line[fromt]))
                    hqs['to'].append(iso.parse_datetime(line[tot]))
                    hqs['low'].append(float(line[low]))
                    hqs['up'].append(float(line[up]))
                    hqs['A'].append(float(line[A]))
                    hqs['B'].append(float(line[B]))
                    hqs['C'].append(float(line[C]))
                    hqs['K'].append(float(line[K]))
                except:
                    pass
        #raise sosException.SOSException(3,"%s" %(hqs))
        return hqs
        
    def execute(self):
        raise sosException.SOSException(3,"function execute must be overridden")

#--this while is not
#import TEST as Vproc        
#----------------------------------

def BuildobservedPropertyList(pgdb,offering):
    list=[]
    sql = "SELECT distinct(name_opr) as nopr FROM %s.procedures, %s.proc_obs p," %(sosConfig.schema,sosConfig.schema)
    sql += " %s.observed_properties, %s.off_proc o, %s.offerings" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
    sql += " WHERE id_opr_fk=id_opr AND p.id_prc_fk=id_prc AND o.id_prc_fk=id_prc AND id_off=id_off_fk"
    sql += " AND name_off='%s' ORDER BY nopr" %(offering)
    rows=pgdb.select(sql)
    for row in rows:
        list.append(row["nopr"])
    return list

def BuildfeatureOfInterestList(pgdb,offering):
    list=[]
    sql = "SELECT distinct(name_foi) as nfoi FROM %s.foi, %s.procedures " %(sosConfig.schema,sosConfig.schema)
    sql += " , %s.off_proc, %s.offerings" %(sosConfig.schema,sosConfig.schema)
    sql += " WHERE id_foi=id_foi_fk AND id_prc_fk=id_prc"
    sql += " AND id_off=id_off_fk AND name_off='%s' ORDER BY nfoi"  %(offering)
  
    try:
        rows=pgdb.select(sql)
    except:
        raise sosException.SOSException(1,"sql: %s" %(sql))
    for row in rows:
        list.append(row["nfoi"])
    return list
    
def BuildProcedureList(pgdb,offering):
    list=[]
    sql = "SELECT name_prc FROM %s.procedures, %s.off_proc, %s.offerings"  %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
    sql += " WHERE id_prc=id_prc_fk AND id_off=id_off_fk AND name_off='%s'" %(offering)
    sql += " ORDER BY name_prc"
    rows=pgdb.select(sql)
    for row in rows:
        list.append(row["name_prc"])    
    return list

def BuildOfferingList(pgdb):
    list=[]
    sql = "SELECT distinct(name_off) FROM %s.procedures,%s.off_proc,%s.offerings" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
    sql += " WHERE  id_prc=id_prc_o_fk AND id_off_fk=id_off ORDER BY name_off"
    rows=pgdb.select(sql)
    for row in rows:
        list.append(row["name_off"])


def buildQuery(parameters):
    """Documentation"""


class offInfo:
    def __init__(self,off_name,pgdb):
        sql = "SELECT name_off, desc_off FROM %s.offerings WHERE name_off='%s'" %(sosConfig.schema,off_name)
        try:
            off = pgdb.select(sql)[0]
            self.name=off["name_off"]
            self.desc=off["desc_off"]
        except:
            raise sosException.SOSException(2,"Parameter \"offering\" sent with invalid value: %s"%(off_name))
        
class observation:
    def __init__(self):
        self.procedure=None
        self.name = None
        self.id_prc=None
        self.procedureType=None
        self.samplingTime=None
        self.reqTZ = None
        self.refsys = None
        self.timeResUnit=None
        self.timeResVal=None
        self.observedProperty=None
        self.opr_urn=None
        self.uom=None
        self.featureOfInterest=None
        self.foi_urn=None
        self.foiGml = None
        self.dataType=None
        self.timedef = None
        self.qualitydef = None
        self.data=[]
        
    def baseInfo(self,pgdb,o):
        #set base information of registered procedure
        #=============================================
        
        k = o.keys()
        if not ("id_prc" in k and "name_prc" in k and  "name_oty" in k and "stime_prc" in k and "etime_prc" in k and "time_res_prc" in k and "name_tru" in k ):
            raise sosException.SOSException(3,"Error, baseInfo argument: %s"%(o))
        
        #SET PROCEDURE NAME AND ID
        #===========================
        self.id_prc=o["id_prc"]
        self.name = o["name_prc"]
        #self.procedure = sosConfig.urn["procedure"] + ":" + o["name_prc"]
        self.procedure = sosConfig.urn["procedure"] + o["name_prc"]
        
        #SET PROCEDURE TYPE
        #========================= --> ADD OTHER TYPES (IN CONFIG??)
        if o["name_oty"].lower() in ["fixpoint","mobilepoint","virtual"]:
            self.procedureType=o["name_oty"]
            #TO BE IMPLEMENTED FOR MORE OPTIONS
        else:
            raise sosException.SOSException(2,"error in procedure type setting")
        
        #SET TIME: RESOLUTION VALUE AND UNIT
        #===================================
        self.timeResVal = o["time_res_prc"]        
        self.timeResUnit = o["name_tru"]
        
        #SET SAMPLING TIME
        #===================================
        if o["stime_prc"]!=None and o["etime_prc"]!=None:
            self.samplingTime=[o["stime_prc"],o["etime_prc"]]
        else:
            self.samplingTime = None
        
        self.dataType = sosConfig.urn["dataType"] + "timeSeries"
        self.timedef = sosConfig.urn["parameter"] + "time:iso8601"
        self.qualitydef = None #sosConfig.urn["parameter"] + "qualityIndex"
        
        
    def setData(self,pgdb,o,filter):
        """get data according to request filters"""

	# @todo mettere da qualche altra parte
	defaultQI = 100
        
        #SET FOI OF PROCEDURE
        #=========================================
        sqlFoi  = "SELECT name_fty, name_foi, ST_AsGml(ST_Transform(geom_foi,%s)) as gml" %(filter.srsName)
        sqlFoi += " FROM %s.procedures, %s.foi, %s.feature_type" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
        sqlFoi += " WHERE id_foi_fk=id_foi AND id_fty_fk=id_fty AND id_prc=%s" %(o["id_prc"])
        try:
            resFoi = pgdb.select(sqlFoi)
        except:
            raise sosException.SOSException(3,"SQL: %s"%(sqlFoi))
        
        self.featureOfInterest = resFoi[0]["name_foi"]
        self.foi_urn = sosConfig.urn["feature"] + resFoi[0]["name_fty"] + ":" + resFoi[0]["name_foi"]
        if resFoi[0]["gml"].find("srsName")<0:
            srs = filter.srsName or sosConfig.istSOSepsg
            self.foiGml = resFoi[0]["gml"][:resFoi[0]["gml"].find(">")] + " srsName=\"EPSG:%s\"" % srs + resFoi[0]["gml"][resFoi[0]["gml"].find(">"):]
        else:
            self.foiGml = resFoi[0]["gml"]
        
        #SET INFORMATION ABOUT OBSERVED_PROPERTIES
        #=========================================       
        sqlObsPro = "SELECT id_opr, name_opr, name_uom FROM %s.observed_properties, %s.proc_obs, %s.uoms" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
        sqlObsPro += " WHERE id_opr_fk=id_opr AND id_uom_fk=id_uom AND id_prc_fk=%s" %(o["id_prc"])
        sqlObsPro += " AND ("
        #sqlObsPro += " OR ".join(["name_opr='" + str(i) + "'" for i in filter.observedProperty])
        sqlObsPro += " OR ".join(["name_opr SIMILAR TO '%(:|)" + str(i) + "(:|)%'" for i in filter.observedProperty])
        sqlObsPro += " ) ORDER BY name_opr ASC"
        try:
            obspr_res = pgdb.select(sqlObsPro)
        except:
            raise sosException.SOSException(3,"SQL: %s"%(sqlObsPro))
            
        self.observedProperty = []
        self.opr_urn = []
        self.uom = []
        self.qualityIndex = filter.qualityIndex
        
        for row in obspr_res:
            self.observedProperty += [str(row["name_opr"])]
            self.opr_urn += [str(row["name_opr"])]
            self.uom += [str(row["name_uom"])]
            if self.qualityIndex==True:
                self.observedProperty += [str(row["name_opr"])+":qualityIndex"]
                self.opr_urn += [str(row["name_opr"] +":qualityIndex")]
                self.uom += ["-"]
        
        #SET DATA
        #=========================================
        #CASE "fixpoint" or "mobilepoint"
        #-----------------------------------------
        if self.procedureType in ["fixpoint","mobilepoint"]:
            sqlSel = "SELECT et.time_eti as t," 
            joinar=[]
            cols=[]

            aggrCols=[]
            aggrNotNull=[]

            valeFieldName = []
            for idx, obspr_row in enumerate(obspr_res):
                if self.qualityIndex==True:
                    cols.append("C%s.val_msr as c%s_v, C%s.id_qi_fk as c%s_qi" %(idx,idx,idx,idx))
                    valeFieldName.append("c%s_v" %(idx))
                    valeFieldName.append("c%s_qi" %(idx))
                else:
                    cols.append("C%s.val_msr as c%s_v" %(idx,idx))
                    valeFieldName.append("c%s_v" %(idx))

                # If Aggregatation funtion is set
                #---------------------------------
                if filter.aggregate_interval != None:
                    aggrCols.append("COALESCE(%s(dt.c%s_v),%s) as c%s_v\n" %(filter.aggregate_function,idx,filter.aggregate_nodata,idx))
                    if self.qualityIndex==True:
                        #raise sosException.SOSException(3,"QI: %s"%(self.qualityIndex))
                        aggrCols.append("COALESCE(MIN(dt.c%s_qi),%s) as c%s_qi\n" %(idx,defaultQI,idx))
                    aggrNotNull.append(" c%s_v > -900 " %(idx))

                
                
                # Set SQL JOINS
                #---------------
                join_txt  = " left join (\n"
                join_txt += " SELECT distinct A%s.id_msr, A%s.val_msr, A%s.id_eti_fk\n" %(idx,idx,idx)
                if self.qualityIndex==True:
                    join_txt += ",A%s.id_qi_fk\n" %(idx)
                join_txt += "   FROM %s.measures A%s, %s.event_time B%s\n" %(sosConfig.schema,idx,sosConfig.schema,idx)
                join_txt += " WHERE A%s.id_eti_fk = B%s.id_eti\n" %(idx,idx)
                join_txt += " AND A%s.id_opr_fk=%s\n" %(idx,obspr_row["id_opr"])
                join_txt += " AND B%s.id_prc_fk=%s\n" %(idx,o["id_prc"])
                
                # if qualityIndex has filter
                #------------------------------
                #if filter.qualityIndex and filter.qualityIndex.__class__.__name__=='str':
                #    join_txt += " AND %s\n" %(filter.qualityIndex)

                # ATTETION: HERE -999 VALUES ARE EXCLUDED WHEN ASKING AN AGGREAGATE FUNCTION
                if filter.aggregate_interval != None:
                    join_txt += " AND A%s.val_msr > -900 " % idx
                
                # If eventTime is set add to JOIN part
                #--------------------------------------
                if filter.eventTime:
                    join_txt += " AND ("
                    etf=[]
                    for ft in filter.eventTime:
                        if len(ft)==2:
                            etf.append("B%s.time_eti > timestamptz '%s' AND B%s.time_eti <= timestamptz '%s' \n" %(idx,ft[0],idx,ft[1]))
                        elif len(ft)==1:
                            etf.append("B%s.time_eti = timestamptz '%s' \n" %(idx,ft[0]))
                        else:
                            raise sosException.SOSException(2,"error in time filter")
                    join_txt += " OR ".join(etf)
                    join_txt +=  ")\n"
                else:
                    join_txt += " AND B%s.time_eti = (SELECT max(time_eti) FROM %s.event_time WHERE id_prc_fk=%s) \n" %(idx,sosConfig.schema,o["id_prc"])
                
                # close SQL JOINS
                #-----------------
                join_txt += " ) as C%s\n" %(idx)
                join_txt += " on C%s.id_eti_fk = et.id_eti" %(idx)
                joinar.append(join_txt)
            
            
            #If MOBILE PROCEDURE
            #--------------------
            if self.procedureType=="mobilepoint":
                join_txt  = " left join (\n"
                join_txt += " SELECT distinct Ax.id_pos, X(ST_Transform(Ax.geom_pos,%s)) as x,Y(ST_Transform(Ax.geom_pos,%s)) as y,Z(ST_Transform(Ax.geom_pos,%s)) as z, Ax.id_eti_fk\n" %(filter.srsName,filter.srsName,filter.srsName)
                if self.qualityIndex==True:
                    join_txt += " Ax.id_qi_fk as posqi\n"
                join_txt += "   FROM %s.positions Ax, %s.event_time Bx\n" %(sosConfig.schema,sosConfig.schema)
                join_txt += " WHERE Ax.id_eti_fk = Bx.id_eti"
                join_txt += " AND Bx.id_prc_fk=%s" %(o["id_prc"])
                
                if filter.eventTime:
                    join_txt += " AND ("
                    etf=[]
                    for ft in filter.eventTime:
                        if len(ft)==2:
                            etf.append("Bx.time_eti > timestamptz '%s' AND Bx.time_eti <= timestamptz '%s' " %(ft[0],ft[1]))
                        elif len(ft)==1:
                            etf.append("Bx.time_eti = timestamptz '%s' " %(ft[0]))                        
                        else:
                            raise sosException.SOSException(2,"error in time filter")
                    join_txt += " OR ".join(etf)
                    join_txt +=  ")\n"
                else:
                    join_txt += " AND Bx.time_eti = (SELECT max(time_eti) FROM %s.event_time WHERE id_prc_fk=%s) " %(sosConfig.schema,o["id_prc"])
                
                join_txt += " ) as Cx on Cx.id_eti_fk = et.id_eti\n"
                sqlSel += " Cx.x as x, Cx.y as y, Cx.z as z, "
                if self.qualityIndex==True:
                    sqlSel += "Cx.posqi, "
                joinar.append(join_txt)
            
            
            # Set FROM CLAUSE
            #-----------------    
            sqlSel += ", ".join(cols)
            sqlSel += " FROM %s.event_time et\n" %(sosConfig.schema)

            #====================            
            # Set WHERE CLAUSES
            #====================
            sqlData = " ".join(joinar)
            sqlData += " WHERE et.id_prc_fk=%s\n" %(o["id_prc"])

            # Set FILTER ON RESULT (OGC:COMPARISON) -
            #----------------------------------------
            if filter.result:
                for ind, ov in enumerate(self.observedProperty):
                    if ov.find(filter.result[0])>0:
                        sqlData += " AND C%s.val_msr %s" %(ind,filter.result[1])
                #sqlData += " AND C%s.val_msr %s" %(self.observedProperty.index(filter.result[0]),filter.result[1])
                
            # Set FILTER ON EVENT-TIME -
            #---------------------------
            if filter.eventTime:
                sqlData += " AND ("
                etf=[]
                for ft in filter.eventTime:
                    if len(ft)==2:
                        etf.append("et.time_eti > timestamptz '%s' AND et.time_eti <= timestamptz '%s' " %(ft[0],ft[1]))
                    elif len(ft)==1:
                        etf.append("et.time_eti = timestamptz '%s' " %(ft[0]))                        
                    else:
                        raise sosException.SOSException(2,"error in time filter")
                sqlData += " OR ".join(etf)
                sqlData +=  ")"
            else:
                sqlData += " AND et.time_eti = (SELECT max(time_eti) FROM %s.event_time WHERE id_prc_fk=%s) " %(sosConfig.schema,o["id_prc"])

            sqlData += " ORDER by et.time_eti"

            sql = sqlSel+sqlData
            
            #
            if filter.aggregate_interval != None:
                self.aggregate_function = filter.aggregate_function.upper()
                '''
                for i in range(0,len(self.observedProperty)):
                    self.observedProperty[i] = "%s:%s" % (self.observedProperty[i], filter.aggregate_function)

                for ob in self.observedProperty:
                    ob = "%s:%s" % (ob, filter.aggregate_function)'''
                
                # Interval preparation
                # Converting ISO 8601 duration
                isoInt = iso.parse_duration(filter.aggregate_interval)
                sqlInt = ""

                if isinstance(isoInt, timedelta):
                    if isoInt.days>0:
                        sqlInt += "%s days " % isoInt.days
                    if isoInt.seconds>0:
                        sqlInt += "%s seconds " % isoInt.seconds
                elif isinstance(isoInt, iso.Duration): 
                    if isoInt.years>0:
                        sqlInt += "%s years " % isoInt.years
                    if isoInt.months>0:
                        sqlInt += "%s months " % isoInt.months
                    if isoInt.days>0:
                        sqlInt += "%s days " % isoInt.days
                    if isoInt.seconds>0:
                        sqlInt += "%s seconds " % isoInt.seconds


                # calculate how many step are included in the asked interval.
                hopBefore = 1
                hop = 0
                tmpStart = iso.parse_datetime(filter.eventTime[0][0])
                tmpEnd = self.samplingTime[1]
                
                while (tmpStart+isoInt)<=tmpEnd and (tmpStart+isoInt)<=iso.parse_datetime(filter.eventTime[0][1]):
                    
                    if   tmpStart <  self.samplingTime[0]:
                        hopBefore+=1
                        hop+=1

                    elif (tmpStart >= self.samplingTime[0]) and ((tmpStart+isoInt)<=self.samplingTime[1]):
                        hop+=1
                        
                    tmpStart=tmpStart+isoInt


                '''
                hop = 0
                tmp = iso.parse_datetime(filter.eventTime[0][0])+isoInt
                tmpEnd = iso.parse_datetime(filter.eventTime[0][1])-isoInt
                while tmp<=tmpEnd:
                    tmp=tmp+isoInt
                    hop+=1'''
                
                sql = '''\
                    select
                      ts.sint  as t,
                      %s
                    from
                      (
                            select
                              (('%s'::TIMESTAMP WITH TIME ZONE) + s.a * '%s'::interval)::TIMESTAMP WITH TIME ZONE as sint
                            from
                              generate_series(%s, %s) as s(a)
                      ) as ts
                    LEFT JOIN (
                        %s
                    ) as dt
                    on (dt.t > (ts.sint-'%s'::interval) AND dt.t <= (ts.sint))
                    group by ts.sint
                    order by ts.sint
                ''' % (", ".join(aggrCols), filter.eventTime[0][0], sqlInt, hopBefore, hop, sql, sqlInt)

            else:
                self.aggregate_function = None
                
            #--------- debug execute query --------
            #raise sosException.SOSException(3,sql)
            #--------------------------------------
            try:
                data_res = pgdb.select(sql)
            except:
                raise sosException.SOSException(3,"SQL: %s"%(sql))
            
            #raise sosException.SOSException(3,"SQL: %s"%(sql))
            '''
            k = ""
            for key in valeFieldName:
                k += "%s / " % key
            raise sosException.SOSException(3,k)'''

            #------------------------------------            
            #--------- APPEND DATA IN ARRAY -----
            #------------------------------------            
            #append data
            for line in data_res:
                if self.procedureType=="fixpoint":
                    data_array = [line["t"]]
                elif self.procedureType=="mobilepoint":
                    if self.qualityIndex==True:
                        data_array = [line["t"],line["x"],line["y"],line["z"],line["posqi"]]
                    else:
                        data_array = [line["t"],line["x"],line["y"],line["z"]]
                data_array.extend([line[field] for field in valeFieldName])
                self.data.append(data_array)
            #raise sosException.SOSException(3,self.data)
            #else:
            #    raise sosException.SOSException(3,"SQLEEE: %s"%(sql))
        
        #-----------------------------------------                
        #CASE "virtual"
        #-----------------------------------------       
        elif self.procedureType in ["virtual"]:
            #import procedure process
            exec "import %s as Vproc" %(self.name)
            
            #get evaluation function
            #--self.observedProperty
            VP = Vproc.istvp(filter,pgdb)
            self.data = VP.execute()
            try:
                self.samplingTime = VP.st
            except:
                pass
            
            try:
                self.aggregate_function = VP.aggregate_function
            except:
                self.aggregate_interval = None
                
            try:
                self.aggregate_interval = VP.aggregate_interval
            except:
                self.aggregate_interval = None
                
            #raise sosException.SOSException(3,self.data)
            
            #get procedures
            
            #get data
            
            #apply function
            
            #set self.data [ [time,val1,val2,...,valN],[...],[...] ]
        
        
class observations:
    def __init__(self,filter,pgdb):
        self.offInfo = offInfo(filter.offering,pgdb)
        self.refsys = sosConfig.urn["refsystem"] + filter.srsName
        self.filter = filter
        
        #CHECK FILTER VALIDITY
        #=========================================
        if filter.procedure:
            pl = BuildProcedureList(pgdb,filter.offering)
            for p in filter.procedure:
                if not p in pl:
                    raise sosException.SOSException(2,"Parameter \"procedure\" sent with invalid value: %s -  available options for offering \"%s\": %s"%(p,filter.offering,pl))
        
        if filter.featureOfInterest:
            fl = BuildfeatureOfInterestList(pgdb,filter.offering)
            if not filter.featureOfInterest in fl:
                raise sosException.SOSException(2,"Parameter \"featureOfInterest\" sent with invalid value: %s - available options: %s"%(filter.featureOfInterest,fl))
        
        if filter.observedProperty:
            opl = BuildobservedPropertyList(pgdb, filter.offering)
            opr_sel = "SELECT name_opr FROM %s.observed_properties WHERE " %(sosConfig.schema,)
            opr_sel_w = []
            for op in filter.observedProperty:
                opr_sel_w += ["name_opr SIMILAR TO '%%(:|)%s(:|)%%'" %(op)]
            opr_sel = opr_sel + " OR ".join(opr_sel_w)
            try:
                opr_filtered = pgdb.select(opr_sel)
            except:
                raise sosException.SOSException(3,"SQL: %s"%(opr_sel))
            if not len(opr_filtered)>0:
                raise sosException.SOSException(2,"Parameter \"observedProperty\" sent with invalid value: %s - available options: %s"%(filter.observedProperty,opl))
        
        #SET TIME PERIOD
        #=========================================
        tp=[]
        if filter.eventTime == None:
            tp = [None,None]
        else:
            for t in filter.eventTime:
                if len(t) == 2:
                    tp.append(iso.parse_datetime(t[0]))
                    tp.append(iso.parse_datetime(t[1]))
                if len(t)==1:
                    tp.append(iso.parse_datetime(t[0]))
        #else: rise error ???
        self.period = [min(tp),max(tp)]
        
        self.obs=[]
        
        # SET REQUEST TIMEZONE
        #===================================
        if filter.eventTime:
            if iso.parse_datetime(filter.eventTime[0][0]).tzinfo:
                self.reqTZ = iso.parse_datetime(filter.eventTime[0][0]).tzinfo
            else:
                self.reqTZ = pytz.utc
        else:
            self.reqTZ = pytz.utc
        
        #BUILD PROCEDURES LIST
        #=========================================
        #---select part of query
        sqlSel = "SELECT DISTINCT"
        sqlSel += " id_prc, name_prc, name_oty, stime_prc, etime_prc, time_res_prc, name_tru"
        #---from part of query
        sqlFrom = "FROM %s.procedures, %s.proc_obs p, %s.observed_properties, %s.uoms, %s.time_res_unit," %(sosConfig.schema,sosConfig.schema,sosConfig.schema,sosConfig.schema,sosConfig.schema)
        sqlFrom += " %s.off_proc o, %s.offerings, %s.obs_type" %(sosConfig.schema,sosConfig.schema,sosConfig.schema)
        if filter.featureOfInterest or filter.featureOfInterestSpatial:
            sqlFrom += " ,%s.foi, %s.feature_type" %(sosConfig.schema,sosConfig.schema)
        
        sqlWhere = "WHERE id_prc=p.id_prc_fk AND id_opr_fk=id_opr AND o.id_prc_fk=id_prc AND id_off_fk=id_off AND id_uom=id_uom_fk AND id_tru=id_tru_fk AND id_oty=id_oty_fk"
        sqlWhere += " AND name_off='%s'" %(filter.offering)
        
        #---where condition based on featureOfInterest
        if filter.featureOfInterest:
            sqlWhere += " AND id_foi=id_foi_fk AND id_fty=id_fty_fk AND (name_foi='%s')" %(filter.featureOfInterest)
        if filter.featureOfInterestSpatial:
            sqlWhere += " AND %s" %(filter.featureOfInterestSpatial)
        
        #---where condition based on procedures
        if filter.procedure:
            sqlWhere += " AND ("
            procWhere = []
            for proc in filter.procedure:
                procWhere.append("name_prc='%s'" %(proc))
            sqlWhere += " OR ".join(procWhere)
            sqlWhere += ")"
        
        #---where condition based on observed properties
        sqlWhere += " AND ("
        obsprWhere = []
        for obs in opr_filtered:
            obsprWhere.append("name_opr='%s'" %(obs["name_opr"])) 
        sqlWhere += " OR ".join(obsprWhere)
        sqlWhere += ")"
        
        #---where condition based on feature of interest
        #if many foi are allowed
        #if filter.seatureOdInterest:
        #    sqlWhere += " AND ("
        #    foiWhere = []
        #    for ffoi in filter.seatureOdInterest:
        #        foiWhere.append("name_foi='%s' " %(filter.featureOfInterest))
        #    sqlWhere += "AND".join(foiWhere) 
        #    sqlWhere += ")" 
        #######################################
        #raise sosException.SOSException(3,"SQL: %s"%(sqlSel + " " + sqlFrom + " " + sqlWhere))
        #######################################
       
        try:
            res = pgdb.select(sqlSel + " " + sqlFrom + " " + sqlWhere)
        except:
            raise sosException.SOSException(3,"SQL: %s"%(sqlSel + " " + sqlFrom + " " + sqlWhere))
        
        #FOR EACH PROCEDURE
        #=========================================
        for o in res:
            #id_prc, name_prc, name_oty, stime_prc, etime_prc, time_res_prc, name_tru
            
            #CRETE OBSERVATION OBJECT
            #=================================================
            ob = observation()
            
            #BUILD BASE INFOS FOR EACH PROCEDURE (Pi)
            #=================================================
            ob.baseInfo(pgdb,o)
            
            #GET DATA FROM PROCEDURE ACCORDING TO THE FILTERS
            #=================================================
            ob.setData(pgdb,o,filter)
            
            #ADD OBSERVATIONS
            #=================================================
            self.obs.append(ob)
            
            