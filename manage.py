import os
from fly_bbs import create_app
from flask_script import Manager

config_name = os.environ.get('FLASK_CONFIG') or 'Dev'
app = create_app(config_name)
manager = Manager(app)
import pdb
pdb.set_trace()
if __name__ == '__main__':
    manager.run()
