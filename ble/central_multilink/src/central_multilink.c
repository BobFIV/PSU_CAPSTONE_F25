/* main.c - Application main entry point */

/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 * Copyright (c) 2015-2016 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "main.h"

struct gatt_ess_data ess_data[CONFIG_BT_MAX_CONN];

#if defined(CONFIG_BT_GATT_CLIENT)
void mtu_exchange_cb(struct bt_conn *conn, uint8_t err,
			    struct bt_gatt_exchange_params *params)
{
	printk("MTU exchange %u %s (%u)\n", bt_conn_index(conn),
	       err == 0U ? "successful" : "failed", bt_gatt_get_mtu(conn));
}

struct bt_gatt_exchange_params mtu_exchange_params[CONFIG_BT_MAX_CONN];

/* GATT Client discovery and notification structures */
struct bt_gatt_discover_params discover_params[CONFIG_BT_MAX_CONN];
struct bt_gatt_subscribe_params subscribe_params[CONFIG_BT_MAX_CONN * 3]; /* 3 characteristics per connection */

int mtu_exchange(struct bt_conn *conn)
{
	uint8_t conn_index;
	int err;

	conn_index = bt_conn_index(conn);

	printk("MTU (%u): %u\n", conn_index, bt_gatt_get_mtu(conn));

	mtu_exchange_params[conn_index].func = mtu_exchange_cb;

	err = bt_gatt_exchange_mtu(conn, &mtu_exchange_params[conn_index]);
	if (err) {
		printk("MTU exchange failed (err %d)", err);
	} else {
		printk("Exchange pending...");
	}

	return err;
}

/* GATT Client implementation for Environmental Sensing Service */
uint8_t ess_notify_cb(struct bt_conn *conn, struct bt_gatt_subscribe_params *params, const void *data, uint16_t length)
{
	uint8_t conn_index = bt_conn_index(conn);
	char addr[BT_ADDR_LE_STR_LEN];
	
	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	if (!data || length == 0) {
		printk("ESS notification from %s: subscription ended\n", addr);
		return BT_GATT_ITER_STOP;
	}
	
	/* Determine which characteristic this notification is for */
	if (params->value_handle == ess_data[conn_index].temp_handle) {
		int16_t temp_val = sys_get_le32(data);
		uint32_t temp_celsius_int = (temp_val * 100) / 10000;  /* Convert to integer with 2 decimal places */
		uint32_t temp_celsius_frac = ((temp_val * 100) % 10000) / 100;
		printk("ESS [%s] Temperature: %d.%02d°C (raw: %d)\n", addr, temp_celsius_int, temp_celsius_frac, temp_val);
		ble_value_a_received(conn, temp_val);
		flash_data_led();  /* Flash LED2 to indicate data reception */
	} else if (params->value_handle == ess_data[conn_index].pressure_handle) {
		uint32_t press_val = sys_get_le32(data);
		uint32_t press_pa_int = press_val / 100;
		uint32_t press_pa_frac = (press_val % 100);
		printk("ESS [%s] Pressure: %u.%02u Pa (raw: %u)\n", addr, press_pa_int, press_pa_frac, press_val);
		ble_value_b_received(conn, press_val);
		flash_data_led();  /* Flash LED2 to indicate data reception */
	} else if (params->value_handle == ess_data[conn_index].humidity_handle) {
		uint16_t humid_val = sys_get_le32(data);
		uint32_t humid_percent_int = humid_val / 100;
		uint32_t humid_percent_frac = humid_val % 100;
		printk("ESS [%s] Humidity: %u.%02u%% (raw: %u)\n", addr, humid_percent_int, humid_percent_frac, humid_val);
		ble_value_c_received(conn, humid_val);
		flash_data_led();  /* Flash LED2 to indicate data reception */
	} else {
		printk("ESS [%s] Unknown notification: handle=0x%04x, len=%u\n", 
		       addr, params->value_handle, length);
	}
	
	return BT_GATT_ITER_CONTINUE;
}

uint8_t ess_discover_func(struct bt_conn *conn, const struct bt_gatt_attr *attr, struct bt_gatt_discover_params *params)
{
	uint8_t conn_index = bt_conn_index(conn);
	char addr[BT_ADDR_LE_STR_LEN];
	
	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	if (!attr) {
		printk("ESS discovery complete for %s\n", addr);
		ess_discover_complete(conn, 0);
		return BT_GATT_ITER_STOP;
	}
	
	if (params->type == BT_GATT_DISCOVER_PRIMARY) {
		const struct bt_gatt_service_val *gatt_service = (const struct bt_gatt_service_val *)attr->user_data;
		
		if (gatt_service->uuid->type == BT_UUID_TYPE_16) {
			uint16_t uuid16 = BT_UUID_16(gatt_service->uuid)->val;
			printk("ESS [%s] Found service: 0x%04x, handle range: 0x%04x-0x%04x\n", 
			       addr, uuid16, attr->handle, gatt_service->end_handle);
			
			if (uuid16 == BT_UUID_ESS_VAL) {
				printk("ESS [%s] Found Environmental Sensing Service! Starting characteristic discovery...\n", addr);
				
				/* Found ESS service, now discover characteristics */
				discover_params[conn_index].type = BT_GATT_DISCOVER_CHARACTERISTIC;
				discover_params[conn_index].uuid = NULL;
				discover_params[conn_index].start_handle = attr->handle;
				discover_params[conn_index].end_handle = gatt_service->end_handle;
				discover_params[conn_index].func = ess_discover_func;
				
				int err = bt_gatt_discover(conn, &discover_params[conn_index]);
				if (err) {
					printk("ESS [%s] Characteristic discovery failed: %d\n", addr, err);
					ess_discover_complete(conn, err);
					return BT_GATT_ITER_STOP;
				}
				return BT_GATT_ITER_STOP;
			}
		}
	} else if (params->type == BT_GATT_DISCOVER_CHARACTERISTIC) {
		struct bt_gatt_chrc *chrc = (struct bt_gatt_chrc *)attr->user_data;
		
		if (chrc->uuid->type == BT_UUID_TYPE_16) {
			uint16_t uuid16 = BT_UUID_16(chrc->uuid)->val;
			printk("ESS [%s] Found characteristic: 0x%04x, handle=0x%04x, properties=0x%02x\n", 
			       addr, uuid16, chrc->value_handle, chrc->properties);
			
			if (uuid16 == BT_UUID_TEMP_CHAR_VAL) {
				ess_data[conn_index].temp_handle = chrc->value_handle;
				printk("ESS [%s] Found Temperature characteristic: handle=0x%04x\n", 
				       addr, chrc->value_handle);
			} else if (uuid16 == BT_UUID_PRESSURE_CHAR_VAL) {
				ess_data[conn_index].pressure_handle = chrc->value_handle;
				printk("ESS [%s] Found Pressure characteristic: handle=0x%04x\n", 
				       addr, chrc->value_handle);
			} else if (uuid16 == BT_UUID_HUMIDITY_CHAR_VAL) {
				ess_data[conn_index].humidity_handle = chrc->value_handle;
				printk("ESS [%s] Found Humidity characteristic: handle=0x%04x\n", 
				       addr, chrc->value_handle);
			}
		}
	} else if (params->type == BT_GATT_DISCOVER_DESCRIPTOR) {
		if (attr->uuid->type == BT_UUID_TYPE_16 && 
		    BT_UUID_16(attr->uuid)->val == BT_UUID_GATT_CCC_VAL) {
			
			printk("ESS [%s] Found CCC descriptor: handle=0x%04x\n", addr, attr->handle);
			
			/* Determine which CCC this is based on the handle */
			if (attr->handle == ess_data[conn_index].temp_handle + 1) {
				ess_data[conn_index].temp_ccc_handle = attr->handle;
				printk("ESS [%s] Found Temperature CCC: handle=0x%04x\n", addr, attr->handle);
			} else if (attr->handle == ess_data[conn_index].pressure_handle + 1) {
				ess_data[conn_index].pressure_ccc_handle = attr->handle;
				printk("ESS [%s] Found Pressure CCC: handle=0x%04x\n", addr, attr->handle);
			} else if (attr->handle == ess_data[conn_index].humidity_handle + 1) {
				ess_data[conn_index].humidity_ccc_handle = attr->handle;
				printk("ESS [%s] Found Humidity CCC: handle=0x%04x\n", addr, attr->handle);
			}
		}
	}
	
	return BT_GATT_ITER_CONTINUE;
}

void ess_discover_complete(struct bt_conn *conn, int err)
{
	char addr[BT_ADDR_LE_STR_LEN];
	
	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	if (err) {
		printk("ESS discovery failed for %s: %d\n", addr, err);
		return;
	}
	
	printk("ESS discovery completed for %s\n", addr);
	
	/* Subscribe to notifications */
	ess_subscribe_notifications(conn);
}

int ess_discover_services(struct bt_conn *conn)
{
	uint8_t conn_index = bt_conn_index(conn);
	char addr[BT_ADDR_LE_STR_LEN];
	int err;
	
	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	/* Initialize ESS data for this connection */
	ess_data[conn_index].conn = conn;
	ess_data[conn_index].temp_handle = 0;
	ess_data[conn_index].pressure_handle = 0;
	ess_data[conn_index].humidity_handle = 0;
	ess_data[conn_index].temp_ccc_handle = 0;
	ess_data[conn_index].pressure_ccc_handle = 0;
	ess_data[conn_index].humidity_ccc_handle = 0;
	ess_data[conn_index].temp_notify_enabled = false;
	ess_data[conn_index].pressure_notify_enabled = false;
	ess_data[conn_index].humidity_notify_enabled = false;
	
	/* Start with discovering all primary services to see what's available */
	discover_params[conn_index].type = BT_GATT_DISCOVER_PRIMARY;
	discover_params[conn_index].uuid = NULL;  /* Discover all services */
	discover_params[conn_index].start_handle = 0x0001;
	discover_params[conn_index].end_handle = 0xffff;
	discover_params[conn_index].func = ess_discover_func;
	
	printk("Starting service discovery for %s\n", addr);
	
	err = bt_gatt_discover(conn, &discover_params[conn_index]);
	if (err) {
		printk("Service discovery start failed for %s: %d\n", addr, err);
		return err;
	}
	
	return 0;
}

int ess_subscribe_notifications(struct bt_conn *conn)
{
	uint8_t conn_index = bt_conn_index(conn);
	char addr[BT_ADDR_LE_STR_LEN];
	int err;
	int param_count = 0;
	seeed_conn_t *node = find_node_by_conn(conn); // Might need to add error handling if node not found
    node->subscribed_mask = 0;
	
	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	printk("ESS [%s] Attempting to subscribe to notifications...\n", addr);
	printk("ESS [%s] Found handles - Temp: 0x%04x, Pressure: 0x%04x, Humidity: 0x%04x\n", 
	       addr, ess_data[conn_index].temp_handle, ess_data[conn_index].pressure_handle, ess_data[conn_index].humidity_handle);
	
	/* Subscribe to temperature notifications */
	if (ess_data[conn_index].temp_handle) {
		/* Assume CCC handle is characteristic handle + 1 */
		uint16_t ccc_handle = ess_data[conn_index].temp_handle + 1;
		
		subscribe_params[conn_index * 3 + param_count].notify = ess_notify_cb;
		subscribe_params[conn_index * 3 + param_count].value = BT_GATT_CCC_NOTIFY;
		subscribe_params[conn_index * 3 + param_count].value_handle = ess_data[conn_index].temp_handle;
		subscribe_params[conn_index * 3 + param_count].ccc_handle = ccc_handle;
		
		err = bt_gatt_subscribe(conn, &subscribe_params[conn_index * 3 + param_count]);
		if (err) {
			printk("ESS [%s] Temperature subscription failed: %d\n", addr, err);
		} else {
			printk("ESS [%s] Temperature notifications subscribed (handle=0x%04x, ccc=0x%04x)\n", 
			       addr, ess_data[conn_index].temp_handle, ccc_handle);
			ess_data[conn_index].temp_notify_enabled = true;
		}
		param_count++;
		if (!err) node->subscribed_mask |= BIT(0); // value_a subscribed

	}
	
	/* Subscribe to pressure notifications */
	if (ess_data[conn_index].pressure_handle) {
		/* Assume CCC handle is characteristic handle + 1 */
		uint16_t ccc_handle = ess_data[conn_index].pressure_handle + 1;
		
		subscribe_params[conn_index * 3 + param_count].notify = ess_notify_cb;
		subscribe_params[conn_index * 3 + param_count].value = BT_GATT_CCC_NOTIFY;
		subscribe_params[conn_index * 3 + param_count].value_handle = ess_data[conn_index].pressure_handle;
		subscribe_params[conn_index * 3 + param_count].ccc_handle = ccc_handle;
		
		err = bt_gatt_subscribe(conn, &subscribe_params[conn_index * 3 + param_count]);
		if (err) {
			printk("ESS [%s] Pressure subscription failed: %d\n", addr, err);
		} else {
			printk("ESS [%s] Pressure notifications subscribed (handle=0x%04x, ccc=0x%04x)\n", 
			       addr, ess_data[conn_index].pressure_handle, ccc_handle);
			ess_data[conn_index].pressure_notify_enabled = true;
		}
		param_count++;
		if (!err) node->subscribed_mask |= BIT(1); // value_b subscribed
	}
	
	/* Subscribe to humidity notifications */
	if (ess_data[conn_index].humidity_handle) {
		/* Assume CCC handle is characteristic handle + 1 */
		uint16_t ccc_handle = ess_data[conn_index].humidity_handle + 1;
		
		subscribe_params[conn_index * 3 + param_count].notify = ess_notify_cb;
		subscribe_params[conn_index * 3 + param_count].value = BT_GATT_CCC_NOTIFY;
		subscribe_params[conn_index * 3 + param_count].value_handle = ess_data[conn_index].humidity_handle;
		subscribe_params[conn_index * 3 + param_count].ccc_handle = ccc_handle;
		
		err = bt_gatt_subscribe(conn, &subscribe_params[conn_index * 3 + param_count]);
		if (err) {
			printk("ESS [%s] Humidity subscription failed: %d\n", addr, err);
		} else {
			printk("ESS [%s] Humidity notifications subscribed (handle=0x%04x, ccc=0x%04x)\n", 
			       addr, ess_data[conn_index].humidity_handle, ccc_handle);
			ess_data[conn_index].humidity_notify_enabled = true;
		}
		param_count++;
		if (!err) node->subscribed_mask |= BIT(2); // value_c subscribed
	}
	
	if (param_count == 0) {
		printk("ESS [%s] No characteristics found for subscription\n", addr);
		return -ENOENT;
	}
	
	printk("ESS [%s] Successfully subscribed to %d characteristics\n", addr, param_count);
	return 0;
}

#endif /* CONFIG_BT_GATT_CLIENT */

void connected(struct bt_conn *conn, uint8_t reason)
{
	char addr[BT_ADDR_LE_STR_LEN];
	const bt_addr_le_t *conn_addr = bt_conn_get_dst(conn);

	bt_addr_le_to_str(conn_addr, addr, sizeof(addr));

	if (reason) {
		printk("Failed to connect to %s (%u)\n", addr, reason);

		bt_conn_unref(conn_connecting);
		conn_connecting = NULL;

		start_scan();
		return;
	}

	conn_connecting = NULL;

	/* Track this connection */
	track_device_connect(conn_addr);

	conn_count++;
	if (conn_count < conn_count_max) {
		start_scan();
	}

	printk("Connected (%u): %s\n", conn_count, addr);

	/* Start LED blinking effect based on device count */
	start_led_blinking(conn_count);

	on_ble_connected(conn, addr);

#if defined(CONFIG_BT_SMP)
	int err = bt_conn_set_security(conn, BT_SECURITY_L2);

	if (err) {
		printk("Failed to set security (%d).\n", err);
	}
#endif

#if defined(CONFIG_BT_GATT_CLIENT)
	mtu_exchange(conn);
	/* Start ESS discovery after a short delay to allow MTU exchange to complete */
	k_sleep(K_MSEC(100));
	ess_discover_services(conn);
#endif
}

void disconnected(struct bt_conn *conn, uint8_t reason)
{
	char addr[BT_ADDR_LE_STR_LEN];
	const bt_addr_le_t *conn_addr = bt_conn_get_dst(conn);

	bt_addr_le_to_str(conn_addr, addr, sizeof(addr));

	printk("Disconnected: %s, reason 0x%02x %s\n", addr, reason, bt_hci_err_to_str(reason));

#if defined(CONFIG_BT_GATT_CLIENT)
	/* Clean up ESS subscriptions */
	uint8_t conn_index = bt_conn_index(conn);
	if (conn_index < CONFIG_BT_MAX_CONN) {
		/* Unsubscribe from all notifications */
		for (int i = 0; i < 3; i++) {
			if (subscribe_params[conn_index * 3 + i].value_handle) {
				bt_gatt_unsubscribe(conn, &subscribe_params[conn_index * 3 + i]);
			}
		}
		/* Clear ESS data */
		memset(&ess_data[conn_index], 0, sizeof(ess_data[conn_index]));
	}
#endif

	/* Track this disconnection */
	track_device_disconnect(conn_addr, reason);

	bt_conn_unref(conn);

	if ((conn_count == 1U) && (is_disconnecting || (reason == BT_HCI_ERR_CONN_FAIL_TO_ESTAB))) {
		is_disconnecting = false;
		start_scan();
	}
	conn_count--;

	/* Update LED effect based on remaining connections */
	if (conn_count == 0) {
		/* No devices connected, start breathing effect */
		start_led_breathing();
	} else {
		/* Still have devices connected, update blinking pattern */
		start_led_blinking(conn_count);
	}
}

bool app_le_param_req(struct bt_conn *conn, struct bt_le_conn_param *param)
{
	char addr[BT_ADDR_LE_STR_LEN];
	const bt_addr_le_t *conn_addr = bt_conn_get_dst(conn);
	device_entry_t *entry;

	bt_addr_le_to_str(conn_addr, addr, sizeof(addr));

	printk("LE conn param req: %s int (0x%04x, 0x%04x) lat %d to %d\n",
	       addr, param->interval_min, param->interval_max, param->latency,
	       param->timeout);

	/* Mark that this device has made a parameter request */
	entry = get_or_create_device_entry(conn_addr);
	if (entry) {
		entry->has_made_param_request = true;
	}

	/* Manual whitelist mode - no automatic whitelisting/blacklisting based on parameters */
	printk("Device %s connection parameters received (manual whitelist mode)\n", addr);

	return true;
}

void app_le_param_updated(struct bt_conn *conn, uint16_t interval, uint16_t latency, uint16_t timeout)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("LE conn param updated: %s int 0x%04x lat %d to %d\n",
	       addr, interval, latency, timeout);
}

struct bt_conn_cb conn_callbacks = {
	.connected = connected,
	.disconnected = disconnected,
	.le_param_req = app_le_param_req,
	.le_param_updated = app_le_param_updated,

#if defined(CONFIG_BT_SMP)
	.security_changed = security_changed,
#endif

#if defined(CONFIG_BT_USER_PHY_UPDATE)
	.le_phy_updated = le_phy_updated,
#endif /* CONFIG_BT_USER_PHY_UPDATE */

#if defined(CONFIG_BT_USER_DATA_LEN_UPDATE)
	.le_data_len_updated = le_data_len_updated,
#endif /* CONFIG_BT_USER_DATA_LEN_UPDATE */
};

void remote_info(struct bt_conn *conn, void *data)
{
	struct bt_conn_remote_info remote_info;
	char addr[BT_ADDR_LE_STR_LEN];
	int err;

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("Get remote info %s...\n", addr);
	err = bt_conn_get_remote_info(conn, &remote_info);
	if (err) {
		printk("Failed remote info %s.\n", addr);
		return;
	}
	printk("success.\n");

	uint8_t *actual_count = (void *)data;

	(*actual_count)++;
}

void disconnect(struct bt_conn *conn, void* data)
{
	char addr[BT_ADDR_LE_STR_LEN];
	int err;

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("Disconnecting %s...\n", addr);
	err = bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
	if (err) {
		printk("Failed disconnection %s.\n", addr);
		return;
	}
	on_ble_disconnected(conn);
	printk("success.\n");
}

int init_central(uint8_t max_conn, uint8_t iterations)
{
	int err;

	conn_count_max = max_conn;

	/* Initialize LED PWM device */
	led_pwm = DEVICE_DT_GET(LED_PWM_NODE_ID);
	if (!device_is_ready(led_pwm)) {
		printk("PWM LED device not ready, LED effects disabled\n");
		led_pwm = NULL;
	} else {
		printk("PWM LED device initialized successfully\n");
	}

	/* Initialize LED timer and work */
	k_timer_init(&led_timer, led_timer_handler, NULL);
	k_work_init(&led_work, led_work_handler);

	/* Initialize DK LEDs for fallback */
	err = dk_leds_init();
	if (err) {
		printk("DK LEDs init failed (err %d)\n", err);
	}
	
	if (usb_init() != 0) {
        printk("Failed to initialize USB CDC ACM\n");
        // Continue anyway - UART console still works
    }

	/* Initialize whitelist/blacklist system */
	init_manual_whitelist();
	device_entry_count = 0;

	err = bt_enable(NULL);
	if (err) {
		printk("Bluetooth init failed (err %d)\n", err);
		return err;
	}

	printk("Bluetooth initialized\n");
	printk("Manual Whitelist system initialized\n");
	
	printk("Only manually whitelisted devices will be connected to\n");

	bt_conn_cb_register(&conn_callbacks);

	/* Start LED breathing effect (no devices connected initially) */
	start_led_breathing();
	
	/* Test LED to make sure it's working */
	if (led_pwm && device_is_ready(led_pwm)) {
		led_set_brightness(led_pwm, 0, MAX_BRIGHTNESS);
		k_sleep(K_SECONDS(1));
		led_set_brightness(led_pwm, 0, 0);
	}

	start_scan();
	// start_passive_scan(); // Scanning for RSSI advertisments

	while (true) {
		while (conn_count < conn_count_max) {
			k_sleep(K_MSEC(10));
		}

		is_disconnecting = true;

		/* Let us perform version exchange on all connections to ensure
		 * there is actual communication.
		 */
		uint8_t actual_count = 0U;

		bt_conn_foreach(BT_CONN_TYPE_LE, remote_info, &actual_count);
		if (actual_count < conn_count_max) {
			k_sleep(K_MSEC(10));

			continue;
		}

		/* Lets wait sufficiently to ensure a stable connection
		 * before starting to disconnect for next iteration.
		 */
		k_sleep(K_SECONDS(60));

		if (!iterations) {
			break;
		}
		iterations--;
		printk("Iterations remaining: %u\n", iterations);

		/* Device needing multiple connections is the one
		 * initiating the disconnects.
		 */
		if (conn_count_max > 1U) {
			printk("Disconnecting all...\n");
			bt_conn_foreach(BT_CONN_TYPE_LE, disconnect, NULL);
		} else {
			printk("Wait for disconnections...\n");
		}

		while (is_disconnecting) {
			k_sleep(K_MSEC(10));
		}
		printk("All disconnected.\n");
	}

	return 0;
}


#if defined(CONFIG_BT_SMP)
void security_changed(struct bt_conn *conn, bt_security_t level,
			     enum bt_security_err err)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	if (!err) {
		printk("Security changed: %s level %u\n", addr, level);
	} else {
		printk("Security failed: %s level %u err %d %s\n", addr, level,
		       err, bt_security_err_to_str(err));
	}
}
#endif

#if defined(CONFIG_BT_USER_PHY_UPDATE)
void le_phy_updated(struct bt_conn *conn,
			   struct bt_conn_le_phy_info *param)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("LE PHY Updated: %s Tx 0x%x, Rx 0x%x\n", addr, param->tx_phy,
	       param->rx_phy);
}
#endif /* CONFIG_BT_USER_PHY_UPDATE */

#if defined(CONFIG_BT_USER_DATA_LEN_UPDATE)
void le_data_len_updated(struct bt_conn *conn,
				struct bt_conn_le_data_len_info *info)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("Data length updated: %s max tx %u (%u us) max rx %u (%u us)\n",
	       addr, info->tx_max_len, info->tx_max_time, info->rx_max_len,
	       info->rx_max_time);
}
#endif /* CONFIG_BT_USER_DATA_LEN_UPDATE */



