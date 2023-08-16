import os
from peewee import *
from dotenv import load_dotenv
from peewee_migrate import Router


load_dotenv()  # take environment variables from .env.

mysql_db = MySQLDatabase(database=os.getenv('FTP_DB_NAME'), user=os.getenv('FTP_USERNAME'),
                         password=os.getenv('FTP_PASSWORD'), host=os.getenv('FTP_URL'), port=3306)
router = Router(mysql_db)

# router.create('test_migration')

# Run all unapplied migrations
router.run()
