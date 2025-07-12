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
  display.drawString(0, 0, "LoRa Bridge");
  display.drawString(0, 16, "Initializing...");
  display.display();

  if (lora.begin(915.0) == RADIOLIB_ERR_NONE) {
    lora.setSpreadingFactor(9);
    lora.setBandwidth(125.0);
    lora.setCodingRate(5);
    lora.setSyncWord(0x34);  // Private sync word
    
    // Start in receive mode
    lora.startReceive();
    
    display.clear();
    display.drawString(0, 0, "LoRa Bridge");
    display.drawString(0, 16, "Ready");
    display.drawString(0, 32, "Waiting...");
    display.display();
  } else {
    display.clear();
    display.drawString(0, 0, "LoRa Bridge");
    display.drawString(0, 16, "FAILED!");
    display.display();
    while (true);
  }
}

void loop() {
  // Check for incoming serial data from Pi
  if (Serial.available()) {
    String outgoingMessage = Serial.readStringUntil('\n');
    outgoingMessage.trim();
    
    if (outgoingMessage.length() > 0) {
      // Switch to transmit mode
      lora.standby();
      delay(5);
      
      // Transmit the message from Pi
      int txState = lora.transmit(outgoingMessage);
      
      if (txState == RADIOLIB_ERR_NONE) {
        // Update display
        display.clear();
        display.drawString(0, 0, "TX OK");
        drawWrappedString(display, outgoingMessage, 0, 16);
        display.display();
        delay(100);  // Brief display of TX status
      }
      
      // Return to receive mode
      lora.startReceive();
    }
  }
  
  // Check for incoming LoRa messages
  String incomingMessage;
  int rxState = lora.receive(incomingMessage);
  
  if (rxState == RADIOLIB_ERR_NONE) {
    // Message received successfully - send to Pi via Serial
    Serial.println(incomingMessage);
    
    // Update display
    display.clear();
    display.drawString(0, 0, "RX OK");
    drawWrappedString(display, incomingMessage, 0, 16);
    display.display();
    delay(100);  // Brief display of RX status
    
  } else if (rxState != RADIOLIB_ERR_RX_TIMEOUT) {
    // Handle receive errors (but not timeouts)
    display.clear();
    display.drawString(0, 0, "RX Error");
    display.drawString(0, 16, String(rxState));
    display.display();
    delay(100);
  }
  
  // Update display to show waiting status if no recent activity
  static unsigned long lastActivity = 0;
  if (millis() - lastActivity > 1000) {  // Update every second
    display.clear();
    display.drawString(0, 0, "LoRa Bridge");
    display.drawString(0, 16, "Ready");
    display.drawString(0, 32, "Listening...");
    display.display();
    lastActivity = millis();
  }
}
