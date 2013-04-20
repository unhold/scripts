NAME="${1%.m3u}"

echo "$NAME"

mkdir "$NAME.copy_m3u"

cat "${NAME}.m3u" | while read LINE
do
	FILE=`basename "$LINE"`
	cp -l "$LINE" "$NAME.copy_m3u"/"$FILE"
	echo "$FILE" >> "$NAME.copy_m3u"/"$NAME".m3u
done

