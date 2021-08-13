#!/usr/bin/env python
# coding: utf-8

# In[1]:


from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import requests
import json
from bs4 import BeautifulSoup as BS
from psycopg2 import connect, extensions, sql
import pandas as pd
import csv
import os.path
import os

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)    # 1 -> searching, 2 -> parsing, 3 -> writing to csv, 4 -> connect to DB, 5 -> inserting into DB
    
    def start_script(self, minVal, maxVal):
        self.question_id = []
        self.link_to_question = []
        self.tags = []
        self.j_string = []
        self.conn = connect(dbname = "stackoverflow", user = "ahsan", host = "localhost", password = "postgres")
        self.page_num = 1
        self.progress.emit(1)
        self.json_data, self.question_id, self.link_to_question, self.tags = self.get_questions_list(minVal, maxVal, self.page_num)
        while self.json_data["has_more"]:
            self.page_num += 1
            self.json_data, self.question_id, self.link_to_question, self.tags = self.get_questions_list(minVal, maxVal, self.page_num)
        self.progress.emit(2)
        for i in range(0, len(self.question_id)):
            self.qa_string = self.parse_page(i)
            self.j_string.append(self.qa_string)
        self.progress.emit(3)
        self.write_to_csv()
        self.progress.emit(4)
        self.connect_to_DB()
        self.finished.emit()
        
    def get_questions_list(self, min_vote, max_vote, page_num):
        self.url = "https://api.stackexchange.com/2.3/questions?page=" + str(page_num) + "&pagesize=100&order=desc&sort=votes&min=" + min_vote + "&max=" + max_vote + "&site=stackoverflow"
        self.r = requests.get(self.url)
        self.json_data = self.r.json()
        for i in range(0, len(self.json_data["items"])):
            if self.json_data["items"][i]["is_answered"]:
                self.question_id.append(self.json_data["items"][i]["question_id"])
                self.link_to_question.append(self.json_data["items"][i]["link"])
                self.tags.append(self.json_data["items"][i]["tags"])
        return self.json_data, self.question_id, self.link_to_question, self.tags

    def connect_to_DB(self):
        self.cursor = self.conn.cursor()

        self.table_exist = "SELECT table_name FROM information_schema.tables WHERE (table_schema = 'public') ORDER BY table_name"
        self.cursor.execute(self.table_exist)
        self.list_tables = self.cursor.fetchall()
        self.conn.commit()
        self.table_list = []

        for table_name in self.list_tables:
            self.table_list.append(table_name[0])

        if not "questions_and_answers" in self.table_list:
            self.create_table = "CREATE TABLE questions_and_answers (question_id INTEGER NOT NULL PRIMARY KEY, tags TEXT NOT NULL, qa_data JSON NOT NULL)"
            self.cursor = self.conn.cursor()
            self.cursor.execute(self.create_table)       #if table not exists, create new table
            self.conn.commit()

    def parse_page(self, num):
        self.qa = requests.get(self.link_to_question[num])
        self.soup = BS(self.qa.content, 'html.parser')
        self.question_title = self.soup.find(class_="question-hyperlink")
        self.question = self.question_title.get_text()
        self.question = self.question.replace("'","''")
        self.answers = self.soup.find(class_="answer").find(class_="js-post-body")
        self._answer = self.answers.get_text()
        self._answer = self._answer.replace("'","''")
        self.answer = self._answer.split('\n')
        self.answer = list(filter(None, self.answer))
        self.json_string = {
            "question": self.question,
            "answer": self.answer
        }
        return self.json_string

    def write_to_csv(self):
        if not os.path.isfile('questions_answers.csv'):
            self.f = open('questions_answers.csv', 'w')
            self.writer = csv.writer(self.f)
            self.writer.writerow(['a','b'])
            self.f.close()
        self.header = pd.read_csv('questions_answers.csv', nrows=0)
        if self.header.columns[0] != 'Question_ID':
            self.df = pd.DataFrame(columns=['Question_ID', 'Tags', 'QA_JSON'])
            self.df.to_csv('questions_answers.csv', index = False)
        for i in range(0, len(self.question_id)):
            self.df = pd.DataFrame([[self.question_id[i], self.tags[i], self.j_string[i]]] , columns=['Question_ID', 'Tags', 'QA_JSON'])
            self.df.to_csv('questions_answers.csv', index=False, mode='a', header=False)


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(200, 200, 500, 500)
        self.setWindowTitle("Search Stack Overflow")
        self.initUI()
        
    def initUI(self):
        self.label = QtWidgets.QLabel(self)
        self.label.setText("Enter minimum rating:")
        self.label.setGeometry(QRect(30, 0, 200, 50))
        self.label.setFont(QFont('Times', 10))
        
        self.label2 = QtWidgets.QLabel(self)
        self.label2.setText("Enter maximum rating:")
        self.label2.setGeometry(QRect(200, 0, 200, 50))
        self.label2.setFont(QFont('Times', 10))
        
        self.min_bar = QtWidgets.QLineEdit(self)
        self.min_bar.setGeometry(QRect(30, 60, 100, 27))
        
        self.max_bar = QtWidgets.QLineEdit(self)
        self.max_bar.setGeometry(QRect(200, 60, 100, 27))
        
        self.btn = QtWidgets.QPushButton(self)
        self.btn.setText("Search")
        self.btn.move(350 ,58)
        self.btn.clicked.connect(self.clicked)
        
        self.label3 = QtWidgets.QLabel(self)
        self.label3.setText("")
        self.label3.setFont(QFont('Times', 12))
        self.label3.setGeometry(QRect(30, 100, 350, 40))
        
        self.label4 = QtWidgets.QLabel(self)
        self.label4.setText("")
        self.label4.setFont(QFont('Times', 12))
        self.label4.setGeometry(QRect(30, 120, 350, 40))
        
        self.label5 = QtWidgets.QLabel(self)
        self.label5.setText("")
        self.label5.setFont(QFont('Times', 12))
        self.label5.setGeometry(QRect(30, 140, 350, 40))
        
        self.label6 = QtWidgets.QLabel(self)
        self.label6.setText("")
        self.label6.setFont(QFont('Times', 12))
        self.label6.setGeometry(QRect(30, 160, 350, 40))
        
    def clicked(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.minVal = self.min_bar.text()
        self.maxVal = self.max_bar.text()
        
        self.thread.started.connect(
            lambda: self.worker.start_script(self.minVal, self.maxVal)
        )
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.worker.progress.connect(self.current_task)
        
        self.thread.start()
        
        self.btn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.btn.setEnabled(True)
        )
        
    def current_task(self, n):
        if n == 1:
            self.label3.setText("Searching Stack Overflow for questions...")
        elif n == 2:
            self.label4.setText("Getting Questions....")
        elif n == 3:
            self.label5.setText("Writing to CSV File....")
        elif n == 4:
            self.label6.setText("Connecting to Database...")
    
            
            
    
def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    
    win.show()
    sys.exit(app.exec_())
    
window()


# In[ ]:





# In[ ]:





# In[ ]:




