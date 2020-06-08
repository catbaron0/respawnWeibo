set -eu
python3 respawn.py -f ../Weibo/cached/68.txt -u 185043090 -c 8
for i in $(seq 67 -1 1)
do
    echo '------ '$i '.txt ------'
    python3 respawn.py -f ../Weibo/cached/$i.txt -s sender.sess -u 185043090
done
