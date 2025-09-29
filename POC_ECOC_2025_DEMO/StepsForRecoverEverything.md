# Step1: Delete the appInstances and apps by using CAMARA Swagger Api
## Note: The appInstanceId and appId can be found under table of APP_INSTANCE_INFO in h2 database
# Step2: Delete the data record in table of APP_PROFILE, INSIGHT_SUB, NETWORKFLOW_INFO, NETWORKSLICE_INFO, QOSSESSION
# Step3: Clean and initialize the yang datastore:
## You can excute these commands in your vm terminal:
## 1. onosIp = 192.168.198.111:8181
## 2. curl -X POST -H "content-type:application/json" http://${onosIp}/pncsimu/v1/clear-data -d'{}'
## 3. curl -X POST -H "content-type:application/json"  http://${onosIp}/restconf/data -d'{"camara-qod:qod-instances":{}}'
## 4. curl -X POST -H "content-type:application/json"  http://${onosIp}/restconf/data -d'{"ietf-network-slice-service:network-slice-services":{}}'
## 5. curl -X POST -H "content-type:application/json"  http://${onosIp}/restconf/data -d'{"ietf-l3vpn-svc:l3vpn-services":{}}'
## 7. post initial network json to http://192.168.198.111:8181/restconf/data
##    The json is Topology_Init.json under POC_ECOC_2025_DEMO folder 
# Step4: delete the networkslice_data.db in osm code which is pythonProject2.py
