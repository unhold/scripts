#!/bin/bash
# verify bzip-compressed file against disk image

zimage="$1"
disk="$2"

size=$(zcat "$zimage" | wc -c)
if [ -e "$disk" -a ! -r "$disk" ] ; then sudo=sudo ; else sudo= ; fi
diff <(zcat "$zimage") <($sudo dd if="$disk" bs=1M | head -c $size) >/dev/null
status=$?
[ $status == 0 ] || echo "zimgverify failed ($status)"
exit $status
