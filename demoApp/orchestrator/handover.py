import time
import requests
import uuid
from ui.models import HandoverEvent, HandoverState

def trigger_handover(mac, old_gw, new_gw):
    print(f"\n🔀 Handover required for {mac}: {old_gw} → {new_gw}\n")

    # Remove from every gateway's whitelist
    gateways = ["gw-A", "gw-B", "gw-C"]   # adjust to your config
    for gw in gateways:
        post_inbox_command(gw, f"WL_DEL {mac}")

    time.sleep(0.2)

    # Add to new gateway
    post_inbox_command(new_gw, f"WL_ADD {mac}")

    # Disconnect from old gateway
    post_inbox_command(old_gw, f"DC {mac}")

    # Update state
    HandoverState.objects.update_or_create(mac=mac, defaults={"current_gateway": new_gw})

    # Log event
    HandoverEvent.objects.create(mac=mac, from_gw=old_gw, to_gw=new_gw)

    print(f"✅ Handover complete {mac}: {old_gw} → {new_gw}")

def post_inbox_command(gateway, command):
    try:
        url = f"http://127.0.0.1:8080/cse-in/{gateway}/inbox"
        headers = {
            "X-M2M-Origin": "CAdmin",
            "X-M2M-RI": f"req-{uuid.uuid4()}",
            "X-M2M-RVI": "3",
            "Content-Type": "application/json;ty=4",
        }
        payload = {
            "m2m:cin": {
                "con": command
            }
        }

        r = requests.post(url, headers=headers, json=payload)
        if r.status_code in (200, 201):
            print(f"📤 Sent command to {gateway}: {command}")
        else:
            print(f"⚠ Inbox command failed: {r.status_code} {r.text}")

    except Exception as e:
        print(f"[ERROR] post_inbox_command: {e}")


def update_current_gateway(mac, gateway):
    """
    Stores which gateway the device is CURRENTLY attached to.
    """
    print(f"🔗 Device {mac} → connected to {gateway}")

    # TODO: requires creating HandoverState model
    # HandoverState.objects.update_or_create(
    #     mac=mac,
    #     defaults={"current_gateway": gateway}
    # )