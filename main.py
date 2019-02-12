import feedparser
import re
import time
from bs4 import BeautifulSoup
import boto3
import os
import datetime

proj_name = 'Ridehome AWS'
file_name = 'index.html'

aws_key = os.environ['AWS_ACC_KEY']
aws_secret = os.environ['AWS_SEC_KEY']

def generate_index(file_name):

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("Parsing website")
    rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')
    print("Website parsed")

    print("Writing data to index")
    with open(file_name,'w',encoding='utf-8') as html_file:

        html_file.write(f"""<html>
        <head><meta charset="utf-8"></head>
        <body>
        <div style="width:100%; text-align:right">Last updated: {timestamp}</div>
        
        """)

        for post in rhfeed.entries:
            postPubTime = time.strftime("%A, %B %d %Y", post.published_parsed)
            podTitle = ""
            podTitleArray = post.title.split(' - ')
            if len(podTitleArray) > 1:
                podTitle = podTitleArray[1]
            else:
                podTitle = podTitleArray[0]

            html_file.write("\n<h3>" + postPubTime + " - " + podTitle + "</h3>\n")
            cleanPost = post.summary.replace('\n', '')
            soup = BeautifulSoup(cleanPost, 'html5lib')
            linksBlock = soup.find_all("p", string=re.compile("^Links(:*)(\ *)$|Stories:$"))

            # check to see if we found anything
            # specifically at least one paragraph stating Links were coming and that the following ul contains a tags
            # this is a horrible way to do things but it's working so far
            if len(linksBlock) > 0 and len(linksBlock[0].next_sibling.find_all('li')) > 0:
                ul = str(linksBlock[0].next_sibling)
                html = ul
                html_file.write(html)
            else:
                uls = soup.find_all("ul")
                if len(uls) == 1:
                    html_file.write(str(uls[0]))
                else:
                    html_file.write("No show links for this episode ¯\_(ツ)_/¯\n")
    print("Index written.")

#######################################################################################################################

def ship_to_s3(file_name):

    bucket_name = "web-host-example"
    local_file_name = file_name
    remote_file_name = file_name

    session = boto3.Session(
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
    )

    s3 = session.client('s3',)

    print("Sending file to S3")
    s3.upload_file(local_file_name, bucket_name, remote_file_name,  ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})
    print("File sent.")

#######################################################################################################################

def run(event, context):

    generate_index(file_name)
    ship_to_s3(file_name)

    return 'Success'

if __name__ == '__main__':

    run()


