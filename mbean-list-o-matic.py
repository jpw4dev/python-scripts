#!/usr/bin/env python

import argparse, json
from jmxquery import JMXConnection, JMXQuery

HOST=""
PORT=0
USER=""
PASS=""
OUTPUT=""
DOMAINS=[]


def get_args():

	global HOST
	global PORT
	global USER
	global PASS
	global OUTPUT
	global DOMAINS
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("--host", type=str, default="localhost", help="jmx host")
	parser.add_argument("--port", type=int, default=1099, help="jmx port")
	parser.add_argument("--jmxUser", type=str, help="jmx username")
	parser.add_argument("--jmxPass", type=str, help="jmx password")
	parser.add_argument("--domain", type=str, default="com.company,micrometer", help="comma delimited list of domains to search")
	parser.add_argument("--output", type=str, help="file path to save json")
	
	args = parser.parse_args()
	
	HOST=args.host
	PORT=args.port
	USER=args.jmxUser
	PASS=args.jmxPass
	DOMAINS=args.domain.split(",")
	OUTPUT=args.output
	
def get_mbeans():

	root = {"domains": []}
	
	for domain in DOMAINS:
		root["domains"].append({"name": domain, "mbeans": build_list_for_domain(domain)})
			
	mbeans = json.dumps(root, indent=4)
	
	if OUTPUT:
		with open(OUTPUT, 'w') as f:
			f.write(mbeans)
	else:
		print(mbeans)

def build_list_for_domain(domain):
	
	metrics = run_jmx_query(domain)

	mbeans = []
	
	for metric in metrics:
		
		beanName = metric.mBeanName
		beanAttr = {"name": metric.attribute, "type": metric.value_type}

		index = next((i for i,d in enumerate(mbeans) if beanName in d["name"]), None)

		if index:
			mbeans[index]["attributes"].append(beanAttr)
		else:
			mbeans.append({"name": beanName, "attributes": [beanAttr]})
			
	return mbeans

def run_jmx_query(domain):
	connectString = "service:jmx:rmi:///jndi/rmi://{}:{}/jmxrmi".format(HOST,PORT)
	jmxConn = JMXConnection(connectString, USER, PASS)	
	return jmxConn.query([JMXQuery(domain + ":*")])
	
if __name__ == '__main__':
	get_args()
	get_mbeans()