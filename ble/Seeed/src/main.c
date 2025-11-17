#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/drivers/gpio.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

#define DEVICE_NAME CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)

static const struct gpio_dt_spec led0 = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static bool device_connected = false;
static struct bt_conn *current_conn = NULL;

// Extended advertising instances
static struct bt_le_ext_adv *main_adv;
static struct bt_le_ext_adv *test_adv;

// Main advertising data
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA(BT_DATA_NAME_COMPLETE, DEVICE_NAME, DEVICE_NAME_LEN),
};

// Test beacon advertising data
static const struct bt_data test_ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_NO_BREDR),
    BT_DATA(BT_DATA_NAME_COMPLETE, "SEEED_TEST", 10),
};

// Main connectable advertiser parameters
static struct bt_le_adv_param main_adv_params = {
    .id = BT_ID_DEFAULT,
    .sid = 0,
    .secondary_max_skip = 0,
    .options = BT_LE_ADV_OPT_CONNECTABLE | BT_LE_ADV_OPT_USE_IDENTITY,
    .interval_min = BT_GAP_ADV_FAST_INT_MIN_2,
    .interval_max = BT_GAP_ADV_FAST_INT_MAX_2,
    .peer = NULL,
};

// Test beacon advertiser parameters (non-connectable)
static struct bt_le_adv_param test_adv_params = {
    .id = BT_ID_DEFAULT,
    .sid = 1,
    .secondary_max_skip = 0,
    .options = BT_LE_ADV_OPT_USE_IDENTITY,
    .interval_min = 8000,
    .interval_max = 8000,
    .peer = NULL,
};

// Connection callbacks
static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        LOG_ERR("Connection failed (err 0x%02x)", err);
    } else {
        LOG_INF("*** DEVICE CONNECTED ***");
        device_connected = true;
        current_conn = bt_conn_ref(conn);
        
        // START test advertiser when connected
        int start_err = bt_le_ext_adv_start(test_adv, BT_LE_EXT_ADV_START_DEFAULT);
        if (start_err) {
            LOG_WRN("Failed to start test advertiser (err %d)", start_err);
        } else {
            LOG_INF("Test advertiser started (device now connected)");
        }
    }
}

static void restart_advertising_work_handler(struct k_work *work)
{
    // Only restart main advertising (connectable)
    int err = bt_le_ext_adv_start(main_adv, BT_LE_EXT_ADV_START_DEFAULT);
    if (!err) {
        LOG_INF("Main advertising restarted (connectable)");
    }
    // Do NOT restart test advertiser - it should only run when connected
}

K_WORK_DELAYABLE_DEFINE(restart_adv_work, restart_advertising_work_handler);

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    LOG_INF("Disconnected, stopping test advertiser and restarting main advertiser...");
    
    // Stop test advertiser immediately on disconnect
    int stop_err = bt_le_ext_adv_stop(test_adv);
    if (stop_err) {
        LOG_WRN("Failed to stop test advertiser (err %d)", stop_err);
    } else {
        LOG_INF("Test advertiser stopped (device disconnected)");
    }
    
    device_connected = false;
    if (current_conn) {
        bt_conn_unref(current_conn);
        current_conn = NULL;
    }
    
    k_work_reschedule(&restart_adv_work, K_MSEC(150));
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

bool is_device_connected(void)
{
    return device_connected;
}

struct bt_conn *get_current_connection(void)
{
    return current_conn;
}

int main(void)
{
    int err;
    printk("\n\n");
    printk("========================================\n");
    printk("  XIAO nRF54L15 - Sensor with Notify\n");
    printk("========================================\n\n");

    // Configure LED
    if (!gpio_is_ready_dt(&led0)) {
        LOG_ERR("LED device not ready");
        return -1;
    }

    err = gpio_pin_configure_dt(&led0, GPIO_OUTPUT_INACTIVE);
    if (err) {
        LOG_ERR("Failed to configure LED (err %d)", err);
        return -1;
    }
    LOG_INF("LED configured");

    // Initialize Bluetooth
    err = bt_enable(NULL);
    if (err) {
        LOG_ERR("Bluetooth init failed (err %d)", err);
        return -1;
    }
    LOG_INF("Bluetooth initialized");

    // Create main connectable advertiser
    err = bt_le_ext_adv_create(&main_adv_params, NULL, &main_adv);
    if (err) {
        LOG_ERR("Failed to create main advertiser (err %d)", err);
        return -1;
    }

    err = bt_le_ext_adv_set_data(main_adv, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        LOG_ERR("Failed to set main adv data (err %d)", err);
        return -1;
    }

    err = bt_le_ext_adv_start(main_adv, BT_LE_EXT_ADV_START_DEFAULT);
    if (err) {
        LOG_ERR("Failed to start main advertisement (err %d)", err);
        return -1;
    }
    LOG_INF("Main advertising started - Device name: %s", DEVICE_NAME);

    // Create test beacon advertiser (but don't start it yet)
    err = bt_le_ext_adv_create(&test_adv_params, NULL, &test_adv);
    if (err) {
        LOG_ERR("Failed to create test advertiser (err %d)", err);
        return -1;
    }

    err = bt_le_ext_adv_set_data(test_adv, test_ad, ARRAY_SIZE(test_ad), NULL, 0);
    if (err) {
        LOG_ERR("Failed to set test adv data (err %d)", err);
        return -1;
    }

    LOG_INF("Test advertiser created (will start when device connects)");

    // LED blink loop
    while (1) {
        if (device_connected) {
            gpio_pin_toggle_dt(&led0);
            k_sleep(K_MSEC(200));
        } else {
            gpio_pin_toggle_dt(&led0);
            k_sleep(K_MSEC(1000));
        }
    }

    return 0;
}