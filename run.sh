dir=`dirname $0`
insmod $dir/cp210x.ko
export QT_QPA_PLATFORM='offscreen'
sleep 60
cd $dir
./rfid_adapter -p /dev/ttyUSB0
