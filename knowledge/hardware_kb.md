# I2C 总线基础
SDA/SCL 通常需要上拉电阻，典型阻值为 4.7kΩ 或 10kΩ。
上拉电阻一端连接 SDA/SCL，另一端连接 VCC。

# SHT30 温湿度传感器
SHT30 是 Sensirion 的 I2C 温湿度传感器。
I2C 地址：0x44（ADDR引脚接GND）或 0x45（ADDR引脚接VCC）。
供电范围：2.4V–5.5V，推荐 3.3V。
封装：DFN-8，尺寸 2.5mm x 2.5mm。

# 电源滤波
传感器 VCC 与 GND 之间建议加 0.1μF 去耦电容（MLCC，尽量靠近芯片放置）。

# 上拉电阻说明
SDA/SCL 通过电阻连接到 VCC，阻值选择：
- 100kHz 标准模式：10kΩ
- 400kHz 快速模式：4.7kΩ
