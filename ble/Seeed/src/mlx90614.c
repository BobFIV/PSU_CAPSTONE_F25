#include "mlx90614.h"
#include <zephyr/sys/printk.h>

int mlx90614_init(const struct device **dev_out) {
    const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c30));
    if (!device_is_ready(i2c_dev)) {
        printk("I2C0 not ready!\n");
        return -ENODEV;
    }
    *dev_out = i2c_dev;
    return 0;
}

int mlx90614_read_temp_c(const struct device *dev, uint8_t reg, double *out_c) {
    uint8_t cmd = reg;
    uint8_t rx[3];
    int ret = i2c_write_read(dev, MLX90614_I2C_ADDR, &cmd, 1, rx, sizeof(rx));
    if (ret) {
        printk("I2C read error %d\n", ret);
        return ret;
    }

    uint16_t raw = (uint16_t)rx[0] | ((uint16_t)rx[1] << 8);
    float temp_k = raw * 0.02f;
    *out_c = (double)(temp_k - 273.15f);
    return 0;
}
