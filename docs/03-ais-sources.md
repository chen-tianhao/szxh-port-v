# aisstream.io / AISHub / IMF PortWatch 到底给什么

2026-11-05 逐个查官方文档与 API 元数据核实。三条源完全不是一类东西：
**前两个是实时船舶报文流，第三个是港口层面的日度汇总指标，没有船位。**

---

## 1. aisstream.io —— 全球免费实时 AIS 报文流

- 接入：`wss://stream.aisstream.io/v0/stream`，WebSocket，一条连接订阅一次。
  API key 在账号页生成（GitHub 登录授权），免费。
- 订阅参数：`BoundingBoxes`（必填，经纬度对角数组）、`FiltersShipMMSI`（可选，≤200 个 9 位 MMSI）、
  `FilterMessageTypes`（可选）。
- **25 种消息类型**（文档列的完整清单）：PositionReport、ExtendedClassBPositionReport、
  StandardClassBPositionReport、BaseStationReport、LongRangeAisBroadcastMessage、
  ShipStaticData、StaticDataReport、AidsToNavigationReport、SafetyBroadcastMessage、
  AddressedSafetyMessage、AddressedBinaryMessage、BinaryBroadcastMessage、BinaryAcknowledge、
  SingleSlotBinaryMessage、MultiSlotBinaryMessage、GnssBroadcastBinaryMessage、
  Interrogation、AssignedModeCommand、ChannelManagement、DataLinkManagementMessage(+Data)、
  GroupAssignmentCommand、CoordinatedUTCInquiry、StandardSearchAndRescueAircraftReport、
  UnknownMessage。
  实际用得上的就是前三类位置报文 + ShipStaticData / StaticDataReport / AidsToNavigationReport。
- 消息结构：`{ MessageType, MetaData{MMSI, ShipName, Latitude, Longitude}, Message{<类型>{…} } }`，
  PositionReport 里含 Sog / Cog / TrueHeading / NavigationalStatus / RateOfTurn / Timestamp 等；
  ShipStaticData 含 IMO、CallSign、Destination、ETA、Draught、尺寸（A/B/C/D）、ShipType。
  二进制帧承载 UTF-8 JSON。
- **硬限制**（官方文档原话）：账号 3 条订阅连接、同源 IP 3 条；连上后 3 秒内必须发订阅；
  订阅更新 ≤1 次/秒；MMSI 过滤 200 个；**读得不够快会丢消息**；不允许浏览器直连（必须自己后端代理）；
  2026 年 9 月起未启用压缩的连接按带宽限额丢包。
- **没有历史**：官方明确「不保证 SLA、事件不做持久化重放」。要历史只能自己 7×24 落库。
- 许可：无 ODbL 之类的正式许可条款，服务免费但无 SLA/可用性承诺。

## 2. AISHub —— 志愿者台站交换网络

- 机制：你交一台自己的 AIS 接收机（NMEA 原始流推到他们给的 IP/UDP），换一把 API key，
  才能读全网合并数据。**不交台站就没有 key**。
- 规模（2026-11-05 首页实时）：**1,788 个台站**（在线 1,452 / 离线 336）、82 个国家、
  24 小时内 **79,529 艘**船。台站是个人爱好者架设，海岸线为主。
- 接口：`https://data.aishub.net/ws.php?username=KEY`，**每分钟只能请求一次**
  （更快返回 "Too frequent requests!"），GET 参数支持 `format`（0=原始 AIS 编码 / 1=可读值）、
  `output`(xml/json/csv)、`compress`(0 无 / 1 zip / 2 gzip / 3 bzip2)、
  矩形范围 `latmin/latmax/lonmin/lonmax`、`mmsi`、`imo`、`interval`（只要最近 N 分钟的船位）。
- 返回字段（每船一条最新记录）：`MMSI, TIME, LONGITUDE, LATITUDE, COG, SOG, HEADING, ROT, PAC,
  NAVSTAT, IMO, NAME, CALLSIGN, TYPE, A(船首距), B(船尾距), C(左舷距), D(右舷距), DRAUGHT, DEST, ETA`。
  比 aisstream 省事的地方：**静态+航次信息（DEST/ETA/DRAUGHT）与位置已经在同一条记录里**，不用自己拼。
  CSV 格式没有 ROT/PAC，时间列叫 TSTAMP。
- **只有"最新状态快照"**：`interval` 只是限定"最近 N 分钟内"的船位，不是历史查询。没有归档接口。
- 另有 Stations API（台站列表，同样 1 次/分钟）。
- 许可（Terms of Use，2026-10-08 更新）：鼓励做网站/应用/研究/商业产品，要求署名
  **"Data: AISHub contributors" 并链接 aishub.net**；**不允许把原始数据转给第三方**（免费或收费都不行）。
  数据来自志愿者，"as is"，不得用于航行。

## 3. IMF PortWatch —— 港口级日度指标（没有船位、没有轨迹）

- 形态：ArcGIS FeatureServer（免费、可直接 REST 查询），配套 portwatch.imf.org 可视化。
- **港口库 2,065 个**（原 PDF 写的 1,648 已过时），字段：
  `portid, portname, fullname, country, ISO3, continent, lat, lon, LOCODE,
  vessel_count_total / _container / _dry_bulk / _general_cargo / _RoRo / _tanker,
  industry_top1/2/3, share_country_maritime_import, share_country_maritime_export`。
- **日度港口数据 Daily_Ports_Data**：2019-01-01 → 2026-10-30（约 590 万行），字段
  `date, year, month, day, portid, portname, country, ISO3,
  portcalls_{container,dry_bulk,general_cargo,roro,tanker,cargo}, portcalls,
  import_{container,dry_bulk,general_cargo,roro,tanker,cargo}, import,
  export_{…同上一组…}, export`。
  - **port call 定义**（官方）：船舶进入港口边界即计一次；**排除周转 <5 小时且装卸前后吃水不变的船**，
    以滤掉加油/锚泊/补给的过境船。
  - **import/export 单位是公吨**：用船长/船宽/吃水/容量/方形系数估船载量，进出港吃水差
    × 载重吨 → 货量估算。集装箱类别同理给的是吨不是 TEU。
- **日度咽喉点数据 Daily_Chokepoints_Data**：28 个海峡/运河（苏伊士、巴拿马、马六甲、霍尔木兹、
  好望角、直布罗陀、多佛、厄勒、台湾海峡、朝鲜海峡…），字段
  `n_{container,dry_bulk,general_cargo,roro,tanker,cargo,total}` 与 `capacity_{…}`（单位公吨）。
- 来源：IMF 用 UN Global Platform 的 AIS 数据加工（方法论见 IMF WP 2021/225
  "Tracking Trade from Space"）。只发布**指标**，不发布逐船轨迹；不允许反推单船。
- 许可：IMF 使用条款（imf.org/external/terms.htm）。

---

## 对苏州研究的直接结论

1. **PortWatch 已经覆盖苏州，而且是拆成三个港**（这是最有价值的一条）：
   - `port1253` Suzhou (Taicang)　31.6875N, 121.1376E　24h 在港 8,374 艘
     （集装箱 1,516 / 干散 3,116 / 油轮 1,641），首位产业 Mineral Products
   - `port1425` Suzhou (Zhangjiagang)　31.9746N, 120.4288E　2,849 艘，首位产业 Vegetable Products
   - `port227` Suzhou (Changshu)　31.7578N, 120.9643E　701 艘，首位产业 Mineral Products
   → 太仓的日度靠港次数与进出口公吨数可以直接拉 2019 年至今的序列，和港口吞吐量统计交叉验证。
2. **要船位/轨迹**：aisstream（免费、实时、可框选太仓段、要自己存档）优先；
   AISHub 需要先有接收台站，长江内河覆盖不可控，且不允许转发原始数据 —— 论文里用要谨慎。
3. **要事件级指标**（靠港次数、按船型、按进出口）：PortWatch 现成，别再自己从 AIS 里识别靠泊。
