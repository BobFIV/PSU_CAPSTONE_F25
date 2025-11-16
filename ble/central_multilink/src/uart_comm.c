#include "main.h"
#include <zephyr/usb/usb_device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <ctype.h>

#define PKT_START        0xAA
#define PKT_END          0x55
#define PKT_TYPE_SENSOR  0x01
#define PKT_TYPE_TEST    0x02
#define MAX_USB_PKT_LEN  64   /* must remain 64 bytes or less */

/* UART Variables (existing - for console/debug via UART0) */
const struct device *uart_dev = DEVICE_DT_GET(DT_NODELABEL(uart0));

/* USB CDC ACM Variables (new - for data via nRF5340 USB) */
const struct device *usb_dev = DEVICE_DT_GET(DT_NODELABEL(cdc_acm_uart0));
static bool usb_ready = false;

seeed_conn_t seeed_nodes[MAX_SEEED_CONN];

/* Buffer for incoming USB data */
#define USB_RX_BUF_SIZE 128
static char usb_rx_buf[USB_RX_BUF_SIZE];
static size_t usb_rx_len = 0;

/* Forward declaration */
static void usb_rx_handler(const struct device *dev, void *user_data);
static void process_usb_command(char *cmd);

/* -------------------------------------------------------------------------- */
/* USB initialization function - call this in your main() */
int usb_init(void)
{
    if (!device_is_ready(usb_dev)) {
        printk("USB CDC ACM device not ready\n");
        return -1;
    }


    /* Wait for host (Raspberry Pi) to enumerate the device */
    printk("Waiting for USB enumeration...\n");
    k_sleep(K_MSEC(1000));
    usb_ready = true;
    printk("USB CDC ACM ready\n");

    /* Enable interrupt-driven RX */
    uart_irq_callback_user_data_set(usb_dev, usb_rx_handler, NULL);
    uart_irq_rx_enable(usb_dev);

    return 0;
}

/* -------------------------------------------------------------------------- */
/* EXISTING: UART send function (for debug output on UART0) */
void uart_send_data(const uint8_t *data, size_t len)
{
    if (!device_is_ready(uart_dev)) {
        printk("UART device not ready!");
        return;
    }

    for (size_t i = 0; i < len; i++) {
        uart_poll_out(uart_dev, data[i]);
    }
}

/* -------------------------------------------------------------------------- */
/* NEW: USB send function (for sensor data to Raspberry Pi) */
void usb_send_data(const uint8_t *data, size_t len)
{
    if (!device_is_ready(usb_dev)) {
        printk("USB device not ready!\n");
        return;
    }

    if (!usb_ready) {
        printk("USB not enumerated yet\n");
        return;
    }

    for (size_t i = 0; i < len; i++) {
        uart_poll_out(usb_dev, data[i]);
    }
}

/* -------------------------------------------------------------------------- */
/* NEW: USB receive interrupt handler (for commands from Raspberry Pi) */
static void usb_rx_handler(const struct device *dev, void *user_data)
{
    uint8_t c;

    while (uart_irq_update(dev) && uart_irq_rx_ready(dev)) {
        int recv_len = uart_fifo_read(dev, &c, 1);
        if (recv_len <= 0)
            continue;

        /* End of command (newline or carriage return) */
        if (c == '\n' || c == '\r') {
            if (usb_rx_len > 0) {
                usb_rx_buf[usb_rx_len] = '\0';
                process_usb_command(usb_rx_buf);
                usb_rx_len = 0;
            }
        } else if (usb_rx_len < USB_RX_BUF_SIZE - 1) {
            usb_rx_buf[usb_rx_len++] = (char)c;
        }
    }
}

/* -------------------------------------------------------------------------- */
/* NEW: Parse commands sent from Raspberry Pi */
static void process_usb_command(char *cmd)
{
    printk("USB RX command: %s\n", cmd);

    /* WL_ADD command - adds to manual whitelist */
    if (strncmp(cmd, "WL_ADD ", 7) == 0) {
        char *mac_str = cmd + 7;
        
        /* Validate MAC format */
        if (strlen(mac_str) < 17) {
            printk("Invalid MAC format: %s (too short)\n", mac_str);
            return;
        }
        
        /* Extract just first 17 chars in case of trailing whitespace */
        char mac_clean[18];
        strncpy(mac_clean, mac_str, 17);
        mac_clean[17] = '\0';
        
        add_mac_to_manual_whitelist(mac_clean);
    } 
    /* WL_DEL command - removes from manual whitelist */
    else if (strncmp(cmd, "WL_DEL ", 7) == 0) {
        char *mac_str = cmd + 7;
        
        /* Validate MAC format */
        if (strlen(mac_str) < 17) {
            printk("Invalid MAC format: %s (too short)\n", mac_str);
            return;
        }
        
        /* Extract just first 17 chars */
        char mac_clean[18];
        strncpy(mac_clean, mac_str, 17);
        mac_clean[17] = '\0';
        
        remove_mac_from_manual_whitelist(mac_clean);
    }
    /* DC command - disconnect */
    else if (strncmp(cmd, "DC ", 3) == 0) {
        char *mac_str = cmd + 3;
        
        /* Validate MAC format */
        if (strlen(mac_str) < 17) {
            printk("Invalid MAC format: %s (too short)\n", mac_str);
            return;
        }
        
        /* Extract first 17 chars */
        char mac_clean[18];
        strncpy(mac_clean, mac_str, 17);
        mac_clean[17] = '\0';
        
        seeed_conn_t* conn = find_node_by_mac_addr(mac_clean);
        if(conn){
            bt_conn_disconnect(conn->conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
            printk("Disconnecting device %s\n", mac_clean);
        } else{
            printk("Device (%s) not connected!\n", mac_clean);
        }
    } 
    else {
        printk("Unknown command: %s\n", cmd);
    }
}

/* -------------------------------------------------------------------------- */
/* BLE Connection Management Functions (unchanged) */
void on_ble_connected(struct bt_conn *conn, char* addr)
{
    for (int i = 0; i < MAX_SEEED_CONN; i++) {
        if (!seeed_nodes[i].active) {
            seeed_nodes[i].conn = conn;
            seeed_nodes[i].active = true;
            memset(&seeed_nodes[i].data, 0, sizeof(sensor_packet_t));

            strncpy(seeed_nodes[i].data.device_addr, addr, sizeof(seeed_nodes[i].data.device_addr));
            seeed_nodes[i].data.device_addr[sizeof(seeed_nodes[i].data.device_addr) - 1] = '\0';
            printk("Seeed node connected (slot %d)\n", i);
            return;
        }
    }

    printk("No available slot for new Seeed connection!\n");
}

void on_ble_disconnected(struct bt_conn *conn)
{
    for (int i = 0; i < MAX_SEEED_CONN; i++) {
        if (seeed_nodes[i].conn == conn) {
            seeed_nodes[i].active = false;
            seeed_nodes[i].conn = NULL;
            printk("Seeed node disconnected (slot %d)\n", i);
            return;
        }
    }
}

seeed_conn_t *find_node_by_conn(struct bt_conn *conn)
{
    for (int i = 0; i < MAX_SEEED_CONN; i++) {
        if (seeed_nodes[i].active && seeed_nodes[i].conn == conn)
            return &seeed_nodes[i];
    }
    return NULL;
}

seeed_conn_t *find_node_by_mac_addr(char* addr)
{
    if (addr == NULL) {
        return NULL;
    }
    
    for (int i = 0; i < MAX_SEEED_CONN; i++) {
        if (seeed_nodes[i].active &&  
            strncmp(seeed_nodes[i].data.device_addr, addr, 17) == 0) {
            return &seeed_nodes[i];
        }
    }

    return NULL;
}

/* -------------------------------------------------------------------------- */
/* Send packet over USB (for data) and optionally UART (for debug) */
void try_send_packet(seeed_conn_t *node)
{
    if (!node || !node->active)
        return;

    uint8_t ready_mask = 0;
    if (node->a_ready) ready_mask |= BIT(0);
    if (node->b_ready) ready_mask |= BIT(1);
    if (node->c_ready) ready_mask |= BIT(2);

    /* Only send when *all subscribed fields* are ready */
    if ((ready_mask & node->subscribed_mask) != node->subscribed_mask)
        return;

    /* Build payload dynamically: [device_addr (30 bytes)] [field id(s) + value(s)] */
    uint8_t payload[48]; /* 30 + (1+4)+(1+2)+(1+2) max comfortably fits */
    size_t offset = 0;

    /* device_addr: 30 bytes, null-padded */
    memset(payload, 0, 30);
    size_t copy_len = strnlen(node->data.device_addr, sizeof(node->data.device_addr));
    if (copy_len > 30) copy_len = 30;
    memcpy(payload, node->data.device_addr, copy_len);
    offset += 30;

    /* Add subscribed fields in fixed order A,B,C */
    if (node->subscribed_mask & BIT(0)) {
        payload[offset++] = 0x01; /* field id A */
        memcpy(&payload[offset], &node->data.value_a, sizeof(node->data.value_a));
        offset += sizeof(node->data.value_a);
    }
    if (node->subscribed_mask & BIT(1)) {
        payload[offset++] = 0x02; /* field id B */
        memcpy(&payload[offset], &node->data.value_b, sizeof(node->data.value_b));
        offset += sizeof(node->data.value_b);
    }
    if (node->subscribed_mask & BIT(2)) {
        payload[offset++] = 0x03; /* field id C */
        memcpy(&payload[offset], &node->data.value_c, sizeof(node->data.value_c));
        offset += sizeof(node->data.value_c);
    }

    /* Send as a single framed USB packet (type = sensor) */
    usb_send_framed(PKT_TYPE_SENSOR, payload, offset);
    printk("USB sent sensor packet (payload %zu bytes) for %s\n\n", offset, node->data.device_addr);

    /* Reset ready flags for subscribed fields */
    if (node->subscribed_mask & BIT(0)) node->a_ready = false;
    if (node->subscribed_mask & BIT(1)) node->b_ready = false;
    if (node->subscribed_mask & BIT(2)) node->c_ready = false;
}

/* -------------------------------------------------------------------------- */
/* BLE notification handling (unchanged) */
void ble_value_a_received(struct bt_conn *conn, int16_t val)
{
    seeed_conn_t *node = find_node_by_conn(conn);
    if (!node) return;

    node->data.value_a = val;
    node->a_ready = true;
    try_send_packet(node);
}

void ble_value_b_received(struct bt_conn *conn, uint32_t val)
{
    seeed_conn_t *node = find_node_by_conn(conn);
    if (!node) return;

    node->data.value_b = val;
    node->b_ready = true;
    try_send_packet(node);
}

void ble_value_c_received(struct bt_conn *conn, uint16_t val)
{
    seeed_conn_t *node = find_node_by_conn(conn);
    if (!node) return;

    node->data.value_c = val;
    node->c_ready = true;
    try_send_packet(node);
}

/* ---------- Framing helper (poll-based, single buffer, <=64 bytes) ---------- */
void usb_send_framed(uint8_t type, const uint8_t *payload, size_t len)
{
    if (!device_is_ready(usb_dev) || !usb_ready) {
        printk("usb_send_framed(): USB not ready\n");
        return;
    }

    /* total bytes on wire = 1(start) +1(type)+1(len) + len(payload) +1(checksum)+1(end) */
    if (len + 5 > MAX_USB_PKT_LEN) {
        printk("usb_send_framed(): payload too large (%zu bytes) - max payload %d\n",
               len, MAX_USB_PKT_LEN - 5);
        return;
    }

    uint8_t packet[MAX_USB_PKT_LEN];
    size_t pkt_len = 0;

    packet[pkt_len++] = PKT_START;
    packet[pkt_len++] = type;
    packet[pkt_len++] = (uint8_t)len;

    if (len > 0 && payload != NULL) {
        memcpy(&packet[pkt_len], payload, len);
        pkt_len += len;
    }

    uint8_t checksum = 0;
    for (size_t i = 0; i < len; i++) {
        checksum ^= payload[i];
    }

    packet[pkt_len++] = checksum;
    packet[pkt_len++] = PKT_END;

    /* Send the whole packet synchronously via uart_poll_out (keeps within one USB frame) */
    for (size_t i = 0; i < pkt_len; i++) {
        uart_poll_out(usb_dev, packet[i]);
    }
}

/* Call this when you want to send a single-device RSSI report */
void send_rssi_report(const char *mac17, int8_t rssi, uint8_t connected_flag)
{
    rssi_packet_t pkt;
    memset(&pkt, 0, sizeof(pkt));
    size_t copy_len = strnlen(mac17, 17);
    if (copy_len > 29) copy_len = 29;
    memcpy(pkt.mac_addr, mac17, copy_len);
    pkt.mac_addr[copy_len] = '\0';
    pkt.rssi = (int8_t)rssi;
    pkt.connected = connected_flag ? 1 : 0;

    /* Payload is exactly sizeof(rssi_packet_t) == 32 bytes (30+1+1) */
    usb_send_framed(PKT_TYPE_TEST, (const uint8_t *)&pkt, sizeof(pkt));
    printk("[BEACON] Sent RSSI report: %s rssi=%d connected=%d\n\n", pkt.mac_addr, pkt.rssi, pkt.connected);
}