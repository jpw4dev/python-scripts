from hashlib import sha256
import csv

class App:

	hashFormat = '{}|{}|{}|{}|{}'
	numFields = 9
	
	def __init__(self, row):
		self.id = row[1].strip()
		self.name = row[2].strip()
		self.version = row[3].strip()
		self.shortVersion = row[4].strip()
		self.bundleId = row[5].strip()
		self.externalId = row[6].strip()
		self.hash = row[7].strip()
		self.generatedHash = sha256(App.hashFormat \
			.format(self.name, self.version, self.shortVersion, self.bundleId, self.externalId).lower().encode('utf-8')).hexdigest()
	
	def toString(self):
		return 'id="{}", name="{}", version="{}", shortVersion="{}", bundleId="{}", externalId="{}", hash="{}", generatedHash="{}"' \
			.format(self.id, self.name, self.version, self.shortVersion, self.bundleId, self.externalId, self.hash, self.generatedHash)

sqlPath = input('Enter path to file: ').strip()

with open(sqlPath, newline='') as csvfile:

	appsByBundleId = {}
	mismatching = []
	total = 0
	
	for row in csv.reader(csvfile, delimiter='|', quotechar='"'):
		
		if len(row) == App.numFields and row[1].strip() != 'id':
			try:
				app = App(row)
			
				if app.hash != app.generatedHash:		
					mismatching.append(app)
					
				if app.bundleId in appsByBundleId:
					appsByBundleId[app.bundleId].append(app)
				else:
					appsByBundleId[app.bundleId] = [app]
					
				total = total + 1
					
			except:
				pass
				
	print('\n--- mismatching hashes --\n')
		
	for app in mismatching:
		print(app.toString(), '\n')
		
	print('total: {}, mismatches: {}\n'.format(total, len(mismatching)))