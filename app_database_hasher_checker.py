from mysql.connector import connect, Error
from hashlib import sha256

dbHost = "localhost"
dbUser = "root"
dbPass = "root"
dbName = "jamfsoftware"

sql = "SELECT name, version, short_version, bundle_id, external_version_identifier, lookup_hash FROM mobile_device_application_details"

hashFormat = "{name}|{s_version}|{version}|{bundle}|{external}"

try:
    with connect(
        host=dbHost,
        user=dbUser,
        password=dbPass,
        database=dbName,
    ) as connection:
        with connection.cursor(dictionary = True) as cursor:
        	
        	cursor.execute(sql)
        	
        	for app in cursor.fetchall():
        		stringToHash = hashFormat
        			.format(name=app["name"], s_version=app["short_version"], version=app["version"], bundle=app["bundle_id"], external=app["external_version_identifier"])
        		generatedHash = sha256(stringToHash.encode('utf-8')).hexdigest()
        		
        		if generatedHash != app["lookup_hash"]:
        			print("name: {name}, bundle_id: {bundle} - lookup_hash: {lookup}, generated: {generated}"
        				.format(name=app["name"], bundle=app["bundle_id"], lookup=app["lookup_hash"], generated=generatedHash))
        			
except Error as e:
    print(e)