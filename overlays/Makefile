DTC=dtc

all: spi0-3cs.dtbo mcp2515-can2.dtbo

spi0-3cs.dtbo: spi0-3cs-overlay.dts
	$(DTC) -@ -I dts -O dtb -o $@ $<

mcp2515-can2.dtbo: mcp2515-can2-overlay.dts
	$(DTC) -@ -I dts -O dtb -o $@ $<
	
install: all
	install -o root spi0-3cs.dtbo /boot/overlays
	install -o root mcp2515-can2.dtbo /boot/overlays
	install -o root can0.interface /etc/network/interfaces.d/can0
	# enable i2c and spi in config.txt
	# assume that a rejected patch means that the changes were already applied
	patch -p0 -f -d /boot < config.txt.0.diff || true
	# add custom pins for spi0.2
	# here, check whether the patch was already applied
	grep -q \
		'### LINES NEEDED BY SH-RPI-DAEMON ###' \
		/boot/config.txt \
		|| patch -p0 -f -d /boot < config.txt.1.diff
	# load the i2c module at boot time
	patch -p0 -f -d /etc < modules.0.diff || true

uninstall:
	rm -f /boot/overlays/spi0-3cs.dtbo /boot/overlays/mcp2515-can2.dtbo
	patch -p0 -R -f -d /boot < config.txt.0.diff || true
	patch -p0 -R -f -d /boot < config.txt.1.diff || true

clean:
	rm -f *.dtbo

.PHONY: all install uninstall clean
