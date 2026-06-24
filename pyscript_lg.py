import aiowebostv
import pyscript

CLOSE_TOAST = "system.notifications/closeToast"
CREATE_ALERT = "system.notifications/createAlert"
CLOSE_ALERT = "system.notifications/closeAlert"

STATIC_PROJECTOR_IP = "192.168.20.117"

def setup_connection():
    if len(input_text.projector_secret_helper) > 10:
        APP_KEY = input_text.projector_secret_helper
    else: 
        APP_KEY = None
    try:
        # Fetch the IP dynamically from the Unifi device tracker
        # In pyscript, you can usually use state.getattr or standard dot notation
        projector_ip = state.getattr("device_tracker.lgwebostv_2").get("ip")
        
        if not projector_ip:
            log.warning("IP address missing from device_tracker.lgwebostv_2, falling back to static IP.")
            projector_ip = STATIC_PROJECTOR_IP
    except Exception as e:
        log.error(f"Error fetching dynamic IP: {e}. Falling back to static IP.")
        projector_ip = STATIC_PROJECTOR_IP

    web_os_client = aiowebostv.WebOsClient(projector_ip, APP_KEY)
    web_os_client.connect()
    input_text.projector_secret_helper = web_os_client.client_key

    return web_os_client

@service
def change_picture_mode(picture_mode):
    web_os_client = setup_connection()

    uri = "com.webos.settingsservice/setSystemSettings"
    params = {"category": "picture", "settings": {"pictureMode": picture_mode}}
    log.info("Changing WebOS picture mode to {}".format(picture_mode))
    luna_request(web_os_client, uri, params)

    web_os_client.disconnect()

@service
def change_picture_backlight(backlight):
    web_os_client = setup_connection()
    # if backlight < 1 or backlight > 100:
    #     raise PyLGTVCmdException("Invalid backlight value {}".format(backlight))
    
    uri = "com.webos.settingsservice/setSystemSettings"
    settings = {"backlight": backlight}
    params = {"category": "picture", "settings": settings}
    log.info("Changing WebOS backlight to {}".format(backlight))
    luna_request(web_os_client, uri, params)

    log.info(get_picture_settings(web_os_client))

    web_os_client.disconnect()

def luna_request(client, uri, params):
    lunauri = f"luna://{uri}"
    buttons = [{"label": "", "onClick": lunauri, "params": params}]
    payload = {
        "message": " ",
        "buttons": buttons,
        "onclose": {"uri": lunauri, "params": params},
        "onfail": {"uri": lunauri, "params": params},
    }
    ret = client.request(CREATE_ALERT, payload)
    alertId = ret.get("alertId")
    if alertId is None:
        raise PyLGTVCmdException("Invalid alertId")
    return client.request(CLOSE_ALERT, payload={"alertId": alertId})

def get_picture_settings(client, keys=["contrast", "backlight", "brightness", "color"]):
    payload = {"category": "picture", "keys": keys}
    ret = client.request("settings/getSystemSettings", payload=payload)
    return ret["settings"]