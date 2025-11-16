#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/sys/printk.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/drivers/i2c.h>

#include <mlx90614.h>

// Enable to use the provided simulated sensor
#define SIMULATED_SENSOR 1

// Enable GATT Characteristic Subscription
#define ENABLE_TEMP 1
#define ENABLE_PRESSURE 1
#define ENABLE_HUMIDITY 1

#define SENSOR_THREAD_PRIORITY 7
#define SENSOR_THREAD_STACKSIZE 2048

// External functions from main.c
extern bool is_device_connected(void);
extern struct bt_conn *get_current_connection(void);

// Standard Environmental Sensing Service: 0x181A
#define BT_UUID_ESS_VAL 0x181a

// CCC callbacks
#if(ENABLE_TEMP)

// Standard Tempurature characteristic UUID
#define BT_UUID_TEMP_CHAR_VAL     0x2a6e

// Notification flag
static uint8_t temp_notify_enabled = 0;

static void temp_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    temp_notify_enabled = (value == BT_GATT_CCC_NOTIFY);
    printk(">>> Temp notifications %s <<<\n", temp_notify_enabled ? "ENABLED" : "DISABLED");
}
#endif

#if(ENABLE_PRESSURE)

// Standard Pressure characteristic UUID
#define BT_UUID_PRESSURE_CHAR_VAL 0x2a6d

// Notification flag
static uint8_t pressure_notify_enabled = 0;

static void pressure_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    pressure_notify_enabled = (value == BT_GATT_CCC_NOTIFY);
    printk(">>> Pressure notifications %s <<<\n", pressure_notify_enabled ? "ENABLED" : "DISABLED");
}
#endif

#if(ENABLE_HUMIDITY)

// Standard Humidity characteristic UUID
#define BT_UUID_HUMIDITY_CHAR_VAL 0x2a6f

// Notification flag
static uint8_t humidity_notify_enabled = 0;

static void humidity_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    humidity_notify_enabled = (value == BT_GATT_CCC_NOTIFY);
    printk(">>> Humidity notifications %s <<<\n", humidity_notify_enabled ? "ENABLED" : "DISABLED");
}
#endif

// GATT service with THREE characteristics
BT_GATT_SERVICE_DEFINE(ess_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_16(BT_UUID_ESS_VAL)),
    
    #if(ENABLE_TEMP)
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(BT_UUID_TEMP_CHAR_VAL),
                          BT_GATT_CHRC_NOTIFY,
                          BT_GATT_PERM_NONE,
                          NULL, NULL, NULL),
    BT_GATT_CCC(temp_ccc_cfg_changed,
               BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
    #endif

    #if(ENABLE_PRESSURE)
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(BT_UUID_PRESSURE_CHAR_VAL),
                          BT_GATT_CHRC_NOTIFY,
                          BT_GATT_PERM_NONE,
                          NULL, NULL, NULL),
    BT_GATT_CCC(pressure_ccc_cfg_changed,
               BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
    #endif

    #if(ENABLE_HUMIDITY)
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(BT_UUID_HUMIDITY_CHAR_VAL),
                          BT_GATT_CHRC_NOTIFY,
                          BT_GATT_PERM_NONE,
                          NULL, NULL, NULL),
    BT_GATT_CCC(humidity_ccc_cfg_changed,
               BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
    #endif
);

#if(SIMULATED_SENSOR)
// Get simulated sensor
static const struct device *get_simulated_sensor(void)
{
    const struct device *const dev = DEVICE_DT_GET(DT_NODELABEL(sensor_sim));
    if (dev == NULL || !device_is_ready(dev)) {
        printk("ERROR: Sensor not ready\n");
        return NULL;
    }
    printk("Sensor ready\n");
    return dev;
}
#endif
// Sensor thread
int sensor_data_collector(void)
{
    #if(SIMULATED_SENSOR)
        const struct device *sim_dev = get_simulated_sensor();
        if (sim_dev == NULL) {
            return -1;
        }

        printk("\n>>> Sensor thread started <<<\n\n");
        k_sleep(K_SECONDS(2));

        int count = 0;

        while (1) {
            struct sensor_value temp, press, humidity, acc[3];
            
            int ret = sensor_sample_fetch(sim_dev);
            if (ret) {
                k_sleep(K_SECONDS(1));
                continue;
            }

            sensor_channel_get(sim_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
            sensor_channel_get(sim_dev, SENSOR_CHAN_PRESS, &press);
            sensor_channel_get(sim_dev, SENSOR_CHAN_HUMIDITY, &humidity);
            sensor_channel_get(sim_dev, SENSOR_CHAN_ACCEL_XYZ, acc);

            printk("\n=== Reading #%d ===\n", ++count);
            printk("Temp: %d.%02d°C | Press: %d.%02dkPa | Humid: %d.%02d%%\n", 
                temp.val1, abs(temp.val2)/10000,
                press.val1, abs(press.val2)/10000,
                humidity.val1, abs(humidity.val2)/10000);

            struct bt_conn *conn = get_current_connection();
            if (conn) {
                if (temp_notify_enabled) {
                    int16_t temp_val = (int16_t)(temp.val1 * 100 + temp.val2 / 10000);
                    int err = bt_gatt_notify(conn, &ess_svc.attrs[1], &temp_val, sizeof(temp_val));
                    printk("Temp: %d (err=%d)\n", temp_val, err);
                }
                
                if (pressure_notify_enabled) {
                    uint32_t press_val = (uint32_t)(press.val1 * 10000 + press.val2 / 100);
                    int err = bt_gatt_notify(conn, &ess_svc.attrs[4], &press_val, sizeof(press_val));
                    printk("Press: %u (err=%d)\n", press_val, err);
                }
                
                if (humidity_notify_enabled) {
                    uint16_t humid_val = (uint16_t)(humidity.val1 * 100 + humidity.val2 / 10000);
                    int err = bt_gatt_notify(conn, &ess_svc.attrs[7], &humid_val, sizeof(humid_val));
                    printk("Humid: %u (err=%d)\n", humid_val, err);
                }
            }

            k_sleep(K_SECONDS(1));
        }
    #else
        const struct device *mlx_dev;
        if (mlx90614_init(&mlx_dev)) {
            printk("MLX90614 init failed\n");
            return -1;
        }

        printk("MLX90614 ready!\n");
        k_sleep(K_SECONDS(1));

        while (1) {
            double ambient_c, object_c;
            mlx90614_read_temp_c(mlx_dev, MLX90614_REG_TA, &ambient_c);
            mlx90614_read_temp_c(mlx_dev, MLX90614_REG_TOBJ1, &object_c);

            printk("Ambient: %.2f °C | Object: %.2f °C\n", ambient_c, object_c);

            struct bt_conn *conn = get_current_connection();
            if (conn && temp_notify_enabled) {
                int16_t temp_val = (int16_t)(object_c * 100);  // 0.01°C units
                bt_gatt_notify(conn, &ess_svc.attrs[1], &temp_val, sizeof(temp_val));
            }

            k_sleep(K_SECONDS(1));
        }
    #endif
    return 0;
}

K_THREAD_DEFINE(sensor_data_collector_id, SENSOR_THREAD_STACKSIZE, 
                sensor_data_collector, NULL, NULL, NULL, 
                SENSOR_THREAD_PRIORITY, 0, 0);
