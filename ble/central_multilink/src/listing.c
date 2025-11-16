#include "main.h"

sys_slist_t whitelist;
sys_slist_t blacklist;
device_entry_t device_entries[MAX_DEVICE_LIST];
uint8_t device_entry_count;

struct bt_conn *conn_connecting;
uint8_t conn_count_max;
uint8_t volatile conn_count;
bool volatile is_disconnecting;

/* Dynamic manual whitelist */
manual_whitelist_entry_t manual_whitelist[MAX_MANUAL_WHITELIST];
uint8_t manual_whitelist_count = 0;

/* Initialize manual whitelist with default MACs */
void init_manual_whitelist(void)
{
    /* Initialize all entries as inactive */
    for (int i = 0; i < MAX_MANUAL_WHITELIST; i++) {
        manual_whitelist[i].active = false;
        memset(manual_whitelist[i].mac, 0, 18);
    }
    
    /* OPTIONAL: Add default MACs here */
    const char* default_macs[] = {
        "D2:29:B2:D0:66:FC",
        "7C:DF:A1:FB:72:7D"
    };
    
    int default_count = sizeof(default_macs) / sizeof(default_macs[0]);
    for (int i = 0; i < default_count && i < MAX_MANUAL_WHITELIST; i++) {
        strncpy(manual_whitelist[i].mac, default_macs[i], 17);
        manual_whitelist[i].mac[17] = '\0';
        manual_whitelist[i].active = true;
        manual_whitelist_count++;
    }
    
    printk("Manual whitelist initialized with %d devices\n", manual_whitelist_count);
}

/* Add MAC to manual whitelist */
bool add_mac_to_manual_whitelist(const char *mac_str)
{
    if (mac_str == NULL) {
        printk("Cannot add NULL MAC to whitelist\n");
        return false;
    }
    
    /* Check if already exists */
    for (int i = 0; i < MAX_MANUAL_WHITELIST; i++) {
        if (manual_whitelist[i].active && 
            strncmp(manual_whitelist[i].mac, mac_str, 17) == 0) {
            printk("MAC %s already in manual whitelist\n", mac_str);
            return true;
        }
    }
    
    /* Find empty slot */
    for (int i = 0; i < MAX_MANUAL_WHITELIST; i++) {
        if (!manual_whitelist[i].active) {
            strncpy(manual_whitelist[i].mac, mac_str, 17);
            manual_whitelist[i].mac[17] = '\0';
            manual_whitelist[i].active = true;
            manual_whitelist_count++;
            printk("Added %s to manual whitelist (count: %d)\n", 
                   mac_str, manual_whitelist_count);
            return true;
        }
    }
    
    printk("Manual whitelist full! Cannot add %s\n", mac_str);
    return false;
}

/* Remove MAC from manual whitelist */
bool remove_mac_from_manual_whitelist(const char *mac_str)
{
    if (mac_str == NULL) {
        printk("Cannot remove NULL MAC from whitelist\n");
        return false;
    }
    
    for (int i = 0; i < MAX_MANUAL_WHITELIST; i++) {
        if (manual_whitelist[i].active && 
            strncmp(manual_whitelist[i].mac, mac_str, 17) == 0) {
            manual_whitelist[i].active = false;
            memset(manual_whitelist[i].mac, 0, 18);
            manual_whitelist_count--;
            printk("Removed %s from manual whitelist (count: %d)\n", 
                   mac_str, manual_whitelist_count);
            return true;
        }
    }
    
    printk("MAC %s not found in manual whitelist\n", mac_str);
    return false;
}

/* Check if device is in manual whitelist */
bool is_device_manually_whitelisted(const bt_addr_le_t *addr)
{
    char addr_str[BT_ADDR_LE_STR_LEN];
    bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));
    
    /* Extract just the MAC address part (first 17 chars) */
    char mac_only[18];
    strncpy(mac_only, addr_str, 17);
    mac_only[17] = '\0';
    
    /* Check against manual whitelist */
    for (int i = 0; i < MAX_MANUAL_WHITELIST; i++) {
        if (manual_whitelist[i].active && 
            strncmp(manual_whitelist[i].mac, mac_only, 17) == 0) {
            return true;
        }
    }
    
    return false;
}

/* Whitelist/Blacklist management functions */
device_status_t get_device_status(const bt_addr_le_t *addr)
{
	sys_snode_t *node;
	device_entry_t *entry;

	/* Check whitelist first */
	SYS_SLIST_FOR_EACH_NODE(&whitelist, node) {
		entry = CONTAINER_OF(node, device_entry_t, node);
		if (bt_addr_le_cmp(&entry->addr, addr) == 0) {
			return DEVICE_STATUS_WHITELISTED;
		}
	}

	/* Check blacklist */
	SYS_SLIST_FOR_EACH_NODE(&blacklist, node) {
		entry = CONTAINER_OF(node, device_entry_t, node);
		if (bt_addr_le_cmp(&entry->addr, addr) == 0) {
			return DEVICE_STATUS_BLACKLISTED;
		}
	}

	return DEVICE_STATUS_UNKNOWN;
}

device_entry_t *find_or_create_device_entry(const bt_addr_le_t *addr)
{
	sys_snode_t *node;
	device_entry_t *entry;

	/* First, check if device already exists in either list */
	SYS_SLIST_FOR_EACH_NODE(&whitelist, node) {
		entry = CONTAINER_OF(node, device_entry_t, node);
		if (bt_addr_le_cmp(&entry->addr, addr) == 0) {
			return entry;
		}
	}

	SYS_SLIST_FOR_EACH_NODE(&blacklist, node) {
		entry = CONTAINER_OF(node, device_entry_t, node);
		if (bt_addr_le_cmp(&entry->addr, addr) == 0) {
			return entry;
		}
	}

	/* Create new entry if we have space */
	if (device_entry_count < MAX_DEVICE_LIST) {
		entry = &device_entries[device_entry_count++];
		bt_addr_le_copy(&entry->addr, addr);
		entry->status = DEVICE_STATUS_UNKNOWN;
		entry->disconnect_count = 0;
		entry->connect_count = 0;
		entry->scan_found_count = 0;
		entry->has_made_param_request = false;
		return entry;
	}

	return NULL;
}

void add_device_to_whitelist(const bt_addr_le_t *addr)
{
	device_entry_t *entry = find_or_create_device_entry(addr);
	if (!entry) {
		printk("Warning: Cannot add device to whitelist - list full\n");
		return;
	}

	/* Remove from blacklist if it exists there */
	sys_slist_find_and_remove(&blacklist, &entry->node);

	/* Add to whitelist if not already there */
	if (!sys_slist_find(&whitelist, &entry->node, NULL)) {
		sys_slist_append(&whitelist, &entry->node);
		entry->status = DEVICE_STATUS_WHITELISTED;
	}
}

void remove_device_from_whitelist(const bt_addr_le_t *addr)
{
	device_entry_t *entry = find_or_create_device_entry(addr);
	if (!entry) {
		printk("Warning: Cannot remove device from whitelist - Not in Whitelist\n");
		return;
	}

	/* Remove from whitelist if it exists there */
	sys_slist_find_and_remove(&whitelist, &entry->node);

	entry->status = DEVICE_STATUS_UNKNOWN;
}

void add_device_to_blacklist(const bt_addr_le_t *addr)
{
	device_entry_t *entry = find_or_create_device_entry(addr);
	if (!entry) {
		printk("Warning: Cannot add device to blacklist - list full\n");
		return;
	}

	/* Remove from whitelist if it exists there */
	sys_slist_find_and_remove(&whitelist, &entry->node);

	/* Add to blacklist if not already there */
	if (!sys_slist_find(&blacklist, &entry->node, NULL)) {
		sys_slist_append(&blacklist, &entry->node);
		entry->status = DEVICE_STATUS_BLACKLISTED;
	}
}

bool is_device_whitelisted(const bt_addr_le_t *addr)
{
	return get_device_status(addr) == DEVICE_STATUS_WHITELISTED;
}

bool is_device_blacklisted(const bt_addr_le_t *addr)
{
	return get_device_status(addr) == DEVICE_STATUS_BLACKLISTED;
}

device_entry_t *get_or_create_device_entry(const bt_addr_le_t *addr)
{
	return find_or_create_device_entry(addr);
}

void track_device_connect(const bt_addr_le_t *addr)
{
	device_entry_t *entry = get_or_create_device_entry(addr);
	if (entry) {
		entry->connect_count++;
		char addr_str[BT_ADDR_LE_STR_LEN];
		bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));
		printk("Track connect: %s (conn_count=%d, disconnect_count=%d, has_param_req=%d)\n",
		       addr_str, entry->connect_count, entry->disconnect_count, entry->has_made_param_request);
	}
}

void track_device_disconnect(const bt_addr_le_t *addr, uint8_t reason)
{
	device_entry_t *entry = get_or_create_device_entry(addr);
	if (entry) {
		entry->disconnect_count++;
		char addr_str[BT_ADDR_LE_STR_LEN];
		bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));
		printk("Track disconnect: %s (conn_count=%d, disconnect_count=%d, has_param_req=%d)\n",
		       addr_str, entry->connect_count, entry->disconnect_count, entry->has_made_param_request);
		
		/* Manual whitelist mode - no automatic blacklisting */
		printk("Device %s disconnected (manual whitelist mode - no auto blacklisting)\n", addr_str);
	}
}

// -----------------------------------------------------------------------------
// UNIFIED SCAN CALLBACK - Handles both connectable and non-connectable advertisements
// -----------------------------------------------------------------------------
static void unified_scan_callback(const bt_addr_le_t *addr, int8_t rssi,
                                  uint8_t type, struct net_buf_simple *ad)
{
	char addr_str[BT_ADDR_LE_STR_LEN];
	bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));
	
	/* Extract MAC-only part (first 17 chars) */
	char mac_only[18];
	strncpy(mac_only, addr_str, 17);
	mac_only[17] = '\0';

	/* ===== HANDLE NON-CONNECTABLE BEACONS (RSSI Monitoring) ===== */
	/* Process beacons FIRST and independently of connection state */
	if (type == BT_GAP_ADV_TYPE_ADV_NONCONN_IND) {
		/* Parse advertisement data to find "SEEED_TEST" name */
		bool is_seeed_test = false;
		struct net_buf_simple temp_buf = *ad;

		while (temp_buf.len > 1) {
			uint8_t len = net_buf_simple_pull_u8(&temp_buf);
			if (len == 0 || len > temp_buf.len)
				break;
			uint8_t type_field = net_buf_simple_pull_u8(&temp_buf);

			if (type_field == BT_DATA_NAME_COMPLETE) {
				char name[32];
				size_t nc = MIN((size_t)(len - 1), sizeof(name) - 1);
				memcpy(name, temp_buf.data, nc);
				name[nc] = '\0';
				if (strcmp(name, "SEEED_TEST") == 0) {
					is_seeed_test = true;
					break;
				}
			}
			net_buf_simple_pull(&temp_buf, len - 1);
		}

		/* Only process if it's a SEEED_TEST beacon */
		if (is_seeed_test) {
			/* Check if this MAC corresponds to a connected node */
			seeed_conn_t *node = find_node_by_mac_addr(mac_only);
			uint8_t connected_flag = (node != NULL) ? 1 : 0;

			/* Send RSSI report for all SEEED_TEST beacons, regardless of whitelist */
			send_rssi_report(mac_only, (int8_t)rssi, connected_flag);

			/* Optional: Only log whitelisted devices to reduce console spam */
			if (is_device_manually_whitelisted(addr)) {
				printk("[BEACON] %s RSSI: %d dBm (connected=%d)\n", 
				       mac_only, rssi, connected_flag);
			}
		}
		
		/* Always return after processing beacons - don't try to connect to them */
		return;
	}

	/* ===== HANDLE CONNECTABLE ADVERTISEMENTS (Device Connection) ===== */
	/* Only process connectable advertisements if not currently connecting */
	if (conn_connecting) {
		return;
	}

	/* We're only interested in connectable events */
	if (type != BT_GAP_ADV_TYPE_ADV_IND &&
	    type != BT_GAP_ADV_TYPE_ADV_DIRECT_IND &&
	    type != BT_GAP_ADV_TYPE_EXT_ADV) {
		return;
	}

	/* Connect only to devices in close proximity */
	if (rssi < -100) {
		return;
	}

	/* Only connect to manually whitelisted devices */
	if (!is_device_manually_whitelisted(addr)) {
		return;
	}

	printk("Device found (manually whitelisted): %s (RSSI %d) - attempting connection\n", 
	       addr_str, rssi);

	/* Attempt connection */
	struct bt_conn_le_create_param create_param = {
		.options = BT_CONN_LE_OPT_NONE,
		.interval = INIT_INTERVAL,
		.window = INIT_WINDOW,
		.interval_coded = 0,
		.window_coded = 0,
		.timeout = 0,
	};
	struct bt_le_conn_param conn_param = {
		.interval_min = CONN_INTERVAL,
		.interval_max = CONN_INTERVAL,
		.latency = CONN_LATENCY,
		.timeout = CONN_TIMEOUT,
	};

	printk("Stopping scan to attempt connection to %s\n", addr_str);
	int err = bt_le_scan_stop();
	if (err != 0) {
		printk("Failed to stop scanning (err %d)\n", err);
		return;
	}

	err = bt_conn_le_create(addr, &create_param, &conn_param, &conn_connecting);
	if (err) {
		printk("Create conn to %s failed (%d)\n", addr_str, err);
		start_scan();
	}
}

void start_scan(void)
{
	struct bt_le_scan_param scan_param = {
		.type       = BT_LE_SCAN_TYPE_PASSIVE,
		.options    = BT_LE_SCAN_OPT_NONE,  /* REMOVED duplicate filtering for RSSI tracking */
		.interval   = SCAN_INTERVAL,
		.window     = SCAN_WINDOW,
	};
	int err;

	err = bt_le_scan_start(&scan_param, unified_scan_callback);
	if (err && err != -EALREADY) {
		printk("Scanning failed to start (err %d)\n", err);
		return;
	}

	printk("Unified scanning started (handles both connection and RSSI monitoring)\n");
}