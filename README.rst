LogDashboard
============

LogDashboard extracts logging events saved to a MongoDB store with Zarkov and displays the events on a calendar. The jQuery FullCalendar app is used for the calendar. The status of the event is used to color the background so that if an error occurred, the background is set to red.

Flask is used for the (micro)framework. The MongoAlchemy flask extension is used for the MongoDB ORM.
