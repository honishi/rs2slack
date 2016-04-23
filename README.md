rs2slack
==
scraping yahoo real-time search, and post tweets to slack.

setup
--
```
brew install pyenv pyenv-virtualenv
pyenv install 3.4.4
pyenv virtualenv 3.4.4 rs2slack
pip install -r requirements.txt
cp rs2slack.config.sample rs2slack.config
vi rs2slack.config
```

usage
--
```
# start
./rs2slack.sh start

# stop
./rs2slack.sh stop
```

license
--
copyright &copy; 2016- honishi, hiroyuki onishi.

distributed under the [MIT license][mit].
[mit]: http://www.opensource.org/licenses/mit-license.php
