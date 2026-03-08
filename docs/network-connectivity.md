# MIXTEE: Network Connectivity Plan (v1)

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [Firmware](firmware.md) · [System Topology](system-topology.md)*

------

## 1. Common network stack

- **Hardware**
  - Audio-capable boxes (synth, mixer, hub): Teensy 4.1 with native 100 M Ethernet (RMII PHY).
  - Control-only boxes (motorized controllers): cheaper Teensy + external MAC/PHY, same UDP/IP stack, no audio.
- **Network layer**
  - IPv4 only, single LAN, no routing.
  - UDP for audio, MIDI, discovery; TCP optional for config UI.

---

## 2. Addressing and naming

- **IP**
  - Use DHCP if available.
  - Fallback: IPv4 link-local (`169.254.x.x`) AutoIP when no DHCP.
- **Hostnames (via mDNS)**
  - `device-type-XXXX.local`, where `XXXX` is a short unique suffix (e.g. last 4 MAC hex digits).
  - Examples:
    - `synth-a3f2.local`
    - `mixer-01b7.local`
    - `ctrl-92cc.local`

---

## 3. Discovery (mDNS + DNS-SD)

### Service types

- Audio endpoints:
  - `_jfa-audio._udp.local`
- MIDI 2.0 endpoints:
  - `_jfa-midi2._udp.local`

### Service instance naming

- `Synth Out 1-2._jfa-audio._udp.local`
- `Mixer Main._jfa-audio._udp.local`
- `Main Controller._jfa-midi2._udp.local`

### TXT fields: `_jfa-audio._udp`

- `role=`: `synth` | `mixer` | `hub`
- `dir=`: `tx` | `rx` | `txrx`
- `ch=`: channel count (e.g. `2`, `8`, `16`)
- `sr=`: sample rate (e.g. `48000`)
- `fmt=`: `pcm24`
- `pkt=`: packet time in ms (e.g. `1`)
- `stream=`: short stream ID (`main`, `aux1`, `busA`, ...)

### TXT fields: `_jfa-midi2._udp`

- `dir=`: `in` | `out` | `inout`
- `ump=`: UMP version (e.g. `2.0`)
- `ep=`: endpoint role (`synth` | `mixer` | `ctrl` | `hub`)
- `ch=`: logical channel count or groups

Each Teensy:

- Registers its services at boot (mDNS/DNS-SD).
- Answers queries for its host/service names.
- Optionally browses for peers (for auto-pairing).

---

## 4. Time sync and audio clocking (audio devices)

- **PTP (IEEE 1588v2) on Teensy 4.1**
  - Use i.MX RT hardware timestamping.
  - One device (default: mixer) is PTP **grandmaster**.
  - Other audio devices are PTP slaves.
- **Audio profile**
  - 48 kHz, 24-bit PCM.
  - 1 ms packet time (48 samples/channel/packet).
  - RTP timestamps derived from PTP clock.

Control-only controllers: no PTP required.

---

## 5. Media transports

### Audio (Teensy 4.1 synth/mixer/hub)

- RTP over UDP, AES67-style fixed profile:
  - 48 kHz, 24-bit, 1 ms packets.
  - Fixed channel counts per stream (2 / 8 / 16).
- UDP ports:
  - Either static per-device (e.g. 50000 + stream index), or
  - Advertised in DNS-SD TXT or SRV records.
- Subscriptions:
  - Receiver uses sender IP + port + stream ID.
  - Multicast or unicast depending on design.

### MIDI 2.0 (all devices)

- Network MIDI 2.0 (UDP + UMP):
  - One UDP port per MIDI endpoint.
  - Endpoint port and name advertised via `_jfa-midi2._udp`.
  - Simple session model: once discovered, endpoints handshake and start UMP exchange.

---

## 6. Roles per device

### Virtual synth (Teensy)

- Publishes 1-N `_jfa-audio._udp` TX streams (main/aux outs).
- Publishes one `_jfa-midi2._udp` endpoint:
  - `dir=inout`, `ep=synth`.
- Optionally browses for controller `_jfa-midi2._udp` services.

### Digital mixer (Teensy 4.1)

- PTP grandmaster.
- Publishes multiple `_jfa-audio._udp`:
  - RX (inputs) and TX (buses/mains/auxes).
- Publishes `_jfa-midi2._udp` (IN/OUT) for full control.
- Optional small HTTP server at `http://mixer-XXXX.local/` for UI.

### MIDI/audio hub/interface

- Subscribes to selected audio streams from synth/mixer.
- Publishes `_jfa-audio._udp` TX if it exposes its own stream(s).
- Bridges Network MIDI 2.0 <-> DIN/USB, publishing `_jfa-midi2._udp` endpoints.

### Motorized-fader controller

- No audio, no PTP.
- Publishes one `_jfa-midi2._udp` endpoint (`ep=ctrl`, `dir=inout`).
- Browses for mixer `_jfa-midi2._udp` and pairs automatically or on user action.

---

## 7. Patchbay "brain"

- Runs on mixer or hub.
- Periodically browses `_jfa-audio._udp` and `_jfa-midi2._udp`.
- Builds in-RAM graph of devices and ports from TXT data.
- Exposes:
  - Simple web UI (HTTP/JSON + minimal HTML/JS), or
  - Simple OSC/JSON API.
- Applies routes by:
  - Opening/closing RTP sockets for audio subscriptions.
  - Initiating Network MIDI 2.0 sessions between chosen endpoints.

---

## 8. Security / isolation (v1)

- Assume trusted studio LAN.
- No auth, no encryption in v1.
- Keep all custom UDP ports in a documented, non-conflicting range (e.g. 50000-50100).
- Use a clear prefix for all custom service types (`_jfa-*`) to avoid clashes.

------

## Feasibility Assessment

*Based on analysis of MIXTEE hardware resources (Teensy 4.1 + DP83825I PHY).*

### Verdict: Fully feasible

The plan is well-matched to the Teensy 4.1 hardware. All proposed network services fit comfortably within available CPU, memory, and bandwidth.

### CPU Budget

| Task | CPU % |
|------|-------|
| Audio DSP (existing) | ~30% |
| RTP audio encode/decode | 1-3% |
| PTP software timestamping | 2-5% |
| mDNS/DNS-SD | <0.5% |
| MIDI 2.0 over UDP | <1% |
| UDP/IP stack (QNEthernet) | 2-3% |
| **Total** | **~40%** |

**~60% CPU headroom** remains after all network services.

### Bandwidth

- 16ch x 48 kHz x 24-bit = **18.4 Mbps** uncompressed RTP audio
- 100 Mbps Ethernet link provides ample headroom for audio + mDNS + MIDI + PTP
- 1 ms packet time (48 samples) matches AES67 standard

### Memory

- 8 MB PSRAM total, ~2 MB used for recording buffers
- **6 MB available** for RTP ring buffers, PTP logs, mDNS cache

### Network Audio Readiness

| Feature | Status | Notes |
|---------|--------|-------|
| Ethernet PHY | Ready | DP83825I on Teensy 4.1; 100 Mbps full-duplex |
| RTP Audio (AES67-style) | Ready | 18.4 Mbps << 100 Mbps link capacity |
| PTP Timestamping | Software-feasible | GPT @ 1 MHz (1 us); ~10-100 us accuracy; nanosecond PTP needs PHY with hardware support (not available on DP83825I) |
| mDNS / DNS-SD | Ready | Lightweight; ~0.5% CPU |
| MIDI 2.0 over RTP | Ready | AppleMIDI or custom RTP-MIDI; ~0.5-1% CPU |

### Caveats

1. **PTP accuracy is software-limited.** The DP83825I PHY has no hardware PTP timestamping. Achievable accuracy is ~10-100 us via Teensy's GPT timer in the RX ISR — sufficient for studio use with 1 ms packet times (48-sample buffer absorbs jitter), but not nanosecond-grade like a proper AES67 endpoint with a PTP-capable PHY (e.g., DP83640).

2. **Control-only boxes on cheaper Teensy + external MAC/PHY** — the library situation for SPI Ethernet (W5500, ENC28J60) is less mature for mDNS/PTP. Consider whether Teensy 4.1 across the board (~$30 each) simplifies development vs. mixed hardware.

3. **Multicast vs. unicast for RTP audio** — on a small studio LAN with <10 devices, unicast is simpler and avoids IGMP snooping headaches on consumer switches. Multicast becomes worthwhile only with multiple receivers per stream.

### Integration Architecture

```
Audio Callback (interrupt, ~2.67 ms):
  +-- TDM RX (SAI1/SAI2) -- Codecs -> memory
  +-- ChannelStrip DSP (16 ch inline)
  +-- Mixer matrix (16->8) -- bus summing
  +-- TDM TX (SAI1/SAI2) -- memory -> Codecs
  +-- [RTP encode] -- if audio streaming enabled
  +-- [PTP timestamp capture] -- if Ethernet RX coincides

Main Loop (low priority):
  +-- Ethernet RX ISR (DMA-driven, ~1-2% CPU)
  +-- UDP/TCP socket operations (QNEthernet event loop)
  +-- RTP/PTP message processing (async)
  +-- mDNS daemon (polled, ~100 ms interval)
  +-- MIDI parsing (USB host ISR + SPI0 XMOS polling)
  +-- SD card writes (ring buffer -> SDIO DMA)
  +-- UI updates (encoder/button debounce, display UART)
  +-- NeoPixel updates (if needed)
```
