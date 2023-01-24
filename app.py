from flask import Flask,request,jsonify,render_template
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_caching import Cache

app=Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Use the credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(credentials)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1bIYD7ka9YgOzqRaY3hY7ygGm6lL7bYVJCdCWbxRdHmc/edit?usp=sharing"
spreadsheet = client.open_by_url(spreadsheet_url)

def is_present(text, pattern):
    str=text
    if str.find(pattern) != -1:
      return True
    else:
        return False

@cache.cached(timeout=3600)
def get_data_from_sheet():
    sheet = spreadsheet.sheet1
    data = sheet.get_all_values()
    return data

@app.route('/',methods=['GET'])
def get_data():
    return render_template('index.html')

@app.route('/subjects', methods=['GET'])
def get_subjects():
    data = get_data_from_sheet()
    subjects = set()
    counter=0
    for row in data:
        if counter==0:
            counter=1
            continue
        subjects.add(row[3].upper().strip())
    return jsonify(list(subjects))

@app.route('/data',methods=['POST'])
def show_data():
    global dict_search
    data = get_data_from_sheet()
    incoming_data=request.get_json()
    PageNo =incoming_data.get('page')
    BookAccNo = incoming_data.get('accNo')
    BookName = incoming_data.get('title')
    BookAuthor = incoming_data.get('author')
    BookSubject = incoming_data.get('subjectType')
    BooksList = []
    limst_1=[]
    limst_2=[]
    limst_3=[]
    iter=1
    
    while(iter < len(data)):
            counter=0
            acc=data[iter][0]
            bookname=data[iter][1]
            bookauthor=data[iter][2]
            booksubject=data[iter][3]
            json_output = {'accNo':acc,'title':bookname,'author':bookauthor,'subjectType':booksubject}
            if str(BookAccNo).lower()==str(acc).lower() and BookAccNo and acc!=None:
                counter=counter+1
            if is_present(bookname.lower(),BookName.lower()) and BookName and bookname!=None:
                counter=counter+1
            if is_present(bookauthor.lower(),BookAuthor.lower()) and BookAuthor and bookauthor!=None:
                counter=counter+1
            iter+=1
            if counter>=3:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_3.append(json_output)
                else:
                    limst_3.append(json_output)
            elif counter==2:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_2.append(json_output)
                else:
                    limst_2.append(json_output)
            elif counter==1:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_1.append(json_output)
                else:
                    limst_1.append(json_output)
    BooksList=limst_3+limst_2+limst_1

    PageNo=int(PageNo)
    iter = (PageNo-1)*20
    limit = PageNo*20
    TotalPages=len(BooksList)
    BooksFinalList=[]
    while(iter<limit and iter<TotalPages):
        BooksFinalList.append(BooksList[iter])
        iter+=1
    return [{'MaxPage':int(TotalPages/20)+(TotalPages%20!=0)},{'BookList':BooksFinalList}]

if __name__ == '__main__':
    app.run(debug=True,port=5000)