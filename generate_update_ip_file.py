import os
import sys

str_file = """#!/bin/bash


### BEGIN INIT INFO
# Provides: update_ip.sh
# Required-Start: $network $remote_fs $local_fs
# Required-Stop: $network $remote_fs $local_fs
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: update_ip
# Description: update_ip
### END INIT INFO

# Forked from benkulbertis/cloudflare-update-record.sh
# CHANGE THESE

# Global API Key (Deprecated + Dangerous)
# Note: Please be caution as the Global API key can have unlimited access to **all** domain and features in your account.
auth_email="key_mail"            # The email used to login 'https://dash.cloudflare.com'
auth_key="key_auth_key"   # Top right corner, "My profile" > "Global API Key"

# API Token (Recommended)
#####                                                                             #####
# WARNING: If you put any value inside the API Token variable,                        #
#            the script will automatically use the token and omit the Global API key, #
#            regardless if the Global API key is defined or not.                      #
#####                                                                             #####
auth_token="key_auth_token"

# Domain and DNS record for synchronization
zone_identifier="key_zone" # Can be found in the "Overview" tab of your domain
record_name="key_record"                     # Which record you want to be synced

# DO NOT CHANGE LINES BELOW

# SCRIPT START
echo -e "Check Initiated"

# Check for current external network IP
ip=$(curl -s4 https://icanhazip.com/)
if [[ ! -z "${ip}" ]]; then
  echo -e "  > Fetched current external network IP: ${ip}"
else
  >&2 echo -e "Network error, cannot fetch external network IP."
fi

# The execution of update
if [[ ! -z "${auth_token}" ]]; then
  header_auth_paramheader=( -H '"Authorization: Bearer '${auth_token}'"' )
else
  header_auth_paramheader=( -H '"X-Auth-Email: '${auth_email}'"' -H '"X-Auth-Key: '${auth_key}'"' )
fi

# Seek for the record
seek_current_dns_value_cmd=( curl -s -X GET '"https://api.cloudflare.com/client/v4/zones/'${zone_identifier}'/dns_records?name='${record_name}'&type=A"' "${header_auth_paramheader[@]}" -H '"Content-Type: application/json"' )
record=`eval ${seek_current_dns_value_cmd[@]}`

# Can't do anything without the record
if [[ -z "${record}" ]]; then
  >&2 echo -e "Network error, cannot fetch DNS record."
  exit 1
elif [[ "${record}" == *'"count":0'* ]]; then
  >&2 echo -e "Record does not exist, perhaps create one first?"
  exit 1
fi

# Set the record identifier from result
record_identifier=`echo "${record}" | sed 's/.*"id":"//;s/".*//'`

# Set existing IP address from the fetched record
old_ip=`echo "${record}" | sed 's/.*"content":"//;s/".*//'`
echo -e "  > Fetched current DNS record value   : ${old_ip}"

# Compare if they're the same
if [ "${ip}" == "${old_ip}" ]; then
  echo -e "Update for A record '${record_name} (${record_identifier})' cancelled.\n  Reason: IP has not changed."
  exit 0
else
  echo -e "  > Different IP addresses detected, synchronizing..."
fi

# The secret sause for executing the update
json_data_v4="'"'{"id":"'${zone_identifier}'","type":"A","proxied":false,"name":"'${record_name}'","content":"'${ip}'","ttl":120}'"'"
update_cmd=( curl -s -X PUT '"https://api.cloudflare.com/client/v4/zones/'${zone_identifier}'/dns_records/'${record_identifier}'"' "${header_auth_paramheader[@]}" -H '"Content-Type: application/json"' )

# Execution result
update=`eval ${update_cmd[@]} --data $json_data_v4`

# The moment of truth
case "$update" in
*'"success":true'*)
  echo -e "Update for A record '${record_name} (${record_identifier})' succeeded.\n  - Old value: ${old_ip}\n  + New value: ${ip}";;
*)
  >&2 echo -e "Update for A record '${record_name} (${record_identifier})' failed.\nDUMPING RESULTS:\n${update}"
  exit 1;;
esac"""

os.chdir("/etc/init.d/")

key_mail = sys.argv[1]
key_auth_key = sys.argv[2]
key_auth_token = sys.argv[3]
key_zone = sys.argv[4]
key_record = sys.argv[5]


with open("update_ip.sh", "w") as f:
    f.write(
        str_file.replace("key_mail", key_mail)
        .replace("key_auth_key", key_auth_key)
        .replace("key_auth_token", key_auth_token)
        .replace("key_zone", key_zone)
        .replace("key_record", key_record)
    )
os.system("chmod +x update_ip.sh")
os.system("update-rc.d update_ip.sh defaults")
