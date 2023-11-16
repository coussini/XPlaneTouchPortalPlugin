import TouchPortalAPI as TP

TPClient = TP.client()

def StateUpdates():
    while running:
        try:
            statesData = json.loads(http.request("GET", f"http://{YTMD_server}:9863/query", headers={"Authorization": f"bearer {LoginPass}"}).data.decode("utf-8"))
            currentPlaylist = json.loads(http.request("GET", f"http://{YTMD_server}:9863/query/playlist", headers={"Authorization": f"bearer {LoginPass}"}).data.decode("utf-8"))['list']
            queryQueue = json.loads(http.request("GET", f"http://{YTMD_server}:9863/query/queue", headers={"Authorization": f"bearer {LoginPass}"}).data.decode("utf-8"))
            Lyricsdata = json.loads(http.request("GET", f"http://{YTMD_server}:9863/query/lyrics", headers={"Authorization": f"bearer {LoginPass}"}).data.decode("utf-8"))
            isYTMDRunning = True
            if connectionStatus != isYTMDRunning:
                print("Connected to YTMD")
                connectionStatus = isYTMDRunning
        except Exception as e:
            if "refused" in str(e).split():
                isYTMDRunning = False
            else:
                isYTMDRunning = False
            if connectionStatus != isYTMDRunning:
                print("YTMD Server shutdown")
                connectionStatus = isYTMDRunning
            TPClient.settingUpdate("Status", "YTMD is Not open")
        if isYTMDRunning:
            TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.YTMD.States.TrackCurrentLyrics", Lyricsdata["data"])
            def traitement1():
            	pass 
            def traitement2():
            	traitement1()
            	pass 
        sleep(0.23)


@TPClient.on(TYPES.onConnect)
def onConnect(data):
    print(data)
    running = True

    host = xxx
    port = 33333

    
    
    YTMD_server = data['settings'][0]['IPv4 address']
    LoginPass = data['settings'][1]['Passcode']

    lyricsRange = data['settings'][2]['Lyrics Range']
    lyricsRange = lyricsRange.split(",")
        #print(lyricsRange)
    print(list(range(int(lyricsRange[0]), int(lyricsRange[1]))))
    for x in range(int(lyricsRange[0]), int(lyricsRange[1])):
        TPClient.createState("KillerBOSS.TP.Plugin.YTMD.States.ScrollLyrics.Line"+str(x), "Scrolling Lyrics Show line "+str(x), "", "Lyrics line")
        lyricsStatesList.append("KillerBOSS.TP.Plugin.YTMD.States.ScrollLyrics.Line"+str(x))
    print("Trying to Connect to", YTMD_server+":9863/query", "With passcode:", LoginPass)
    threading.Thread(target=stateUpdate).start()

@TPClient.on(TYPES.onAction)
def Actions(data):
    if isYTMDRunning:
        ActionData = json.loads(http.request("GET", f"http://{YTMD_server}:9863/query", headers={'Authorization': f'bearer {LoginPass}'}).data.decode('utf-8'))
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.Play/Pause":
            PauseStates = ActionData['player']['isPaused']
            if data['data'][0]['value'] == "Play":
                if PauseStates:
                    YTMD_Actions("track-play")
            elif data['data'][0]['value'] == "Pause":
                if PauseStates == False:
                    YTMD_Actions("track-pause")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.Next/Previous":
            if data['data'][0]['value'] == "Next":
                YTMD_Actions("track-next")
            elif data['data'][0]['value'] == "Previous":
                YTMD_Actions("track-previous")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.Like/Dislike":
            if data['data'][0]['value'] == "Like":
                YTMD_Actions("track-thumbs-up")
            elif data['data'][0]['value'] == "Dislike":
                YTMD_Actions("track-thumbs-down")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.VUp/VDown":
            if data['data'][0]['value'] == "Up":
                YTMD_Actions("player-volume-up")
            elif data['data'][0]['value'] == "Down":
                YTMD_Actions("player-volume-down")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.forward/rewind":
            if data['data'][0]['value'] == "Forward":
                YTMD_Actions("player-forward")
            elif data['data'][0]['value'] == "Rewind":
                YTMD_Actions("player-rewind")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.RepeatPic":
            repeatState = ActionData['player']['repeatType']
            if data['data'][0]['value'] == "ONE":
                if repeatState != "ONE":
                    if repeatState == "ALL":
                        YTMD_Actions("player-repeat", value="ONE")
                    elif repeatState == "NONE":
                        for x in range(2):
                            YTMD_Actions("player-repeat", value="ONE")
            elif data['data'][0]['value'] == "All":
                if repeatState != "ALL":
                    if repeatState == "ONE":
                        for x in range(2):
                            YTMD_Actions("player-repeat", value="ALL")
                    elif repeatState == "NONE":
                        YTMD_Actions("player-repeat", value="ALL")
            elif data['data'][0]['value'] == "OFF":
                if repeatState != "NONE":
                    if repeatState == "ONE":
                        YTMD_Actions("player-repeat", value="NONE")
                    elif repeatState == "ALL":
                        for x in range(2):
                            YTMD_Actions("player-repeat", value="NONE")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.mute/unmute":
            global globalVol
            if data['data'][0]['value'] == "Mute":
                globalVol = ActionData['player']['volumePercent']
                YTMD_Actions("player-set-volume", value=0)
            elif data['data'][0]['value'] == "Unmute":
                YTMD_Actions("player-set-volume", value=globalVol)
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.AddToPlaylist":
            YTMD_Actions("player-add-playlist", value=str(json.loads(http.request("GET", f"http://{YTMD_server}:9863/query/playlist", headers={"Authorization": f"bearer {LoginPass}"}).data.decode("utf-8"))['list'].index(data['data'][0]['value'])))
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.SetSeekBar":
            YTMD_Actions("player-set-seekbar", value=data['data'][0]['value'])
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.SetVolume":
            YTMD_Actions("player-set-volume", value=data['data'][0]['value'])
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.PlayTrackNumber":
            YTMD_Actions("player-set-queue", value=data['data'][0]['value'])
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.AddToLibrary":
            YTMD_Actions("player-add-library")
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.Shuffle":
            YTMD_Actions("player-shuffle")    

        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.StartPlaylist":
            YTMD_Actions("start-playlist", data['data'][0]['value'])
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.PlayURL":
            YTMD_Actions("play-url", data['data'][0]['value'])
        if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.YTMD.Action.SkipAd":
            YTMD_Actions("skip-ad")

@TPClient.on(TYPES.onShutdown)
def Disconnect(data): 
    global running
    running = False
    try:
        TPClient.disconnect()
    except (ConnectionResetError,AttributeError):
        pass
    print("Shutting Down")
    exit(0)


TPClient.connect()