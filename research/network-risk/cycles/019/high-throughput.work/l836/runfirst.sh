cd /home/user/v4-core/research/network-risk/cycles/019/high-throughput.work
while read h b; do [ -s l836/first-143-$h.json ] || timeout 900 python3 firstpm.py 143 https://rpc-mainnet.monadinfra.com $h l836/first-143-$h.json > /dev/null 2>> l836/first-err.txt; done < l836/jobs-143.txt &
while read h b; do [ -s l836/first-4326-$h.json ] || timeout 900 python3 firstpm.py 4326 https://mainnet.megaeth.com/rpc $h l836/first-4326-$h.json > /dev/null 2>> l836/first-err.txt; done < l836/jobs-4326.txt &
wait; echo done > l836/first-done
