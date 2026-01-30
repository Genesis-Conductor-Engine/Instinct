#include <tunables/global>

profile aios-agent flags=(attach_disconnected) {
  #include <abstractions/base>
  network inet,
  network inet6,
  capability net_bind_service,
  capability chown,
  capability setgid,
  capability setuid,
  file,
  /usr/local/bin/aios-agent ix,
  /etc/aios/aios.yaml r,
  /var/log/aios/** rw,
  /var/lib/aios/** rw,
  deny /proc/kcore rwklx,
}
