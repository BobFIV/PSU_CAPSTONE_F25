#include <NimBLEDevice.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <esp_system.h>   // put at top of file
#include <esp_mac.h>


Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// BLE UUIDs
#define SERVICE_UUID        "181A"  // Environmental Sensing Service
#define TEMP_CHAR_UUID      "2A6E"  // Temperature characteristic

NimBLECharacteristic *tempCharacteristic;

#define TEMP_UPDATE_INTERVAL 1000
unsigned long lastUpdate = 0;

// ======== BLE SERVER CALLBACKS ========
class MyServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        Serial.println("✅ Central connected");
    }

    void onDisconnect(NimBLEServer* pServer) {
        Serial.println("❌ Central disconnected — restarting advertising");
        NimBLEDevice::startAdvertising();
    }
};

// ======== BLE SETUP ========
void setupBLE() {
    Serial.println("Initializing BLE...");

    NimBLEDevice::init("ESP32_Temp_Sensor");
    NimBLEServer *pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create the Environmental Sensing Service
    NimBLEService *essService = pServer->createService(SERVICE_UUID);

    // Temperature characteristic (read + notify)
    tempCharacteristic = essService->createCharacteristic(
        TEMP_CHAR_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );

    tempCharacteristic->createDescriptor("2901")->setValue("Temperature (°C)");

    // Start service
    essService->start();

    // Setup advertising
    NimBLEAdvertising *pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setName("ESP32_Temp_Sensor");
    // Fallback: if setScanResponse() doesn’t exist, skip it
    // #if defined(CONFIG_BT_NIMBLE_EXT_ADV) || defined(CONFIG_BT_NIMBLE_ENABLED)
    //     pAdvertising->setScanResponseData(true);
    // #endif
    pAdvertising->start();

    Serial.println("📡 Advertising started...");
}

// ======== SENSOR SETUP ========
void setupSensor() {
    Serial.println("Initializing MLX90614...");
    Wire.begin(8, 9);  // SDA=8, SCL=9
    if (!mlx.begin()) {
        Serial.println("❌ MLX90614 not found. Check wiring!");
        while (1) delay(1000);
    }
    Serial.println("✅ MLX90614 ready!");
}

// ======== MAIN ========
void setup() {
    Serial.begin(115200);
    delay(500);
    // Print the BLE MAC address
    printBTMac();
    setupSensor();
    setupBLE();
}

void loop() {
    unsigned long now = millis();
    if (now - lastUpdate >= TEMP_UPDATE_INTERVAL) {
        lastUpdate = now;

        float tempC = mlx.readObjectTempC();
        int16_t tempFixed = (int16_t)(tempC * 100);  // BLE uses 0.01°C units

        Serial.printf("🌡️  Temp = %.2f°C\n", tempC);

        // Notify central if connected
        if (NimBLEDevice::getServer()->getConnectedCount() > 0) {
            tempCharacteristic->setValue((uint8_t*)&tempFixed, sizeof(tempFixed));
            tempCharacteristic->notify();
            Serial.println("🔔 Sent temperature notification");
        }
    }
    delay(1000);
}



void printBTMac() {
    uint8_t mac[6];
    esp_err_t res = esp_read_mac(mac, ESP_MAC_BT); // ESP_MAC_BT for controller (BLE/BT)
    if (res == ESP_OK) {
        char macStr[18];
        snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
                 mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        Serial.print("Bluetooth MAC (esp_read_mac): ");
        Serial.println(macStr);
    } else {
        Serial.printf("esp_read_mac failed: %d\n", res);
    }
}