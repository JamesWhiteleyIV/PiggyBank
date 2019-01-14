import datetime as dt
import os
import pandas as pd
import time
from dateutil.relativedelta import relativedelta

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(FILE_DIR, "..", "output") 
BUDGET_FILE = os.path.join(FILE_DIR, "budget.txt") 

class Budget(object):
    def __init__(self):
        self.data = {}
        self._parseBudgetDoc()
        self._generateGrid()

    def _parseBudgetDoc(self):
        if not os.path.exists(BUDGET_FILE):
            raise IOError("{} file does not exist!".format(unicode(BUDGET_FILE)))

        with open(BUDGET_FILE, 'r') as fp:
            content = fp.readlines()

        curkey = None
        for line in content:
            line = line.strip()

            # comment or empty line
            if not line or line.startswith('//') or line.startswith(' '):
                continue

            # category
            elif line.startswith('[') and line.endswith(']'):
                curkey = line
                self.data[curkey] = []

            # budget data
            else:
                line = line.split(',')
                line = [l.strip() for l in line]
                self.data[curkey].append(line)

    def mapItem(self, item, type_, rng):
        amount = item[0]
        note = item[2]
    
        if type_ == 'one':
            dates = [self.mapDate(item[1])]
        elif type_ == 'week':
            dayOfWeek = int(item[1])
            start = self.mapDate(item[3])
            end = self.mapDate(item[4])
            dates = [d for d in rng if d.weekday() == dayOfWeek and d > start and d < end]
        elif type_ == 'biweek':
            dayOfWeek = int(item[1])
            start = self.mapDate(item[3])
            end = self.mapDate(item[4])
            dates = [d for d in rng if d.weekday() == dayOfWeek and d > start and d < end and d.week % 2 == int(item[5])] 
        elif type_ == 'month':
            dayOfMonth = int(item[1])
            start = self.mapDate(item[3])
            end = self.mapDate(item[4])
            dates = [d for d in rng if d.day == dayOfMonth and d < end and d > start] 

        return amount, dates, note
        
    def _generateGrid(self):
        start = self.data.pop('[START DATE]')[0][0]
        start = self.mapDate(start)
        end = self.data.pop('[END DATE]')[0][0]
        end = self.mapDate(end)

        if end < start:
            end = start + relativedelta(years=1)

        rng = pd.date_range(start, end, normalize=True)
        self.grid = pd.DataFrame(0, index=rng, columns=['Income', 'Expenses', 'Net', 'Balance', 'Note'], dtype='float')
        self.grid.ix[:, 'Note'] = ""

        for item in self.data.pop('[ONE TIME INCOME]'):
            amount, dates, note = self.mapItem(item, 'one', rng)
            for date in dates:
                self.addIncome(amount, date, note)
   
        for item in self.data.pop('[ONE TIME EXPENSES]'):
            amount, dates, note = self.mapItem(item, 'one', rng)
            for date in dates:
                self.addExpense(amount, date, note)
   
        for item in self.data.pop('[WEEKLY INCOME]'):
            amount, dates, note = self.mapItem(item, 'week', rng)
            for date in dates:
                self.addIncome(amount, date, note)

        for item in self.data.pop('[WEEKLY EXPENSES]'):
            amount, dates, note = self.mapItem(item, 'week', rng)
            for date in dates:
                self.addExpense(amount, date, note)

        for item in self.data.pop('[BIWEEKLY INCOME]'):
            amount, dates, note = self.mapItem(item, 'biweek', rng)
            for date in dates:
                self.addIncome(amount, date, note)
                
        for item in self.data.pop('[BIWEEKLY EXPENSES]'):
            amount, dates, note = self.mapItem(item, 'biweek', rng)
            for date in dates:
                self.addExpense(amount, date, note)
                
        for item in self.data.pop('[MONTHLY INCOME]'):
            amount, dates, note = self.mapItem(item, 'month', rng)
            for date in dates:
                self.addIncome(amount, date, note)
                
        for item in self.data.pop('[MONTHLY EXPENSES]'):
            amount, dates, note = self.mapItem(item, 'month', rng)
            for date in dates:
                self.addExpense(amount, date, note)

        self.grid['Net'] = self.grid['Income'] + self.grid['Expenses']
        currentBalance = float(self.data.pop('[CURRENT BALANCE]')[0][0])

        self.grid['Balance'] = currentBalance + self.grid['Net'].cumsum()

    def mapDate(self, date):
        if date.lower() == 'today':
            return dt.datetime.now()
        elif date.lower() == 'forever':
            return dt.datetime.max
        else:
            return dt.datetime.strptime(date, "%Y-%m-%d") 
        
    def printDate(self, date):
        """
        :param string date: 2018-1-29 
        """
        if not isinstance(date, dt.datetime):
            date = dt.datetime.strptime(date, "%Y-%m-%d") 
        print self.grid.loc[date]


    def addIncome(self, amount, date, note):
        """
        :param string amount: 100  OR  120.12 
        :param string date: 2018-1-29 
        :param string note: tax return 
        """
        if not isinstance(date, dt.datetime):
            date = dt.datetime.strptime(date, "%Y-%m-%d") 
        amount = float(amount)
        self.grid.ix[date, 'Income'] += amount
        if self.grid.ix[date, 'Note'] != "":
            note = ', ' + note
        self.grid.ix[date, 'Note'] += note 
         
    def addExpense(self, amount, date, note):
        """
        :param string amount: 100  OR  120.12 
        :param string date: 2018-1-29 
        :param string note: tax return 
        """
        if not isinstance(date, dt.datetime):
            date = dt.datetime.strptime(date, "%Y-%m-%d") 
        amount = float(amount)
        self.grid.ix[date, 'Expenses'] -= amount
        if self.grid.ix[date, 'Note'] != "":
            note = ', ' + note
        self.grid.ix[date, 'Note'] += note 
         
    def generateReport(self):
        fname = self.data.pop('[OUTPUT FILE NAME]')[0][0]
        date = dt.datetime.now()
        year = date.year
        month = date.month
        day = date.day
        hour = date.hour
        minute = date.minute
        date = '{}-{}-{}-{}{}'.format(year, month, day, hour, minute)
        fname = '{}-{}.csv'.format(fname, date)
        
        # make sure data dir exists
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        outpath = os.path.join(OUTPUT_DIR, fname)
        self.grid.to_csv(outpath)


if __name__ == "__main__":
    budget = Budget()
    budget.generateReport()
