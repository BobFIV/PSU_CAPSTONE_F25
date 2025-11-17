#pragma once
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

#define MLX90614_I2C_ADDR 0x5A
#define MLX90614_REG_TA   0x06
#define MLX90614_REG_TOBJ1 0x07

int mlx90614_init(const struct device **dev_out);
int mlx90614_read_temp_c(const struct device *dev, uint8_t reg, double *out_c);
