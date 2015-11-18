# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import path

from flask import Flask, make_response, render_template, request, abort, redirect, url_for, Markup

# Import the helper functions
from identitytoolkit import gitkitclient
import json
import hashlib
import dataset
app = Flask(__name__)
app.debug = True
output=""
# Import the configuration file you downloaded from Google Developer Console
server_config_json = path.join(path.dirname(path.realpath(__file__)), 'gitkit-server-config.json')
gitkit_instance = gitkitclient.GitkitClient.FromConfigFile(
      server_config_json)

def makeList(database,filters,table):
    try:
        print filters
        query="SELECT * FROM users WHERE 1=1"
        for item in filters:
            print item
            if(item[0]!=1):
                query+=" AND "+str(item[0])+" = \'"+str(item[1])+"\'"
            print query
        query+=" ORDER BY total_Ks DESC;"
        print query
        test=database.query(query)
        test=list(test)
    except:
        print "Nope!"
    for user in test:
        user=dict(user)
        table+='<tr><td><a href="'+str(url_for('view',user_id=user['id'],page=1))+'">'+user['name']+'</a></td><td>'+str(user['total_Ks'])+'</td>'
        table+='<td>'+str(user['division'])+'</td><td>'+str(user['acct_type'])+'</td><td>'+str(user['team'])+'</td></tr>'
    return table

@app.route("/", methods=['GET', 'POST'])
def index():
  text = "You are not signed in."

  # Check for and read the Google Identity Toolkit token if present
  if 'gtoken' in request.cookies:
    gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
    if gitkit_user:
      database = dataset.connect('sqlite:///Skidata.db')
      
      users=database.get_table('users')
      match=0
      if(match==0):
        inData=vars(gitkit_user)
        key=str(inData['user_id'])
        for info in inData:
            if(info=='name'):
                continue;
            out=str(inData[info])
            data={'user_id':key,info:out}
            print data
            if(info!='email_verified'):
                try:
                    users.upsert(data,['user_id'],ensure=True)
                except:
                    return redirect(url_for('index'))
            else:
                if(out=='True'):
                    out=1
                else:
                    out=0
                data={'user_id':key,info:out}
                users.upsert(data,['user_id'],ensure=True)
            
            
        if(users.columns.count('total_Ks')==0):
            users.upsert({'user_id':key,'total_Ks':None},['user_id'],ensure=True)
            print "Added total_Ks"
        if(users.columns.count('team')==0):
            users.upsert({'user_id':key,'team':None},['user_id'],ensure=True)
            print "Added team"
        if(users.columns.count('division')==0):
            users.upsert({'user_id':key,'division':None},['user_id'],ensure=True)
            print "Added division"
        if(users.columns.count('name')==0):
            users.upsert({'user_id':key,'name':None},['user_id'],ensure=True)
            print "Added name"
        try:
            me=dict(users.find_one(user_id=key))
            if(me['acct_type']==None):
                users.upsert({'user_id':key,'acct_type':"Student"},['user_id'],ensure=True)
        except:
            users.upsert({'user_id':key,'acct_type':"Student"},['user_id'],ensure=True)
        try:
            me=dict(users.find_one(user_id=key))
            if(me['acct_type']=="Student"):
                return redirect(url_for('profile'))
        except:
            print "Um..."
        
        text = "Welcome " + str(gitkit_user.name)
      else:
        text = "Welcome back " + user['name']
  response = make_response(render_template('index.html', CONTENT=text))
  response.headers['Content-Type'] = 'text/html'
  return response

@app.route("/widget", methods=['GET', 'POST'])
def signInPage():

  response = make_response(render_template('widget.html'))

  # OPTIONAL (only for Yahoo support): Take information sent by POST request to the sign-in-page and forward it to the Javascript
  #post_body = ''
  #if request.method == 'POST':
  #   post_body = urlencode(request.data)
  #response = make_response(render_template('sign-in-page.html', 
  #                                         POST_BODY=post_body))

  response.headers['Content-Type'] = 'text/html'
  return response


@app.route("/home",methods=['GET','POST'])
def home():
    if(request.method=='POST'):
        form=request.form
        form=dict(form)
        table='<tr> Filtering by: '
        filters=[[1,1]]
        if(form['typefilter']!=[u'None']):
            filters.append(['acct_type',form['typefilter'][0]])
            table+='<td>'+str(form['typefilter'][0])+'</td>'
        if(form['divisionfilter']!=[u'None']):
            filters.append(['division',form['divisionfilter'][0]])
            table+='<td>'+str(form['divisionfilter'][0])+'</td>'
        table+='</tr>'
        if(table=='<tr> Filtering by: </tr>'):
            table=''
        try:
            database=dataset.connect('sqlite:///Skidata.db')
            users=database.get_table('users')
            table=makeList(database,filters,table)
            print table
            table=Markup(table)
        except:
            table=Markup('<tr><td>It did not work. Sorry.</td></tr>')
        response=render_template('home.html',TABLE=table)
        return response
        print form
    if 'gtoken' in request.cookies:
        gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
        table=''
        teamtable=''
        if(gitkit_user and request.method!='POST'):
            key=str(vars(gitkit_user)['user_id'])
            try:
                database=dataset.connect('sqlite:///Skidata.db')
                try:
                    teams=database.query("SELECT * FROM teams WHERE team != '' ORDER BY total_Ks DESC")
                    for team in teams:
                        team= dict(team)
                        print team['team']
                        teamtable+='<tr><td>'+team['team']+'</td><td>'+str(team['total_Ks'])+'</td></tr>'
                except:
                    print "team fail"
                if(teamtable!=''):
                    teamtable=Markup(teamtable)
                users=database.get_table('users')
                filters=[[1,1]]
                table=makeList(database,filters,table)
                table=Markup(table)
            except:
                table=Markup('<tr><td>There is nobody in that category. Try a different filter.</td></tr>')
            response=render_template('home.html',TABLE=table,TEAMTABLE=teamtable)
            return response
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route("/enter", methods=['GET','POST'])
def enter():
  if 'gtoken' in request.cookies:
    gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
    if gitkit_user:
        key=str(vars(gitkit_user)['user_id'])
  if(request.method=='POST'):
    hi=request.form['text']
    workouttype = request.form['type']
    try:
        hi=float(hi)
        try:
            database = dataset.connect('sqlite:///Skidata.db')
            
            users=database.get_table('users')
            try:
                find=dict(users.find_one(user_id=key))
                total=find['total_Ks']
                if(total==None):
                    if(workouttype=="Classic"):
                        total=hi*1.2
                    else:
                        total=hi
                else:
                    if(workouttype=="Classic"):
                        total+=hi*1.2
                    else:
                        total+=hi
            except:
                total=hi
            workoutnum="workout"
            typenum="type"
            lastCol=1
            try:
                test=find[workoutnum+str(lastCol)]
                while(test!=None):
                    lastCol+=1
                    test=find[workoutnum+str(lastCol)]
                if(find[workoutnum+str(lastCol)]==None):
                    workoutnum+=str(lastCol)
                    typenum+=str(lastCol)
                    print workoutnum
                    users.upsert({'user_id':key,workoutnum:hi,typenum:workouttype},['user_id'])
                
                
                users.upsert({'user_id':key,'total_Ks':total},['user_id'],ensure=True)
            except:
                print lastCol
                workoutnum+=str(lastCol)
                typenum+=str(lastCol)
                print "Last workout at: "+str(lastCol)
                try:
                    users.upsert({'user_id':key,'total_Ks':total},['user_id'],ensure=True)
                    
                    
                except:
                    print "Total doesn't exist for some reason"
                users.upsert({'user_id':key,workoutnum:hi,typenum:workouttype},['user_id'],ensure=True)
            
        except:
            print "Connection FAIL!"
        global output
        output=str(hi)+" Ks added!"
    except:
        output="I know you wish that "+hi+" was a number, but it is not. Sorry, try again."
        response = make_response(render_template('addKs.html',QUESTION=output))
        response.headers['Content-Type'] = 'text/html'
        return response
  else:
    response = make_response(render_template('addKs.html',QUESTION="How many Ks"))
    response.headers['Content-Type'] = 'text/html'
    return response
  return redirect(url_for('home'))

@app.route("/manage/<page>",methods=['GET','POST'])
def manage(page):
    if 'gtoken' in request.cookies:
        gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
        if gitkit_user:
            key=str(vars(gitkit_user)['user_id'])
    if request.method=='POST':
        hi=request.form
        delete=int(dict(hi).keys()[0])
        try:
            database=dataset.connect('sqlite:///Skidata.db')
            
            users=database.get_table('users')
            me=dict(users.find_one(user_id=key))
            base="workout"
            base2="type"
            test=delete+1
            WOtype=me[base2+str(delete)]
            if(WOtype=="Classic"):
                me['total_Ks']-=1.2*int(me[base+str(delete)])
            else:
                me['total_Ks']-=int(me[base+str(delete)])
            while(test>0):
                test=delete+1
                print delete
                try:
                    if(me[base+str(delete)]!=None):
                        print me[base+str(delete)]
                        me[base+str(delete)]=me[base+str(test)]
                        me[base2+str(delete)]=me[base2+str(test)]
                        delete+=1
                    else:
                        test=0
                except:
                    me[base+str(delete)]=None
                    me[base2+str(delete)]=None
                    test=0
                    print "Double Fail!"
            users.update(me,['id'])
            
        except:
            print "Fail!"
        table=Markup('<tr><td>It worked!</td></tr>')
        response=make_response(render_template('Workouts.html',TABLE=table,NEXT="url_for('manage',page="+str(int(page)+1)+")"))
        response.headers['Content-Type'] = 'text/html'
        return redirect(url_for('manage',page=page))
    else:
        rows=['','','']
        page=int(page)
        if(page<0):
            page=1
        i=14*(page-1)+1

        while(i>0 and i<15*page):
            form=''
            write=''
            info=''
            #print form
            try:
                database = dataset.connect('sqlite:///Skidata.db')
                
                users=database.get_table('users')
                me=dict(users.find_one(user_id=key))
                
                base="workout"
                if(me[base+str(i)]!=None):
                    form='<form action='+str(url_for("manage",page=1))+' method="POST"><input type="submit" name='+str(i)+' value="delete"></form>'
                    write='Workout '+str(i)+':'
                    info=str(me[base+str(i)])+' Ks '+str(me["type"+str(i)])
                    i+=1
                else:
                    i=0
            except:
                i=0
            rows[0]+='<td>'+write+'</td>'
            rows[1]+='<td>'+form+'</td>'
            rows[2]+='<td>'+info+'</td>'
        print rows
        if(rows[0]=='<td></td>'):
            rows[0]='<td>Sorry, no content here. Try going back a page</td>'
        table=Markup('<tr>'+rows[0]+'</tr><tr>'+rows[2]+'</tr><tr>'+rows[1]+'</tr>')
        response=make_response(render_template('Workouts.html',TABLE=table,PREV=str(int(page)-1),NEXT=str(int(page)+1)))
        response.headers['Content-Type'] = 'text/html'
        return response
@app.route("/admin",methods=['GET','POST'])
def admin():
  if 'gtoken' in request.cookies:
    gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
    if gitkit_user:
        if(request.method=='POST'):
            form=request.form
            form=dict(form)
            keys=form.keys()
            insert=[]
            for key in keys:
                if(key=="acct_type"):
                    insert.append(['acct_type',form['acct_type'][0]])
                elif(key=="division"):
                    insert.append(['division',form['division'][0]])
                elif(key=="team"):
                    insert.append(['team',form['team'][0]])
                else:
                    insert.append(['user_id',key])
            print insert
            print {insert[0][0]:insert[0][1],insert[1][0]:insert[1][1]}
            database=dataset.connect('sqlite:///Skidata.db')
            
            users=database.get_table('users')
            users.update({insert[1][0]:insert[1][1],insert[0][0]:insert[0][1]},['user_id'],ensure=True)
            
            return redirect(url_for('admin'))
            print form
        database=dataset.connect('sqlite:///Skidata.db')
        key=vars(gitkit_user)['user_id']
        
        users=database.get_table('users')
        me=dict(users.find_one(user_id=key))
        print me['acct_type']
        if(me['acct_type']!="Coach"):
            print "DENIED user"+key
        else:
            everybody=users.all()
            out='<tr><td></td></tr>'
            for person in everybody:
                person=dict(person)
                print person['name']
                out+='<tr><td><a href="'+str(url_for('view',user_id=person['id'],page=1))+'">'+person['name']+'</a></td><td>'
                form='<form action='+str(url_for("admin"))+' method="POST"><input type="submit" name='+person['user_id']+' value="Send">'
                divisionoptions=[]
                divisionoptions=["Other","Upperclassmen","Underclassmen","Middle_School","Coach"]
                location=divisionoptions.index(person['acct_type'])
                temp=divisionoptions[0]
                divisionoptions[0]=person['acct_type']
                divisionoptions[location]=temp
                form+='<select name ="acct_type">'
                for i in divisionoptions:
                    form+='<option value='+i+'>'+i+'</option>'
                
                form+='</select></form></td><td>'
                out+=form
                form='<form action='+str(url_for("admin"))+' method="POST"><input type="submit" name='+person['user_id']+' value="Send">'
                divisionoptions=[]
                divisionoptions=["Red","White","Other","Coach"]
                try:
                    location=divisionoptions.index(person['division'])
                    temp=divisionoptions[0]
                    divisionoptions[0]=person['division']
                    divisionoptions[location]=temp
                except:
                    print "Welp. The divisions are all screwy!"
                form+='<select name ="division">'
                for i in divisionoptions:
                    form+='<option value='+i+'>'+i+'</option>'
                
                form+='</select></form></td><td>'
                out+=form
                form='<form action='+str(url_for("admin"))+' method="POST"><input type="submit" name='+person['user_id']+' value="Send">'
                try:
                    person['team']
                    form+='<input type="text" name="team" value='+str(person['team'])+'>'
                except:
                    form+='<input type="text" name="team" >'
                form+='</input>'
                out+=form
                if(person['total_Ks']!=None):
                    out+=str(person['total_Ks'])+' Ks</td></tr>'
                else:
                    out+=str(person['total_Ks'])+'</td></tr>'
            print out
            out=Markup(out)
            response=make_response(render_template('Students.html',TABLE=out))
            response.headers['Content-Type'] = 'text/html'
            return response
        
  return redirect(url_for('home'))
@app.route("/profile",methods=['GET','POST'])
def profile():
    if(request.method=='GET'):
        response=make_response(render_template('SetUp.html'))
        return response
    else:
        if 'gtoken' in request.cookies:
            gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
            if gitkit_user:
                info=request.form
                key=str(vars(gitkit_user)['user_id'])
                try:
                    database=dataset.connect('sqlite:///Skidata.db')
                    users=database.get_table('users')
                    
                except:
                
                    print "An error occured"
                    return redirect(url_for('profile'))
                try:
                    users.update(dict(user_id=key,acct_type=info['type']),['user_id'],ensure=True)
                    print "type"
                    users.update({'user_id':key,'division':info['division']},['user_id'],ensure=True)
                    print "division"
                    users.update({'user_id':key,'name':info['text']},['user_id'],ensure=True)
                    print "name"
                except:
                    print "FAIL!"
                    return redirect(url_for('index'))
                
    return redirect(url_for('index'))
@app.route("/view/<user_id>/<page>",methods=['GET','POST'])
def view(user_id,page):
    key=user_id
    print page
    rows=['','','']
    page=int(page)
    if(page<0):
        page=1
    i=14*(page-1)+1
    while(i>0 and i<15*page):
        form=''
        write=''
        info=''
        #print form
        try:
            database = dataset.connect('sqlite:///Skidata.db')
            users=database.get_table('users')
            me=dict(users.find_one(id=key))
            print me
            
            base="workout"
            print i
            if(me[base+str(i)]!=None):
                write='Workout '+str(i)+':'
                info=str(me[base+str(i)])+' Ks '+str(me["type"+str(i)])
                i+=1
            else:
                i=0
        except:
            i=0
        rows[0]+='<td>'+write+'</td>'
        rows[2]+='<td>'+info+'</td>'
    print rows
    if(rows[0]=='<td></td>'):
        rows[0]='<td>Sorry, no content here. Try going back a page</td>'
    table=Markup('<tr>'+rows[0]+'</tr><tr>'+rows[2]+'</tr>')
    response=make_response(render_template('ViewKs.html',TABLE=table,USER=user_id,PREV=str(int(page)-1),NEXT=str(int(page)+1)))
    response.headers['Content-Type'] = 'text/html'
    return response
@app.route("/team",methods=['GET','POST'])
def team():
    print "hi"
    output="Enter the name of a team to join."
    if(request.method=='GET'):
        response=make_response(render_template('TeamSetUp.html',CONTENT=output))
        return response
    else:
        if 'gtoken' in request.cookies:
            gitkit_user = gitkit_instance.VerifyGitkitToken(request.cookies['gtoken'])
            if(gitkit_user):
                key=str(vars(gitkit_user)['user_id'])
                try:
                    database=dataset.connect('sqlite:///Skidata.db')
                    users=database.get_table('users')
                    teams=database.get_table('teams')
                    me=dict(users.find_one(user_id=key))
                    count=0
                    for user in users:
                        user=dict(user)
                        try:
                            if(user['team']==request.form['text']):
                                count+=1
                        except:
                            print "Team not found"
                    if(count<2):
                        try:
                            try:
                                my_team=None
                                for team in teams:
                                    team=dict(team)
                                    if(team['team']==me['team']):
                                        my_team=team
                                Ks=int(my_team['total_Ks'])
                                my_Ks=int(me['total_Ks'])
                                Ks-=my_Ks
                                teams.upsert(dict(team=my_team['team'],total_Ks=Ks),['team'],ensure=True)
                            except:
                                "I am not on a team"
                            users.upsert(dict(user_id=key,team=request.form['text']),['user_id'],ensure=True)
                            try:
                                my_team=None
                                for team in teams:
                                    team=dict(team)
                                    if(team['team']==request.form['text']):
                                        my_team=team
                                print my_team
                                if(my_team==None):
                                    teams.upsert(dict(team=request.form['text'],total_Ks=me['total_Ks']),['team'],ensure=True)
                                else:
                                    Ks=int(my_team['total_Ks'])
                                    try:
                                        Ks+=int(me['total_Ks'])
                                        teams.upsert(dict(team=request.form['text'],total_Ks=Ks),['team'],ensure=True)
                                    except:
                                        print "I don't have any Ks to give!"
                                    print Ks
                            except:
                                print "Nope"
                                teams.upsert(dict(team=request.form['text'],total_Ks=me['total_Ks']),['team'],ensure=True)
                            output="Welcome to team " +str(request.form['text'])
                        except:
                            print("Error uploading")
                    else:
                        output="Team "+str(request.form['text'])+" is full. Try joining a different team."
                    response=make_response(render_template('TeamSetUp.html',CONTENT=output))
                    return response
                except:
                    print "ERROR 404! User not found!"
        response=make_response(render_template('TeamSetUp.html',CONTENT=output))
        return response
if __name__ == "__main__":
    app.run(port=8000)

