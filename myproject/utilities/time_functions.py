from datetime import datetime, timedelta


def day_of_week():
	# returns day in string: monday or tuesday or ...
	return datetime.today().strftime('%A').lower()


def add_time(time, minutes=0, hours=0,):
	# adds <h> hours and <m> minutes to the <time> parameter
	return (datetime.combine(datetime.today(), time) + timedelta(hours=hours, minutes=minutes)).time()

