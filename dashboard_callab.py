# coding=utf_8
import os, sys, re
import datetime, requests
import configparser, base64
from atlassian import Confluence
from xml.etree import ElementTree as ET
import argparse

script_folder = os.path.dirname(os.path.realpath(__file__))
build_folder = os.path.dirname(script_folder)

PAGE_TITLE = {
    'CRASH_ERROR' : 'History of Crash ID Report',
    'COVERITY_FAILURE' : ' Coverity: Module failure report',
    'MEASURE_DATA 1' : ' Report Measure Data Daily',
    'MEASURE_DATA 2' : ' Report Measure Data Daily of each-service',
    'CONFIDENCE_INDEX' : ' Confidence Index - Monitor All Committest',
    'HISTORY_COMMITTEST' : ' History of All Commit-test',
    'EMERGENCY_ERROR' : 'Emergency Error Monitor All Projects',
    'TAF_BOARD' : 'TAF : Tiger-Autotest-Framework',
    'MEMORY_LEAK' : ' Memory leak summary',
    'AWARETEST_REPORT' : ' Analyze commit aware service testing',
    'CHECK_ITEMS' : 'Check list items of DailyTest and WeeklyTest',
    'DASH_BOARD' : 'Test.md'
}


class COLLAB_HANDLE:
    confluence = None
    url = "http://collab.lge.com/main"
    page_space = None
    page_title = None
    page_id = None
    body_content = None

    def __init__(self, project_name, page_space="TIGER", mode=None, userCollab=None, passCollab=None):
        self.page_space = page_space
        self.project_name = project_name
        self.confluence = Confluence(url=self.url, username=userCollab, password=passCollab)
        if mode:
            self.UpdateMode(mode)

    def UpdateMode(self, mode):
        if mode in [ 'CRASH_ERROR', 'TAF_BOARD', 'EMERGENCY_ERROR', 'DASH_BOARD']:
            self.page_title = PAGE_TITLE[mode]
        else:
            self.page_title = '[' + self.project_name + ']' + PAGE_TITLE[mode]
        print("UPDATE PAGE: ", self.page_title)
        print(self.GetBodyContent())
        self.body_content = self.GetBodyContent()

    def CheckLegalAuthen(self, page_title):
        if not self.confluence is None:
            if self.confluence.page_exists(space=self.page_space, title=page_title):
                return True
            print('Page not found')
            return None
        print('Object confluence is illegal! Please check the account or config.ini file')
        exit()

    def GetBodyContent(self, page_title=''):
        if page_title == '':
            page_title = self.page_title
        if not self.CheckLegalAuthen(page_title):
            return None
        self.page_id = self.confluence.get_page_id(self.page_space, page_title)
        confluence_content = self.confluence.get_page_by_id(self.page_id)
        confluence_content = ((self.confluence.get_page_by_id(self.page_id, expand="body.storage") or {}).get("body") or {}).get("storage") or {}
        confluence_body_content = confluence_content.get("value")
        print('confluence_body_content:[',confluence_body_content , ']')
        result = ''
        frontArr = confluence_body_content.split('<ac:structured-macro')
        frontList = []
        oldCDATA = {}
        newCDATA = {}
        titleRe = re.compile('<ac:parameter ac:name="title">\s*(?P<title>\S+)\s*</ac:parameter>')
        id = ''
        for s in frontArr:
            grp = titleRe.search(s)
            if grp:
                id = grp.group('title')
                print('title:',id)
            ft = ''
            endList = []
            endArr = s.split(']]></ac:plain-text-body></ac:structured-macro>')
            for e in endArr:
                match = '<ac:plain-text-body><![CDATA['
                idx = e.find(match)
                if idx != -1:
                    oldCDATA[id] = e[idx+len(match):]
                    hdr = e[:idx + len(match)]
                    hdr += '||||' + id + '||||' + '-_-thisIis__your_contentS_*^^*'
                    newCDATA[id] = hdr
                    endList.append(hdr)
                else:
                    endList.append(e)
            ft = ']]></ac:plain-text-body></ac:structured-macro>'.join(endList)
            frontList.append(ft)
        result = '<ac:structured-macro'.join(frontList)
        print('result:',result)
        print('oldCDATA:',oldCDATA)
        print('newCDATA:',newCDATA)
        return result

    def GetTableContent(self, html_str=''):
        if html_str == '':
            html_str = self.body_content
        return re.findall(r'<tbody.*?</tbody>', html_str, flags=re.DOTALL)

    def UpdateTableContent(self, hTable):
        table_content = str(ET.tostring(hTable.root))[2:-1]
        self.body_content = re.sub(r'<tbody.*?</tbody>', table_content, self.body_content, flags=re.DOTALL)

    def UpdateToPage(self, id, body_content):
        user = os.popen('whoami').read().strip()
        print("UPDATE USER: ", user)
        # body = body_content
        self.body_content = self.body_content.replace('||||' + id + '||||' + '-_-thisIis__your_contentS_*^^*' , body_content)
        print("self.body_content:[",self.body_content,']')
        # print("body:[",body,']')
        #body = body.replace('ac_', 'ac:').replace('ri_', 'ri:').replace('\x00', '').replace('\\n', '<br/>')
        print("PAGE ID: ", self.page_id)
        print("PAGE TITLE: ", self.page_title)
    def upload(self):
        self.confluence.update_page(parent_id=None, page_id=self.page_id, title=self.page_title, body=self.body_content)


########### Update TAF Dash Board ##############
def updateDashBoard(username, password):
    print("Update to http://collab.lge.com/main/display/TIGER/TEST.md")
    print(username,password)

    hCollab = COLLAB_HANDLE("", "TIGER", 'DASH_BOARD', username, password)
    uml_path = 'total.md'
    uml_content = ''
    try:
        with open(uml_path, 'r') as r_file:
            uml_content = r_file.read().strip()
            # update_content = "</ac_parameter><ac_rich-text-body><p>" + uml_content + "</p></ac_rich-text-body></ac_structured-macro>"
            #hCollab.body_content = re.sub(r'(</ac_parameter><ac_rich-text-body><p>).*?(</p></ac_rich-text-body></ac_structured-macro>)', update_content, hCollab.body_content, flags=re.DOTALL).replace('\n', '<br/>')
            hCollab.UpdateToPage('total.md',uml_content)
        with open('intuitiveui.md', 'r') as rf:
            u2 = rf.read().strip()
            # update_content = "</ac_parameter><ac_rich-text-body><p>" + uml_content + "</p></ac_rich-text-body></ac_structured-macro>"
            #hCollab.body_content = re.sub(r'(</ac_parameter><ac_rich-text-body><p>).*?(</p></ac_rich-text-body></ac_structured-macro>)', update_content, hCollab.body_content, flags=re.DOTALL).replace('\n', '<br/>')
            hCollab.UpdateToPage('second',u2)
        hCollab.upload()
    except Exception as e:
        print(e)

    print("DONE!")
    return


###### MAIN ######

if (__name__ == "__main__"):
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=
        sys.argv[0] + ' generates plantuml for process map'
    )

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

    args = parser.parse_args()

    ## add your username password
    updateDashBoard(username=args.authname, password=args.authpasswd)


    
