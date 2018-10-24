Development
================

1. Install docker
2. Run `npm start`
3. Open [localhost:10101](http://localhost:10101/) in the browser

API Calls
=========

GET /api/status 
- returns the status of the app

POST /api/urls/ 
mega_url=$SOME_URL
- sends the url to the backend

DELETE /api/urls/{url_id}
- deletes a url from the history
