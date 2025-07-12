#!/bin/bash
# Raspberry Pi UART Configuration Script
# Run this on both UAV and Ground Station Raspberry Pi systems

echo "Configuring Raspberry Pi UART for LoRa communication..."

# Backup original config
sudo cp /boot/config.txt /boot/config.txt.backup

# Enable UART
echo "Enabling UART..."
echo "enable_uart=1" | sudo tee -a /boot/config.txt

# Enable additional UART ports
echo "Enabling UART2 and UART5..."
echo "dtoverlay=uart2" | sudo tee -a /boot/config.txt
echo "dtoverlay=uart5" | sudo tee -a /boot/config.txt

# Disable Bluetooth to free up UART (optional but recommended)
echo "Disabling Bluetooth to free up primary UART..."
echo "dtoverlay=disable-bt" | sudo tee -a /boot/config.txt

# Create symlinks for easier device access
echo "Creating device symlinks..."
sudo tee /etc/udev/rules.d/99-uart.rules > /dev/null << EOF
# UART device rules for UAV gas localization system
KERNEL=="ttyAMA2", SYMLINK+="lora", GROUP="dialout", MODE="0666"
KERNEL=="ttyAMA1", SYMLINK+="co2sensor", GROUP="dialout", MODE="0666"
KERNEL=="ttyAMA5", SYMLINK+="co2sensor", GROUP="dialout", MODE="0666"
EOF

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user pyserial numpy

echo "Configuration complete!"
echo "Please reboot the Raspberry Pi for changes to take effect."
echo ""
echo "After reboot, UART devices will be available as:"
echo "  /dev/lora -> LoRa module (UART2/3)"
echo "  /dev/co2sensor -> CO2 sensor (UART1/5)"
echo ""
echo "To reboot now, run: sudo reboot"
