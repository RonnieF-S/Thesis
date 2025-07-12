// serial_test.ino 
// This sketch is designed to test Serial2 communication with a Raspberry Pi. 
// Use a serial terminal on the pi to send messages.
// Ensure that the USB cable of the Heltec board is disconnected to avoid interference.

#include "heltec.h"
#include "HT_SSD1306Wire.h"

// OLED setup
static SSD1306Wire display(0x3C, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED);

void VextON() {
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW);
}

void setup() {
  // NO USB Serial - only Serial2 for Pi communication
  // Hardware Serial2 for Pi communication (Tx=43, Rx=44)
  Serial2.begin(115200, SERIAL_8N1, 44, 43);  // RX, TX
  
  VextON();
  delay(100);

  // Initialize display
  display.init();
  display.setFont(ArialMT_Plain_16);
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.clear();
  display.drawString(0, 0, "Pi Only Test");
  display.drawString(0, 16, "No USB Serial");
  display.drawString(0, 32, "Ready!");
  display.display();
}

void loop() {
  // Check for data from Pi (Serial2) - MAIN FUNCTION
  if (Serial2.available()) {
    String receivedData = Serial2.readStringUntil('\n');
    receivedData.trim();
    
    if (receivedData.length() > 0) {
      // Update OLED display
      display.clear();
      display.drawString(0, 0, "FROM PI:");
      display.drawString(0, 16, receivedData.substring(0, 10)); // First 10 chars
      display.drawString(0, 32, "Echoing back...");
      display.display();
      
      // Echo back to Pi with prefix
      Serial2.println("ECHO: " + receivedData);
      
      delay(1000); // Show message longer
    }
  }
  
  // Show status every 3 seconds when idle
  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > 3000) {
    display.clear();
    display.drawString(0, 0, "Waiting for");
    display.drawString(0, 16, "Pi messages");
    display.drawString(0, 32, "on Serial2...");
    display.display();
    
    lastStatusUpdate = millis();
  }
}
