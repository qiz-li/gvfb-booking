from bs4 import BeautifulSoup
import datetime
import requests
import time
import yaml


def get_config():
    """Reads user config from config.yaml.

    Returns:
        dict: User credentials and time of the shift(s) to book.
    """
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def login(config):
    """Login to get cookie for further actions.

    Args:
        config (dict): User configuration with credentials.

    Returns:
        Requests authenticated session object.
    """
    client = requests.session()
    login_url = 'https://app.betterimpact.com/Login/Login'

    # Retrieve the login CSRF token
    login_page = BeautifulSoup(client.get(
        login_url).content, features='html.parser')
    csrftoken = login_page.find(
        'input', {'name': '__RequestVerificationToken'})['value']

    login_data = {'username': config['username'],
                  'password': config['password'],
                  '__RequestVerificationToken': csrftoken}
    client.post(login_url, data=login_data)

    return client


def find_shift(date, shifts_times):
    """Take the day and shift times to form a list of readable shift dates.

    There are only three options for shift_times,
    either '912', which is 9 AM - 12 PM, or '14', which is 1 PM - 4 PM, or
    '58', which is 5 PM to 8 PM.

    Args:
        date (str): Human readable weekday name (monday, saturday...).
        shift_times (list): List of shift times to book that day (see above).

   Returns:
        list: List of shift date and times in a human readable format.
    """
    today = datetime.date.today()

    shifts_times = [shifts_times] if isinstance(
        shifts_times, int) else shifts_times

    # Find how many days there are until the specified day
    weekday_as_int = time.strptime(date, "%A").tm_wday
    days_until_next = (weekday_as_int - 1 - today.weekday()) % 7 + 1

    shifts = []
    # Find that day for the next three weeks
    for i in range(3):
        shift_date = (today +
                      datetime.timedelta(
                          days_until_next + i * 7)).strftime('%A, %B %-d, %Y')
        # Add the corresponding specified time
        for shift_time in shifts_times:
            if shift_time == 912:
                shifts.append(shift_date + " 9:00 AM - 12:00 PM")
            elif shift_time == 14:
                shifts.append(shift_date + " 1:00 PM - 4:00 PM")
            elif shift_time == 58:
                shifts.append(shift_date + " 5:00 PM - 8:00 PM")
    return shifts


def get_ids(config, client, shifts_url):
    """Scrape the sign-up page for ids.

    Args:
        config (dict): User configuration with times.
        client (obj): Authenticated Requests session object.
        shifts_url (str): Page url where all the shifts can be found.

    Returns:
        Tuple with ID of the member, ID of the activity,
        and ID of the shifts to book.
    """
    shifts_page = BeautifulSoup(client.get(
        shifts_url).content, features='html.parser')

    member_id = shifts_page.find(
        'input', {'id': 'OrganizationMemberId'})['value']
    activity_id = shifts_page.find(
        'input', {'name': 'activityId'})['value']

    shift_ids = []
    # Find the shift ID using the shift name
    for date, shift_times in config['time'].items():
        for shift_name in find_shift(date, shift_times):
            try:
                shift_ids.append(shifts_page.find(
                    'tr', {'data-details': shift_name})['data-id'])
            except TypeError:
                continue

    return member_id, activity_id, shift_ids


def book_shifts(client, member_id, activity_id, shift_ids):
    """Book all the specified shifts using the given IDs.

    Args:
        client (obj): Authenticated Requests session object.
        member_id (str): ID of the member in the organization.
        activity_id (str): ID of the activity to book.
        shift_ids (list): List of shift IDs to book, in strings.

    Returns:
        dict: JSON Response from all the bookings.
    """
    shift_headers = {'X-Requested-With': 'XMLHttpRequest'}
    shift_params = {'activityId': activity_id,
                    'organizationMemberId': member_id, 'groupSize': '1'}

    responses = []
    for shift_id in shift_ids:
        shift_params['activityShiftId'] = shift_id
        responses.append(client.post(
            "https://app.betterimpact.com/Volunteer/Schedule/SignupForShift",
            params=shift_params, headers=shift_headers).json())
    return responses


def parse_response(responses):
    """Parse JSON message into readable message.

    Args:
        responses (list): List of all JSON responses from the booking.

    Returns:
        Human readable message stating which shifts, if any, were booked.
    """
    count = 0
    message = ""
    for response in responses:
        if response['WasSuccessful']:
            count += 1

            # Parse start and end times from the JSON response
            time_end_str = response['TimeIntervalString'].split('/')[1]
            time_end_obj = datetime.datetime.strptime(
                time_end_str, '%Y-%m-%dT%H:%M:%S.%f0')
            time_start_obj = time_end_obj - datetime.timedelta(hours=3)

            message += (
                f"- {time_start_obj.strftime('%A, %B %-d, %Y %-I:%M %p')}"
                f" to {time_end_obj.strftime('%-I:%M %p')}\n")
    if count:
        return f"Successfully signed up for {count} shifts:\n{message.strip()}"
    else:
        return "Sorry, the shifts are full or could not be found."


def main():
    config = get_config()
    client = login(config)

    shifts_url = (
        'https://app.betterimpact.com/Volunteer/Schedule/'
        'OpportunityDetails?guid=857823bf-2f37-447e-a841-a73e446aa916')
    return(parse_response(book_shifts(client,
                                      *get_ids(config, client, shifts_url))))


if __name__ == "__main__":
    print(main())
