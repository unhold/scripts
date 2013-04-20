#!/bin/sh

FIREFOX_DIR=PortableApps/FirefoxPortable/Data/profile
FIREFOX_PRO=~/.mozilla/firefox/14fd2nuh.default

if [ -h "${FIREFOX_PRO}/lock" ]; then
	echo "ERROR: Firefox seems to be open"
	sleep 3
	exit 1
fi

#mv "${FIREFOX_DIR}" "${FIREFOX_DIR}_backup"
#cp -r "${FIREFOX_PRO}" "${FIREFOX_DIR}"
#rm -rf "${FIREFOX_DIR}_backup"
rsync -vrLt -delete "${FIREFOX_PRO}/" "${FIREFOX_DIR}"

THUNDERBIRD_DIR=PortableApps/ThunderbirdPortable/Data/profile
THUNDERBIRD_PRO=~/.mozilla-thunderbird/apcr6pef.default

if [ -h "${THUNDERBIRD_PRO}/lock" ]; then
	echo "ERROR: Thunderbird seems to be open"
	sleep 3
	exit 2
fi

#mv "${THUNDERBIRD_DIR}" "${THUNDERBIRD_DIR}_backup"
#cp -r "${THUNDERBIRD_PRO}" "${THUNDERBIRD_DIR}"
#rm -rf "${THUNDERBIRD_DIR}_backup"
rsync -vrlt -delete "${THUNDERBIRD_PRO}/" "${THUNDERBIRD_DIR}"

echo "Profile copy done"
sleep 5
exit 0

