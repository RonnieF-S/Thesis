/*
 * Heltec WiFi LoRa 32 V3.2 Firmware
 * Simple LoRa bridge: UART <-> LoRa RF
 * 
 * This firmware acts as a transparent bridge between the Raspberry Pi
 * and the LoRa radio. It simply forwards data between UART and LoRa.
 * 
 * Hardware: Heltec WiFi LoRa 32 V3.2 (ESP32-S3 + SX1262)
 * Author: Ronnie Fellows-Smith
 */

#include <Arduino.h>
#include <RadioLib.h>
#include "heltec.h"
#include "HT_SSD1306Wire.h"

// OLED setup
static SSD1306Wire display(0x3C, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED);

// LoRa pin definitions
#define LORA_CS   8
#define LORA_RST  12
#define LORA_BUSY 13
#define LORA_DIO1 14

SX1262 lora = new Module(LORA_CS, LORA_DIO1, LORA_RST, LORA_BUSY);

void VextON() {
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW);
}

void drawWrappedString(SSD1306Wire &display, const String &msg, int x = 0, int y = 0, int lineHeight = 16, int maxWidth = 128) {
  display.setFont(ArialMT_Plain_16);
  display.setTextAlignment(TEXT_ALIGN_LEFT);

  int lineY = y;
  String line = "";
  for (int i = 0; i < msg.length(); i++) {
    line += msg[i];
    if (display.getStringWidth(line) > maxWidth) {
      display.drawString(x, lineY, line.substring(0, line.length() - 1));
      lineY += lineHeight;
      line = msg[i];
    }
  }
  if (line.length() > 0) {
    display.drawString(x, lineY, line);
  }
}

void setup() {
  Serial.begin(115200);
  VextON();
  delay(100);

  display.init();
  display.setFont(ArialMT_Plain_16);
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.clear();
  display.drawString(0, 0, "LoRa RX Init...");
  display.display();

  if (lora.begin(915.0) == RADIOLIB_ERR_NONE) {
    lora.setSpreadingFactor(9);
    display.drawString(0, 20, "LoRa Ready");
  } else {
    display.drawString(0, 20, "LoRa Fail");
    display.display();
    while (true);
  }

  display.display();
}

void loop() {
  String incoming;
  int state = lora.receive(incoming);

  display.clear();
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("[RX OK] " + incoming);
    display.drawString(0, 0, "RX OK:");
    drawWrappedString(display, incoming, 0, 20);

    String reply = "Hello World!";

    // Pause and send response
    lora.standby();   // Switch to standby before sending
    delay(10);
    int txState = lora.transmit(reply);

    if (txState == RADIOLIB_ERR_NONE) {
      Serial.println("[TX OK] " + reply);
      display.drawString(0, 48, "Reply Sent");
    } else {
      Serial.print("[TX FAIL] ");
      Serial.println(txState);
      display.drawString(0, 48, "Reply Fail");
    }

    // Return to receive mode
    delay(10);
    lora.startReceive();

  } else if (state != RADIOLIB_ERR_RX_TIMEOUT) {
    Serial.print("[RX FAIL] ");
    Serial.println(state);
    display.drawString(0, 0, "RX Error");
  } else {
    display.drawString(0, 0, "Waiting...");
  }

  display.display();
}
