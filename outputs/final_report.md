# 硬件设计最终报告

## 用户需求
设计一个3.3V供电的温湿度传感器小板，包含I2C接口

## 需求摘要
3.3V 供电的 SHT30 温湿度传感器小板，包含 I2C 接口、SDA/SCL 上拉电阻和去耦电容。

## 电源设计
- 供电电压：3.3V
- 去耦电容：0.1uF

## 元件清单
- SHT30 (sensor): Sensirion I2C 温湿度传感器，推荐 3.3V 供电。
- J1 (connector): I2C 接口连接器，包含 VCC、GND、SDA、SCL。
- R1 (resistor): SDA 上拉电阻，典型值 4.7kΩ 或 10kΩ。
- R2 (resistor): SCL 上拉电阻，典型值 4.7kΩ 或 10kΩ。
- C1 (capacitor): 0.1uF MLCC 去耦电容，靠近 SHT30 VCC/GND 放置。

## 关键连接
- SHT30.VCC -> 3.3V: 传感器电源连接
- SHT30.GND -> GND: 传感器接地
- J1.VCC -> 3.3V: 接口供电引脚
- J1.GND -> GND: 接口地引脚
- SHT30.SDA -> J1.SDA: I2C 数据线
- SHT30.SCL -> J1.SCL: I2C 时钟线
- R1.1 -> J1.SDA: SDA 上拉电阻一端连接 SDA
- R1.2 -> 3.3V: SDA pullup 另一端连接 VCC
- R2.1 -> J1.SCL: SCL 上拉电阻一端连接 SCL
- R2.2 -> 3.3V: SCL pullup 另一端连接 VCC
- C1.1 -> 3.3V: 去耦电容连接 VCC
- C1.2 -> GND: 去耦电容连接 GND
- SHT30.ADDR -> GND: 默认 I2C 地址 0x44

## 规则校验
- 总体结果：通过
- 修正状态：未触发

## 知识库引用
- # I2C 总线基础 SDA/SCL 通常需要上拉电阻，典型阻值为 4.7kΩ 或 10kΩ。 上拉电阻一端连接 SDA/SCL，另一端连接 VCC。
- # SHT30 温湿度传感器 SHT30 是 Sensirion 的 I2C 温湿度传感器。 I2C 地址：0x44（ADDR引脚接GND）或 0x45（ADDR引脚接VCC）。 供电范围：2.4V…
- # 电源滤波 传感器 VCC 与 GND 之间建议加 0.1μF 去耦电容（MLCC，尽量靠近芯片放置）。

## 不确定项
- I2C 总线速度未指定，100kHz 可用 10kΩ，400kHz 可用 4.7kΩ。
- ADDR 引脚可接 GND 使用 0x44，也可接 VCC 使用 0x45。
