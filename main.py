import argparse
import requests

from lxml import html


def main():
    parser = argparse.ArgumentParser(description='Get today\'s workout from Catalyst Athletics.')
    parser.add_argument('-u', dest='user', help='Username', required=True)
    parser.add_argument('-p', dest='password', help='Password', required=True)
    parser.add_argument('-discord', dest='discord', help='Discord webhook URL')

    args = parser.parse_args()

    # Create a session and log in
    session_requests = requests.session()
    login_url = 'https://www.catalystathletics.com/profile/index.php'
    payload = get_login_payload(args.user, args.password)
    
    # Force correct headers for multipart form
    files = {'file': ''}

    result = session_requests.post(
        login_url, 
        data = payload, 
        headers = dict(referer=login_url),
        files=files
    )

    if result.status_code != 200:
        raise("Unexpected http status code %d" % result.code)

    # Get the workout list
    workouts_url = 'https://www.catalystathletics.com/olympic-weightlifting-workouts/'
    result = session_requests.get(
        workouts_url,
        headers = dict(referer = workouts_url)
    )

    # Get the link for the most recent workout (that should be today's)
    tree = html.fromstring(result.content)
    todays_workout_url = get_todays_workout_url(tree)

    # Get todays workout
    result = session_requests.get(
        todays_workout_url,
        headers = dict(referer = workouts_url)
    )

    tree = html.fromstring(result.content)
    todays_workout = get_todays_workout(tree)
    todays_workout = [x.strip() for x in todays_workout]
    todays_workout_text = "\n".join(todays_workout)
    
    if args.discord:
        post_to_discord_webhook(args.discord, todays_workout_text)
    else:
        for x in todays_workout:
            print(x.encode('ascii', 'ignore').decode('ascii'))


def post_to_discord_webhook(webhook_url, message):
    data = {
        "content": message
    }
    requests.post(webhook_url, data)


def get_login_payload(username, password):
    return {
	    "fm_email": username, 
	    "fm_password": password,
        "fm_where_user_came_from": 'https://www.catalystathletics.com/',
        "fm_password_md5": "",
        "submit_login": "",
        "fm_login_remember_me": "Yes"
    }


def get_todays_workout(tree):
    main_workout = tree.xpath("""//body/div[@id='pageWrapper']
                                   /div[@id='contentWrapper']
                                   /div[@id='main_content_container']
                                   /div[@id='leftColumn']
                                   /div[@class='workouts_list_text']
                                   /ul/li/text()""")
    accessories = tree.xpath("""//body/div[@id='pageWrapper']
                                   /div[@id='contentWrapper']
                                   /div[@id='main_content_container']
                                   /div[@id='leftColumn']
                                   /div[@class='workouts_list_text']
                                   /ul/following-sibling::text()""")

    return main_workout + ["------"] + accessories


def get_todays_workout_url(tree):
    todays_workout_url = tree.xpath("""//body/div[@id='pageWrapper']
                                       /div[@id='contentWrapper']
                                       /div[@id='main_content_container']
                                       /div[@id='leftColumn']
                                       /div[@class='workouts_list_text'][1]
                                       /span[@class='workouts_list_date']
                                       /a/@href""")[0]
    todays_workout_url = "https://www.catalystathletics.com" + todays_workout_url
    
    return todays_workout_url


if __name__ == '__main__':
    main()
