import re
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import string

nltk.download('punkt')

def preprocess(data):
    pattern = '\d{1,2}\/\d{1,2}\/\d{2,4},\s\d{1,2}:\d{2}\s[a|p]?m?\s?-\s'
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if dates[0].split()[2] == 'am' or dates[0].split()[2] == 'pm':
        # extaract time '10:07 am' only
        def time_extract(msg):
            return msg.split(',')[1].split('-')[0].strip()

        # convert time into 24hr format
        def convert24(str1):

            # Checking if last two elements of time
            # is AM and first two elements are 12
            if str1[-2:] == "am" and str1[:2] == "12":
                return "00" + str1[2:-2]

            # remove the AM    
            elif str1[-2:] == "am":
                return str1[:-2]

            # Checking if last two elements of time
            # is PM and first two elements are 12
            elif str1[-2:] == "pm" and str1[:2] == "12":
                return str1[:-2]
            else:
                # add 12 to hours and remove PM
                if len(str1.split(':')[0]) == 1:
                    str1 = str(0)+str1[:-3]
                else:
                    str1[:-3]

                return str(int(str1[:2]) + 12) + str1[2:5]
        
        # creating dataframe
        df = pd.DataFrame({'user_message':messages,'message_date':dates})
        df['time'] = df['message_date'].apply(time_extract)
        df['time'] = df['time'].apply(convert24)

        # adding time in 24 hr to date inside a list
        date_time = []
        for i in range(df.shape[0]):
            date_time.append(df['message_date'][i].split(',')[0] + ', ' + df['time'][i])

        # creating dataframe of new 24hr format time
        temp_df = pd.DataFrame(date_time)
        temp_df.rename(columns= {0:'date_t'},inplace=True)

        # joining 2 dataframes
        df = pd.concat([df, temp_df],axis=1)
        df.drop(['message_date','time'],axis=1, inplace=True)
        df.rename(columns={'date_t':'message_date'},inplace=True)
        df['message_date'] = pd.to_datetime(df['message_date'], infer_datetime_format=True)
        df.rename(columns={'message_date':'date'},inplace=True)
    
    else:
        df = pd.DataFrame({'user_message':messages,'message_date':dates})
        df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M - ')
        df.rename(columns={'message_date':'date'},inplace=True)

    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split(':', message)
        if entry[1:]:
            users.append(entry[0])
            messages.append(entry[1])
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)
    df = df[df['user'] != 'group_notification']

    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month_name()
    df['month_num'] = df['date'].dt.month
    df['only_date'] = df['date'].dt.date
    df['day_name'] = df['date'].dt.day_name()
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    def remove_punctuation(word):
        word_list = word_tokenize(word)
        lst = []
        for i in word_list:
            if i not in string.punctuation:
                lst.append(i)

        return ' '.join(lst)

    df['message'] = df['message'].apply(remove_punctuation)

    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(str(hour) + '-' + str('00'))
        elif hour == 0:
            period.append(str('00') + '-' + str(hour + 1))
        else:
            period.append(str(hour) + '-' + str(hour + 1))

    df['period'] = period

    return df
