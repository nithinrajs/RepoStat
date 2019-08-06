from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
from github import Github
import slack
from data import current_repo_list
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
import boto3
from boto3.session import Session


def repo_diff(current, updated):
    diff = list(set(current) ^ set(updated))
    return diff


def slack_stats(update=False, changes=[]):
    SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
    client = slack.WebClient(SLACK_TOKEN)
    now = datetime.datetime.now()
    log = now.strftime("%Y-%m-%d %H:%M")

    if (not update):
        app.logger.warning(
            "\n****EOD ( %s )****\n" % log)

        ''' Session for AWS S3 Bucket '''
        AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
        AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

        session = Session(AWS_ACCESS_KEY, AWS_SECRET_KEY)
        s3 = session.client('s3')
        folder = "test/debug/"  # Folder inside the S3 Buckets for the Logs

        filename = "progress.log"
        path = "./debug/"

        s3.upload_file(path+filename, 'repostat-bucker', folder+filename)

        ''' ######################  '''

        response = client.chat_postMessage(
            channel='#security', text="I am doing well on Heroku!")

    # elif(not update and change_flag != 0):
    #     app.logger.warning(
    #         "\n%d changes Made to the Public Repos At the EOD ( %s ).\n" % (change_flag, log))

    #     response = client.chat_postMessage(
    #         channel='#security', text="Changes Made to the Public Repos At the EOD")

    elif (update and len(changes) != 0):
        l = '\n'.join(changes)
        m = "*Changes were made to the Zendesk Public Repo's!*\n"
        message = m+l
        message = "```" + message + "```"
        response = client.chat_postMessage(
            channel='#security', text=message)

    else:
        app.logger.error("<><><> AN ERROR HAS OCCURRED <><><>")


app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/script")
def script():
    GIT_TOKEN = os.environ.get('GIT_TOKEN')

    r = []
    now = datetime.datetime.now()
    log = now.strftime("%Y-%m-%d %H:%M")

    gh = Github(GIT_TOKEN)
    org = gh.get_organization('zendesk')
    public_repos = org.get_repos()
    for repo in public_repos:
        r.append(repo.full_name)

    current_list = current_repo_list()

    if (len(r) != len(current_list)):
        app.logger.info("New Repos Added!\n")

        ''' Session for AWS S3 Bucket '''
        AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
        AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

        session = Session(AWS_ACCESS_KEY, AWS_SECRET_KEY)
        s3 = session.client('s3')
        folder = "test/logs/"  # Folder inside the S3 Buckets for the Logs

        ''' ######################  '''
        filename = "repos-%s.txt" % log
        path = "./logs/"

        with open(path+filename, "w") as f:
            f.write("<><><><><><> Repo List Updated on %s. <><><><><><>\n" % log)
            f.write('\n'.join(r))

        s3.upload_file(path+filename, 'repostat-bucker', folder+filename)

        with open('repos.txt', 'w') as f:
            f.write('\n'.join(r))

        new = repo_diff(current_list, r)
        slack_stats(update=True, changes=new)

        app.logger.info("\nRepo list updated\n")
        app.logger.warning("Repo's Made Public are %s at %s" % (new, log))

    else:
        app.logger.info("No changes in Number of Repos!")
        app.logger.warning("No Changes to Public Repo's at %s" % log)


sched = BackgroundScheduler(daemon=True)
sched.add_job(script, 'interval', minutes=2)
sched.start()

slack_sched = BackgroundScheduler(daemon=True)
slack_sched.add_job(slack_stats, 'interval', minutes=3)
slack_sched.start()


if __name__ == "__main__":
    handler = RotatingFileHandler(
        './debug/progress.log', maxBytes=10000, backupCount=2)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    port = int(os.environ.get("PORT", 33507))
    app.run(host='0.0.0.0', port=port)


'''
Format the array for slack messages
Time the report appropriately
Do a daily end of the day update to slack

Think of other possibilites
Check if you can do this without a github token
'''
