#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import json

t = input("Enter tag to search stackoverflow: ")

url = "https://api.stackexchange.com/2.3/questions?page=1&pagesize=100&order=desc&sort=votes&min=2&tagged=" + t + "&site=stackoverflow"

r= requests.get(url)

json_data = r.json()

# json_object = json.loads(json_data)

print(json.dumps(json_data, indent = 1))


# In[2]:


print(len(json_data["items"]))

question_id = []
link_to_question = []

for i in range(0, len(json_data["items"])):
    question_id.append(json_data["items"][i]["question_id"])
    link_to_question.append(json_data["items"][i]["link"])
    print(json_data["items"][i]["question_id"])
    print(json_data["items"][i]["link"])
print(question_id)
print(link_to_question)


# In[3]:


from bs4 import BeautifulSoup as BS
n = 64
qa = requests.get(link_to_question[n])

soup = BS(qa.content, 'html.parser')

print(soup.prettify())


# In[4]:


question_title = soup.find(class_="question-hyperlink")
question = question_title.get_text()

print(question)


# In[5]:


answers = soup.find(class_="answer").find(class_="js-post-body")
_answer = answers.get_text()
_answer = _answer.replace("'","''") 

answer = _answer.split('\n')
answer = list(filter(None, answer))

print(answer)


# In[32]:


json_string = {
    "question": question,
    "answer": answer
}
# question_id[n],
print(question_id[n])
print(json.dumps(json_string))


# In[31]:


from psycopg2 import connect, extensions, sql

conn = connect(
dbname = "stackoverflow",
user = "ahsan",
host = "localhost",
password = "postgres"
)

cursor = conn.cursor()

table_exist = "SELECT table_name FROM information_schema.tables WHERE (table_schema = 'public') ORDER BY table_name"
cursor.execute(table_exist)
list_tables = cursor.fetchall()
table_list = []

for table_name in list_tables:
    table_list.append(table_name[0])
    
if t in table_list:
    print('Table already exists')
else: 
    create_table = "CREATE TABLE " + t + " (question_id INTEGER NOT NULL PRIMARY KEY, qa_data JSON NOT NULL)"
    cursor = conn.cursor()
    cursor.execute(create_table)
    conn.commit()
    print("Table with name " + t + " created")
    
cursor = conn.cursor()
# print(str(json_string))
insert_data = "INSERT INTO "+t+" (question_id, qa_data) VALUES (" + str(question_id[n]) +", '" + json.dumps(json_string) + "')"
cursor.execute(insert_data)
conn.commit()


# create_table = "CREATE TABLE " + t + " (question_id INTEGER NOT NULL PRIMARY KEY, qa_data JSON NOT NULL)"

# cursor.execute(create_table)
# cursor.close()
# conn.commit()

# print("Table with name " + t +" created")
# conn.close()


# In[ ]:




