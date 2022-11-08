import sys, re, os
import time
import sqlite3
import win10toast
from win10toast import ToastNotifier
from datetime import datetime, date, timedelta
from time import localtime, strptime, strftime
from threading import Thread


from os.path import exists


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QTextCharFormat,QFont, QBrush,QPalette,QIcon
from PyQt5.QtCore import (
    QObject,
    QSize, 
    Qt, 
    QTimer,
    QDate,QTime, 
    QModelIndex,
    QDateTime,
    QRunnable, 
    QThreadPool, 
    QTimer, 
    pyqtSlot,
    pyqtSignal
)
from PyQt5.QtSql import QSqlTableModel

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCalendarWidget,
    QSizePolicy,
    QListWidget,
    QDateEdit,
    QTimeEdit,
    QAbstractItemView,
    QMessageBox,
    QListWidgetItem,
    QGroupBox,
    QLayout,
    QGridLayout,    
    QFormLayout,
)



basedir = os.path.dirname(__file__)

connection = sqlite3.connect(os.path.join(basedir, "reminders.db"))

cursor = connection.cursor()

#First run create table, else skip
cursor.execute(
    """CREATE TABLE IF NOT EXISTS reminders 
    (date varchar(10), 
     time varchar(5), 
     meridian varchar(2), 
     memo varchar(150))"""
)

# #commit the changes to db			
connection.commit()
# #close the connection
connection.close()




class WorkerSignals(QObject):
    finished = pyqtSignal()

class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self):
        super().__init__()
        #NOTICE: Create an instance of the
        # signal class
        self.signals = WorkerSignals()


    @pyqtSlot()# turn simple python method to Qt slot.

    def run(self):
        '''
        Your code you want to run on a 
        different thread goes in this function
        '''
         # start timer close to 0 seconds
        print("THREAD START")
        secs = localtime().tm_sec
        if secs == 0:
            self.signals.finished.emit()
        try:
            if secs != 0:
                while secs != 0:
                    secs = localtime().tm_sec
                    if secs == 0:
                        self.signals.finished.emit()
        except:
            pass


basedir = os.path.dirname(__file__)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()


        self.setWindowTitle("NuReminders")
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'dh.ico')))

        self.createCalendarGroupBox()
        self.createEntryGroupBox()
        self.createButtonsGroupBox()
        self.createListViewGroupBox()


        # arrange group boxes in layout
        layout = QGridLayout()
        layout.addWidget(self.calendarGroupBox,0,0,1,1)
        layout.addWidget(self.entryGroupBox, 0,1,1,2)
        layout.addWidget(self.buttonsGroupBox, 1, 0,1,3)
        layout.addWidget(self.listviewGroupBox, 2,0,1,3)

        # We set the grid layout's resize policy 
        # to QLayout:.SetFixedSize to prevent the 
        # user from resizing the window.
        #  In that mode, the window's size is 
        # set automatically by QGridLayout based 
        # on the size hints of its contents widgets.
        layout.setSizeConstraint(QLayout.SetFixedSize)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        #below created in createPreviewGroupBox
        # function
        #self.previewLayout = QGridLayout()
        # To ensure that the window isn't 
        # automatically resized every time we 
        # change a property of the QCalendarWidget 
        # (for example, hiding the navigation bar, 
        # the vertical header, or the grid), we 
        # set the minimum height of row 0 and 
        # the minimum width of column 0 to 
        # the initial size of the QCalendarWidget.
        # ****ADD LATER for CALENDAR**************
        self.previewLayout.setRowMinimumHeight(0, self.calendar.sizeHint().height())
        self.previewLayout.setColumnMinimumWidth(0, self.calendar.sizeHint().width())

        self.itemsToList()

        #NOTICE: Setup thread pool
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(4)
        
        self.startTimer()


        self.noteTimer = QTimer()
        self.noteTimer.setInterval(20000)
        self.noteTimer.timeout.connect(self.winNote)


    def createCalendarGroupBox(self):
        self.calendarGroupBox = QGroupBox()
        self.calendarGroupBox.setTitle("Calendar")

        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate(1970,1,1))
        self.calendar.setMaximumDate(QDate(3000,1,1))
        self.calendar.setVisible(True)

        self.previewLayout = QGridLayout()
        self.previewLayout.addWidget(self.calendar, 0, 0, Qt.AlignCenter)

        self.calendarGroupBox.setLayout(self.previewLayout)

    def createEntryGroupBox(self):
        self.entryGroupBox = QGroupBox()
        self.entryGroupBox.setTitle("Entry")
        

        self.entryLayout = QGridLayout()


        self.infoLabel = QLabel("Select Date, Time and Input Reminder")
        self.infoLabel.setAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )
        self.infoLabel.setFixedHeight(35)

        # Date widget and label
        self.dateEdit = QDateEdit()
        self.dateEdit.setFixedSize(110,24)
        self.dateEdit.setMinimumDate(QDate(1970,1,1))
        self.dateEdit.setDate(
            self.calendar.selectedDate()
        )
        self.dateEdit.setFixedSize(136,40)

        self.dateLabel = QLabel("Date")
        self.dateLabel.setBuddy(self.dateEdit)

        # current time
        nowTime = QTime.currentTime()

        # Time widget and label
        self.timeEdit = QTimeEdit()
        self.timeEdit.setFixedSize(115,24)
        self.timeEdit.setTime(nowTime)
        self.timeLabel = QLabel("Time")
        self.timeLabel.setBuddy(self.timeEdit)

        # LineEdit widget and label
        self.remLineEdit = QLineEdit()
        self.remLineEdit.setFixedSize(300,24)
        self.remLineEdit.setMaxLength(75)
        self.remLineEdit.setClearButtonEnabled(True)
        self.remLineEdit.setPlaceholderText("Enter reminder text")
        
        self.remLabel = QLabel("Text")
        self.remLabel.setBuddy(self.remLineEdit)
        
        
        self.entryLayout.addWidget(self.infoLabel, 0, 0, 1, 4)
        self.entryLayout.addWidget(self.dateLabel,1,0,1,1)
        self.entryLayout.addWidget(self.dateEdit,1,1,1, 3)
        self.entryLayout.addWidget(self.timeLabel,2,0,1,1)
        self.entryLayout.addWidget(self.timeEdit,2,1,1,3)
        self.entryLayout.addWidget(self.remLabel,3,0,1,0)
        self.entryLayout.addWidget(self.remLineEdit,3,1,1,3)
        
        self.entryGroupBox.setLayout(self.entryLayout)




    
    def createButtonsGroupBox(self):
        self.buttonsGroupBox = QGroupBox()
        self.buttonsGroupBox.setTitle("Actions")

        self.buttonsLayout = QHBoxLayout()

        self.setRemBtn = QPushButton("Set Reminder")
        self.setRemBtn.clicked.connect(self.addReminder)
        self.buttonsLayout.addWidget(self.setRemBtn)


        self.editBtn = QPushButton("Edit  Reminder")
        self.editBtn.clicked.connect(self.editReminder)
        self.buttonsLayout.addWidget(self.editBtn)

        self.delRemBtn = QPushButton("Delete Reminder")
        self.delRemBtn.clicked.connect(self.deleteReminder)
        self.buttonsLayout.addWidget(self.delRemBtn)

        self.buttonsGroupBox.setLayout(self.buttonsLayout)

    def createListViewGroupBox(self):
        self.listviewGroupBox = QGroupBox()
        self.listviewGroupBox.setTitle("Items")

        self.lstvwLayout = QVBoxLayout()


        self.lstwidgt = QListWidget()

        self.lstvwLayout.addWidget( self.lstwidgt)


        self.listviewGroupBox.setLayout(self.lstvwLayout)





       
    def addReminder(self):
    
        dataitem = []

        nuDate = self.dateEdit.date()
        nuDate = nuDate.toString(Qt.ISODate)


        nuTime = self.timeEdit.time()
        nuTime = nuTime.toString(Qt.DefaultLocaleShortDate)
        

        nuMemo = self.remLineEdit.text()
        
        rmurgxchar = re.compile(r'[\^\$\*\?\+\{\}\[\]\\\|\(\)"\'%]')

        res = rmurgxchar.findall(nuMemo)
        
        
        if (len(res) > 0):
            QMessageBox.warning(
                self, 
                "Error", 
                "The following characters in memo field" \
                "are not allowed: ^ $ * + { } [ ] \ | ( ) \" ' %"
            )
            return
        if (nuDate=="" or nuTime=="" or nuMemo ==""):
            QMessageBox.warning(
                self, 
                "Error", 
                "Memo field cannot " \
                "be blank."
            )
            return
        nuMemo = nuMemo.replace("%s","")
        

        nuDate = nuDate.split('-')
        nuDate = f"{nuDate[1]}/{nuDate[2]}/{nuDate[0]}"
        onTime = nuTime.split(' ')
        nuTime = onTime[0]
        nuMeridian = onTime[1]
        data= (nuDate, nuTime, nuMeridian, nuMemo)
        
        
        self.lstwidgt.addItem(
            f'{nuDate} {nuTime} {nuMeridian} {nuMemo}'
        )

        # add item to database
        self.itemToDb(data)
        self.remLineEdit.setText("")

    def startTimer(self):
        self.noteTimer = QTimer()
        self.noteTimer.setInterval(20000)
        self.noteTimer.timeout.connect(self.winNote)
        global worker
        worker = Worker()
        worker.signals.finished.connect(self.worker_complete)
        self.threadpool.start(worker)

    def worker_complete(self):
        # START TIMER HERE
        self.noteTimer.start()
        print("THREAD COMPLETE!")


    def itemsToList(self):
        connection = sqlite3.connect(os.path.join(basedir,"reminders.db"))

        cursor = connection.cursor()

        cursor.execute('''SELECT * FROM reminders;''')

        rows = cursor.fetchall()

        rows.sort()
 
        for row in rows:
            rowlzt = list(row)

            self.lstwidgt.addItem(
                f'{rowlzt[0]} {rowlzt[1]} {rowlzt[2]} {rowlzt[3]}'
            )
            
        

        # #commit the changes to db			
        connection.commit()
        # #close the connection
        connection.close()


        # for row in rows
        # take row[0] to style calendar
        # date with that date
        #DATE MUST BE QDATE!!!!!!!!!!
        for row in rows:
            month = int(row[0][0:2])
            day = int(row[0][3:5])
            year = int(row[0][6:])

            #make QDate
            date2bMarked = QDate(
                self.calendar.yearShown(), month,day
            )

            date2bMarkedFormat = QTextCharFormat()
            if date2bMarked != self.calendar.selectedDate():
                date2bMarkedFormat.setBackground(
                    Qt.green
                )
            else:
                pass

            self.calendar.setDateTextFormat(
                date2bMarked,
                date2bMarkedFormat
            )



        # redraw calendar
        self.calendar.update()





    def editReminder(self):
        curItem = QListWidgetItem(self.lstwidgt.currentItem()).text()
        curItemLst = curItem.split(' ')

        # Isolate date time and meridian
        # values to use to create date and time
        d = curItem[0:10]
        t = curItem[11:16]
        ap =curItem[16:19].strip()



        thsDate = curItemLst[0]
        thsTime = f'{curItemLst[1]} {curItemLst[2]}'
        thsMemo = curItem[19:]
        ddLst = thsDate.split('/')

        # set dateedit with date of selected item
        year = int(ddLst[2])
        month = int(ddLst[0])
        numday = int(ddLst[1])
        self.dateEdit.setDate(QDate(year, month, numday))

        # set timeedit with time of selected item
        tmesplit = t.split(':')
        h = int(tmesplit[0])
        m = int(tmesplit[1])
        if ap == "PM":
            h += 12
        self.timeEdit.setTime(QTime(h, m))

        # set LineEdite widget with memo value
        self.remLineEdit.setText(thsMemo)
         
        readListwdgt = []
        readListwdgt = self.remove_update(readListwdgt)

        self.updateDb(readListwdgt)
        self.lstwidgt.clear()
        self.itemsToList()

    def remove_update(self,data):
        # find del item to remove highlight from calendar
        for item in self.lstwidgt.selectedItems():
            itemNum = self.lstwidgt.row(item)
            delItem = ""
            delItem = self.lstwidgt.item(itemNum).text()
            month = int(delItem[0:2])
            day = int(delItem[3:5])
            
            
             #make QDate
            date2bCleared = QDate(
                self.calendar.yearShown(), month,day
            )

            date2bClearedFormat = QTextCharFormat()
            if date2bCleared != self.calendar.selectedDate():
                date2bClearedFormat.setBackground(
                    Qt.white
                )

            self.calendar.setDateTextFormat(
                date2bCleared,
                date2bClearedFormat
            )
            
            # remove selected item
            self.lstwidgt.takeItem(self.lstwidgt.row(item))


        for i in range(self.lstwidgt.count()):
            thsItem = self.lstwidgt.item(i).text()
            d = thsItem[0:10]
            t = thsItem[11:16]
            ap =thsItem[16:19].strip()
            m = thsItem[19:].strip()
            data.append((d,t,ap,m))
        
        return data


    def updateDb(self, data):
        connection = sqlite3.connect(os.path.join(basedir,"reminders.db"))

        cursor = connection.cursor()

        # delete all rows from table
        cursor.execute('DELETE FROM reminders;',);

        print('We have deleted', cursor.rowcount, 'records from the table.')


        cursor.executemany('INSERT INTO reminders VALUES(?,?,?,?);',data)

        print('We have inserted', cursor.rowcount, 'records to the table.')
        # #commit the changes to db			
        connection.commit()
        # #close the connection
        connection.close()
        self.lstwidgt.clear()
        self.itemsToList()


    def itemToDb(self, data):
        connection = sqlite3.connect(os.path.join(basedir, "reminders.db"))

        cursor = connection.cursor()
        
        cursor.execute('INSERT INTO reminders \
        (date, time, meridian, memo) \
        VALUES (?,?,?,?)', data  )

        # #commit the changes to db			
        connection.commit()
        # #close the connection
        connection.close()
        self.lstwidgt.clear()
        self.itemsToList()


    def deleteReminder(self, data):
        #remove selected item from listwidget
        readListwdgt = []
        readListwdgt = self.remove_update(readListwdgt)

        # redraw calendar
        self.calendar.update()

        # update db minus item removed
        self.updateDb(readListwdgt)

    global numNotes
    numNotes = 0
    def app_notify(self,msg):
        global numNotes
        numNotes+=1
        toaster = "toaster"
        myvar = toaster + str(numNotes)
        myvar = ToastNotifier()
        try:
            myvar.show_toast(
                "Reminder",
                my_message,
                icon_path="dh.ico",
                duration=15,
                threaded=True)
        except Exception as ex: 
            pass

    global compareItems
    compareItems = []
    def winNote(self):

        # get listwidget item to make comparedate list
        for i in range(self.lstwidgt.count()):
            thsItem = self.lstwidgt.item(i).text()
            year = int(thsItem[6:10])
            month = int(thsItem[0:2])
            day = int(thsItem[3:5])
            hr_mn = thsItem[11:16].strip()
            meridian = thsItem[16:19].strip()
            memo = thsItem[19:] 

            # separate hr/mi vals
            hr_mnvals = hr_mn.split(':')  
            hr = int(hr_mnvals[0]) 
            mn = int(hr_mnvals[1])  
            # increase hour by 12 if pm
            if meridian == "PM":
                hr+=12   

            # create QDateTime for each list item
            thsItemDate = datetime(year, month, day, hr, mn)
            #thsItmDate = QDateTime(year, month, day, hr, mn, 0, 0)
            thsItmLst =[thsItemDate, memo]
            global compareItems
            compareItems.append(thsItmLst)

        compareItems.sort()
        self.initNotify()#
        # clear compareItems
        compareItems = []

    def get_now_time(default=None):
        # create datetime struct of current time
        cur_time = strftime("%Y-%m-%d %I:%M:%S%p", localtime())

        cur_time_date = strptime(cur_time, "%Y-%m-%d %I:%M:%S%p")


        my_year = cur_time_date.tm_year
        my_month = cur_time_date.tm_mon
        my_day =cur_time_date.tm_mday
        my_hour = cur_time_date.tm_hour
        my_min = cur_time_date.tm_min

        # create datetime from time.struct values
        my_datetime = datetime(my_year,my_month,my_day,my_hour,my_min)
        
        return my_datetime
    

    def initNotify(self):
        compareTime = self.get_now_time()
        compareTime60 = compareTime + timedelta(seconds=60)

        memo = ""
        for i in compareItems:
            if i[0] == compareTime: 
                global my_message
                my_message=i[1]
                my_app_name = "Memos"

                self.app_notify(my_message)

        # style listitems in listview past current time
        ltcount = 0
        # get number of list items with datetime less
        # than current time
        for i in compareItems:
            if i[0] < compareTime: 
                ltcount += 1

        for f in range(ltcount):
            qlstItem = self.lstwidgt.item(f).setForeground(QtGui.QColor("#FF0000"))

            

        

app = QApplication(sys.argv)
# Set app styles
app.setStyleSheet(
    '''

QLabel, QSpinBox, QPushButton, QListWidget, QDateEdit, QTimeEdit {
    font-size: 24px;
}

QLineEdit {
    font-size: 16px;
}

QListView {
    alternate-background-color: yellow;
}


QListView::item:selected:!active {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #ABAFE5, stop: 1 #8588B2);
}

'''
)

window = MainWindow()
window.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'dh.ico')))
window.show()

app.exec_()
