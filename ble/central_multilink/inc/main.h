#include <zephyr/types.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <errno.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/slist.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/led.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <dk_buttons_and_leds.h>
#include <zephyr/drivers/uart.h>

/* Environmental Sensing Service UUIDs */
#define BT_UUID_ESS_VAL 0x181a
#define BT_UUID_TEMP_CHAR_VAL     0x2a6e
#define BT_UUID_PRESSURE_CHAR_VAL 0x2a6d
#define BT_UUID_HUMIDITY_CHAR_VAL 0x2a6f

#define SCAN_INTERVAL 0x0010 /* 10 ms */
#define SCAN_WINDOW   0x0010 /* 10 ms */
#define INIT_INTERVAL 0x0010 /* 10 ms */
#define INIT_WINDOW   0x0010 /* 10 ms */
#define CONN_INTERVAL 0x0320 /* 1000 ms */
#define CONN_LATENCY  0
#define CONN_TIMEOUT  MIN(MAX((CONN_INTERVAL * 125 * \
			       MAX(CONFIG_BT_MAX_CONN, 6) / 1000), 10), 3200)

/* LED Configuration */
#define LED_PWM_NODE_ID	 DT_COMPAT_GET_ANY_STATUS_OKAY(pwm_leds)
#define MAX_BRIGHTNESS	100
#define PWM_FADE_DELAY	50
#define BLINK_INTERVAL  2000  /* 2 seconds between blinks */
#define BLINK_DURATION  200   /* 200ms blink duration */
#define CON_STATUS_LED  DK_LED1  /* GPIO LED1 as fallback */

/* Manual Whitelist system */
#define MAX_DEVICE_LIST 200  /* Increased from 50 to handle more devices */
#define MAX_MANUAL_WHITELIST 10  /* Maximum number of manually whitelisted devices */

/* UART */
#define UART_LABEL DT_LABEL(DT_NODELABEL(uart0))
#define MAX_SEEED_CONN 4  // Max number of simultaneous Seeed BLE devices

/* Manual whitelist entry structure */
typedef struct {
    char mac[18];  // "AA:BB:CC:DD:EE:FF\0"
    bool active;
} manual_whitelist_entry_t;

/* Whitelist/Blacklist Structs*/
typedef enum {
	DEVICE_STATUS_UNKNOWN = 0,
	DEVICE_STATUS_WHITELISTED,
	DEVICE_STATUS_BLACKLISTED
} device_status_t;

typedef struct device_entry {
	bt_addr_le_t addr;
	device_status_t status;
	uint8_t disconnect_count;
	uint8_t connect_count;
	uint8_t scan_found_count;
	bool has_made_param_request;
	sys_snode_t node;
} device_entry_t;

/* GATT Client structures for Environmental Sensing Service */
struct gatt_ess_data {
	struct bt_conn *conn;
	uint16_t temp_handle;
	uint16_t pressure_handle;
	uint16_t humidity_handle;
	uint16_t temp_ccc_handle;
	uint16_t pressure_ccc_handle;
	uint16_t humidity_ccc_handle;
	bool temp_notify_enabled;
	bool pressure_notify_enabled;
	bool humidity_notify_enabled;
};

extern struct gatt_ess_data ess_data[CONFIG_BT_MAX_CONN];

/* Packet structure sent over UART */
typedef struct __packed {
    char device_addr[BT_ADDR_LE_STR_LEN];  // Seeed device ID or slot index
    int16_t value_a;
    uint32_t value_b;
    uint16_t value_c;
} sensor_packet_t;

typedef struct __packed {
    char mac_addr[30];   // ASCII MAC string, null-padded
    int8_t rssi;         // signed 8-bit RSSI
    uint8_t connected;   // 1 = connected to this central, 0 = not connected
} rssi_packet_t;

/* Per-connection state */
typedef struct {
    struct bt_conn *conn;
    sensor_packet_t data;
    bool a_ready;
    bool b_ready;
    bool c_ready;
    bool active;
    uint8_t subscribed_mask;  // bitmask of subscribed characteristics (bit0=A, bit1=B, bit2=C)
} seeed_conn_t;



void start_scan(void);
void start_passive_scan(void);
device_status_t get_device_status(const bt_addr_le_t *addr);
void add_device_to_whitelist(const bt_addr_le_t *addr);
void remove_device_from_whitelist(const bt_addr_le_t *addr);
void add_device_to_blacklist(const bt_addr_le_t *addr);
bool is_device_whitelisted(const bt_addr_le_t *addr);
bool is_device_blacklisted(const bt_addr_le_t *addr);
bool is_device_manually_whitelisted(const bt_addr_le_t *addr);
device_entry_t *get_or_create_device_entry(const bt_addr_le_t *addr);
void track_device_connect(const bt_addr_le_t *addr);
void track_device_disconnect(const bt_addr_le_t *addr, uint8_t reason);

/* Manual whitelist management functions */
void init_manual_whitelist(void);
bool add_mac_to_manual_whitelist(const char *mac_str);
bool remove_mac_from_manual_whitelist(const char *mac_str);

/* LED control functions */
void led_work_handler(struct k_work *work);
void led_timer_handler(struct k_timer *timer);
void start_led_breathing(void);
void start_led_blinking(uint8_t device_count);
void stop_led_effects(void);
void flash_data_led(void);

#if defined(CONFIG_BT_GATT_CLIENT) /* GATT Client functions */
extern struct bt_gatt_exchange_params mtu_exchange_params[CONFIG_BT_MAX_CONN];
extern struct bt_gatt_discover_params discover_params[CONFIG_BT_MAX_CONN];
extern struct bt_gatt_subscribe_params subscribe_params[CONFIG_BT_MAX_CONN * 3]; /* 3 characteristics per connection */

void mtu_exchange_cb(struct bt_conn *conn, uint8_t err, struct bt_gatt_exchange_params *params);
int mtu_exchange(struct bt_conn *conn);
uint8_t ess_notify_cb(struct bt_conn *conn, struct bt_gatt_subscribe_params *params, const void *data, uint16_t length);
uint8_t ess_discover_func(struct bt_conn *conn, const struct bt_gatt_attr *attr, struct bt_gatt_discover_params *params);
void ess_discover_complete(struct bt_conn *conn, int err);
int ess_discover_services(struct bt_conn *conn);
int ess_subscribe_notifications(struct bt_conn *conn);
#endif /* CONFIG_BT_GATT_CLIENT */

#if defined(CONFIG_BT_SMP)
void security_changed(struct bt_conn *conn, bt_security_t level, enum bt_security_err err);
#endif

#if defined(CONFIG_BT_USER_PHY_UPDATE)
void le_phy_updated(struct bt_conn *conn, struct bt_conn_le_phy_info *param);
#endif

#if defined(CONFIG_BT_USER_DATA_LEN_UPDATE)
void le_data_len_updated(struct bt_conn *conn, struct bt_conn_le_data_len_info *info);
#endif

/* Central Multilink BLE Functions*/
void connected(struct bt_conn *conn, uint8_t reason);
void disconnected(struct bt_conn *conn, uint8_t reason);
bool app_le_param_req(struct bt_conn *conn, struct bt_le_conn_param *param);
void app_le_param_updated(struct bt_conn *conn, uint16_t interval, uint16_t latency, uint16_t timeout);
void remote_info(struct bt_conn *conn, void *data);
void disconnect(struct bt_conn *conn, void* data);
int init_central(uint8_t max_conn, uint8_t iterations);
extern struct bt_conn_cb conn_callbacks;

/* UART Control Functions */
void uart_send_data(const uint8_t *data, size_t len);
void on_ble_connected(struct bt_conn *conn, char* addr);
void on_ble_disconnected(struct bt_conn *conn);
seeed_conn_t *find_node_by_conn(struct bt_conn *conn);
seeed_conn_t *find_node_by_mac_addr(char* addr);
void try_send_packet(seeed_conn_t *node);
void ble_value_a_received(struct bt_conn *conn, int16_t val);
void ble_value_b_received(struct bt_conn *conn, uint32_t val);
void ble_value_c_received(struct bt_conn *conn, uint16_t val);

/* Whitelist/Blacklist system variables*/
extern sys_slist_t whitelist;
extern sys_slist_t blacklist;
extern device_entry_t device_entries[MAX_DEVICE_LIST];
extern uint8_t device_entry_count;

extern struct bt_conn *conn_connecting;
extern uint8_t conn_count_max;
extern uint8_t volatile conn_count;
extern bool volatile is_disconnecting;

/* Manual whitelist variables */
extern manual_whitelist_entry_t manual_whitelist[MAX_MANUAL_WHITELIST];
extern uint8_t manual_whitelist_count;

/* LED control variables */
extern const struct device *led_pwm;
extern int16_t current_brightness;
extern bool brightness_increasing;
extern struct k_timer led_timer;
extern struct k_work led_work;
extern bool led_blink_state;
extern uint8_t blink_count;

/* UART Variables */
extern const struct device *uart_dev;
extern seeed_conn_t seeed_nodes[MAX_SEEED_CONN];

int usb_init(void);
void usb_send_data(const uint8_t *data, size_t len);
void usb_send_framed(uint8_t type, const uint8_t *payload, size_t len);
void send_rssi_report(const char *mac17, int8_t rssi, uint8_t connected_flag);