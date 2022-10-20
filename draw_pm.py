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
    def __init__(self , input,id,passwd):
        self.input = input
        self.id = id
        self.passwd = passwd
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
                self.D['Project'][project]['Key'][key][target][f]['_' + s] = self.parseCheckPoint(sc,r,s)

        return (project,f,_group,_name,key)

    def setValue(self,r):
    
        p , f , fg , fn , key = self.getProjectAndGroupAndInit('From',r)
        # p , e , eg , en , key = self.getProjectAndGroupAndInit('Execution',r)
        p , t , tg , tn , key = self.getProjectAndGroupAndInit('To',r)

        row = r
        dateRe = re.compile('(?P<date>(?P<year>20[0-9]+)-(?P<month>[0-9]+)-(?P<day>[0-9]+))')
        for field in row:
            if field in ['FromLocation','ToLocation']:
                a = row[field].strip().split(':')
                if a[0].strip() == 'ssh':
                    hostname = a[1].strip()
                    originFileName = a[2].strip()
                    targetFileName = 'server-data/'+field+'.'+originFileName.replace('/','.')
                    if row['Periodic']:
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
                            file_date = datetime.datetime(int(year),int(month),int(day)) - datetime.timedelta(days=int(r['Periodic']))
                            now_date = datetime.datetime.now() 
                            print('file:',file_date,'old:',now_date,grp.group('date'))
                            if file_date < now_date:  # ok
                                tmp = field.replace('Location','')
                                r[tmp+'LastTime'] = grp.group('date')
                                print('date:',r[tmp+'LastTime'])
                                s = "sshpass -p " + self.passwd + " scp -o StrictHostKeyChecking=no " + self.id + '@' + hostname + ':' + originFileName + ' ' + targetFileName
                                print()
                                print(s)
                                os.system(s)
                                self.analysisLogFile(targetFileName,r)

    def analysisLogFile(self,targetFileName,r):
        
        return

    def parseCheckPoint(self,sc,r,msg):
        idx = 0
        ans = []
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
                        cCom = [ 1]  * len(c)
                        print('cCom:',cCom)
                        for c1 in c:
                            if c1.strip() == '':
                                continue
                            else :
                                d = c1.split('_OR_')
                                for d1 in d:
                                    if d1.strip() == '':
                                        continue
                                    else:
                                        ans.append(d1.strip())
        # print(msg , "sc:",sc,"ans:",ans)
        return ans

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
                        plantumlbody += '    (' + n + ') --> (' + self.D['Project'][p]['Key'][k]['From'][f]['_execution'] + ') : ' + self.D['Project'][p]['Key'][k]['From'][f]['Description'] + '\n'
                        usecaseExecutionSet.add(self.D['Project'][p]['Key'][k]['From'][f]['_execution'])
                for f in self.D['Project'][p]['Key'][k]['To']:
                    for n in self.D['Project'][p]['Key'][k]['To'][f]['_name']:
                        plantumlbody += '    (' + self.D['Project'][p]['Key'][k]['To'][f]['_execution'] + ') --> (' + n + ') : ' + self.D['Project'][p]['Key'][k]['To'][f]['Description'] + '\n'
                        usecaseExecutionSet.add(self.D['Project'][p]['Key'][k]['To'][f]['_execution'])
            for u in usecaseExecutionSet:
                totalbody += '    usecase (' + u  + ') as (' + u + ') << Execution >>\n'
            for k in self.D['Project'][p]['Key']:
                for f in self.D['Project'][p]['Key'][k]['From']:
                    for n in self.D['Project'][p]['Key'][k]['From'][f]['_name']:
                        totalbody += '    (' + n + ') --> (' + self.D['Project'][p]['Key'][k]['From'][f]['_execution'] + ') : ' + self.D['Project'][p]['Key'][k]['From'][f]['Description'] + '\n'
                for f in self.D['Project'][p]['Key'][k]['To']:
                    for n in self.D['Project'][p]['Key'][k]['To'][f]['_name']:
                        totalbody += '    (' + self.D['Project'][p]['Key'][k]['To'][f]['_execution'] + ') --> (' + n + ') : ' + self.D['Project'][p]['Key'][k]['To'][f]['Description'] + '\n'
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

    args = parser.parse_args()



    dpm = DrawProcessMap(input= args.input,id=args.authname,passwd=args.authpasswd)
    dpm.drawMap()
