# Provider Access Playbook

这份 playbook 只服务当前这套“上海租售比地图”内部研究 Beta，用来回答三件事：

1. 这个 provider 主要拿什么数据
2. 现在最现实的接入路径是什么
3. 你下一步应该去哪里申请或导出

## 总体顺序

1. 先接 `高德`，把底图、行政区、地址链和几何增强跑通。
2. 再接 `上海开放数据`，把行政区 / 小区主档 / 地址字典做实。
3. 再接 `贝壳开放平台`，优先试用和官方导出。
4. `58 / 安居客` 优先走商务授权或系统导出，不假设公开自助 API。
5. 在所有官方通道还没正式接通之前，用 `授权离线批次` 做 staging 与 conformance harness。
6. 如果短期内还是拿不到正式授权，就走 `公开页面人工采样`，但只作为 staging 补洞。

## beike-open-platform

- 角色：主商业 listing / dictionary 来源候选
- 官网：[open.ke.com](https://open.ke.com/)
- 申请试用：[试用申请使用教程](https://open.ke.com/serviceSupport/tutorialtryout/)
- 技术文档入口：[TOKEN 获取接口](https://open.ke.com/serviceSupport/getToken/)
- 联系方式：`jiaoxiadan001@ke.com`

建议动作：

1. 先注册 / 登录开放平台。
2. 先走“申请试用”。
3. 拿到试用后先验证 `getToken`。
4. 再决定先接网页版导出，还是接 API 服务。

适合当前项目的字段优先级：

- `resblock / standResblock`
- `building / standBuilding`
- `unit / standUnit`
- `floor / standFloor`
- `挂牌总价 / 月租 / 户型 / 面积 / 发布时间`

## 58-anjuke-open

- 角色：补充型 listing 来源
- 官网：[58 同城](https://www.58.com/)
- 当前公开协议参考：[58 协议 PDF](https://static.58.com/git/passport-mapp/pdf/announcement.pdf)

建议动作：

1. 不假设存在和贝壳同等级的公开自助 API 入口。
2. 优先走商务合作、门店 / 中介授权导出、现有房产系统对接。
3. 如果只拿到导出文件，直接走本项目的 `authorized-batch-import` 链路。

适合当前项目的角色：

- 多平台样本补充
- 同小区挂牌 / 出租重复样本对照
- 去重、异常值过滤和时间衰减校验

## shanghai-open-data

- 角色：行政区 / 小区主档 / 地址字典底座
- 平台入口：[data.sh.gov.cn](https://data.sh.gov.cn/view/)
- 操作指南：[平台操作指南 PDF](https://data.sh.gov.cn/assets/data/%E4%B8%8A%E6%B5%B7%E5%B8%82%E5%85%AC%E5%85%B1%E6%95%B0%E6%8D%AE%E5%BC%80%E6%94%BE%E5%B9%B3%E5%8F%B0%E6%93%8D%E4%BD%9C%E6%8C%87%E5%8D%9720210729V2.2.5.pdf)
- 安全沙箱：[安全计算沙箱](https://data.sh.gov.cn/view/sandbox/index.html)
- 客服邮箱：`sjkf@shanghai.gov.cn`

建议动作：

1. 先检索无条件开放的数据集，直接下载或接口调用。
2. 对有条件开放的数据，走平台“申请”流程。
3. 对敏感或受限场景，优先走安全沙箱。
4. 把拿到的小区主档先落成 reference dictionary，再去喂 listing / geometry 批次。

优先目标：

- 上海行政区字典
- 物业小区主档
- 地址标准化辅助字段
- 能映射到地图服务的地理信息

## amap-aoi-poi

- 角色：主地图底座、地址链和几何增强来源
- 开放平台：[lbs.amap.com](https://lbs.amap.com/)
- JSAPI 文档：[a.amap.com/jsapi/static/doc/index.html](https://a.amap.com/jsapi/static/doc/index.html)

建议动作：

1. 登录高德开放平台。
2. 进入“应用管理”创建应用。
3. 分别申请当前项目需要的 `JSAPI Key` 和 `Web 服务 Key`。
4. 地图前端先接 JSAPI，AOI / footprint 暂时仍走离线几何批次导入。

适合当前项目的能力：

- 底图与行政区展示
- 地址与经纬度转换
- 坐标链路对齐
- AOI / POI / 几何增强

## authorized-batch-import

- 角色：官方导出文件 / 商务授权数据的 staging 通道
- 导入说明：[授权导入说明](/docs/import-authorized-data.md)
- 几何导入说明：[几何批次导入说明](/docs/import-geo-assets.md)
- 主档导入说明：[reference dictionary 导入说明](/docs/import-reference-dictionary.md)

建议动作：

1. 官方 API 还没开通时，先让对方给 CSV / Excel / GeoJSON 导出。
2. 先跑 `jobs/import_reference_dictionary.py`。
3. 再跑 `jobs/import_authorized_listings.py` 和 `jobs/import_geo_assets.py`。
4. 最后把 staging 批次写入 PostgreSQL，切数据库主读。

## manual-geometry-staging

- 角色：重点区楼栋 footprint 的研究阶段勾绘与人工校正
- 入口：[几何批次导入说明](/docs/import-geo-assets.md)

建议动作：

1. 当官方 AOI / footprint 还没到位时，先把重点区高价值楼栋手工整理成 GeoJSON。
2. 导入时使用 `manual-geometry-staging` provider，让系统明确知道这是一批 staging 几何。
3. 后续如果拿到官方 AOI / footprint，再用新批次覆盖，不要直接改旧 staging run。

适合当前项目的角色：

- 重点区楼栋 footprint 补洞
- 持续套利楼层榜相关楼栋的几何校正
- GIS / 研究同学之间的人工交接资产

## public-browser-sampling

- 角色：正式授权拿不到时的公开页面补洞通道
- 导入说明：[公开页面人工采样导入](/docs/import-public-browser-capture.md)

建议动作：

1. 研究员在浏览器里打开公开房源页或小区详情页。
2. 把核心文本人工复制进 capture CSV。
3. 先跑 `jobs/import_public_browser_capture.py` 生成标准 `sale/rent CSV`。
4. 再并进 `public-browser-sampling` import run 或 `materialize_public_snapshot.py`。

边界：

- 只读公开页面
- 不依赖登录态
- 不做批量抓取
- 统一作为 staging-only provider 处理

## 进入生产前的最小闭环

1. `高德 Key` 已申请
2. `上海开放数据` 至少有一份小区主档
3. `贝壳` 至少完成试用申请
4. 至少 1 批授权 listing 已导入
5. 至少 1 批楼栋 footprint 已导入
6. `POSTGRES_DSN` 已配置并完成一次落库

做到这一步，系统就已经不是原型，而是一个真正可承接真实世界数据的内部研究台。
