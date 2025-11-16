#ifndef SENSOR_DATA_COLLECTOR_H
#define SENSOR_DATA_COLLECTOR_H

#include <zephyr/drivers/sensor.h>
#include <zephyr/bluetooth/conn.h>

#include <mlx90614.h>

typedef struct {
	struct sensor_value temp;
	struct sensor_value press;
	struct sensor_value humidity;
	struct sensor_value gas_res;
	struct sensor_value gyr[3];
	struct sensor_value acc[3];
} sensorsreadings;

// Functions to access connection state from main.c
struct bt_conn *get_current_connection(void);
bool is_device_connected(void);

#endif