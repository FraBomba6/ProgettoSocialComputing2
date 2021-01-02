import string
import random
import boto3
import json
import os
import smtplib
import ssl
import credentials


def s3Init():
    return boto3.resource(
        's3',
        aws_access_key_id=credentials.worker_key_id,
        aws_secret_access_key=credentials.worker_access_key
    )


def downloadWorkers(s3):
    bucket = s3.Bucket('sc-cs-tasks')
    bucket.download_file('ProgettoSocialComputing2/Batch1/Task/workers.json', './workers.json')
    print('Workers downloaded from S3')


def uploadWorkers(s3):
    bucket = s3.Bucket('sc-cs-tasks')
    bucket.upload_file('./workers.json', 'ProgettoSocialComputing2/Batch1/Task/workers.json')
    print('Workers uploaded to S3')


def serialize_json(filename, data):
    with open(filename, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data serialized to path: {filename}")


def read_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf8") as file:
            data = json.load(file)
        print(f"Data read from path: {file_path}")
        return data
    else:
        print(f"No data found at path: {file_path}")
        return {}


def send_mail(plain, html, to):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    print('Composing message...')

    user = credentials.address
    password = credentials.password

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    provider_connection = smtplib.SMTP('smtp.office365.com', 587)
    provider_connection.ehlo()
    provider_connection.starttls(context=context)
    provider_connection.ehlo()
    provider_connection.login(user, password)

    message = MIMEMultipart('alternative')
    message['Subject'] = 'Partecipazione al progetto di Social Computing'
    message['From'] = 'bombasseidebona.francesco@spes.uniud.it'
    message['To'] = to
    message['Cc'] = 'zanatta.alessandro@spes.uniud.it, cantarutti.andrea@spes.uniud.it'

    plainText = MIMEText(plain, 'plain')
    htmlText = MIMEText(html, 'html')

    message.attach(plainText)
    message.attach(htmlText)

    provider_connection.send_message(message)
    provider_connection.close()

    return 'Message sent!'


def generateUserId():
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(5))


s3 = s3Init()
to = input("Enter a mail address or a list of addresses separated by commas: ")
toList = to.split(",")
downloadWorkers(s3)
tokenList = read_json('./tokens.json')
lastToken = read_json('./last.json')['token'] + 1
workers = read_json('./workers.json')
whitelist = workers['whitelist']
for i in range(len(toList)):
    userID = generateUserId()
    tokenIndex = (lastToken + i) % len(tokenList)
    token = tokenList[tokenIndex]['token_input']

    plain = f"""Grazie per averci dato la sua disponibilità a partecipare al nostro progetto per il corso di Social Computing.
    Sarà sottoposto a un breve questionario su alcuni libri. Non le sono richieste abilità particolari e non le è richiesto di essere un lettore abituale.
    
    Per iniziare copi il token di input riportato di seguito e lo inserisca quando richiesto.
    
    Token di input: {token}
    
    
    Ora è necessario che apra il seguente link per iniziare il questionario, sarà guidato dal sistema durante la compilazione.
    
    https://sc-cs-deploy.s3.eu-south-1.amazonaws.com/ProgettoSocialComputing2/Batch1/index.html?workerID={userID}"""

    html = f"""Grazie per averci dato la sua disponibilità a partecipare al nostro progetto per il corso di Social Computing.<br>
    Sarà sottoposto a un breve questionario su alcuni libri. Non le sono richieste abilità particolari e non le è richiesto di essere un lettore abituale.<br><br>
    Per iniziare copi il token di input riportato di seguito e lo inserisca quando richiesto.<br>
    <h4>Token di input: {token}</h4>
    Ora è necessario che apra il seguente <a href="https://sc-cs-deploy.s3.eu-south-1.amazonaws.com/ProgettoSocialComputing2/Batch1/index.html?workerID={userID}">link per iniziare il questionario</a>, sarà guidato dal sistema durante la compilazione.
    <br>
    La ringraziamo per aver partecipato a questa esperienza, aiutandoci così nel nostro percorso di studi.
    <br><br><br><br><br><br>
    Nel caso il link precedente non funzionasse:<br>
    https://sc-cs-deploy.s3.eu-south-1.amazonaws.com/ProgettoSocialComputing2/Batch1/index.html?workerID={userID}"""

    print(send_mail(plain, html, toList[i]))
    whitelist.append(userID)
    lastToken = tokenIndex
workers['whitelist'] = whitelist
serialize_json('./workers.json', workers)
serialize_json('./last.json', {"token": lastToken})
uploadWorkers(s3)