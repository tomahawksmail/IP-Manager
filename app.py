from flask import Flask, render_template, request
import ipaddress
from collections import defaultdict
import os

app = Flask(__name__)

BLACKLIST_FILE = 'blacklist.txt'
WHITELIST_FILE = 'whitelist.txt'

port = 5061

def load_ips(file):
    if not os.path.exists(file):
        return []
    with open(file, 'r') as f:
        return sorted(
            set(str(ipaddress.ip_network(line.strip(), strict=False))
                for line in f if line.strip()),
            key=lambda ip: ipaddress.ip_network(ip)
        )

def save_ips(file, ips):
    with open(file, 'w') as f:
        for ip in sorted(ips, key=lambda ip: ipaddress.ip_network(ip)):
            f.write(f"{ip}\n")

def group_by_first_octet(ips):
    groups = defaultdict(list)
    for ip in ips:
        first_octet = ip.split('.')[0]
        groups[first_octet].append(ip)
    for k in groups:
        groups[k] = sorted(groups[k], key=lambda ip: ipaddress.ip_network(ip))
    return dict(sorted(groups.items(), key=lambda item: int(item[0])))

@app.route("/", methods=["GET", "POST"])
def index():
    message = ''
    found_ip = None
    found_matches = []
    tab = request.args.get('tab', 'black')

    blacklist = load_ips(BLACKLIST_FILE)
    whitelist = load_ips(WHITELIST_FILE)

    if request.method == "POST":
        action = request.form.get('action')
        ip_raw = request.form.get('ip', '').strip()
        tab = request.form.get('tab', 'black')

        file = BLACKLIST_FILE if tab == 'black' else WHITELIST_FILE
        ip_list = blacklist if tab == 'black' else whitelist

        if not ip_raw:
            message = "⚠️ IP/Network cannot be empty."
        else:
            if action == "find":
                raw = ip_raw.replace(' ', '').lower()
                matched = []

                # Determine if it's a valid IP (not network)
                try:
                    test_ip = ipaddress.ip_address(raw)
                    is_ip = True
                except ValueError:
                    is_ip = False

                for entry in ip_list:
                    net = ipaddress.ip_network(entry, strict=False)
                    base = entry.split('/')[0].lower()
                    if is_ip:
                        if test_ip in net:
                            matched.append(entry)
                    else:
                        if raw in base:
                            matched.append(entry)

                if matched:
                    message = f"✅ Found {len(matched)} match(es) for '{ip_raw}' in {tab}list."
                    found_ip = matched[0]
                    found_matches = matched
                else:
                    message = f"❌ No matches found for '{ip_raw}' in {tab}list."

            elif action == "add":
                try:
                    valid_ip = str(ipaddress.ip_network(ip_raw if '/' in ip_raw else ip_raw + '/32', strict=False))
                except ValueError:
                    message = f"❌ Invalid IP/network: '{ip_raw}'"
                else:
                    if valid_ip in ip_list:
                        message = f"⚠️ Network {valid_ip} already exists in {tab}list."
                    else:
                        ip_list.append(valid_ip)
                        save_ips(file, ip_list)
                        message = f"✅ Network {valid_ip} added to {tab}list."

            elif action == "delete":
                try:
                    valid_ip = str(ipaddress.ip_network(ip_raw if '/' in ip_raw else ip_raw + '/32', strict=False))
                except ValueError:
                    message = f"❌ Invalid IP/network: '{ip_raw}'"
                else:
                    if valid_ip in ip_list:
                        ip_list.remove(valid_ip)
                        save_ips(file, ip_list)
                        message = f"🗑️ Network {valid_ip} removed from {tab}list."
                    else:
                        message = f"❌ Network {valid_ip} not found for deletion."

    grouped_blacklist = group_by_first_octet(blacklist)
    grouped_whitelist = group_by_first_octet(whitelist)

    return render_template("index.html",
        tab=tab,
        message=message,
        found_ip=found_ip,
        found_matches=found_matches,
        grouped_blacklist=grouped_blacklist,
        grouped_whitelist=grouped_whitelist
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)
