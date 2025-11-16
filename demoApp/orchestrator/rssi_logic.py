from orchestrator.handover import trigger_handover
from ui.models import HandoverState, RSSIReading

RSSI_BAD_THRESHOLD = -65
RSSI_HANDOVER_MARGIN = 6

def latest_rssi(mac, gateway):
    last = RSSIReading.objects.filter(mac=mac, gateway=gateway).order_by('-timestamp').first()
    return last.rssi if last else -200

def evaluate_handover(mac):
    try:
        state = HandoverState.objects.get(mac=mac)
    except HandoverState.DoesNotExist:
        print(f"⚠ No handover state for {mac}")
        return

    current_gw = state.current_gateway

    # Get the latest scan reports
    scans = RSSIReading.objects.filter(mac=mac).order_by('-timestamp')[:4]
    if not scans:
        return
    
    # Determine the best gateway based on highest RSSI
    best_gateway = None
    best_rssi = -200

    for s in scans:
        if s.rssi > best_rssi:
            best_rssi = s.rssi
            best_gateway = s.gateway

    if best_gateway is None:
        return

    current_rssi = latest_rssi(mac, current_gw)

    # 1. If the current gateway is still dominant → do nothing
    if current_rssi > best_rssi - RSSI_HANDOVER_MARGIN:
        return

    # 2. Only switch when current gateway is truly bad
    if current_rssi > RSSI_BAD_THRESHOLD:
        return
    
    if best_gateway == current_gw:
        return

    trigger_handover(
        mac,
        current_gw,
        best_gateway,
        current_rssi,   # ← old RSSI
        best_rssi       # ← new RSSI
    )
