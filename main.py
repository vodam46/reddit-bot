import praw
from gtts import gTTS
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
import imgkit
from moviepy.editor import *
import datetime
from time import sleep
from simple_youtube_api.Channel import Channel
from simple_youtube_api.LocalVideo import LocalVideo
import string

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import traceback

reddit = praw.Reddit(
        client_id = "Xfonp9P2zlG9TA",
        client_secret = "RwUYIJkoZ8Q7ljH41eJL2jd1RplaPw",
        user_agent = "r/youtube bot",
)
post_file = open("posts","a+")

pposts = post_file.read().split("\n")

days_file = open("days","a+")
days_file_r = open("days","r")
days = days_file_r.read().split("\n")

channel=Channel()
channel.login("google-secret.json", "credentials.storage")

def clean(s):
    return ''.join([c for c in s if c in set(string.printable)])
def main():
    posts = reddit.subreddit("askreddit").top(time_filter="day")
    for post in posts:
        if post.id not in pposts:
            break

    print(post.title)
    post.title=clean(post.title)
    pposts.append(post.id)
    post_file.write(post.id+"\n")

    # """
    audio = gTTS(text=post.title,lang="en")
    audio.save("audio/"+post.id+"_0.mp3")

    post_html = BeautifulSoup(open("post.html").read(), "html.parser")
    post_html.find(id="comments").string=str(post.num_comments)
    post_html.find(id="title").string=post.title
    post_html.find(id="upvotes").string=str(post.score)
    post_html.find(id="subreddit").string="r/AskReddit"
    post_w = open("html/"+post.id+"_0.html","w+")
    post_w.write(str(post_html))
    post_w.close()

    imgkit.from_file("./html/"+post.id+"_0.html","png/"+post.id+"_0.png",options={"enable-local-file-access": ""})

    length = 0
    i = 1
    comments = [post.id+"_0"]
    try:
        for comment in sorted(post.comments, key=lambda c: c.score if type(c) != praw.models.MoreComments else 0, reverse=True):
            if comment.body != "[deleted]" and comment.body != "[ Removed by Reddit ]":
                print(f"{i} {length} {comment.score} comment:\n {comment.body}")

                audio = gTTS(text=comment.body,lang="en")
                audio.save("audio/"+post.id+"_"+str(i)+".mp3")
                length += MP3("audio/"+post.id+"_"+str(i)+".mp3").info.length

                comment_html = BeautifulSoup(open("comment.html").read(),"html.parser")
                comment_html.find(id="upvotes").string=str(comment.score)
                comment_html.find(id="author").string=comment.author.name
                comment_html.find(id="content").string=clean(comment.body)
                comment_w = open("html/"+post.id+"_"+str(i)+".html","w+")
                comment_w.write(str(comment_html))
                comment_w.close()

                imgkit.from_file("html/"+post.id+"_"+str(i)+".html","png/"+post.id+"_"+str(i)+".png",options={"enable-local-file-access": ""})
                comments.append(post.id+"_"+str(i))

                i+=1
            if length >= 600:
                break

    except Exception as e:
        print(traceback.format_exc())

    video_sv = concatenate_videoclips([
        ImageClip("png/"+c+".png").set_duration(MP3("audio/"+c+".mp3").info.length) for c in comments
        ],method="compose")
    audio = concatenate_audioclips([AudioFileClip("audio/"+c+".mp3") for c in comments])
    audio.write_audiofile("audio/"+post.id+".mp3")
    video_sv.write_videofile(filename="video/"+post.id+".mp4",audio="audio/"+post.id+".mp3",fps=24)
    # """

    # upload to youtube
    print("-"*100)
    print(post.title, "\n", post.id, len(post.title))

    video = LocalVideo(file_path="video/"+post.id+".mp4")

    if len(post.title) > 100:
        tokens = word_tokenize(post.title)
        post.title = ' '.join([w for w in tokens if not w in stopwords.words()])
    print(post.title)
    video.set_title(post.title)
    
    video.set_description(
    "Reddit Daily Asks is a bot, this video was uploaded automatically\n"+
    "source code is available at github.com/vodam46/reddit-bot\n"+
    "original post is at www.reddit.com/r/AskReddit/comments/"+post.id
    )
    tags = ["reddit","askreddit","r/askreddit"]
    video.set_tags(tags)
    video.set_category("entertainment")
    video.set_default_language("en-US")

    video.set_embeddable(True)
    video.set_privacy_status("private")

    video.set_thumbnail_path("png/"+post.id+"_0.png")

    video = channel.upload_video(video)

    print(video.id)

if __name__ == "__main__":
    while True:
        try:
            print(str(datetime.date.today()), days)
            if str(datetime.date.today()) not in days:
                main()
                days.append(str(datetime.date.today()))
                days_file.write(str(datetime.date.today())+"\n")
        except Exception as e:
            print(traceback.format_exc())
            exit(1)
        sleep(60)
