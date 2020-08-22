from django.http import HttpResponse
from django.shortcuts import render
from .models import headt,commit_table,sha_table,cred,commit_info,code_info
from django.db import connection
from django.http import HttpResponseRedirect
import datetime
import hashlib

def cleartable(request):
    with connection.cursor() as cursor:
        cursor.execute("delete from vc_sha_table;")
        cursor.execute("delete from vc_commit_table;")
        cursor.execute("delete from vc_headt;")
        cursor.execute("delete from vc_commit_info;")
    return HttpResponseRedirect('/')

def get_text(lastinv,hh):
    num=str(hh)
    strg=""
    dic={}
    for line in commit_table.objects.filter(code=lastinv).all():
        shas=line.key[hh-1]
        shas=shas[1:-1]
        text=sha_table.objects.filter(pk=shas).values('string')
        if(text.count()==0):
            continue
        text=text[0]["string"]
        if(text=="null"):
            continue
        dic[line.linenum]=str(text)+"\r\n"
    for i in sorted(dic):
        strg+=str(dic[i])
    return strg

def editor(request):
    if request.method == 'POST':
        essay=request.POST['text']
        fixedcode=request.session['code']
        fixedemail=request.session['email']
        text=essay.splitlines()
        head=headt.objects.get(pk=fixedcode)
        hh=head.nextcommit
        num=str(hh)
        line=1
        q=commit_info.objects.filter(code=fixedcode)
        if q.count()==0:
            q=commit_info(code=str(fixedcode),commit_email=["null"])
            q.save()
        q=commit_info.objects.filter(code=fixedcode)
        q=q[0]
        q.commit_email.append(str(fixedemail))
        q.last_commit_time=datetime.datetime.now()
        q.last_commit_date=datetime.date.today()
        q.save()
        for strg in text:
            result = hashlib.sha1(strg.encode())
            result = result.hexdigest()
            result=str(result)
            if sha_table.objects.filter(sha=result).count()==0:
                q=sha_table(sha=result,string=strg)
                q.save()
            result = "\'"+result+"\'"
            if line<=commit_table.objects.filter(code=fixedcode).count():
                q=commit_table.objects.filter(code=fixedcode)
                q=q.filter(linenum=line)
                q=q[0]
                q.key[hh-1]=result
                q.save()
            else:
                arr=[]
                for i in range(0,1000):
                    arr.append('null')
                q=commit_table(code=fixedcode,linenum=line,key=arr)
                #q.save()
                #q=commit_table.objects.filter(code=fixedcode)
                #q=q.filter(linenum=line)
                #q=q[0]
                q.key[hh-1]=result
                q.save()
            line=line+1
        head.head=head.nextcommit
        head.nextcommit+=1
        head.save()
        return HttpResponseRedirect("/edit")
    else:
        lastemail=request.session['email']
        lastinv=request.session['code']
        head=headt.objects.filter(pk=lastinv)
        if head.count()==0:
            q=headt(code=lastinv,head=1,nextcommit=1)
            q.save()
        head=headt.objects.get(pk=lastinv)
        hh=head.head
        strg=get_text(lastinv,hh)
        return render(request, 'vc/editor.html',{'savedtext':strg , 'code': lastinv , 'email' : lastemail})
    

def index(request):
    if request.method=='POST':
        q=cred.objects.filter(pk=request.POST['email'])
        if q == []:
            return HttpResponseRedirect("/")
        if q.count()==0:
            return HttpResponseRedirect('/')
        q=q[0]
        if q.password==request.POST['pass1']:
            request.session['email']=request.POST['email']
            return HttpResponseRedirect('/codes')
        return HttpResponseRedirect("/")
    return render(request,'vc/index.html')

def codes(request):
    if request.method=='POST':
        flag=0
        q=code_info.objects.filter(code=request.POST['code'])
        if q.count()==0:
            return HttpResponseRedirect('/codes')
        q=q[0]
        for data in q.email:
            if data==request.session['email']:
                flag=1
                request.session['code']=request.POST['code']
        if flag==1:
            return HttpResponseRedirect('/edit')
    return render(request,'vc/codes.html')

def createcode(request):
    if request.method=='POST':
        q=code_info.objects.filter(code=request.POST['code2'])
        if q.count()==0:
            q=code_info(code=request.POST['code2'], email=[])
            q.email.append(request.session['email'])
            q.save()
    return HttpResponseRedirect("/codes")

def share(request):
    if request.method=='POST':
        flag=0
        q=code_info.objects.filter(code=request.session['code'])
        if q.count()==0:
            return HttpResponseRedirect('/share')
        q=q[0]
        ll=cred.objects.filter(email=request.POST['email'])
        if ll.count()==0 or request.session['email']!=q.email[0]:
            return HttpResponseRedirect('/share')
        for data in q.email:
            if data==request.POST['email']:
                flag=1
        if flag==0:
            q.email.append(request.POST['email'])
            q.save()
            return HttpResponseRedirect('/edit')
        else:
            return HttpResponseRedirect('/share')
    return render(request,'vc/shares.html')


def signup(request):
    if request.method=='POST':
        q=cred.objects.filter(email=request.POST['email2'])
        q.filter(password=request.POST['pass2'])
        if q.count()==0:
            q=cred(email=request.POST['email2'], password=request.POST['pass2'])
            q.save()
    return HttpResponseRedirect("/")

def rollback(request):
    if request.method=='POST':
        newh=int(request.POST['head'])
        head=headt.objects.get(pk=request.session['code'])
        head.head=min(head.nextcommit-1,newh)
        head.save()
        return HttpResponseRedirect("/edit")
    else:
        ll=headt.objects.get(pk=request.session['code'])
        head=ll.head
        arr=[]
        for i in range(ll.nextcommit-1,0,-1):
            eml=commit_info.objects.get(pk=request.session['code'])
            eml=eml.commit_email[i]
            temp={}
            temp['id']=i
            temp['email']=eml
            temp['text']=get_text(request.session['code'],i)
            arr.append(temp)
        return render(request,'vc/roll.html',{'arr':arr,'email':request.session['email'],'code':request.session['code']})


def comp(request):
    if request.method=='POST':
        a=int(request.POST['one'])
        b=int(request.POST['two'])
        a=get_text(request.session['code'],a)
        b=get_text(request.session['code'],b)
        dic= lcs(a,b)
        
        res=dic[2]
        stra="<span type=\""+dic[0][0]+"\">"
        line=0
        j=-1
        for i in range(len(a)):
            if i<=j:
                continue
            j=i
            if a[i:i+2]=="\r\n":
                stra+="</span><br>"
                if line+1<len(dic[0]):
                    stra+="<span type=\""+dic[0][line+1]+"\">"
                j+=2
                line+=1
                continue
            if res[i]==1:
                stra+="<font color=\"green\">"
                stra+=a[i]
                while(j+1<len(a) and res[j+1]==1 and a[j:j+2]!="\r\n"):
                    j+=1
                    stra+=a[j]
                stra+="</font>"
            else:
                stra+="<font color=\"red\">"
                stra+=a[i]
                while(j+1<len(a) and res[j+1]==0 and a[j:j+2]!="\r\n"):
                    j+=1
                    stra+=a[j]
                stra+="</font>"
            if  a[j:j+2]=="\r\n":
                stra+="</span><br>"
                if line+1<len(dic[0]):
                    stra+="<span type=\""+dic[0][line+1]+"\">"
                j+=2
                line+=1
                continue
        res=dic[3]
        strb="<span type=\""+dic[1][0]+"\">"
        line=0
        j=-1
        for i in range(len(b)):
            if j>=i:
                continue
            j=i
            if b[i:i+2]=="\r\n":
                strb+="</span><br>"
                if line+1<len(dic[1]):
                    strb+="<span type=\""+dic[1][line+1]+"\">"
                j+=2
                line+=1
                continue
            if res[i]==1:
                strb+="<font color=\"green\">"
                strb+=b[i]
                while(j+1<len(b) and res[j+1]==1 and b[j+1:j+1+2]!='\r\n'):
                    j+=1
                    strb+=b[j]
                strb+="</font>"
            else:
                strb+="<font color=\"red\">"
                strb+=b[j]
                while(j+1<len(b) and res[j+1]==0 and b[j+1:j+2+1]!='\r\n'):
                    j+=1
                    strb+=b[j]
                strb+="</font>"
            if b[j:j+2]=="\r\n":
                strb+="</span><br>"
                if line+1<len(dic[1]):
                    strb+="<span type=\""+dic[1][line+1]+"\">"
                j+=2
                line+=1
                continue
        return render(request,'vc/showside.html',{'m1':stra,'m2':strb,'c1':request.POST['one'],'c2':request.POST['two']})
    else:
        ll=headt.objects.get(pk=request.session['code'])
        head=ll.head
        arr=[]
        for i in range(ll.nextcommit-1,0,-1):
            eml=commit_info.objects.get(pk=request.session['code'])
            eml=eml.commit_email[i]
            temp={}
            temp['id']=i
            temp['email']=eml
            temp['text']=get_text(request.session['code'],i)
            arr.append(temp)
        return render(request,'vc/compare.html',{'arr':arr,'email':request.session['email'],'code':request.session['code']})


def lcs(a,b):
    dp=[[0 for i in range(len(b)+1)] for j in range(len(a)+1)]
    resa=[0]*len(a)
    resb=[0]*len(b)
    for i in range(1,len(a)+1):
        for j in range(1,len(b)+1):
            dp[i][j]=max(dp[i-1][j],dp[i][j-1])
            if a[i-1]==b[j-1]:
                dp[i][j]=max(dp[i][j],dp[i-1][j-1]+1)
    ans=""
    i=len(a)
    j=len(b)
    while dp[i][j]!=0:
        if i>=0 and j>=0 and dp[i][j]>dp[i-1][j] and dp[i][j]!=dp[i][j-1]:
            resa[i-1]=1
            ans+=a[i-1]
            resb[j-1]=1
            i-=1
            j-=1
        if i>=0 and dp[i][j]==dp[i-1][j]:
            i-=1
        if j>=0 and dp[i][j]==dp[i][j-1]:
            j-=1
    ans=ans[::-1]
    
    
    diffA=[]
    diffB=[]
    i=0
    j=0
    lineA=0
    lineB=0
    # 0 changed
    # 1 removed / added
    # 2 same
    
    while i<len(a) or j<len(b):
        
        wordsA=0
        matchA=0
        while(True):
            wordsA=0
            matchA=0
            while i<len(a) and a[i:i+2]!="\r\n":
                wordsA+=1;
                if resa[i]==1:
                    matchA+=1
                i+=1
                
            i+=2
            lineA+=1
            if wordsA>0 and matchA==0:
                diffA.append('add')
            else:
                break
        
        wordsB=0
        matchB=0
        
        while(True):
            wordsB=0
            matchB=0
            while j<len(b) and b[j:j+2]!="\r\n":
                wordsB+=1;
                if resb[j]==1:
                    matchB+=1
                j+=1
                
            j+=2
            lineB+=1
            if wordsB>0 and matchB==0:
                diffB.append('remove')
            else:
                break
        
        
        if(matchA==matchB and wordsA==matchA and wordsB==matchB and wordsA>0):
            diffA.append('same')
            diffB.append('same')
            continue
        
        Blist=1        
        Alist=1
        if i>len(a):
            Alist=0
        if j>len(b):
            Blist=0
        
        while matchA!=matchB and i<len(a) and j<len(b):
            if(matchA>matchB and j<len(b)):
                while j<len(b) and b[j:j+2]!="\r\n":
                    if resb[j]==1:
                        matchB+=1
                    j+=1
                j+=2
                lineB+=1
                Blist+=1
            elif i<len(a):
                while i<len(a) and a[i:i+2]!="\r\n":
                    if resa[i]==1:
                        matchA+=1
                    i+=1
                i+=2
                lineA+=1
                Alist+=1
        
        for ind in range(Alist):
            diffA.append('changed')
        for ind in range(Blist):
            diffB.append('changed')
    
    dict={0:diffA,1:diffB,2:resa,3:resb}
    return dict
#lcs("abc\r\ndefgh\r\nijklmnopq\r\nrstuvw\r\nxyz","abc\r\ndefgh\r\nhrs\r\nstuv\r\nabcdefgh")
                   
