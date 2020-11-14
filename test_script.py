
import requests
#open userid file

# some var
message = "HELLOWORD"
bot_token = "1474875052:AAGzRBv4m3X1ewYzz6-D-SuS0N_Y_43y1Tg"

"""
simple test:
url = "https://api.telegram.org/bot1474875052:AAGzRBv4m3X1ewYzz6-D-SuS0N_Y_43y1Tg/sendMessage?chat_id=985996627&text=HelloWorld"
"""
usersid = open(r'User_id.txt')
for userid in usersid:
    #print(userid,end="")
    userid = userid.strip('\n')

    url = "https://api.telegram.org/bot"+bot_token+"/sendMessage?chat_id="+userid+"&text="+message

    response = requests.post(url)
    if response.status_code == 200:print(response.text)
    else : print("something wrong")

