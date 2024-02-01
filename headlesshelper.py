
from langchain.llms import GooglePalm

import google.generativeai as genai

from bs4 import BeautifulSoup

import time

import langchain

import copy

import regex as re
import time
#import pywhatkit
from datetime import datetime

from selenium import webdriver

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
import os


langchain.debug=True

API=""
PALM_API=""


genai.configure(api_key=API)


def getmodelP():
    llm=GooglePalm(google_api_key=PALM_API,temperature=0.3,maxOutputTokens=512)
    return llm

def getmodel():
    return genai.GenerativeModel("gemini-pro")

def getvision():
    return genai.GenerativeModel("gemini-pro-vision")

def queryimage(mdl,prompt,img):
    response=mdl.generate_content([prompt,img])
    response.resolve()
    return (response.text)
    
def querytext(mdl,prompt):
    #print(prompt)
    response=mdl.generate_content(prompt)
    return (response.text)  

llm=getmodel()



manager=f"""

You play the role of a website navigation assistant. Your mission is to analyze the user's query and deduce its intent without executing it. The potential intents are:

- `open-url`: Navigate to a specific URL.
- `extract-text`: Extract text from the webpage.
- `extract-elements`: Extract a particular website element from the webpage.
- `click-button`: Click a specific button on the website.
- `click-link`: Click a specific link on the webpage.
- `type-text`: Input text on a text field/input box on the website.
- `QUIT`: Quit all connections.
- `UNKNOWN`: Unable to infer the intent.

Return `UNKNOWN` if the intent is unclear.

### Examples:

1. **User:** "Open www.google.com"
   - **Intent:** `open-url`
   - **Explanation:** The user explicitly requests to open a URL.

2. **User:** "What is the weather today?"
   - **Intent:** `UNKNOWN`
   - **Explanation:** The query is not specific to website navigation; hence, the intent is unclear.

3. **User:** "Extract the main article text."
   - **Intent:** `extract-text`
   - **Explanation:** The user is asking to extract text, specifying a particular content type.

4. **User:** "Click on the 'Sign In' button."
   - **Intent:** `click-button`
   - **Explanation:** The user instructs the assistant to perform a click action on a specific webpage button.

5. **User:** "Show me the product images."
   - **Intent:** `extract-elements`
   - **Explanation:** The user wants to extract a specific type of content (images) from the webpage.

6. **User:** "Go to my shopping cart."
   - **Intent:** `open-url`
   - **Explanation:** The user instructs to navigate to a specific section of the website by opening a URL.

7. **User:** "Open the search result that says good aspects."
   - **Intent:** `click-link`
   - **Explanation:** The user instructs to navigate to a specific link listed on the webpage by a click action.

8. **User:** "Type 'Hello' in the search box."
   - **Intent:** `type-text`
   - **Explanation:** The user instructs to input text into a search box.

9. **User:** "click on search"
   - **Intent:** `click-button`
   - **Explanation:** The user instructs to perform a click action on search button.

These examples cover a variety of scenarios, showcasing the user's intent categorized based on the provided options.

Only return the intent and not any explaination.

User:
"""

actor="""

As a website navigation assistant, your role is to decipher the user's intent and extract the details of the requested action from their query, without executing it. The potential intents and their corresponding actions are defined as follows:

- `open-url`: Navigate to a specific URL.
- `extract-text`: Extract text from the webpage.
- `extract-elements`: Extract a particular website element from the webpage.
- `click-button`: Click a specific button on the website.
- `click-link`: Click a specific link on the webpage.
- `type-text`: Input text on a text field/input box on the website.
- `QUIT`: Quit all connections.
- `UNKNOWN`: Unable to infer the intent.

Ensure proper formatting of the extracted content. For example, if the intent is `open-url`, return the URL with proper `https://www` formatting. Always wrap extracted content in " `CONTENT` ".

### Examples:

1. **User:** "Open www.google.com"
   - **Intent:** `open-url`
   - **Action:** OPEN_URL `https://www.google.com`

2. **User:** "Browse to twitter.com"
   - **Intent:** `open-url`
   - **Action:** OPEN_URL `https://www.twitter.com`

3. **User:** "Extract text from the article."
   - **Intent:** `extract-text`
   - **Action:** EXTRACT_TEXT

4. **User:** "Show me the product images."
   - **Intent:** `extract-elements`
   - **Action:** EXTRACT_ELEMENT `product-images`

5. **User:** "Click on the 'Sign In' button."
   - **Intent:** `click-button`
   - **Action:** CLICK_BUTTON `sign-in-button`

6. **User:** "What can I do on this page?"
   - **Intent:** `UNKNOWN`
   - **Action:** CLARIFY

7. **User:** "Type 'Hello' in the search box."
   - **Intent:** `type-text`
   - **Action:** TYPE_TEXT `Hello`
   
8. **User:** "Click search."
   - **Intent:** `click-button`
   - **Action:** CLICK_BUTTON `search-button`
   
9. **User:** "open the first link on list."
   - **Intent:** `click-link`
   - **Action:** CLICK_LINK `first-list-item`

These examples cover various scenarios and showcase how the user's intent can be accurately deduced based on the provided options.

Only return the action and not any explaination.

User:
"""



def tagparser(element):
    keys=list(element.attrs.keys())
    TOTALATTRS="class role name aria-label type value id title"
    DATA=''
    for k in keys:
        if TOTALATTRS.find(k)>=0:
            x=element[k]
            temp=''
            if type(x)==type([]):
                for ti in range(len(x)):
                    temp+=x[ti]+" "
                temp=temp[:-1]
            else:
                temp=x
            if len(temp)<1:
                continue
            DATA += f'{k}:{temp},'
    #print("$#%@%#@%@%@#"+DATA)
    return DATA

def getelem(soup,tagname):
    tags=soup.find_all(tagname)
    #print(len(tags))
    DATA=[]
    for t in tags:
        #print("^^^"+t)
        #print(tagparser(t))
        #print(f"&&&&&&&&&{t.text.strip()}")
        txt=t.text.strip()
        res=tagname+","+tagparser(t)
        if len(txt)>=1:
            res=res+f"text():{txt}"
        res=res.replace(",,",",")
        DATA.append(res)
    return DATA

def compare(spec,agnt):
    temp=spec.split(',')
    
    tag=temp[0]
    params=[]

    for j in range(1,len(temp)):
        kv=temp[j].split(':')
        key,value=kv[0],kv[1]
        params.append((key,value))
    #print(f"{tag}???????????{params}")
    drivers=agnt.elements_driver[tag]

    for d in drivers:
        #print(f"????????{d}")
        found=False
        for k in range(len(params)):
            if (params[k][0].find("text()")>=0):
                #if len(params[k][1])>=1:
                if params[k][1]!=d.text.strip():
                    #print(f"******DEVIATION_txt: {params[k][1]} , {d.text.strip()}")
                    found=False
                    break
                found=True

            else:
                if params[k][1]!=d.get_attribute(params[k][0]):
                    #print(f"******DEVIATION_othr: {params[k][0]}:{params[k][1]} , {d.get_attribute(params[k][0])}")
                    found=False
                    break
                found=True
        if found:
            #print(f"?????????????FOUND>>{d}")
            return d

    #print("???????????NOT FOUND")
    return None
                    
class agent:
    """ 
    Agent can infer the user intent and perform action
        intents: open-url (get_url), extract-text (extract_text), extract-elements (extract_elements),
        click-button (click_button) ,  type-text (type_text), click-link (click_link)
    """
    def __init__(self,tasks=[]):
        self.driver=None#webdriver.Chrome
        self.elements={}
        self.elements_driver={}
        self.tasks=tasks
        self.consideredtags=['div','button','input','textbox','textarea','image','img','a','text','svg','span']
        self.intents=self.get_intents()
        self.actions=self.intenttoaction()
        self.run()

    def get_intents(self):
        ints=[]
        if len(self.tasks) >=1 :
            for t in self.tasks:
                temp=querytext(llm,manager+t+"\nIntent:")
                #print(f"{t}>>>>intent:{temp}")
                ints.append(temp)
        return ints

    def intenttoaction(self):
        acts=[]
        if len(self.intents)>=1:
            for int in range(len(self.intents)):
                temp=querytext(llm,actor+self.tasks[int]+"\nIntent:"+self.intents[int]+"\nAction:")
                print(f"Task:{self.tasks[int]}>>>>Intent:{self.intents[int]}>>>>Action:{temp}")
                acts.append(temp)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<")
        return acts
    def run(self):
        if len(self.actions)>=1:
            if self.driver==None:
                self.driver=webdriver.Chrome()
            for i in range(len(self.actions)):
                time.sleep(2)
                act=self.actions[i]
                temp=act.split('`')
                if len(temp)>=2:
                    if temp[0].find("OPEN_URL")>=0:
                        self.openurl(temp[1])
                        self.extractelements()
                        
                    if temp[0].find("EXTRACT_ELEMENT")>=0:
                        self.getelement(temp[1])
                        #self.extractelements()
                        
                    if temp[0].find("CLICK_BUTTON")>=0:
                        self.clickbutton(self.tasks[i])
                        self.extractelements()
                        
                    if temp[0].find("CLICK_LINK")>=0:
                        self.clicklink(self.tasks[i],temp[1])
                        pass
                    if temp[0].find("TYPE_TEXT")>=0:
                        self.sendtext(self.tasks[i],temp[1])
                        self.extractelements()
                else:
                    if temp[0].find("EXTRACT_TEXT")>=0:
                        self.extracttext()
                    if temp[0].find("QUIT")>=0:
                        self.quit()
                    if temp[0].find("UNKNOWN")>=0:
                        self.clarify(self.tasks[i])   
                
                
        pass

    def openurl(self,url):
        try:
            self.driver.get(url)
            #input("OPENED!")
        except:
            print(f"Error opening {url}")

    def extractelements(self):
        """
        extract element options: 
            div, input , textbox, textarea, image, link, text, button, svg, span
        """
        time.sleep(2)
        soup=BeautifulSoup(self.driver.page_source)

        for t in self.consideredtags:
            self.elements[t]=getelem(soup,t)
            self.elements_driver[t]=self.driver.find_elements(By.TAG_NAME,t)
            #print(self.elements[t])

            

    def specifyelement(self,query,tags):
        #print(f"$#asfasnfansfajfsnjaasf$#%%%%")
        lits=[]
        #print(tags)
        lll=''
        for tag in tags:
            #print(self.elements[tag])
            #lits =lits + copy.deepcopy(self.elements[tag])
            for t in self.elements[tag]:
                lll=lll+t
            #print("*@*@@&&#&&#&#&#&#>>>>><<<")
        #print("&@!*&!*$@!*"+lll)
        prompt=f"""
        Look at the following query and list of elements. 
        Return the list element whose attributes closely match the desription in query.
        Make sure you match the tag correctly. 
        If query says click on button, then only choose the element with `button`.
        If query mentions open link, only choose the element with 'a' tag.

        Return the list element as it is mentioned in list, do not modify or parse.

        
        query:{query}
        
        LIST:{lll}
        """
        return querytext(llm,prompt)

    def getxpath(self,spec):
        temp=spec.split(",")
        xpath="//"+temp[0]
        for i in range(1,len(temp)):
            #print(ttt)
            try:
                ttt=temp[i].split(":")
                key,val=ttt[0],ttt[1]
                if key.find("text()")>=0:
                    continue
                #if (key.find(" ")>=0) or (val.find(" ")>=0):
                #    continue
                #val=val.replace(" ","")
                xpath=xpath+f"[@{key}='{val}']"
            except:
                pass
        return xpath
    def getelement(self,element):
        pass

    def getelemspec(self,spec):
        sp=spec.split(',')
        tag=sp[0]
        keys=[]
        values=[]
        for i in range(1,len(sp)):
            ssp=sp[i].split(":")
            keys.append(ssp[0])
            values.append(ssp[-1])

        for j in range(len(self.elements_drive[tag])):
            found=False
            for k in range(len(keys)-1):
                if values[k]!=self.elements_drive[tag][j].get_attribute(keys[k]):
                    
                    found=False
                    break
                found=True
            if found:
                
                return self.elements_drive[tag][j]
        return None

    def clicklink(self,task,query):
        DONE=False
        for i in range(3):
            try:
                spec=self.specifyelement(task+" "+query,["a"])#,"input","textbox", "textarea"])
                print(f"%%%%%%%%%%%%%%task>>>>>>{task}; Clicking {spec}")
                obj=compare(spec,self)
                if obj!=None:
                    obj.click()
                    DONE=True
                    break
            except:
                try:
                    xpath=self.getxpath(spec)
                    print(f"$$$$xpth={xpath}")
                    self.driver.find_element(By.XPATH,xpath).click()
                    DONE=True
                    #print("DONE CLICKING")
                    break
                except:
                    continue

        if DONE:
            print("DONE CLICKING link")
        else:
            print("ERROR IN CLICKING link")
        return
    
    def clickbutton(self,task):
        DONE=False
        for i in range(3):
            try:
                spec=self.specifyelement(task,["button","input","textbox", "textarea"])
                print(f"%%%%%%%%%%%%%%task>>>>>>{task}; Clicking {spec}")
                obj=compare(spec,self)
                if obj!=None:
                    obj.click()
                    DONE=True
                    break
            except:
                try:
                    xpath=self.getxpath(spec)
                    print(f"$$$$xpth={xpath}")
                    self.driver.find_element(By.XPATH,xpath).click()
                    DONE=True
                    #print("DONE CLICKING")
                    break
                except:
                    continue

        if DONE:
            print("DONE CLICKING")
        else:
            print("ERROR IN CLICKING")
        return
    def sendtext(self,task,query):
        DONE=False
        for i in range(3):
            try:
                spec=self.specifyelement(task,["input" , "textbox", "textarea"])
                print(f"%%%%%%%%%%%%%%task>>>>>>{task}; Texting {spec}")
                obj=compare(spec,self)
                if obj!=None:
                    obj.send_keys(query)
                    DONE=True
                    break
            except:
                try:
                    xpath=self.getxpath(spec)
                    print(f"$$$$xpth={xpath}")
                    self.driver.find_element(By.XPATH,xpath).send_keys(query)
                    DONE=True
                    #print("DONE CLICKING")
                    break
                except:
                    continue

        if DONE:
            print("DONE SENDING")
        else:
            print("ERROR IN SENDING")
        return
   
    def extracttext(self):
        print(f"%%%%%%%%%%%%%%Extracting text")

    def clarify(self,query):
        print(f"%%%%%%%%%%%%%%Clarify the following: {query}")

    def quit(self):
        self.driver.quit()
        


#listed=["open google.com","click on textbox","enter 'weather' in input search","click on the search button","Get the first search result"]
listed=["go to wikipedia.com", "type mathematics in searchbox","click search","Get first result link"]
#listed=["open https://facebook.com", "enter phone number `zyxwvu`","enter password `abcdefgh`", "Click on the login button"]
#listed=["Go to https://www.quantamagazine.org/", "click on search","type and search India"]
a=agent(listed)

