#!/bin/bash

#Wipe old socat connections
killall socat
echo "Terminated previous Socat opps"

# Start socat in background and redirect output
socat -d -d PTY,link=/tmp/tty.ms41logger,raw,echo=0 \
             PTY,link=/tmp/tty.ms41emu,raw,echo=0 \
             > /tmp/socat.log 2>&1 &

# Wait a moment for symlinks to be created
sleep 1

# Check that symlinks exist
if [[ -e /tmp/tty.ms41emu && -e /tmp/tty.ms41logger ]]; then
  echo "Virtual serial ports created:"
  echo "  Logger => /tmp/tty.ms41logger"
  echo "  Emulator => /tmp/tty.ms41emu"
else
  echo "❌ socat failed to create PTYs. Exiting."
  exit 1
fi

# Run your emulator
python3 MS41_Emulator.py

