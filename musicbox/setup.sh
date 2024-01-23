sudo apt-get install mpg123
sudo apt-get install supervisor

amixer set Master 80%

sudo cp supervisord/*.conf /etc/supervisor/conf.d/
sudo supervisorctl reload
