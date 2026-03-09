# MIXTEE: Hardware Architecture Diagram

*Back to [README](../README.md) | See also: [System Topology](system-topology.md) | [Hardware](hardware.md)*

------

## System Block Diagram

```mermaid
%%{init: {"flowchart": {"curve": "stepAfter"}} }%%
graph TB
    subgraph DIGITAL["Digital Domain - GND"]
        direction TB

        subgraph POWER_MOD["Power Module - off-the-shelf"]
            STUSB4500["STUSB4500\nUSB PD 5V/5A"]
        end

        subgraph MAIN["Main Board - 4-layer"]
            direction TB
            TPS22965["TPS22965\nLoad Switch"]
            MAIN_IO["ADP7118 3.3V LDO\nSD Card SDIO\n74LVC1G00 Soft-Latch\nPC USB-C"]
            TEENSY["Teensy 4.1\nCortex-M7 600 MHz\nSAI1 + SAI2 TDM\nI2C - SPI0 - SDIO"]
            TCA["TCA9548A\nI2C Mux 0x70"]

            subgraph ISO_BLOCK["Isolation Boundary - x2 each"]
                direction LR
                SI8662["Si8662BB\nTDM Isolator\n6-ch 150 Mbps"]
                ISO1541["ISO1541\nI2C Isolator"]
                MEJ2["MEJ2S0505SC\nIsolated DC-DC\n5V to 5V_ISO"]
            end
        end

        subgraph IO["IO Board - 2-layer"]
            direction TB
            USB_HOST["FE1.1s Hub\n2x TPS2051\nDual USB-A"]
            MIDI["6N138 Opto\n3.5mm TRS\nMIDI IN + OUT"]
            RJ45["RJ45 MagJack\nEthernet"]
        end

        subgraph KEY["Key PCB - 2-layer"]
            KEY_CONTENTS["MCP23017 0x20\n16x WS2812B NeoPixels\n16x CHOC Switches"]
        end

        subgraph PERIPHERALS["Peripherals"]
            direction TB
            ESP32["ESP32-S3\nCustom Display PCB\nWROOM-1-N16R8\n4.3in 800x480 LCD"]
            ENCODERS["3x Rotary Encoders\nNavX - NavY - Edit"]
            PWR_BTN["Power Button\nmomentary"]
        end
    end

    subgraph ANALOG["Analog Domain - GND_ISO - galvanically isolated"]
        direction TB

        subgraph MOTHER1["Board 1-top - Input Mother TDM1 - 4-layer"]
            ADP_1["ADP7118 LDO\n5V_ISO to 3.3V_A"]
            U1["AK4619VN U1\nADC 1-4 / DAC 1-4"]
            U2["AK4619VN U2\nADC 5-8 / DAC 5-8"]
            MCP23008["MCP23008 0x21"]
            TS5A["TS5A3159\n4x Analog Mute Switch"]
            OPAMP_1["OPA1678 Op-Amps\nInput + Output stages"]
        end

        subgraph MOTHER2["Board 2-top - Input Mother TDM2 - 4-layer\n(input only, output DNP)"]
            ADP_2["ADP7118 LDO\n5V_ISO to 3.3V_A"]
            U3["AK4619VN U3\nADC 9-12"]
            U4["AK4619VN U4\nADC 13-16"]
            OPAMP_2["OPA1678 Op-Amps\nInput stages"]
        end

        subgraph DAUGHTERS["Daughter / Output Boards - 2-layer - ESD only"]
            D_IN["1-bot + 2-bot\nInput Daughters\n8x TS input jacks\nESD protection"]
            D_OUT["O-top + O-bot\nOutput Boards\n8x TS output jacks\nESD protection"]
        end

        HP_BOARD["HP Board - 2-layer\nTPA6132/MAX97220 Amp\nVolume Pot - 1/4in TRS"]
    end

    %% Power distribution
    STUSB4500 -. "2-pin JST-PH\n5V + GND" .-> TPS22965
    TPS22965 -. "5V_DIG" .-> MAIN_IO
    TPS22965 -. "5V_DIG" .-> TEENSY
    TPS22965 -. "5V" .-> MEJ2
    MEJ2 -. "5V_ISO isolated" .-> ADP_1
    MEJ2 -. "5V_ISO isolated" .-> ADP_2

    %% TDM audio (SAI1 / TDM1)
    TEENSY == "SAI1 TDM1\nBCLK 24.576 MHz\nLRCLK MCLK TX0 RX0 RX1" ==> SI8662
    SI8662 == "FFC 20-pin #1\nTDM1 isolated" ==> U1
    SI8662 == "TDM1" ==> U2

    %% TDM audio (SAI2 / TDM2)
    TEENSY == "SAI2 TDM2\nBCLK 24.576 MHz\nLRCLK MCLK TX0 RX0 RX1" ==> SI8662
    SI8662 == "FFC 20-pin #2\nTDM2 isolated" ==> U3
    SI8662 == "TDM2" ==> U4

    %% I2C topology
    TEENSY -- "I2C Wire\nSDA/SCL" --> TCA
    TCA -- "Ch 0" --> ISO1541
    ISO1541 -- "Isolated I2C\nvia FFC #1" --> U1
    ISO1541 -- "I2C" --> U2
    ISO1541 -- "I2C" --> MCP23008
    TCA -- "Ch 1" --> ISO1541
    ISO1541 -- "Isolated I2C\nvia FFC #2" --> U3
    ISO1541 -- "I2C" --> U4

    %% Key PCB (single 6-pin cable)
    TEENSY -- "6-pin JST-PH\nI2C + NeoPixel + INT + 5V" --> KEY_CONTENTS

    %% IO Board cables
    TEENSY -- "12-pin FFC\nUSB Host + MIDI + ETH + 5V" --> IO
    TEENSY -- "6-pin ribbon\nETH TX/RX diff pairs" --> RJ45

    %% Peripherals
    TEENSY -- "Serial1 UART\npins 0/1" --> ESP32
    TEENSY -- "GPIO\ninterrupt-capable" --> ENCODERS
    PWR_BTN -- "sense\npins 40/41" --> TEENSY

    %% Analog input path
    D_IN -- "JST-PH 6-pin\nanalog in" --> OPAMP_1
    D_IN -- "JST-PH 6-pin\nanalog in" --> OPAMP_2
    OPAMP_1 -- "buffered" --> U1
    OPAMP_1 -- "buffered" --> U2
    OPAMP_2 -- "buffered" --> U3
    OPAMP_2 -- "buffered" --> U4

    %% Analog output path (Board 1-top)
    U1 -- "DAC out" --> OPAMP_1
    U2 -- "DAC out" --> OPAMP_1
    OPAMP_1 -- "line driver out" --> TS5A
    MCP23008 -. "GPIO mute control" .-> TS5A
    TS5A -- "10-pin JST-PH\n8ch post-mute" --> D_OUT
    TS5A -- "4-pin JST-PH\nMaster L/R + 5V_ISO" --> HP_BOARD

    %% Headphone detect return
    HP_BOARD -. "HP detect\nvia 4-pin cable" .-> MCP23008

    classDef digital fill:#1a1a2e,stroke:#4a9eff,color:#e0e0e0
    classDef analog fill:#1a2e1a,stroke:#4aff7f,color:#e0e0e0
    classDef isolation fill:#2e1a1a,stroke:#ff4a4a,color:#ffe0e0,stroke-width:3px
    classDef power fill:#2e2e1a,stroke:#ffcc4a,color:#e0e0e0

    class TEENSY,TCA,MAIN_IO digital
    class USB_HOST,RJ45,MIDI digital
    class KEY_CONTENTS digital
    class ESP32,ENCODERS,PWR_BTN digital

    class U1,U2,U3,U4,OPAMP_1,OPAMP_2,ADP_1,ADP_2 analog
    class MCP23008,TS5A analog
    class D_IN,D_OUT analog
    class HP_BOARD analog

    class SI8662,ISO1541,MEJ2 isolation
    class STUSB4500,TPS22965 power
```

------

## Legend

| Line style | Meaning |
|-----------|---------|
| `==` thick solid | TDM audio (24.576 MHz BCLK) |
| `--` solid | Control / data (I2C, SPI, USB, Serial, GPIO) |
| `-.` dotted | Power distribution, passive connections, detect signals |

| Node color | Domain |
|-----------|--------|
| Blue border | Digital domain (GND) |
| Green border | Analog domain (GND_ISO) |
| Red border, thick | Galvanic isolation boundary components |
| Yellow border | Power entry / switching |

------

## Signal Path Summary

**Audio input:** 1/4" TS jack > ESD diode (daughter board) > JST-PH cable > op-amp buffer + anti-alias filter (mother board) > AK4619VN ADC > TDM > Si8662BB isolator > FFC 20-pin > Teensy SAI RX

**Audio output:** Teensy SAI TX > FFC 20-pin > Si8662BB isolator > AK4619VN DAC > reconstruction filter + output op-amp > TS5A3159 mute switch > 10-pin JST-PH cable > 1/4" TS jack (output board)

**Headphone:** DAC output (Board 1-top) > TS5A3159 > 4-pin JST-PH > TPA6132/MAX97220 amp > volume pot > 1/4" TRS jack. Detect switch returns to MCP23008 GP6 via same cable.

**DAW audio:** Ethernet (AES67) > RJ45 MagJack (IO Board) > 6-pin ribbon > Teensy DP83825I PHY > QNEthernet stack > RTP encode/decode. 16-in / 8-out to DAW via virtual soundcard. See [network-connectivity.md](network-connectivity.md) §9.

**Isolation boundary:** 2x Si8662BB (TDM), 2x ISO1541 (I2C), 2x MEJ2S0505SC (power) -- all on Main Board, crossing via FFC 20-pin cables to mother boards
