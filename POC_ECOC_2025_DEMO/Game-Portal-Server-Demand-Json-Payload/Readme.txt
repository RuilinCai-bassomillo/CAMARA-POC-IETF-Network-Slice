Steps of calling the API when user click the play button:
1. call Edgecloud by using payloadOfPostAppsInCamaraEdgeCloud.json
2. After recieve the response of responseOfPostAppsInCamaraEdgeCloud.json
   , use the appId which you get to generate the payloadOfInstantiateAppsInCamaraEdgecloud.json to call instantiate App in edgeCloud.
3. Call QoD by using payloadOfPostQoD.json
4. Call insightService by using payloadOfPostApplicationProfile.json
5. After recieve the profileId from the ResponseOfPostApplicationProfile.json, 
    use the profile id to generate the ConnectivitySubscription.json to subscribe the connectivity insight.
6. Wait to recieve the notification from Camara, the payload is GetConnectivityInsightNotificationFromCamara.json