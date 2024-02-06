
import logging
from datetime import datetime, timedelta
import babel.dates as bdates

def setup_template_filters(app):
    @app.template_filter()
    def format_datetime(value, format='medium'):
        if value < datetime(2000, 1, 1):
            return "-"
        if format == 'full':
            format="EEEE, d. MMMM y 'at' HH:mm"
        elif format == 'medium':
            format="EE dd.MM.y HH:mm"
        elif format == 'delta':
            return bdates.format_timedelta(datetime.now() - value, locale='en')
        
        return bdates.format_datetime(value, format, locale='en')


    @app.template_filter()
    def is_online(value):
        return (datetime.now() - value) < timedelta(minutes=5)