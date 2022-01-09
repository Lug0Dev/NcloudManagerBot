import requests
import os
import textwrap
import re
import json

from bs4 import BeautifulSoup

class MoodleClient(object):
    def __init__(self, user,passw):
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.path = 'http://eva.umcc.cu/posgrado/'
        self.userdata = None
        self.userid = ''

    def getsession(self):
        return self.session    

    def getUserData(self):
        tokenUrl = self.path+'login/token.php?service=moodle_mobile_app&username='+self.username+'&password='+self.password
        resp = self.session.get(tokenUrl)
        return self.parsejson(resp.text)

    def getDirectUrl(self,url):
        tokens = str(url).split('/')
        direct = self.path+'webservice/pluginfile.php/'+tokens[4]+'/user/private/'+tokens[-1]+'?token='+self.data['token']
        return direct

    def login(self):
        login = self.path+'login/index.php'
        resp = self.session.get(login)
        cookie = resp.cookies.get_dict()
        soup = BeautifulSoup(resp.text,'html.parser')
        anchor = soup.find('input',attrs={'name':'anchor'})['value']
        logintoken = soup.find('input',attrs={'name':'logintoken'})['value']
        username = self.username
        password = self.password
        payload = {'anchor': '', 'logintoken': logintoken,'username': username, 'password': password, 'rememberusername': 1}
        loginurl = self.path+'login/index.php'
        resp2 = self.session.post(loginurl, data=payload)
        soup = BeautifulSoup(resp2.text,'html.parser')
        
        counter = 0
        for i in resp2.text.splitlines():
            if "loginerrors" in i or (0 < counter <= 3):
                counter += 1
                print(i)
        if counter>0:
            print('No pude iniciar sesion')
            return False
        else:
            self.userid = soup.find('div',{'id':'nav-notification-popover-container'})['data-userid']
            print('E iniciado sesion con exito')
            self.userdata = self.getUserData()
            return True


    def createEvidence(self,name,desc=''):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidenceurl)
        soup = BeautifulSoup(resp.text,'html.parser')

        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        files = self.extractQuery(soup.find('object')['data'])['itemid']



        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=&userid='+self.userid+'&return='
        payload = {'userid':self.userid,
                   'sesskey':sesskey,
                   '_qf__tool_lp_form_user_evidence':1,
                   'name':name,'description[text]':desc,
                   'description[format]':1,
                   'url':'',
                   'files':files,
                   'submitbutton':'Guardar+cambios'}
        resp = self.session.post(saveevidence,data=payload)

        evidenceid = str(resp.url).split('?')[1].split('=')[1]

        return {'name':name,'desc':desc,'id':evidenceid,'url':resp.url,'files':[]}

    def saveEvidence(self,evidence):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id='+evidence['id']+'&userid='+self.userid+'&return=list'
        resp = self.session.get(evidenceurl)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        files = evidence['files']
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id='+evidence['id']+'&userid='+self.userid+'&return=list'
        payload = {'userid':self.userid,
                   'sesskey':sesskey,
                   '_qf__tool_lp_form_user_evidence':1,
                   'name':evidence['name'],'description[text]':evidence['desc'],
                   'description[format]':1,'url':'',
                   'files':files,
                   'submitbutton':'Guardar+cambios'}
        resp = self.session.post(saveevidence,data=payload)
        return evidence

    def getEvidences(self):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid 
        resp = self.session.get(evidencesurl)
        soup = BeautifulSoup(resp.text,'html.parser')
        nodes = soup.find_all('tr',{'data-region':'user-evidence-node'})
        list = []
        for n in nodes:
            nodetd = n.find_all('td')
            evurl = nodetd[0].find('a')['href']
            evname = n.find('a').next
            evid = evurl.split('?')[1].split('=')[1]
            nodefiles = nodetd[1].find_all('a')
            nfilelist = []
            for f in nodefiles:
                directurl = str(f['href']).replace('pluginfile.php','webservice/pluginfile.php') + '&token=' + self.userdata['token']
                nfilelist.append({'name':f.next,'url':directurl})
            list.append({'name':evname,'desc':'','id':evid,'url':evurl,'files':nfilelist})

        return list

    def deleteEvidence(self,evidence):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidencesurl)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        deleteUrl = self.path+'lib/ajax/service.php?sesskey='+sesskey+'&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
        savejson = [{"index":0,"methodname":"core_competency_delete_user_evidence","args":{"id":evidence['id']}},
                    {"index":1,"methodname":"tool_lp_data_for_user_evidence_list_page","args":{"userid":self.userid }}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
        resp = self.session.post(deleteUrl, json=savejson,headers=headers)
        pass



    def upload_file(self,file,evidence,itemid=None):
        fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(fileurl)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        _qf__user_files_form = 1
        query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
        client_id = self.getclientid(resp.text)
        of = open(file,'rb')
        upload_file = {
            'repo_upload_file':(file,of,'application/octet-stream'),
            }

        itempostid = query['itemid']

        if itemid:
            itempostid = itemid

        upload_data = {
            'title':(None,''),
            'author':(None,'ObysoftDev'),
            'license':(None,'allrightsreserved'),
            'itemid':(None,query['itemid']),
            'repo_id':(None,4),
            'p':(None,''),
            'page':(None,''),
            'env':(None,query['env']),
            'sesskey':(None,sesskey),
            'client_id':(None,client_id),
            'maxbytes':(None,query['maxbytes']),
            'areamaxbytes':(None,query['areamaxbytes']),
            'ctx_id':(None,query['ctx_id']),
            'savepath':(None,'/')}
        post_file_url = self.path+'repository/repository_ajax.php?action=upload'
        resp2 = self.session.post(post_file_url, files=upload_file,data=upload_data)
        of.close()

        #save evidence
        evidence['files'] = itempostid

        return itempostid

    def parsejson(self,json):
        data = {}
        tokens = str(json).replace('{','').replace('}','').split(',')
        for t in tokens:
            split = str(t).split(':',1)
            data[str(split[0]).replace('"','')] = str(split[1]).replace('"','')
        return data

    def getclientid(self,html):
        index = str(html).index('client_id')
        max = 25
        ret = html[index:(index+max)]
        return str(ret).replace('client_id":"','')

    def extractQuery(self,url):
        tokens = str(url).split('?')[1].split('&')
        retQuery = {}
        for q in tokens:
            qspl = q.split('=')
            try:
                retQuery[qspl[0]] = qspl[1]
            except:
                 retQuery[qspl[0]] = None
        return retQuery

    def getFiles(self):
        urlfiles = self.path+'user/files.php'
        resp = self.session.get(urlfiles)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        client_id = self.getclientid(resp.text)
        filepath = '/'
        query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
        payload = {'sesskey': sesskey, 'client_id': client_id,'filepath': filepath, 'itemid': query['itemid']}
        postfiles = self.path+'repository/draftfiles_ajax.php?action=list'
        resp = self.session.post(postfiles,data=payload)
        dec = json.JSONDecoder()
        jsondec = dec.decode(resp.text)
        return jsondec['list']
   
    def delteFile(self,name):
        urlfiles = self.path+'user/files.php'
        resp = self.session.get(urlfiles)
        soup = BeautifulSoup(resp.text,'html.parser')
        _qf__core_user_form_private_files = soup.find('input',{'name':'_qf__core_user_form_private_files'})['value']
        files_filemanager = soup.find('input',attrs={'name':'files_filemanager'})['value']
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        client_id = self.getclientid(resp.text)
        filepath = '/'
        query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
        payload = {'sesskey': sesskey, 'client_id': client_id,'filepath': filepath, 'itemid': query['itemid'],'filename':name}
        postdelete = self.path+'repository/draftfiles_ajax.php?action=delete'
        resp = self.session.post(postdelete,data=payload)

        #save file
        saveUrl = self.path+'lib/ajax/service.php?sesskey='+sesskey+'&info=core_form_dynamic_form'
        savejson = [{"index":0,"methodname":"core_form_dynamic_form","args":{"formdata":"sesskey="+sesskey+"&_qf__core_user_form_private_files="+_qf__core_user_form_private_files+"&files_filemanager="+query['itemid']+"","form":"core_user\\form\\private_files"}}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
        resp3 = self.session.post(saveUrl, json=savejson,headers=headers)

        return resp3

#client = MoodleClient('obysoft','Obysoft2001@')
#loged = client.login()
#if loged:
#   list = client.getEvidences()
#   evidence = client.createEvidence('requirements')
#   client.upload_file('requirements.txt',evidence)
#   client.saveEvidence(evidence)
#   print(evidence)