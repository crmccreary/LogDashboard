import datetime
from pytz import timezone, UTC
import json
import re

from jinja2 import evalcontextfilter, Markup, escape

from flask import Flask, request, render_template, jsonify
from flaskext.mongoalchemy import MongoAlchemy
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['MONGOALCHEMY_DATABASE'] = 'zarkov'
app.config['MONGOALCHEMY_SERVER'] = 'kilgore'
db = MongoAlchemy(app)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

class Context(db.Document):
    config_collection_name = 'context'

    status = db.IntField()
    description = db.StringField()
    server = db.StringField()

class Extra(db.Document):
    config_collection_name = 'extra'

    stderr = db.StringField()
    stdout = db.StringField()

class Event(db.Document):
    config_collection_name = 'event'

    id = db.IntField(db_field = '_id')
    timestamp = db.DateTimeField()
    type = db.StringField()
    context = db.DocumentField(Context)
    extra = db.DocumentField(Extra)

'''
Need a custom jinja2 filter to replace line breaks with <br>\n
Courtesy of Dan Jacob - http://flask.pocoo.org/snippets/28/
'''
@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(value))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

'''
The root view is a jQuery calendar app - FullCalendar
http://arshaw.com/fullcalendar
https://github.com/crmccreary/fullcalendar <- forked from https://github.com/arshaw/fullcalendar
'''
@app.route('/')
def show_events():
    return render_template('basic-views.html')

'''
The url that FullCalendar calls to get the events between the start and end
'''
@app.route('/events/')
def list_events():
    """List events for ajax supplied start and end."""
    start = request.args.get('start', 0, type=int)
    end = request.args.get('end', 0, type=int)
    # make a datetime from the timestamp
    start = datetime.datetime.fromtimestamp(start)
    end = datetime.datetime.fromtimestamp(end)
    # Fetch the events from MongoDB
    _events = Event.query.filter(Event.timestamp >= start, Event.timestamp <= end)
    # Build the json so FullCalendar will swallow it
    events = []
    for event in _events:
        # Localize the time and get rid of the microseconds
        event_start = UTC.localize(event.timestamp).astimezone(timezone('US/Central')).replace(microsecond=0)
        # Make the event 5 minutes
        event_end = (event_start + datetime.timedelta(minutes=5)).replace(microsecond=0)
        event_dict = {'title' : event.context.description,
                      'id' : event.id,
                      'allDay' : False,
                      'start' : event_start.isoformat(),
                      'end' : event_end.isoformat(),
                      'url' : '/event/{0}'.format(event.id)} # Url for the event detail
        if event.context.status != 0:
            event_dict.update({'color' : 'red'})
        events.append(event_dict)
    return json.dumps(events)

@app.route('/event/<int:event_id>')
def show_post(event_id):
    # show the post with the given id, the id is an integer
    _event = Event.query.filter(Event.id == event_id).one()
    return render_template('show_event.html', event=_event)

if __name__ == '__main__':
    app.run()

