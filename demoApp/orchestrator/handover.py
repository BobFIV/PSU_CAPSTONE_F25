import time
import requests
import uuid
import json
from ui.models import HandoverEvent, HandoverState

def trigger_handover(mac, old_gw, new_gw, old_rssi, new_rssi):
    print(f"\n🔀 Handover required for {mac}: {old_gw} → {new_gw}\n")

    # Remove from all gateways
    gateways = ["gw-A", "gw-B"]
    for gw in gateways:
        post_inbox_command(gw, {"cmd": "WL_DEL", "mac": mac})

    time.sleep(0.2)

    # Add to the new gateway
    post_inbox_command(new_gw, {"cmd": "WL_ADD", "mac": mac})

    # Disconnect from the old gateway
    post_inbox_command(old_gw, {"cmd": "DC", "mac": mac})

    # Update state
    HandoverState.objects.update_or_create(
        mac=mac,
        defaults={"current_gateway": new_gw}
    )

    # Save handover event
    HandoverEvent.objects.create(
        mac=mac,
        from_gateway=old_gw,
        to_gateway=new_gw,
        old_rssi=old_rssi,
        new_rssi=new_rssi,
    )

    print(f"✅ Handover logged for {mac}: {old_gw} → {new_gw} (RSSI {old_rssi} → {new_rssi})")

    
    

def post_inbox_command(gateway, payload):
    url = f"http://127.0.0.1:8080/cse-in/{gateway}/inbox"

    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": f"req-{uuid.uuid4()}",
        "X-M2M-RVI": "3",
        "Content-Type": "application/json;ty=4",
    }

    r = requests.post(
        url,
        headers=headers,
        json={"m2m:cin": {"con": json.dumps(payload)}}
    )

    if r.status_code in (200, 201):
        print(f"📤 Sent command to {gateway}: {payload}")
    else:
        print(f"⚠ Inbox command failed {r.status_code}: {r.text}")



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