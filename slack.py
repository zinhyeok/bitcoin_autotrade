import requests


def post_message(token, channel, text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text},
    )
    print(response)


myToken = "xoxb-2799366043639-2816286941284-yDDBBjbHhbeGp0xIhnwW3I5c"

post_message(myToken, "#history", "jocoding")
