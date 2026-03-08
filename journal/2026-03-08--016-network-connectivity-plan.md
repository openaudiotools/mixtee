# Network Connectivity Plan (v1)

**Date:** 2026-03-08

## Summary

Drafted and documented the Teensy Network Connectivity Plan (v1) for MIXTEE and related devices (synths, controllers, hubs). The plan covers:

- Common network stack (IPv4/UDP, DHCP + link-local fallback)
- mDNS/DNS-SD discovery with `_jfa-audio._udp` and `_jfa-midi2._udp` service types
- PTP (IEEE 1588v2) time sync with mixer as grandmaster
- RTP audio streaming (AES67-style: 48 kHz, 24-bit, 1 ms packets)
- Network MIDI 2.0 (UDP + UMP)
- Patchbay "brain" for routing (runs on mixer/hub)

## Feasibility Assessment

| Resource | Used | Available | Verdict |
|----------|------|-----------|---------|
| CPU | ~40% (30% audio + 10% network) | ~60% headroom | OK |
| Ethernet bandwidth | ~18.4 Mbps (16ch RTP) | 100 Mbps link | OK |
| PSRAM | ~2 MB (recording) | ~6 MB for network buffers | OK |
| GPIO | 0 additional needed | 6 spare pins | OK |

**Key caveat:** PTP limited to ~10-100 us accuracy (software timestamping only; DP83825I PHY lacks hardware PTP support). Sufficient for studio use with 1 ms packet buffers.

## Files

- Created: `docs/network-connectivity.md`
