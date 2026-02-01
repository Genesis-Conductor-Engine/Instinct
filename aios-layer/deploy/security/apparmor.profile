#include <tunables/global>

profile aios-agent flags=(attach_disconnected) {
  #include <abstractions/base>
  network inet stream,
  network inet6 stream,
  /usr/local/bin/aios-agent ix,
  /etc/aios/aios.yaml r,
  /var/run/docker.sock rw,
  /tmp/** rw,
  deny /** wklx,
}
