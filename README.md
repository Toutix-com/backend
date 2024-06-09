Readme for the Backend:
To update any changes to database:

flask db migrate ->
flask db upgrade

To update any changes to heroku:

Heroku login ->
heroku run bash ->
cd app ->
flask db upgrade(Here do not migrate as it will create duplicate file and cause error, just upgrade would do the job)




test

a