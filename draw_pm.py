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
    def __init__(self , input):
        self.input = input
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
        with open(self.input,'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print('fieldnames:',reader.fieldnames)
            for r in reader:
                if 'Project' not in r:
                    print("Project column should be exist in this csv file.")
                    quit(4)
                tmp = r['Project'].strip()
                if not tmp or tmp[0] == '#':
                    continue
                self.setValue(r)

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
        traverseFile("sample.py",self.D,'D',"w")

        # fsc = r['FromSuccessCheckPoint'].strip()
        # self.parseCheckPoint(fsc,r,'FromSuccessCheckPoint')
        # ffc = r['FromFailCheckPoint'].strip()
        # self.parseCheckPoint(ffc,r,'FromFailCheckPoint')
        # tsc = r['ToSuccessCheckPoint'].strip()
        # self.parseCheckPoint(tsc,r,'ToSuccessCheckPoint')
        # tfc = r['ToFailCheckPoint'].strip()
        # self.parseCheckPoint(tfc,r,'ToFailCheckPoint')

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
            totalhdr += 'package ' + g + '{\n'
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
            for k in self.D['Project'][p]['Key']:
                totalbody += '  rectangle ' + p + '{\n'
                usecaseExecutionSet = set()
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


    parser.add_argument( '--input', default='processmap.csv',metavar="<str>", type=str, help='input csv file')

    args = parser.parse_args()



    dpm = DrawProcessMap(input= args.input)
    dpm.drawMap()
