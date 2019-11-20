export QT_QPA_PLATFORM='offscreen'
dir=`dirname $0`
python3 $dir/rfid_adapter.py -p /dev/ttyUSB0
