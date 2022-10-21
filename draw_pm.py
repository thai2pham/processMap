#from jira import JIRA
#import jira.client
import datetime
import re
import argparse
from collections import defaultdict
import os
import glob
import csv
import sys
#from atlassian import Jira

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# - 특정 조건 : 그 사람 (최근 일주일)
#- 모든 ticket중에서 "그 사람"이 comments를 남긴 내용중에 tiger_weekly_report 이 comments의 첫줄에 적은 ticket들에 적은 comments를 출력한다.
#- status 상관없고, 

debug = 0

class DrawProcessMap :
    def __init__(self , input,id,passwd,debug):
        self.input = input
        self.id = id
        self.passwd = passwd
        self.debug = debug
        os.makedirs('server-data',exist_ok=True)
        self.D = {}
        self.Cnt = 1
        # key : ```from~~~execution~~~to```
        # D['Project'][Project]['Key'][Key]['From'][from]
        # D['Project'][Project]['Key'][Key]['From'][from]['To'] = 
        # D['Project'][Project]['Key'][Key]['From'][from]['Location'][location]
        # D['Project'][Project]['Key'][Key]['From'][from][Type,SuccessCheckPoint , FailCheckPoint , Description
        # D['Project'][Project]['Key'][Key]['To'][to]
        # D['Project'][Project]['Key'][Key]['To'][to]['From'] = 
        # D['Project'][Project]['Key'][Key]['To'][to]['Location'][location]
        # D['Project'][Project]['Key'][Key]['To'][to][Type,SuccessCheckPoint , FailCheckPoint , Description
        #self.group = {}
        # D['Group'][Group]['From'][from]['Key'][Key]
        # D['Group'][Group]['From'][from]['Key'][Key]['To'] = 
        # D['Group'][Group]['From'][from]['Key'][Key]['Location'][location]
        # D['Group'][Group]['From'][from]['Key'][Key][Type,SuccessCheckPoint , FailCheckPoint , Description
        # D['Group'][Group]['To'][to]['Key'][Key] = 
        # D['Group'][Group]['To'][to]['Key'][Key]['From']...
        # D['Group'][Group]['To'][to]['Key'][Key]['Location'][location]
        # D['Group'][Group]['To'][to]['Key'][Key][Type,SuccessCheckPoint , FailCheckPoint , Description
        # if it has no group , 'None'
        # D['Group']['None']['From'][from]['Key'][Key]
        # D['Group']['None']['From'][from]['Key'][Key]['To'] = 
        # D['Group']['None']['From'][from]['Key'][Key]['Location'][location]
        # D['Group']['None']['From'][from]['Key'][Key][Type,SuccessCheckPoint , FailCheckPoint , Description
        # D['Group']['None']['To'][to]['Key'][Key]
        # D['Group']['None']['To'][to]['Key'][Key]['From']...
        # D['Group']['None']['To'][to]['Key'][Key]['Location'][location]
        # D['Group']['None']['To'][to]['Key'][Key][Type,SuccessCheckPoint , FailCheckPoint , Description
        self.D['Project'] = {}
        self.D['Group'] = {}
        self.D['Key'] = {}
        self.D['Replace'] = {}
        with open(self.input,'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print('fieldnames:',reader.fieldnames)
            for r in reader:
                if 'Project' not in r:
                    print("Error : Project column should be exist in this csv file.",r)
                    quit(4)
                tmp = r['Project'].strip()
                if not tmp or tmp[0] == '#':
                    continue
                if r['Replace']:
                    replaceList = [i for i in r['Replace'].strip().split(',') if i.strip()]
                    for replaceItem in replaceList:
                        self.readReplaceFile(replaceItem.strip())
                    print('self.d[Replace]:',self.D['Replace'])
                    rList = [r]
                    rResult = []
                    for replaceItem in replaceList:   # cmu-project
                        for row in rList:
                            # print("1.row:",row)
                            for element in self.D['Replace'][replaceItem]:
                                rowNew = {}
                                for field in row:
                                    rowNew[field] = row[field].replace('['+ replaceItem +']',element)
                                rResult.append(rowNew)
                                # print("2.rowNew:",rowNew)
                        rList = rResult
                        rResult = []
                        # print(replaceItem, ': rList :',rList)
                    for row in rList:
                        self.setValue(row)
                else:
                    self.setValue(r)
        traverseFile("data.py",self.D,'D',"w")

    def readReplaceFile(self,filename):
        if filename in self.D['Replace']:
            return
        else:
            self.D['Replace'][filename] = []
        with open(filename + '.list' , 'r', encoding='utf-8', errors='ignore') as f:
            contents = f.readlines()
            a = [i.strip() for i in contents if i.strip()]
            for s in a:
                self.D['Replace'][filename].append(s)
        return

    def getProjectAndGroupAndInit(self,target,r):
        kk = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip()
        if kk in self.D['Key']:
            key = str(self.D['Key'][kk])
        else:
            key = str(self.Cnt)
            self.D['Key'][kk] = key
            self.Cnt += 1
        f = r[target].strip()
        l = f.split(',')
        _group = []
        _name = []
        for ll in l:
            if ll.strip() == '':
                continue
            tmp = ll.strip().split(':')
            if len(tmp) > 1:
                fg = tmp[0].strip()
                if fg == '':
                    fg = 'None'
                fn = tmp[1].strip()
            else:
                fg = 'None'
                fn = tmp[0].strip()
            _group.append(fg)
            _name.append(fn)
            if fg not in self.D['Group']:
                self.D['Group'][fg] = {}
            if target not in self.D['Group'][fg]:
                self.D['Group'][fg][target] = {}
            if fn not in self.D['Group'][fg][target]:
                self.D['Group'][fg][target][fn] = {}
            if 'Key' not in self.D['Group'][fg][target][fn]:
                self.D['Group'][fg][target][fn]['Key'] = []
            self.D['Group'][fg][target][fn]['Key'].append(key)
            # if key not in self.D['Group'][fg][target][fn]['Key']:
            #     self.D['Group'][fg][target][fn]['Key'][key] = {}

        project = r['Project'].strip()
        if project not in self.D['Project']:
            self.D['Project'][project] = {}
        if 'Key' not in self.D['Project'][project]:
            self.D['Project'][project]['Key'] = {}
        if key not in self.D['Project'][project]['Key']:
            self.D['Project'][project]['Key'][key] = {}
        if target not in self.D['Project'][project]['Key'][key]:
            self.D['Project'][project]['Key'][key][target] = {}
        if f not in self.D['Project'][project]['Key'][key][target]:
            self.D['Project'][project]['Key'][key][target][f] = {}
            self.D['Project'][project]['Key'][key][target][f]['_group'] = _group
            self.D['Project'][project]['Key'][key][target][f]['_name'] = _name
            self.D['Project'][project]['Key'][key][target][f]['_execution'] = r['Execution']
            if not r['Execution']:
                print('Error : Execution field should not be null.' , r)
                quit(4)
        for s in list(r.keys()):
            self.D['Project'][project]['Key'][key][target][f][s] = r[s]
            if s.find('CheckPoint') >= 0:
                sc = r[s].strip()
                self.D['Project'][project]['Key'][key][target][f]['_' + s] , self.D['Project'][project]['Key'][key][target][f]['_Op_' + s]  = self.parseCheckPoint(sc,r,s)

        return (project,f,_group,_name,key)

    def setValue(self,r):
    
        p , f , fg , fn , key = self.getProjectAndGroupAndInit('From',r)
        # p , e , eg , en , key = self.getProjectAndGroupAndInit('Execution',r)
        p , t , tg , tn , key = self.getProjectAndGroupAndInit('To',r)

        row = r
        dateRe = re.compile('(?P<date>(?P<year>20[0-9]+)-(?P<month>[0-9]+)-(?P<day>[0-9]+))')
        for field in row:
            if field in ['FromLocation','ToLocation']:
                direction = field.replace('Location','')
                # print(r[direction+'Type'])
                if r[direction+'Type'] not in ['text','binary']:
                    continue
                if r[direction+'Location'].strip() == '':
                    continue
                a = row[field].strip().split(':')
                if a[0].strip() == 'ssh':
                    hostname = a[1].strip()
                    originFileName = a[2].strip()
                    targetFileName = 'server-data/'+field+'.'+originFileName.replace('/','.')
                    s = "sshpass -p " + self.passwd + " ssh -o StrictHostKeyChecking=no " + self.id + '@' + hostname + ' ' + '''"stat -c '%y' ''' + originFileName + '"'
                    print()
                    print(s)
                    # os.system(s)
                    out = os.popen(s).read()
                    print('out:',out.strip())
                    grp = dateRe.search(out)
                    if grp:
                        year = grp.group('year')
                        month = grp.group('month')
                        day = grp.group('day')
                        if row['Periodic'] and int(row['Periodic']) > 0:
                            file_date = datetime.datetime(int(year),int(month),int(day)) - datetime.timedelta(days=int(r['Periodic']))
                            now_date = datetime.datetime.now() 
                            print('file:',file_date,'old:',now_date,grp.group('date'))
                            if file_date < now_date:  # ok
                                r[direction+'LastTime'] = grp.group('date')
                                print('date:',r[direction+'LastTime'])
                                s = "sshpass -p " + self.passwd + " scp -o StrictHostKeyChecking=no " + self.id + '@' + hostname + ':' + originFileName + ' ' + targetFileName
                                print(s)
                                os.system(s)
                                project = r['Project'].strip()
                                keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                                key = str(self.D['Key'][keyStr])
                                dir = r[direction]
                                target = '_' + direction + 'TargetExist'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetExpired'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                                target = '_' + direction + 'TargetFileName'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = targetFileName
                                target = direction + 'LastTime'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                                self.analysisLogFile(targetFileName,direction,r)
                            else:
                                print('time expired')
                                r[direction+'LastTime'] = grp.group('date')
                                project = r['Project'].strip()
                                keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                                key = str(self.D['Key'][keyStr])
                                dir = r[direction]
                                target = '_' + direction + 'TargetExist'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetExpired'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetFileName'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = targetFileName
                                target = direction + 'LastTime'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                        else:  # 시간 상관없을때
                            print('no periodic')
                            r[direction+'LastTime'] = grp.group('date')
                            print('date:',r[direction+'LastTime'])
                            s = "sshpass -p " + self.passwd + " scp -o StrictHostKeyChecking=no " + self.id + '@' + hostname + ':' + originFileName + ' ' + targetFileName
                            print()
                            print(s)
                            os.system(s)
                            project = r['Project'].strip()
                            keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                            key = str(self.D['Key'][keyStr])
                            dir = r[direction]
                            target = '_' + direction + 'TargetExist'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                            target = '_' + direction + 'TargetExpired'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                            target = '_' + direction + 'TargetFileName'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = targetFileName
                            target = direction + 'LastTime'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                            self.analysisLogFile(targetFileName,direction,r)
                    else :  # 파일이 없을때
                        print('file not exist')
                        r[direction+'LastTime'] = ''
                        project = r['Project'].strip()
                        keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                        key = str(self.D['Key'][keyStr])
                        dir = r[direction]
                        target = '_' + direction + 'TargetExist'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                        target = '_' + direction + 'TargetExpired'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                        target = '_' + direction + 'TargetFileName'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = ""
                else:
                    s = '''stat -c '%y' ''' + r[direction+'Location'].strip()
                    print()
                    print(s)
                    out = os.popen(s).read()
                    print('out:',out.strip())
                    grp = dateRe.search(out)
                    if grp:
                        year = grp.group('year')
                        month = grp.group('month')
                        day = grp.group('day')
                        if row['Periodic'] and int(row['Periodic']) > 0:
                            file_date = datetime.datetime(int(year),int(month),int(day)) - datetime.timedelta(days=int(r['Periodic']))
                            now_date = datetime.datetime.now() 
                            print('file:',file_date,'old:',now_date,grp.group('date'))
                            if file_date < now_date:  # ok
                                r[direction+'LastTime'] = grp.group('date')
                                print('date:',r[direction+'LastTime'])
                                project = r['Project'].strip()
                                keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                                key = str(self.D['Key'][keyStr])
                                dir = r[direction]
                                target = '_' + direction + 'TargetExist'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetExpired'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                                target = '_' + direction + 'TargetFileName'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = r[direction+'Location']
                                target = direction + 'LastTime'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                                self.analysisLogFile(r[direction+'Location'],direction,r)
                            else:
                                project = r['Project'].strip()
                                r[direction+'LastTime'] = grp.group('date')
                                keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                                key = str(self.D['Key'][keyStr])
                                dir = r[direction]
                                target = '_' + direction + 'TargetExist'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetExpired'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                                target = '_' + direction + 'TargetFileName'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = r[direction+'Location']
                                target = direction + 'LastTime'
                                self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                        else:  # 시간 상관없을때
                            r[direction+'LastTime'] = grp.group('date')
                            print('date:',r[direction+'LastTime'])
                            project = r['Project'].strip()
                            keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                            key = str(self.D['Key'][keyStr])
                            dir = r[direction]
                            target = '_' + direction + 'TargetExist'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = True
                            target = '_' + direction + 'TargetExpired'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                            target = '_' + direction + 'TargetFileName'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = r[direction+'Location']
                            target = direction + 'LastTime'
                            self.D['Project'][project]['Key'][key][direction][dir][target]  = grp.group('date')
                            self.analysisLogFile(r[direction+'Location'],direction,r)
                    else:   # file이 없을때
                        r[direction+'LastTime'] = ''
                        project = r['Project'].strip()
                        keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
                        key = str(self.D['Key'][keyStr])
                        dir = r[direction]
                        target = '_' + direction + 'TargetExist'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                        target = '_' + direction + 'TargetExpired'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = False
                        target = '_' + direction + 'TargetFileName'
                        self.D['Project'][project]['Key'][key][direction][dir][target]  = ""
                            

    def analysisLogFile(self,targetFileName,direction,r):
        '''
        get target file from server or local directory
        it runs when ToLocation or FromLocation have value.
        analyze the file with ToSuccessCheckPoint  and ToFailCheckPoint of r
        these CheckPoint split in _To... _From... _Op_To... _Op_From...
        '''
        print('analysisLogFile:',targetFileName,direction)
        project = r['Project'].strip()
        keyStr = r['From'].strip() + '~~~' + r['Execution'].strip() + '~~~' + r['To'].strip() 
        key = str(self.D['Key'][keyStr])
        dir = r[direction]
        ds = self.D['Project'][project]['Key'][key][direction][dir]

        showCheck = direction+'ShowCheckPoint'
        showCheckList = '_'+direction+'ShowCheckPoint'
        showOpCheckList = '_Op_'+direction+'ShowCheckPoint'
        showResult = '_result_'+direction+'ShowCheckPoint'
        # showFinalResult = '_final_result_'+direction+'ShowCheckPoint'
        if ds[showCheck].strip() != '':
            print(showCheck,ds[showCheck])
            with open(targetFileName , 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.readlines()
                pos = 0
                # show checkpoint
                # order check
                foundFlag = False
                # ds[showResult] = ds[showCheck]
                msg = ''
                for i,v in enumerate(ds[showCheckList]):
                    for line in range(pos,len(contents)):
                        if contents[line].find(v) >= 0:  # found
                            foundFlag = True
                            msg += contents[line]
                            if i+1 < len(ds[showOpCheckList]):
                                if ds[showOpCheckList][i+1].find('SEQ') < 0:  # not SEQ
                                    pos = 0
                                else :
                                    pos = line
                            else:
                                pos = 0
                            break
                ds[showResult] = msg
                #     ds[showResult] = ds[showResult].replace(v,str(foundFlag))
                #     print(v,ds[showResult])
                # ds[showResult] = ds[showResult].replace('_AND_','and')
                # ds[showResult] = ds[showResult].replace('_SEQAND_','and')
                # ds[showResult] = ds[showResult].replace('_OR_','or')
                # ds[showResult] = ds[showResult].replace('_SEQOR_','or')
                # ds[showFinalResult] = eval(ds[showResult])
                # print(ds[showResult])
                # print(eval(ds[showResult]))

        failCheck = direction+'FailCheckPoint'
        failCheckList = '_'+direction+'FailCheckPoint'
        failOpCheckList = '_Op_'+direction+'FailCheckPoint'
        failResult = '_result_'+direction+'FailCheckPoint'
        failFinalResult = '_final_result_'+direction+'FailCheckPoint'
        if ds[failCheck].strip() != '':
            print(failCheck,ds[failCheck])
            with open(targetFileName , 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.readlines()
                pos = 0
                # fail checkpoint
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['FromFailCheckPoint'] = '''((fail _AND_ failure)) _OR_ over str'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_FromFailCheckPoint'][list:0] = '''fail'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_FromFailCheckPoint'][list:1] = '''failure'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_FromFailCheckPoint'][list:2] = '''over str'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_Op_FromFailCheckPoint'][list:0] = '''_AND_'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_Op_FromFailCheckPoint'][list:1] = '''_AND_'''
                    # D['Project']['info-doxygen']['Key']['3']['From']['perl-data:info-doxygen.gv']['_Op_FromFailCheckPoint'][list:2] = '''_OR_'''
                # order check
                for i,v in enumerate(ds[failCheckList]):
                    if v in ds[failCheckList][i+1:]:
                        print("Error : your CheckPoint order is wrong:", v , 'should not be prior order.',r)
                        quit(4)
                foundFlag = False
                ds[failResult] = ds[failCheck]
                for i,v in enumerate(ds[failCheckList]):
                    for line in range(pos,len(contents)):
                        if contents[line].find(v) >= 0:  # found
                            foundFlag = True
                            if i+1 < len(ds[failOpCheckList]):
                                if ds[failOpCheckList][i+1].find('SEQ') < 0:  # not SEQ
                                    pos = 0
                                else :
                                    pos = line
                            else:
                                pos = 0
                            break
                    ds[failResult] = ds[failResult].replace(v,str(foundFlag))
                    print(v,ds[failResult])
                ds[failResult] = ds[failResult].replace('_AND_','and')
                ds[failResult] = ds[failResult].replace('_SEQAND_','and')
                ds[failResult] = ds[failResult].replace('_OR_','or')
                ds[failResult] = ds[failResult].replace('_SEQOR_','or')
                ds[failFinalResult] = eval(ds[failResult])
                print(ds[failResult])
                print(eval(ds[failResult]))

                if ds[failFinalResult]:
                    return

            # success checkpoint
                # D['Project']['UTS']['Key']['11']['To']['bmw_icon_nad_log_UTS_LOG_health-service']['ToSuccessCheckPoint'] = '''Overall coverage rate: _SEQAND_ [100%] Built target all_coverage'''
                # D['Project']['UTS']['Key']['11']['To']['bmw_icon_nad_log_UTS_LOG_health-service']['_ToSuccessCheckPoint'][list:0] = '''Overall coverage rate:'''
                # D['Project']['UTS']['Key']['11']['To']['bmw_icon_nad_log_UTS_LOG_health-service']['_ToSuccessCheckPoint'][list:1] = '''[100%] Built target all_coverage'''
                # D['Project']['UTS']['Key']['11']['To']['bmw_icon_nad_log_UTS_LOG_health-service']['_Op_ToSuccessCheckPoint'][list:0] = '''_SEQAND_'''
                # D['Project']['UTS']['Key']['11']['To']['bmw_icon_nad_log_UTS_LOG_health-service']['_Op_ToSuccessCheckPoint'][list:1] = '''_SEQAND_'''
        successCheck = direction+'SuccessCheckPoint'
        successCheckList = '_'+direction+'SuccessCheckPoint'
        successOpCheckList = '_Op_'+direction+'SuccessCheckPoint'
        successResult = '_result_'+direction+'SuccessCheckPoint'
        successFinalResult = '_final_result_'+direction+'SuccessCheckPoint'
        if ds[successCheck].strip() != '':
            print(successCheck,ds[successCheck])
            with open(targetFileName , 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.readlines()
                pos = 0
                # order check
                for i,v in enumerate(ds[successCheckList]):
                    if v in ds[successCheckList][i+1:]:
                        print("Error : your CheckPoint order is wrong:", v , 'should not be prior order.',r)
                        quit(4)
                foundFlag = False
                ds[successResult] = ds[successCheck]
                for i,v in enumerate(ds[successCheckList]):
                    for line in range(pos,len(contents)):
                        if contents[line].find(v) >= 0:  # found
                            foundFlag = True
                            if i+1 < len(ds[successOpCheckList]):
                                if ds[successOpCheckList][i+1].find('SEQ') < 0:  # not SEQ
                                    pos = 0
                                else :
                                    pos = line
                            else:
                                pos = 0
                            break
                    ds[successResult] = ds[successResult].replace(v,str(foundFlag))
                    print(v,ds[successResult])
                ds[successResult] = ds[successResult].replace('_AND_','and')
                ds[successResult] = ds[successResult].replace('_SEQAND_','and')
                ds[successResult] = ds[successResult].replace('_OR_','or')
                ds[successResult] = ds[successResult].replace('_SEQOR_','or')
                ds[successFinalResult] = eval(ds[successResult])
                print(ds[successResult])
                print(eval(ds[successResult]))

        return

    def parseCheckPoint(self,sc,r,msg):
        idx = 0
        ans = []
        ansOp = []
        bitOp = ''
        oldAndOp = ''
        oldOrOp = ''
        oldSeqAndOp = ''
        oldSeqOrOp = ''
        a = sc.split('((')
        for a1 in a:
            if a1.strip() == '':
                continue
            else :
                b = a1.split('))')
                for b1 in b:
                    if b1.strip() == '':
                        continue
                    else:
                        c = b1.split('_AND_')
                        if len(c) > 1 :
                            oldAndOp = bitOp
                            bitOp = '_AND_'
                        for c1 in c:
                            if c1.strip() == '':
                                continue
                            else :
                                d = c1.split('_OR_')
                                if  len(d) > 1:
                                    oldOrOp = bitOp
                                    bitOp = '_OR_'
                                for d1 in d:
                                    if d1.strip() == '':
                                        continue
                                    else:
                                        e = d1.split('_SEQOR_')
                                        if  len(e) > 1:
                                            oldSeqOrOp = bitOp
                                            bitOp = '_SEQOR_'
                                        for e1 in e:
                                            if e1.strip() == '':
                                                continue
                                            else:
                                                f = e1.split('_SEQAND_')
                                                if  len(f) > 1:
                                                    oldSeqAndOp = bitOp
                                                    bitOp = '_SEQAND_'
                                                for f1 in f:
                                                    if f1.strip() == '':
                                                        continue
                                                    else:
                                                        ans.append(f1.strip())
                                                        ansOp.append(bitOp)
                                                if len(e) > 1:
                                                    bitOp = oldSeqOrOp
                                        if len(e) > 1:
                                            bitOp = oldSeqOrOp
                                if len(d) > 1:
                                    bitOp = oldOrOp
                        if len(c) > 1 :
                            bitOp = oldAndOp
        # print(msg , "sc:",sc,"ans:",ans,"ansOp:",ansOp)
        return (ans,ansOp)

    def drawMap(self):
        # https://plantuml.com/ko/use-case-diagram
        totalhdr = ''
        totalhdr += "```plantuml\n"
        totalhdr += '@startuml total.png\n'
        totalhdr += 'left to right direction' + '\n'
        totalhdr += '''
skinparam usecase {
    BackgroundColor<< Execution >> YellowGreen
    BorderColor<< Execution >> YellowGreen

    BackgroundColor<< Email >> LightSeaGreen
    BorderColor<< Email >> LightSeaGreen

    ArrowColor Olive
}
        '''
        for g in self.D['Group']:
            if g == 'None':
                continue
            totalhdr += 'package ' + g + ' {\n'
            gSet = set()
            for g2 in self.D['Group'][g]:
                for g3 in self.D['Group'][g][g2]:
                    if g3 not in gSet:
                        if g == 'email':
                            totalhdr += '    usecase (' + g3 + ') as (' + g3 + ') << Email >>\n'
                        else:
                            totalhdr += '    usecase (' + g3 + ') as (' + g3 + ')\n'
                        gSet.add(g3)
            totalhdr += '}\n'
        totalbody = ''
        for p in self.D['Project']:
            plantumlhdr = ''
            plantumlhdr += "```plantuml\n"
            plantumlhdr += '@startuml ' + p + '.png\n'
            plantumlhdr += 'left to right direction' + '\n'
            plantumlbody = ''
            totalbody += '  rectangle ' + p + ' {\n'
            usecaseExecutionSet = set()
            for k in self.D['Project'][p]['Key']:
                for f in self.D['Project'][p]['Key'][k]['From']:
                    for n in self.D['Project'][p]['Key'][k]['From'][f]['_name']:
                        plantumlbody += '    (' + n + ') --> (' + self.D['Project'][p]['Key'][k]['From'][f]['_execution'] + ') : desc - ' + self.D['Project'][p]['Key'][k]['From'][f]['Description'] + '\n'
                        usecaseExecutionSet.add(self.D['Project'][p]['Key'][k]['From'][f]['_execution'])
                for f in self.D['Project'][p]['Key'][k]['To']:
                    for n in self.D['Project'][p]['Key'][k]['To'][f]['_name']:
                        plantumlbody += '    (' + self.D['Project'][p]['Key'][k]['To'][f]['_execution'] + ') --> (' + n + ') : desc - ' + self.D['Project'][p]['Key'][k]['To'][f]['Description'] + '\n'
                        usecaseExecutionSet.add(self.D['Project'][p]['Key'][k]['To'][f]['_execution'])
            for u in usecaseExecutionSet:
                totalbody += '    usecase (' + u  + ') as (' + u + ') << Execution >>\n'
            for k in self.D['Project'][p]['Key']:
                for f in self.D['Project'][p]['Key'][k]['From']:
                    for n in self.D['Project'][p]['Key'][k]['From'][f]['_name']:
                        direction = 'From'
                        ds = self.D['Project'][p]['Key'][k][direction][f]
                        desc = ds['Description']
                        errFlag = False
                        color = ''
                        if ds[direction+'Type'] in ['text','binary']:
                            if ds.get('_'+direction+'TargetExist',False) == True:   # _ToTargetExist
                                if self.debug:
                                    desc += '\\nfile exist:' + ds[direction+'Location']  # ToLocation
                                if ds.get('_ToTargetExpired',False) == True:
                                    desc += '\\nExpired file date is ' + ds.get(direction+'LastTime',"")
                                    errFlag = True
                                else :
                                    if self.debug:
                                        desc += '\\nfile date is ' + ds.get(direction+'LastTime',"")
                                if ds.get('_result_'+direction+'ShowCheckPoint','') != '':   # _result_ToShowCheckPoint
                                    a= ds.get('_result_'+direction+'ShowCheckPoint','').split('\n')   # _result_ToShowCheckPoint
                                    desc += '\\n' + '\\n'.join(a)
                                if ds.get(direction+'FailCheckPoint','').strip() and ds.get('_final_result_'+direction+'FailCheckPoint',False) == True:  # '_final_result_ToSuccessCheckPoint'
                                    errFlag = True
                                    desc += '\\nError : matched Fail condition - ' + ds.get(direction+'FailCheckPoint',"")
                                else :
                                    if self.debug:
                                        desc += '\\nFail condition - ' + ds.get(direction+'FailCheckPoint',"")
                                if ds.get(direction+'SuccessCheckPoint','').strip() and ds.get('_final_result_'+direction+'SuccessCheckPoint',True) == False:  # '_final_result_ToSuccessCheckPoint'
                                    errFlag = True
                                    desc += '\\nError : not matched Success condition - ' + ds.get(direction+'SuccessCheckPoint',"")
                                else :
                                    if self.debug:
                                        desc += '\\nSuccess condition - ' + ds.get(direction+'SuccessCheckPoint',"")
                            elif ds[direction+'Location'] != '':
                                desc += '\\nError file not exist:' + ds[direction+'Location']  # ToLocation
                                errFlag = True

                            if errFlag:
                                color += '#line:red;line.bold;text:red'
                            else:
                                color += '#line:green;line.dashed;text:green'
                        totalbody += '    (' + n + ') --> (' + ds['_execution'] + ') ' + color + ' : desc - ' + desc + '\n'
                for f in self.D['Project'][p]['Key'][k]['To']:
                    for n in self.D['Project'][p]['Key'][k]['To'][f]['_name']:
                        direction = 'To'
                        ds = self.D['Project'][p]['Key'][k][direction][f]
                        desc = ds['Description']
                        errFlag = False
                        color = ''
                        if ds[direction+'Type'] in ['text','binary']:
                            if ds.get('_'+direction+'TargetExist',False) == True:   # _ToTargetExist
                                if self.debug:
                                    desc += '\\nfile exist:' + ds[direction+'Location']  # ToLocation
                                if ds.get('_ToTargetExpired',False) == True:
                                    desc += '\\nExpired file date is ' + ds.get(direction+'LastTime',"")
                                    errFlag = True
                                else :
                                    if self.debug:
                                        desc += '\\nfile date is ' + ds.get(direction+'LastTime',"")
                                if ds.get('_result_'+direction+'ShowCheckPoint','') != '':   # _result_ToShowCheckPoint
                                    a= ds.get('_result_'+direction+'ShowCheckPoint','').split('\n')   # _result_ToShowCheckPoint
                                    desc += '\\n' + '\\n'.join(a)
                                if ds.get(direction+'FailCheckPoint','').strip() and ds.get('_final_result_'+direction+'FailCheckPoint',False) == True:  # '_final_result_ToSuccessCheckPoint'
                                    errFlag = True
                                    desc += '\\nError : matched Fail condition - ' + ds.get(direction+'FailCheckPoint',"")
                                else :
                                    if self.debug:
                                        desc += '\\nFail condition - ' + ds.get(direction+'FailCheckPoint',"")
                                if ds.get(direction+'SuccessCheckPoint','').strip() and ds.get('_final_result_'+direction+'SuccessCheckPoint',True) == False:  # '_final_result_ToSuccessCheckPoint'
                                    errFlag = True
                                    desc += '\\nError : not matched Success condition - ' + ds.get(direction+'SuccessCheckPoint',"")
                                else :
                                    if self.debug:
                                        desc += '\\nSuccess condition - ' + ds.get(direction+'SuccessCheckPoint',"")

                            elif ds[direction+'Location'] != '':
                                desc += '\\nError file not exist:' + ds[direction+'Location']  # ToLocation
                                errFlag = True

                            if errFlag:
                                color += '#line:red;line.bold;text:red'
                            else:
                                color += '#line:green;line.dashed;text:green'
                        totalbody += '    (' + ds['_execution'] + ') --> (' + n + ') ' + color + ' : desc - ' + desc + '\n'
            totalbody += '  }\n'
            plantumltail = ''
            plantumltail += '@enduml' + '\n'
            plantumltail += "```\n"
            f = open(p + '.md','w')
            f.write(plantumlhdr + plantumlbody + plantumltail)
            f.close()
        totaltail = ''
        totaltail += '@enduml' + '\n'
        totaltail += "```\n"
        f = open('total.md','w')
        # usecaseExecutionHdr = ''
        # for u in usecaseExecutionSet:
        #     usecaseExecutionHdr += 'usecase (' + u + ')\n'
            # usecaseExecutionHdr += 'usecase (' + u + ') << execution >> \n'
            # usecaseExecutionHdr += '(' + u + ') as (' + u + ') << Execution >> \n'
        # f.write(totalhdr + usecaseExecutionHdr + totalbody + totaltail)
        f.write(totalhdr + totalbody + totaltail)
        f.close()

 


def get_process(limit=10):
    argv = sys.argv
    for i,v in enumerate(argv):
        if v == '--authpasswd':
            argv.pop(i)
            argv.pop(i)
    allPath = ' '.join(argv)

    return allPath

def traverseFD(f,vv,start:str):
    # print(start," ",file=f)
    if isinstance(vv, dict):
        print(start ,  " = {}", sep="", file=f)
        for k, v in vv.items():
            traverseFD(f,v,start + "['" + str(k)  + "']")
    elif isinstance(vv, (list, tuple)):
        for i, x in enumerate(vv):
            traverseFD(f,x,start + "[list:" + str(i) + "]" )
    else :
        print(start ,  " = '''", vv , "'''", sep="", file=f)

def traverseFile(filename:str,v,start:str,att):
    with open(filename, att, encoding='utf-8', errors='ignore') as f:
        traverseFD(f,v,start)

if (__name__ == "__main__"):

    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=
        sys.argv[0] + ' generates plantuml for process map'
    )
    # group = parser.add_mutually_exclusive_group()
    #group.add_argument("-v", "--verbose", action="store_true")
    #group.add_argument("-q", "--quiet", action="store_true")

    parser.add_argument(
        '--authname',
        default='None',
        metavar="<id>",
        type=str,
        help='host id  ex) cheoljoo.lee    without @')

    parser.add_argument(
        '--authpasswd',
        default='None',
        metavar="<passwd>",
        type=str,
        help='host passwd')

    parser.add_argument( '--input', default='processmap.csv',metavar="<str>", type=str, help='input csv file')
    parser.add_argument( '--debug', default=False,action="store_true", help='for debug')

    args = parser.parse_args()



    dpm = DrawProcessMap(input= args.input,id=args.authname,passwd=args.authpasswd,debug=args.debug)
    dpm.drawMap()
