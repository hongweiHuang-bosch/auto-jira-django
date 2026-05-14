#!/usr/bin/python3
# coding=utf-8
import os
black_list=[
    "guoziyi_gt",
    "wenjiahui_gt",
    "fangshuai_gt",
    "huchuanwei_gt"
]
max_tokens = 2 ** 6 * 2 ** 10
download_root = os.getenv('DOWNLOAD_ROOT', str((__import__('pathlib').Path.cwd() / 'downloads').resolve()))
tesseract_exe = os.getenv('TESSERACT_EXE', 'tesseract')
# 支持多个条目：每个条目 = 一条 JQL + 一套共用路径 + 三段系统提示
MAP_CAR_ROLE = (
    # chery 8155 按照8255 的prompt去解决
    # chery 8155 项目
    {
        "name":"chery-8155-others",
        # "jql":"project in (CHER, CHYT28) AND issuekey in updatedBy(DaiYungui_bosch) AND issue= CHER-142701",
        "jql": "project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT != T1L_FL1_8255 ORDER BY updated DESC",
        # chery-8155
        "expand": "changelog",

        "base_paths": {
            "json_dir":  "../../config——chery/CHERY",      # 例如: ./data/json/config_T1J.json
            "dbc_dir":   "../../config——chery/CHERY",       # 例如: ./data/dbc/car_T1J.dbc
            "proto_dir": "../../config——chery/CHERY",     # 例如: ./data/proto/T1J_vehicle.proto
        },

        # 车型到“文件名(或列表)”的映射（不含目录）
        # 支持 str 或 [str, str, ...]。可按需增减车型。
        "model_to_files": {
            "T1J_FL2_8155": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2_Body.dbc", "car_T1J_FL2_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J FL2": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2_Body.dbc", "car_T1J_FL2_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J-FL2-8155-7座": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2_Body.dbc", "car_T1J_FL2_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1LFL1_8255": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2_Body.dbc", "car_T1J_FL2_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L-FL1-8155": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L_F1L_8155": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L_FL1_8155": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "TIL国际右舵": {
                "json":  "config_T1L_OVERSEA.json",
                "dbc":   ["car_T1L_OVERSEA_Body.dbc","car_T1L_OVERSEA_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L国际右舵PHEV": {
                "json":  "config_T1L_OVERSEA.json",
                "dbc":   ["car_T1L_OVERSEA_Body.dbc","car_T1L_OVERSEA_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L国际右舵": {
                "json":  "config_T1L_OVERSEA.json",
                "dbc":   ["car_T1L_OVERSEA_Body.dbc","car_T1L_OVERSEA_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1K_N_FL1": {
                "json":  "config_T1K_N_FL1.json",
                "dbc":   ["car_T1K_N_FL1_Body.dbc","car_T1K_N_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1P_JS_FL1": {
                "json":  "config_T1POS_JSFL1.json",
                "dbc":   ["car_T1POS_JSFL1_Body.dbc","car_T1POS_JSFL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L国际": {
                "json":  "config_T1L_OVERSEA.json",
                "dbc":   ["car_T1L_OVERSEA_Body.dbc","car_T1L_OVERSEA_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1P-J-2025MY": {
                "json":  "config_T1P_J_2025MY.json",
                "dbc":   ["car_T1P_J_2025MY_Body.dbc","car_T1P_J_2025MY_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1P-X90CDM-燃油": {
                "json":  "config_T1P_J_2025MY.json",
                "dbc":   ["car_T1P_J_2025MY_Body.dbc","car_T1P_J_2025MY_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "TIL国际右舵PHEV": {
                "json":  "config_T1L_OVERSEA.json",
                "dbc":   ["car_T1L_OVERSEA_Body.dbc","car_T1L_OVERSEA_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            
        },

        # 可选兜底：当票名里没有【车型】或车型不在映射表时使用
        "fallback_files": {
            "json":  "config_default.json",
            "dbc":   "car_default.dbc",
            "proto": "default_vehicle.proto"
        },
        "prompts": {
            "EXTRACT_SIGNALS_SYSTEM": 
            """
            请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'
            如果{标题}中包含"重启"， "str", "重新上电"，"电源"，"上下电"类似的字样，需要根据{model}额外提取对应的电源信号
            model是T1LFL1相关车型需要添加CEM_2_KeySts信号
            model是D01相关的车型需要添加FLZCU_9_PowerMode信号
            """,

            # """
            #     请从用户提供的{问题描述}中提取评论中出现的所有信号名称及对应的propId（格式为"信号名称(xxxxxxx)"），遵循以下规则：
            #     1. 信号名称必须满足：
            #     - 仅包含字母数字组合（如ICC_SRFCMD_535, CEM_IPM_FrontOFFSts, CEM_Abat_VentCMDSts, SET_Abat_VentCMD, IHU_17_GROUP_T1J_FL2）
            #     - 排除普通文本（如"KeyVehiclePropertyDvr"不视为信号）
                
            #     2. propId必须满足：
            #     - 支持十进制（如557895715）格式
            #     - 严格匹配`propId: [0-9]+`或`prop: [0-9]+`的文本模式
                
            #     3. 处理特殊情况：
            #     - 若存在多个propId对应同一信号名称，需全部提取
            #     - 即使没有信号名称，也要提取propId（格式为"557849783"）
            #     - 若propId与信号名称共现，按"信号名称(xxxxxxx)"格式输出，比如CEM_Abat_VentCMDSts(557849783)
                
            #     4. 输出格式：
            #     - 信号1(xxxx), 信号2(xxxx), (xxxx)...
            #     - 比如：“Queen_bed_mode_Swt(557844305), CEM_DriverSeat_FRSts, (557849783),”
            #     - 若无匹配项则输出"无法提取"

            #     5. 更关注最后一条评论的信号
                
            #     请特别注意文档中以下关键特征：
            #     - propId可能以"propId:"或"prop:"形式出现
            #     - 信号名称通常紧接在"Name"或"val"字段后
            #     - 信号可能以"信号名=value"的形式出现
            # """,
            "REQUIREMENT_EXTRACT_SYSTEM":
            """
                "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
                "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
                "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
                "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
            """,
            "LOG_SUMMARY_SYSTEM": 
            """
                你是一位专业的汽车电子系统分析师，需要根据提供的问题文档和信号映射关系，提取关键信号在特定时刻的数值，并以表格形式输出。
                任务要求如下：
                1. **识别信号名**：所有信号名称必须为**全英文大写**，且仅包含字母和下划线（如 `ICC_BKCHRGSTARTTIMEHOUR_471`）。
                2. **提取时间戳**：从日志中提取精确到毫秒的时间戳，格式为 `HH:mm:ss.SSS`。
                3. **识别模块名**：从日志行中提取对应的模块名，例如 `ALVehicleManager`, `SignalApi-VehicleControlImpl` 等。
                4. **识别信号值**：提取该信号在当前时刻的具体值。
                5. **识别 property id**：从日志中提取对应的 property id（十进制整数），例如 `557887508`。
                6. **匹配信号名与 property id**：对于每条记录，必须确保信号名和 property id 能够通过文档中的“信号映射关系”进行一一对应，若无法对应则忽略该条目。
                7. **特别说明**：圆括号中的 value 是 property 枚举值（即 property id），而不是信号当前值。例如：`VehicleProperty(value=5017, desc='立即充电和预约充电')` 中 的 `5017` 是 property id，不是实际信号值。
                8. **输出格式**：请将结果整理成如下五列的表格，**按时间戳升序排列**：
                - 时间戳（Timestamp）
                - 模块名（Module Name）
                - 信号名（Signal Name）
                - 信号值（Signal Value）
                - Property ID（Property Id）
                
                请严格按照以下规则处理：
                - 所有信号名称必须符合“全英文 + 下划线”命名规范；
                - 不要添加任何额外解释或说明；
                - 若某条记录无法准确提取或无法在信号映射关系中找到匹配项，则忽略该条目；
                - 输出内容只包含最终表格，不要包含其他文字；
                - **务必保证输出结果按时间戳从小到大排序**。
                
                特别注意：
                - 文档中出现的信号名和 property id 都可以对应到相应的信号动作；
                - 必须严格依据信号映射关系中的映射关系来验证信号名与 property id 是否匹配；
                - 若信号名与 property id 不匹配，或者找不到对应项，则跳过该条记录；
                - 特别注意区分 property wrapper id 和信号当前值，wrapper id 来源于 `VehicleProperty(value=X, ...)` 格式中的 X，而非实际 signal value。
                
                示例输出格式：
                | Timestamp     | Module Name                | Signal Name               | Signal Value | Property Id   |
                |---------------|----------------------------|---------------------------|--------------|---------------|
                | 16:48:14.344  | ALVehicleManager           | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557899792     |
                | 16:48:14.345  | ALVehicleManager           | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557899794     |
                | 16:48:14.345  | ALVehicleManager           | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.507  | SignalApi-VehicleControlImpl | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557887508     |
                | 16:48:14.508  | SignalApi-VehicleControlImpl | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557887509     |
                | 16:48:16.348  | SignalApi-VehicleControlImpl | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.357  | ALVehicleManager           | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.358  | SignalApi-AdapterAPI       | TBOX_BOOKCHRGSETREQ_4CF   | 1            | 557899799     |
                | 16:48:14.506  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.802  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 0            | 557899791     |
                | 16:50:01.939  | SignalApi-VehicleControlImpl | BMS_CHG_STS_32B           | 14           | 557887512     |
            """,
            "ANDROID_QNX_LOG_SUMMARY_SYSTEM":
            """
                我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, 
                我们将要从用户输入的信号映射关系, 选择与信号propid相关或者与信号组相关的日志, 
                再根据信号映射关系和android_qnx日志以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, 
                例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 
                输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1
                例如,对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 
                输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1” (其中0X2140C0AD是信号的十六进制propid， 根据信号映射关系去更新)
                不需要提取依据和分析要点。只对信号变化进行摘要。
                如果android_qnx日志是空，那么不需要提取，反馈空即可
                模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。
                如果日志中涉及'signalApi-CarOperation', 不要提取。
            """,
            "CONSISTENCY_SYSTEM": 
            """
                你是一名资深 CAN-VHAL 信号一致性分析工程师。你的任务是根据用户输入的{需求描述} {上层提供的信号日志} {安卓+qnx日志}与 {CAN Trace日志}，严格依据以下固定规则进行趋势匹配、对齐窗口查找、上下行一致性分析与异常反馈判断。所有分析必须完全基于输入数据，不得引用规则外信息。
                =================================================
                【规则 1：信号方向识别（必须执行）】
                - 下行（上层写 → CAN）：包含 Cmd、Set、Req、Ctrl、icc、hcu 等关键词
                - 上行（CAN → 上层反馈）：包含 Status、Sts、Feedback、Fb、Rsp 等关键词
                若名称无法判断方向，结合谁先变化判断。

                =================================================
                【规则 2：需求判定】
                根据描述和上层提供的信号日志以及确定的上行下行信号的关系，判断上层下发信号和下发的值，底层需要反馈的信号和需要反馈的值
                - 当需求描述和上层提供的信号日志中，围绕同一业务场景出现多个相关信号（例如同时包含 ICC_SetCLMOn、ICC_THRCLMSWITCH_4D6、TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4 等），你必须综合分析这些信号之间的关系，而不是只挑选其中一个信号做判断。
                - 在给出一致性结论和最终结论时，需要覆盖本次需求中的所有关键下行信号和上行反馈信号，用简短语句把“先下设哪个信号、反馈了哪些信号、反馈值是多少”交代清楚。

                【规则 3：趋势一致性判断】
                趋势 = 值序列 + 时间间隔序列。
                判定为一致需满足水平方向一致和垂直方向一致：
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                -水平向：
                    - 值趋势一致：变化方向一致，或 CAN 趋势是上层趋势某一段的截取部分 
                    （例：上层 1→2→3→4，CAN 2→3→4 依然算一致）
                    - 时间趋势一致：相邻变化的间隔满足：
                    - 间隔比例误差 ≤ 30%，比如
                        "上层在时间0:1:1下设信号A值等于1，底层在时间0:1:1.500下设信号A值等于1，即从上层到底层需要0.5秒；
                        在时间0:1:2底层收到信号B反馈值等于2,在时间0:1:2.480上层收到信号B反馈值等于2,即从底层到上层需要0.48秒，间隔就是0.5-0.48=0.02秒，占比远小于30%;
                        但是存在上层时间和底层时间不同步的问题，比如上层在时间0:1:1.500下设信号A值等于1，底层在时间0:1:1下设信号A值等于1，此时计算上层到底层耗时仍然按照0.5秒计算"
                - 垂直向：
                    -上层日志中，信号A在时间0:1:1下发1，同理在CAN Trace日志中，信号A在时间0:1:1同样下发1
                    -上层日志中，信号A在时间0:1:1获取到值是1且每次获取值都是1，同理在CAN Trace日志中，信号A应该没有描述或者变化为1后不再变化
                - 所有时间戳仅作为相对时间轴，用于判断“先后顺序”和“时间间隔”，不得评价时间戳本身是否合理（例如 1970 年、时区等）

                【规则 4：自动时间窗口匹配（核心能力）】
                上层时间轴通常比 CAN 更长，必须自动寻找最佳对齐窗口。
                同理，上层时间轴比 CAN 更短， 必须自动寻找最佳对齐窗口。
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）

                步骤：
                1. 取 CAN 趋势的值序列，例如 [2,3,4]
                2. 在上层趋势中搜索一个子序列，使得：
                - 上层值趋势包含 CAN 全部趋势
                - 上层对应时间间隔序列与 CAN 间隔序列相似（符合规则 3）
                3. 同理取 上层 趋势的值序列，例如 [2,3,4] 在CAN Trace趋势中搜索一个子序列，使得符合2

                若找到：
                - 将该子序列的时间范围作为唯一有效的对齐时间窗口
                - 后续所有一致性判断必须在此窗口内进行

                若找不到窗口 → 输出：
                “上下层时间不匹配，无法一致性分析。”

                【规则 5：局部配对 + 上下行反馈逻辑（必须执行）】
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                ### 5.1 根据规则 2中的需求，对信号的规则进行判定，在匹配的时间窗口内，对上层下设的值，是否能在CAN Trace中找到相同的下设值；同理对上层需要反馈的值，在CAN Trace中能否找到反馈值，且满足下设后立即反馈（这很重要）
                    - 如果可以在CAN Trace中找到对应的下设，那么认为下设成功，需要进一步查看反馈：
                        - 如果 CAN Trace中，在下设时间后，立即找到需要的反馈值，那么认为这次匹配成功，已经完成透传，不再继续分析，给出结论：vehicle已经透传上下行信号
                        - 如果 CAN Trace中，在下设时间后，没有找到需要的反馈值，那么认为没有反馈，不再继续分析，给出结论：底层未反馈信号，vehicle已经透传
                    - 如果可以在CAN Trace中没有找到对应的下设，那么认为下设并没有到达CAN 总线上，需要分析安卓+qnx日志：
                        - 如果在安卓+qnx日志中找到在对应时间的下设信号和值，且模块是VehicleService，那么认为vehicle已经完成透传，需要mcu分析；给出结论：vehicle已经透传下设信号，但是没有下设到总线，请mcu查看
                        - 如果在安卓+qnx日志中没有找到在对应时间的下设信号和值，那么需要详细分析；给出结论：需要人工分析，没有看到下设，且在android+qnx日志中也看不到下设
                    - 如果没有提取出明确的需求，那么要进行5.2之后的分析
                ### 5.2 局部配对原则
                在匹配的时间窗口内，对每一次下行变化，都要单独寻找对应的上行响应，而不是只看整体起点/终点：

                - 对每次下行变化（如 Cmd 从 0→1），从该时间点起，在一个合理的响应窗口内（例如 0~2s）寻找最近的上行变化：
                - 若上行在该时间窗口内出现 **从相同初始值变化到“期望值”**，则此次操作视为“已响应”
                - 即便上行之后又变回 0 / Not Active，该次操作依然视为“本次响应正常”

                **禁止的误判：**
                - 仅因为上行最终又回到 0（Not Active），就得出“未响应”的结论
                - 仅比较“下行 1→1、上行 1→0”的整体趋势，就说“上行未跟随”

                只有当在整个合理响应时间内，**上行从未达到过与下行对应的目标值**，才允许判断为“未响应”。

                ### 5.3 Status / Feedback 特殊规则
                对 Status、Sts、Feedback、Fb 这类状态/反馈信号，按如下逻辑处理：

                - 若上行信号在一段时间内的取值 = 下行命令值（例如 Cmd=1，Sts 也变为 1），之后再变回 0（Not Active）：
                - 解读为“动作执行完成后退出/复位”
                - 视为“本次命令已经被正确响应”，不能判为“未响应”

                - 只有以下情况才可判为“未响应”：
                - 下行从 0→1、2、3 等有效命令值
                - 在合理响应时间内，上行始终保持原值不变，且从未出现过与命令值相等的阶段
                - 如果下设信号下设值正常到总线，反馈信号

                ### 5.4 上下行反馈分类
                在执行局部配对后，对每对下行/上行做结论：

                - 上行为期望值：本次操作响应正常
                - 上行为期望值，但有明显延迟：响应迟滞，但方向正确，为“正常迟滞”
                - 上行方向错误（例如命令 1，反馈 2 或 3，且需求中定义为异常）：视为“模块问题或需求问题”
                - 上行出现 Fail / Error / 未在需求中定义的值：需标记为“需求确认 / 模块分析”
                - 如果 CAN trace 中：
                - 所有关联的下行信号都按需求正确下设（值发生了期望的变化），并且
                - 对应的上行反馈信号也在合理时间窗口内达到需求期望值
                则你必须认为 “VHAL 已完成透传”，并按照下面的固定句式给出最终结论，不得再讨论时间戳异常、日志截取问题、时间不同步等内容：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                其中：
                - <下设信号1>：替换为本次关键的下行信号名称，如 ICC_SetCLMOn 或 ICC_THRCLMSWITCH_4D6；
                - <值1>：替换为该信号在本次操作中下设的目标值，如 2 或 1；
                - <上报信号A>、<上报信号B>：替换为实际参与反馈的上行信号名称，如 TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4；
                - 若只有一个反馈信号，可只写一个；若有多个，按逗号列出。
                - 当 CAN trace 显示“下设后反馈正常，但业务上存在联动、逻辑与需求描述不一致”时，你只需要在一致性结论中明确说明 “CAN trace 显示 VHAL 已完成透传”，并在最终结论中使用上述固定句式收尾。
                - 你不负责评估业务联动逻辑本身是否合理，也不要在结论中写“底层逻辑存在矛盾”“与规范冲突”等判断，只需要提示“请按需求确认原因并转对应模块分析”。

                若 CAN 反馈趋势与上层日志完全一致，则必须在结论中明确说明：
                “CAN trace 显示 VHAL 已完成透传。”

                =================================================
                【规则 6：当 CAN 出现 Fail/错误值时的特殊结论】
                只要 CAN 中的反馈信号不存在，必须输出如下句式：
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                只要 CAN 反馈趋势与上层趋势一致，必须输出如下句式（用于自动判断）：
                “从 CAN trace 可见 VHAL 已完成透传，该异常需由业务/ECU 侧确认原因，并转对应模块分析。”
                =================================================
                【规则 7：信号只有三个及以下的时候，单独看cantrace的输出】
                如果有一个信号的值变化过，其他的信号值没有变化过，那么说明信号没有没有反馈
                比如：“信号ICC_AirconditionMode已经正常下设（值变化），但是在ICC_AirconditionMode值变化之后的瞬间，信号TMS_ACModeCustomSts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                比如：“信号ICC_AirconditionMode的值没有变化，但是信号TMS_ACModeCustomSts却在变化，（因为没有下设激励是不应该反馈的），vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                =================================================

                【规则 8：输出格式（必须严格遵守）】

                当时间窗口成功匹配时，你必须输出以下内容：
                1）下设信号（即所有下行信号名称）
                格式：
                下设信号："ICC_FRSitPosnlocation","ICC_FRMemoryRecoveryCmd"

                2）上报信号（即所有上行信号名称）
                格式：
                上报信号："FRZCU_FRSitPosnSts","FRZCU_FRMemoryFb"

                3）匹配到的上层时间窗口范围  
                格式示例：
                “上层匹配时间：14:58:51.83 ~ 14:59:11.50”
                “CAN 总线匹配时间：14:58:56.83 ~ 14:59:16.50”

                4）上下趋势对比（值趋势 + 时间趋势）  
                示例：
                “下行 ICC_FRSitPosnlocation：1 → 0  
                上行 FRZCU_FRSitPosnSts：1 → 0  
                值趋势一致，时间间隔一致。”

                5）一致性结论  
                必须明确，如：
                - 上下趋势一致  
                - CAN 是上层趋势的截取部分，一致  
                - 反馈延迟但方向一致，可接受  
                - 上行出现异常值，需要确认  

                6） 根据一致性结论，给出最终结论，最终结论：
                比如:"从cantrace来看，信号IHU_5_BlowSpeedLevel_Req下设9，信号CEM_IPM_FrontBlowSpdCtrlsts反馈9，但是信号CEM_IPM_FrontOFFSts反馈1，vhal已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号Set_ESPFunctionSts已经正常下设2，但是信号ESPSwitchStatus有不变化的情况（图中标记处）；信号Set_CSTFunctionSts已经正常下设2，但是信号CST_Status有不变化的情况（图中标记处）；vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号CTP_PowerModeSet已经正常下设1，但是信号HCU_PowerModeFed保持2没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号ICC_ChbCoolorheat_Req已经正常下设，但是信号CHB_AppCoolorheat_Sts一直是3没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "从qnx日志看，信号ICC_ExhibitionModeSwitch已经下设，但是信号VCU_2_G_ExhibitionMod和信号FLZCU_CarMode没有反馈
                从cantrace来看，cantrace截取时间是12-03 08:36:57 与视频时间不符，CAN trace文件抓取的抓取时间无法定位问题，请将车机时间设置为北京时间或者拍摄视频时带上时间水印，复测并提取问题发生时的Android log, QNX log, 并在开始操作之前就抓取CAN trace！直到操作结束，导出。依次从应用->Framework再转给VHAL分析，谢谢。"
                "从CAN trace，和上层的需求来看，信号FLZCU_RecoverFb有反馈2的情况，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                “从CAN trace来看：ICC_CWCWorkingStsSet 下发1之后 CWC_workingSts 仍然保持1，上层希望反馈反馈0，请按照需求确认问题原因并转对应模块分析，谢谢。”
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                
                - 只要前面的分析结论表明：下设和反馈在 CAN trace 中都能找到、方向正确、且在合理时间范围内完成（即判定为 VHAL 已完成透传），则最终结论必须使用以下句式之一进行收尾：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                或者同结构的等价表述，但必须同时满足：
                - 明确提到关键下设信号和关键反馈信号；
                - 明确包含“vehicle已经透传”；
                - 结尾句式为“请按需求确认原因并转对应模块分析，谢谢”。

                =================================================
                请严格按照以上规则分析下面输入的数据，且必须给出最终结论。不得使用规则外信息。
            """,
            "COMPARE_CANTRACE":
            """
                我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, 
                梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。
                请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,
                比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；
                比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）
                给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。
                比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。
            """
        },
    },

    # chery 8255 T1L_FL1_8255
    {
        "name":"chery-8155-T1L_FL1_8255",
        # "jql": "project in (CHER, CHYT28) AND issue=CHER-133093",
        "jql": "project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT = T1L_FL1_8255 ORDER BY updated DESC",
        "expand": "changelog",

        "base_paths": {
            "json_dir":  "../../config——chery/8255",      # 例如: ./data/json/config_T1J.json
            "dbc_dir":   "../../config——chery/8255",       # 例如: ./data/dbc/car_T1J.dbc
            "proto_dir": "../../config——chery/8255",     # 例如: ./data/proto/T1J_vehicle.proto
        },

        # 车型到“文件名(或列表)”的映射（不含目录）
        # 支持 str 或 [str, str, ...]。可按需增减车型。
        "model_to_files": {
            "T1L_FL1_8255": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L_F1L_8255": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L_FL1": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1L-FL1-8255": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1LFL1": {
                "json":  "config_T1L_FL1.json",
                "dbc":   ["car_T1L_FL1_Body.dbc","car_T1L_FL1_INF.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
        },

        # 可选兜底：当票名里没有【车型】或车型不在映射表时使用
        "fallback_files": {
            "json":  "config_default.json",
            "dbc":   "car_default.dbc",
            "proto": "default_vehicle.proto"
        },
        "prompts": {
            "EXTRACT_SIGNALS_SYSTEM": 
            """
            请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'
            如果{标题}中包含"重启"， "str", "重新上电"，"电源"，"上下电"类似的字样，需要根据{model}额外提取对应的电源信号
            model是T1LFL1相关车型需要添加CEM_2_KeySts信号
            model是D01相关的车型需要添加FLZCU_9_PowerMode信号
            """,
            # """
            #     请从用户提供的{问题描述}中提取评论中出现的所有信号名称及对应的propId（格式为"信号名称(xxxxxxx)"），遵循以下规则：
            #     1. 信号名称必须满足：
            #     - 仅包含字母数字组合（如ICC_SRFCMD_535）
            #     - 排除普通文本（如"KeyVehiclePropertyDvr"不视为信号）
                
            #     2. propId必须满足：
            #     - 支持十进制（如557895715）格式
            #     - 严格匹配`propId: [0-9]+`或`prop: [0-9]+`的文本模式
                
            #     3. 处理特殊情况：
            #     - 若存在多个propId对应同一信号名称，需全部提取
            #     - 即使没有信号名称，也要提取propId（格式为"xxxxxxx"）
            #     - 若propId与信号名称共现，按"信号名称(xxxxxxx)"格式输出
                
            #     4. 输出格式：
            #     - 信号1(xxxx), 信号2(xxxx), (xxxx)...
            #     - 若无匹配项则输出"无法提取"

            #     5. 更关注最后一条评论的信号
                
            #     请特别注意文档中以下关键特征：
            #     - propId可能以"propId:"或"prop:"形式出现
            #     - 信号名称通常紧接在"Name"或"val"字段后
            #     - 信号可能以"信号名=value"的形式出现
            # """,
            "REQUIREMENT_EXTRACT_SYSTEM":
            """
                "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
                "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
                "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
                "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
            """,
            "LOG_SUMMARY_SYSTEM": 
            """
                你是一位专业的汽车电子系统分析师，需要根据提供的问题文档和信号映射关系，提取关键信号在特定时刻的数值，并以表格形式输出。
                任务要求如下：
                1. **识别信号名**：所有信号名称必须为**全英文大写**，且仅包含字母和下划线（如 `ICC_BKCHRGSTARTTIMEHOUR_471`）。
                2. **提取时间戳**：从日志中提取精确到毫秒的时间戳，格式为 `HH:mm:ss.SSS`。
                3. **识别模块名**：从日志行中提取对应的模块名，例如 `ALVehicleManager`, `SignalApi-VehicleControlImpl` 等。
                4. **识别信号值**：提取该信号在当前时刻的具体值。
                5. **识别 property id**：从日志中提取对应的 property id（十进制整数），例如 `557887508`。
                6. **匹配信号名与 property id**：对于每条记录，必须确保信号名和 property id 能够通过文档中的“信号映射关系”进行一一对应，若无法对应则忽略该条目。
                7. **特别说明**：圆括号中的 value 是 property 枚举值（即 property id），而不是信号当前值。例如：`VehicleProperty(value=5017, desc='立即充电和预约充电')` 中 的 `5017` 是 property id，不是实际信号值。
                8. **输出格式**：请将结果整理成如下五列的表格，**按时间戳升序排列**：
                - 时间戳（Timestamp）
                - 模块名（Module Name）
                - 信号名（Signal Name）
                - 信号值（Signal Value）
                - Property ID（Property Id）
                
                请严格按照以下规则处理：
                - 所有信号名称必须符合“全英文 + 下划线”命名规范；
                - 不要添加任何额外解释或说明；
                - 若某条记录无法准确提取或无法在信号映射关系中找到匹配项，则忽略该条目；
                - 输出内容只包含最终表格，不要包含其他文字；
                - **务必保证输出结果按时间戳从小到大排序**。
                
                特别注意：
                - 文档中出现的信号名和 property id 都可以对应到相应的信号动作；
                - 必须严格依据信号映射关系中的映射关系来验证信号名与 property id 是否匹配；
                - 若信号名与 property id 不匹配，或者找不到对应项，则跳过该条记录；
                - 特别注意区分 property wrapper id 和信号当前值，wrapper id 来源于 `VehicleProperty(value=X, ...)` 格式中的 X，而非实际 signal value。
                
                示例输出格式：
                | Timestamp     | Module Name                | Signal Name               | Signal Value | Property Id   |
                |---------------|----------------------------|---------------------------|--------------|---------------|
                | 16:48:14.344  | ALVehicleManager           | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557899792     |
                | 16:48:14.345  | ALVehicleManager           | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557899794     |
                | 16:48:14.345  | ALVehicleManager           | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.507  | SignalApi-VehicleControlImpl | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557887508     |
                | 16:48:14.508  | SignalApi-VehicleControlImpl | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557887509     |
                | 16:48:16.348  | SignalApi-VehicleControlImpl | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.357  | ALVehicleManager           | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.358  | SignalApi-AdapterAPI       | TBOX_BOOKCHRGSETREQ_4CF   | 1            | 557899799     |
                | 16:48:14.506  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.802  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 0            | 557899791     |
                | 16:50:01.939  | SignalApi-VehicleControlImpl | BMS_CHG_STS_32B           | 14           | 557887512     |
            """,
            "ANDROID_QNX_LOG_SUMMARY_SYSTEM":
            """
                我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, 
                我们将要从用户输入的信号映射关系, 选择与信号propid相关或者与信号组相关的日志, 
                再根据信号映射关系和android_qnx日志以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, 
                例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 
                输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1
                例如,对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 
                输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1”
                不需要提取依据和分析要点。只对信号变化进行摘要。
                如果android_qnx日志是空，那么不需要提取，反馈空即可
                模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。
                如果日志中涉及'signalApi-CarOperation', 不要提取。
            """,
            "CONSISTENCY_SYSTEM": 
            """
                你是一名资深 CAN-VHAL 信号一致性分析工程师。你的任务是根据用户输入的{需求描述} {上层提供的信号日志} {安卓+qnx日志}与 {CAN Trace日志}，严格依据以下固定规则进行趋势匹配、对齐窗口查找、上下行一致性分析与异常反馈判断。所有分析必须完全基于输入数据，不得引用规则外信息。
                =================================================
                【规则 1：信号方向识别（必须执行）】
                - 下行（上层写 → CAN）：包含 Cmd、Set、Req、Ctrl、icc、hcu 等关键词
                - 上行（CAN → 上层反馈）：包含 Status、Sts、Feedback、Fb、Rsp 等关键词
                若名称无法判断方向，结合谁先变化判断。

                =================================================
                【规则 2：需求判定】
                根据描述和上层提供的信号日志以及确定的上行下行信号的关系，判断上层下发信号和下发的值，底层需要反馈的信号和需要反馈的值
                - 当需求描述和上层提供的信号日志中，围绕同一业务场景出现多个相关信号（例如同时包含 ICC_SetCLMOn、ICC_THRCLMSWITCH_4D6、TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4 等），你必须综合分析这些信号之间的关系，而不是只挑选其中一个信号做判断。
                - 在给出一致性结论和最终结论时，需要覆盖本次需求中的所有关键下行信号和上行反馈信号，用简短语句把“先下设哪个信号、反馈了哪些信号、反馈值是多少”交代清楚。

                【规则 3：趋势一致性判断】
                趋势 = 值序列 + 时间间隔序列。
                判定为一致需满足水平方向一致和垂直方向一致：
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                -水平向：
                    - 值趋势一致：变化方向一致，或 CAN 趋势是上层趋势某一段的截取部分 
                    （例：上层 1→2→3→4，CAN 2→3→4 依然算一致）
                    - 时间趋势一致：相邻变化的间隔满足：
                    - 间隔比例误差 ≤ 30%，比如
                        "上层在时间0:1:1下设信号A值等于1，底层在时间0:1:1.500下设信号A值等于1，即从上层到底层需要0.5秒；
                        在时间0:1:2底层收到信号B反馈值等于2,在时间0:1:2.480上层收到信号B反馈值等于2,即从底层到上层需要0.48秒，间隔就是0.5-0.48=0.02秒，占比远小于30%;
                        但是存在上层时间和底层时间不同步的问题，比如上层在时间0:1:1.500下设信号A值等于1，底层在时间0:1:1下设信号A值等于1，此时计算上层到底层耗时仍然按照0.5秒计算"
                - 垂直向：
                    -上层日志中，信号A在时间0:1:1下发1，同理在CAN Trace日志中，信号A在时间0:1:1同样下发1
                    -上层日志中，信号A在时间0:1:1获取到值是1且每次获取值都是1，同理在CAN Trace日志中，信号A应该没有描述或者变化为1后不再变化
                - 所有时间戳仅作为相对时间轴，用于判断“先后顺序”和“时间间隔”，不得评价时间戳本身是否合理（例如 1970 年、时区等）

                【规则 4：自动时间窗口匹配（核心能力）】
                上层时间轴通常比 CAN 更长，必须自动寻找最佳对齐窗口。
                同理，上层时间轴比 CAN 更短， 必须自动寻找最佳对齐窗口。
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）

                步骤：
                1. 取 CAN 趋势的值序列，例如 [2,3,4]
                2. 在上层趋势中搜索一个子序列，使得：
                - 上层值趋势包含 CAN 全部趋势
                - 上层对应时间间隔序列与 CAN 间隔序列相似（符合规则 3）
                3. 同理取 上层 趋势的值序列，例如 [2,3,4] 在CAN Trace趋势中搜索一个子序列，使得符合2

                若找到：
                - 将该子序列的时间范围作为唯一有效的对齐时间窗口
                - 后续所有一致性判断必须在此窗口内进行

                若找不到窗口 → 输出：
                “上下层时间不匹配，无法一致性分析。”

                【规则 5：局部配对 + 上下行反馈逻辑（必须执行）】
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                ### 5.1 根据规则 2中的需求，对信号的规则进行判定，在匹配的时间窗口内，对上层下设的值，是否能在CAN Trace中找到相同的下设值；同理对上层需要反馈的值，在CAN Trace中能否找到反馈值，且满足下设后立即反馈（这很重要）
                    - 如果可以在CAN Trace中找到对应的下设，那么认为下设成功，需要进一步查看反馈：
                        - 如果 CAN Trace中，在下设时间后，立即找到需要的反馈值，那么认为这次匹配成功，已经完成透传，不再继续分析，给出结论：vehicle已经透传上下行信号
                        - 如果 CAN Trace中，在下设时间后，没有找到需要的反馈值，那么认为没有反馈，不再继续分析，给出结论：底层未反馈信号，vehicle已经透传
                    - 如果可以在CAN Trace中没有找到对应的下设，那么认为下设并没有到达CAN 总线上，需要分析安卓+qnx日志：
                        - 如果在安卓+qnx日志中找到在对应时间的下设信号和值，且模块是VehicleService，那么认为vehicle已经完成透传，需要mcu分析；给出结论：vehicle已经透传下设信号，但是没有下设到总线，请mcu查看
                        - 如果在安卓+qnx日志中没有找到在对应时间的下设信号和值，那么需要详细分析；给出结论：需要人工分析，没有看到下设，且在android+qnx日志中也看不到下设
                    - 如果没有提取出明确的需求，那么要进行5.2之后的分析
                ### 5.2 局部配对原则
                在匹配的时间窗口内，对每一次下行变化，都要单独寻找对应的上行响应，而不是只看整体起点/终点：

                - 对每次下行变化（如 Cmd 从 0→1），从该时间点起，在一个合理的响应窗口内（例如 0~2s）寻找最近的上行变化：
                - 若上行在该时间窗口内出现 **从相同初始值变化到“期望值”**，则此次操作视为“已响应”
                - 即便上行之后又变回 0 / Not Active，该次操作依然视为“本次响应正常”

                **禁止的误判：**
                - 仅因为上行最终又回到 0（Not Active），就得出“未响应”的结论
                - 仅比较“下行 1→1、上行 1→0”的整体趋势，就说“上行未跟随”

                只有当在整个合理响应时间内，**上行从未达到过与下行对应的目标值**，才允许判断为“未响应”。

                ### 5.3 Status / Feedback 特殊规则
                对 Status、Sts、Feedback、Fb 这类状态/反馈信号，按如下逻辑处理：

                - 若上行信号在一段时间内的取值 = 下行命令值（例如 Cmd=1，Sts 也变为 1），之后再变回 0（Not Active）：
                - 解读为“动作执行完成后退出/复位”
                - 视为“本次命令已经被正确响应”，不能判为“未响应”

                - 只有以下情况才可判为“未响应”：
                - 下行从 0→1、2、3 等有效命令值
                - 在合理响应时间内，上行始终保持原值不变，且从未出现过与命令值相等的阶段
                - 如果下设信号下设值正常到总线，反馈信号

                ### 5.4 上下行反馈分类
                在执行局部配对后，对每对下行/上行做结论：

                - 上行为期望值：本次操作响应正常
                - 上行为期望值，但有明显延迟：响应迟滞，但方向正确，为“正常迟滞”
                - 上行方向错误（例如命令 1，反馈 2 或 3，且需求中定义为异常）：视为“模块问题或需求问题”
                - 上行出现 Fail / Error / 未在需求中定义的值：需标记为“需求确认 / 模块分析”
                - 如果 CAN trace 中：
                - 所有关联的下行信号都按需求正确下设（值发生了期望的变化），并且
                - 对应的上行反馈信号也在合理时间窗口内达到需求期望值
                则你必须认为 “VHAL 已完成透传”，并按照下面的固定句式给出最终结论，不得再讨论时间戳异常、日志截取问题、时间不同步等内容：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                其中：
                - <下设信号1>：替换为本次关键的下行信号名称，如 ICC_SetCLMOn 或 ICC_THRCLMSWITCH_4D6；
                - <值1>：替换为该信号在本次操作中下设的目标值，如 2 或 1；
                - <上报信号A>、<上报信号B>：替换为实际参与反馈的上行信号名称，如 TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4；
                - 若只有一个反馈信号，可只写一个；若有多个，按逗号列出。
                - 当 CAN trace 显示“下设后反馈正常，但业务上存在联动、逻辑与需求描述不一致”时，你只需要在一致性结论中明确说明 “CAN trace 显示 VHAL 已完成透传”，并在最终结论中使用上述固定句式收尾。
                - 你不负责评估业务联动逻辑本身是否合理，也不要在结论中写“底层逻辑存在矛盾”“与规范冲突”等判断，只需要提示“请按需求确认原因并转对应模块分析”。

                    若 CAN 反馈趋势与上层日志完全一致，则必须在结论中明确说明：
                “CAN trace 显示 VHAL 已完成透传。”

                =================================================
                【规则 6：当 CAN 出现 Fail/错误值时的特殊结论】
                只要 CAN 中的反馈信号不存在，必须输出如下句式：
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                只要 CAN 反馈趋势与上层趋势一致，必须输出如下句式（用于自动判断）：
                “从 CAN trace 可见 VHAL 已完成透传，该异常需由业务/ECU 侧确认原因，并转对应模块分析。”
                =================================================
                【规则 7：信号只有三个及以下的时候，单独看cantrace的输出】
                如果有一个信号的值变化过，其他的信号值没有变化过，那么说明信号没有没有反馈
                比如：“信号ICC_AirconditionMode已经正常下设（值变化），但是在ICC_AirconditionMode值变化之后的瞬间，信号TMS_ACModeCustomSts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                比如：“信号ICC_AirconditionMode的值没有变化，但是信号TMS_ACModeCustomSts却在变化，（因为没有下设激励是不应该反馈的），vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                =================================================

                【规则 8：输出格式（必须严格遵守）】

                当时间窗口成功匹配时，你必须输出以下内容：
                1）下设信号（即所有下行信号名称）
                格式：
                下设信号："ICC_FRSitPosnlocation","ICC_FRMemoryRecoveryCmd"

                2）上报信号（即所有上行信号名称）
                格式：
                上报信号："FRZCU_FRSitPosnSts","FRZCU_FRMemoryFb"

                3）匹配到的上层时间窗口范围  
                格式示例：
                “上层匹配时间：14:58:51.83 ~ 14:59:11.50”
                “CAN 总线匹配时间：14:58:56.83 ~ 14:59:16.50”

                4）上下趋势对比（值趋势 + 时间趋势）  
                示例：
                “下行 ICC_FRSitPosnlocation：1 → 0  
                上行 FRZCU_FRSitPosnSts：1 → 0  
                值趋势一致，时间间隔一致。”

                5）一致性结论  
                必须明确，如：
                - 上下趋势一致  
                - CAN 是上层趋势的截取部分，一致  
                - 反馈延迟但方向一致，可接受  
                - 上行出现异常值，需要确认  

                6） 根据一致性结论，给出最终结论，最终结论：
                比如:"从cantrace来看，信号IHU_5_BlowSpeedLevel_Req下设9，信号CEM_IPM_FrontBlowSpdCtrlsts反馈9，但是信号CEM_IPM_FrontOFFSts反馈1，vhal已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号Set_ESPFunctionSts已经正常下设2，但是信号ESPSwitchStatus有不变化的情况（图中标记处）；信号Set_CSTFunctionSts已经正常下设2，但是信号CST_Status有不变化的情况（图中标记处）；vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号CTP_PowerModeSet已经正常下设1，但是信号HCU_PowerModeFed保持2没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号ICC_ChbCoolorheat_Req已经正常下设，但是信号CHB_AppCoolorheat_Sts一直是3没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "从qnx日志看，信号ICC_ExhibitionModeSwitch已经下设，但是信号VCU_2_G_ExhibitionMod和信号FLZCU_CarMode没有反馈
                从cantrace来看，cantrace截取时间是12-03 08:36:57 与视频时间不符，CAN trace文件抓取的抓取时间无法定位问题，请将车机时间设置为北京时间或者拍摄视频时带上时间水印，复测并提取问题发生时的Android log, QNX log, 并在开始操作之前就抓取CAN trace！直到操作结束，导出。依次从应用->Framework再转给VHAL分析，谢谢。"
                " 从CAN trace，和上层的需求来看，信号FLZCU_RecoverFb有反馈2的情况，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                “从CAN trace来看：ICC_CWCWorkingStsSet 下发1之后 CWC_workingSts 仍然保持1，上层希望反馈反馈0，请按照需求确认问题原因并转对应模块分析，谢谢。”
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                
                - 只要前面的分析结论表明：下设和反馈在 CAN trace 中都能找到、方向正确、且在合理时间范围内完成（即判定为 VHAL 已完成透传），则最终结论必须使用以下句式之一进行收尾：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                或者同结构的等价表述，但必须同时满足：
                - 明确提到关键下设信号和关键反馈信号；
                - 明确包含“vehicle已经透传”；
                - 结尾句式为“请按需求确认原因并转对应模块分析，谢谢”。

                =================================================
                请严格按照以上规则分析下面输入的数据，且必须给出最终结论。不得使用规则外信息。
            """,
            "COMPARE_CANTRACE":
            """
                我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, 
                梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。
                请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,
                比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；
                比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）
                给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。
                比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。
            """
        }
    },
    # FL2-15631
    # chery 8255 T1J-FL2-8255
    {
        "name":"chery T1J-FL2-8255",
        # "jql":"project in (CHERY-T1J-FL2-8255) AND issue =FL2-15509",#
        "jql": "project in (CHERY-T1J-FL2-8255) AND assignee in (currentUser()) ORDER BY updated DESC",
        "expand": "changelog",

        "base_paths": {
            "json_dir":  "../../config——chery/8255",      # 例如: ./data/json/config_T1J.json
            "dbc_dir":   "../../config——chery/8255",       # 例如: ./data/dbc/car_T1J.dbc
            "proto_dir": "../../config——chery/8255",     # 例如: ./data/proto/T1J_vehicle.proto
        },

        # 车型到“文件名(或列表)”的映射（不含目录）
        # 支持 str 或 [str, str, ...]。可按需增减车型。
        "model_to_files": {
            "T1J-FL2": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J_FL2": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J_FL2_8255": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J-FL2-8255": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J FL2 8255": {
                "json":  ["config_T1J_FL2.json"],
                "dbc":   ["car_T1J_FL2.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
        },

        # 可选兜底：当票名里没有【车型】或车型不在映射表时使用
        "fallback_files": {
            "json":  "config_default.json",
            "dbc":   "car_default.dbc",
            "proto": "default_vehicle.proto"
        },
        "prompts": {
            "EXTRACT_SIGNALS_SYSTEM": 
            """
            请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'
            如果{标题}中包含"重启"， "str", "重新上电"，"电源"，"上下电"类似的字样，需要根据{model}额外提取对应的电源信号
            model是T1LFL1相关车型需要添加CEM_2_KeySts信号
            model是D01相关的车型需要添加FLZCU_9_PowerMode信号
            """,
            # """
            #     请从用户提供的{问题描述}中提取评论中出现的所有信号名称及对应的propId（格式为"信号名称(xxxxxxx)"），遵循以下规则：
            #     1. 信号名称必须满足：
            #     - 仅包含字母数字组合（如ICC_SRFCMD_535）
            #     - 排除普通文本（如"KeyVehiclePropertyDvr"不视为信号）
                
            #     2. propId必须满足：
            #     - 支持十进制（如557895715）格式
            #     - 严格匹配`propId: [0-9]+`或`prop: [0-9]+`的文本模式
                
            #     3. 处理特殊情况：
            #     - 若存在多个propId对应同一信号名称，需全部提取
            #     - 即使没有信号名称，也要提取propId（格式为"xxxxxxx"）
            #     - 若propId与信号名称共现，按"信号名称(xxxxxxx)"格式输出
                
            #     4. 输出格式：
            #     - 信号1(xxxx), 信号2(xxxx), (xxxx)...
            #     - 若无匹配项则输出"无法提取"

            #     5. 更关注最后一条评论的信号
                
            #     请特别注意文档中以下关键特征：
            #     - propId可能以"propId:"或"prop:"形式出现
            #     - 信号名称通常紧接在"Name"或"val"字段后
            #     - 信号可能以"信号名=value"的形式出现
            # """,
            "REQUIREMENT_EXTRACT_SYSTEM":
            """
                "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
                "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
                "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
                "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
            """,
            "LOG_SUMMARY_SYSTEM": 
            """
                你是一位专业的汽车电子系统分析师，需要根据提供的问题文档和信号映射关系，提取关键信号在特定时刻的数值，并以表格形式输出。
                任务要求如下：
                1. **识别信号名**：所有信号名称必须为**全英文大写**，且仅包含字母和下划线（如 `ICC_BKCHRGSTARTTIMEHOUR_471`）。
                2. **提取时间戳**：从日志中提取精确到毫秒的时间戳，格式为 `HH:mm:ss.SSS`。
                3. **识别模块名**：从日志行中提取对应的模块名，例如 `ALVehicleManager`, `SignalApi-VehicleControlImpl` 等。
                4. **识别信号值**：提取该信号在当前时刻的具体值。
                5. **识别 property id**：从日志中提取对应的 property id（十进制整数），例如 `557887508`。
                6. **匹配信号名与 property id**：对于每条记录，必须确保信号名和 property id 能够通过文档中的“信号映射关系”进行一一对应，若无法对应则忽略该条目。
                7. **特别说明**：圆括号中的 value 是 property 枚举值（即 property id），而不是信号当前值。例如：`VehicleProperty(value=5017, desc='立即充电和预约充电')` 中 的 `5017` 是 property id，不是实际信号值。
                8. **输出格式**：请将结果整理成如下五列的表格，**按时间戳升序排列**：
                - 时间戳（Timestamp）
                - 模块名（Module Name）
                - 信号名（Signal Name）
                - 信号值（Signal Value）
                - Property ID（Property Id）
                
                请严格按照以下规则处理：
                - 所有信号名称必须符合“全英文 + 下划线”命名规范；
                - 不要添加任何额外解释或说明；
                - 若某条记录无法准确提取或无法在信号映射关系中找到匹配项，则忽略该条目；
                - 输出内容只包含最终表格，不要包含其他文字；
                - **务必保证输出结果按时间戳从小到大排序**。
                
                特别注意：
                - 文档中出现的信号名和 property id 都可以对应到相应的信号动作；
                - 必须严格依据信号映射关系中的映射关系来验证信号名与 property id 是否匹配；
                - 若信号名与 property id 不匹配，或者找不到对应项，则跳过该条记录；
                - 特别注意区分 property wrapper id 和信号当前值，wrapper id 来源于 `VehicleProperty(value=X, ...)` 格式中的 X，而非实际 signal value。
                
                示例输出格式：
                | Timestamp     | Module Name                | Signal Name               | Signal Value | Property Id   |
                |---------------|----------------------------|---------------------------|--------------|---------------|
                | 16:48:14.344  | ALVehicleManager           | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557899792     |
                | 16:48:14.345  | ALVehicleManager           | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557899794     |
                | 16:48:14.345  | ALVehicleManager           | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.507  | SignalApi-VehicleControlImpl | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557887508     |
                | 16:48:14.508  | SignalApi-VehicleControlImpl | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557887509     |
                | 16:48:16.348  | SignalApi-VehicleControlImpl | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.357  | ALVehicleManager           | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.358  | SignalApi-AdapterAPI       | TBOX_BOOKCHRGSETREQ_4CF   | 1            | 557899799     |
                | 16:48:14.506  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.802  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 0            | 557899791     |
                | 16:50:01.939  | SignalApi-VehicleControlImpl | BMS_CHG_STS_32B           | 14           | 557887512     |
            """,
            "ANDROID_QNX_LOG_SUMMARY_SYSTEM":
            """
                我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, 
                我们将要从用户输入的信号映射关系, 选择与信号propid相关或者与信号组相关的日志, 
                再根据信号映射关系和android_qnx日志以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, 
                例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 
                输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1
                例如,对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 
                输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1” (其中0X2140C0AD是信号的十六进制propid， 根据信号映射关系去更新)
                不需要提取依据和分析要点。只对信号变化进行摘要。
                如果android_qnx日志是空，那么不需要提取，反馈空即可
                模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。
                如果日志中涉及'signalApi-CarOperation', 不要提取。
            """,
            "CONSISTENCY_SYSTEM": 
            """
                你是一名资深 CAN-VHAL 信号一致性分析工程师。你的任务是根据用户输入的{需求描述} {上层提供的信号日志} {安卓+qnx日志}与 {CAN Trace日志}，严格依据以下固定规则进行趋势匹配、对齐窗口查找、上下行一致性分析与异常反馈判断。所有分析必须完全基于输入数据，不得引用规则外信息。
                =================================================
                【规则 1：信号方向识别（必须执行）】
                - 下行（上层写 → CAN）：包含 Cmd、Set、Req、Ctrl、icc、hcu 等关键词
                - 上行（CAN → 上层反馈）：包含 Status、Sts、Feedback、Fb、Rsp 等关键词
                若名称无法判断方向，结合谁先变化判断。

                =================================================
                【规则 2：需求判定】
                根据描述和上层提供的信号日志以及确定的上行下行信号的关系，判断上层下发信号和下发的值，底层需要反馈的信号和需要反馈的值
                - 当需求描述和上层提供的信号日志中，围绕同一业务场景出现多个相关信号（例如同时包含 ICC_SetCLMOn、ICC_THRCLMSWITCH_4D6、TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4 等），你必须综合分析这些信号之间的关系，而不是只挑选其中一个信号做判断。
                - 在给出一致性结论和最终结论时，需要覆盖本次需求中的所有关键下行信号和上行反馈信号，用简短语句把“先下设哪个信号、反馈了哪些信号、反馈值是多少”交代清楚。

                【规则 3：趋势一致性判断】
                趋势 = 值序列 + 时间间隔序列。
                判定为一致需满足水平方向一致和垂直方向一致：
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                -水平向：
                    - 值趋势一致：变化方向一致，或 CAN 趋势是上层趋势某一段的截取部分 
                    （例：上层 1→2→3→4，CAN 2→3→4 依然算一致）
                    - 时间趋势一致：相邻变化的间隔满足：
                    - 间隔比例误差 ≤ 30%，比如
                        "上层在时间0:1:1下设信号A值等于1，底层在时间0:1:1.500下设信号A值等于1，即从上层到底层需要0.5秒；
                        在时间0:1:2底层收到信号B反馈值等于2,在时间0:1:2.480上层收到信号B反馈值等于2,即从底层到上层需要0.48秒，间隔就是0.5-0.48=0.02秒，占比远小于30%;
                        但是存在上层时间和底层时间不同步的问题，比如上层在时间0:1:1.500下设信号A值等于1，底层在时间0:1:1下设信号A值等于1，此时计算上层到底层耗时仍然按照0.5秒计算"
                - 垂直向：
                    -上层日志中，信号A在时间0:1:1下发1，同理在CAN Trace日志中，信号A在时间0:1:1同样下发1
                    -上层日志中，信号A在时间0:1:1获取到值是1且每次获取值都是1，同理在CAN Trace日志中，信号A应该没有描述或者变化为1后不再变化
                - 所有时间戳仅作为相对时间轴，用于判断“先后顺序”和“时间间隔”，不得评价时间戳本身是否合理（例如 1970 年、时区等）

                【规则 4：自动时间窗口匹配（核心能力）】
                上层时间轴通常比 CAN 更长，必须自动寻找最佳对齐窗口。
                同理，上层时间轴比 CAN 更短， 必须自动寻找最佳对齐窗口。
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）

                步骤：
                1. 取 CAN 趋势的值序列，例如 [2,3,4]
                2. 在上层趋势中搜索一个子序列，使得：
                - 上层值趋势包含 CAN 全部趋势
                - 上层对应时间间隔序列与 CAN 间隔序列相似（符合规则 3）
                3. 同理取 上层 趋势的值序列，例如 [2,3,4] 在CAN Trace趋势中搜索一个子序列，使得符合2

                若找到：
                - 将该子序列的时间范围作为唯一有效的对齐时间窗口
                - 后续所有一致性判断必须在此窗口内进行

                若找不到窗口 → 输出：
                “上下层时间不匹配，无法一致性分析。”

                【规则 5：局部配对 + 上下行反馈逻辑（必须执行）】
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                ### 5.1 根据规则 2中的需求，对信号的规则进行判定，在匹配的时间窗口内，对上层下设的值，是否能在CAN Trace中找到相同的下设值；同理对上层需要反馈的值，在CAN Trace中能否找到反馈值，且满足下设后立即反馈（这很重要）
                    - 如果可以在CAN Trace中找到对应的下设，那么认为下设成功，需要进一步查看反馈：
                        - 如果 CAN Trace中，在下设时间后，立即找到需要的反馈值，那么认为这次匹配成功，已经完成透传，不再继续分析，给出结论：vehicle已经透传上下行信号
                        - 如果 CAN Trace中，在下设时间后，没有找到需要的反馈值，那么认为没有反馈，不再继续分析，给出结论：底层未反馈信号，vehicle已经透传
                    - 如果可以在CAN Trace中没有找到对应的下设，那么认为下设并没有到达CAN 总线上，需要分析安卓+qnx日志：
                        - 如果在安卓+qnx日志中找到在对应时间的下设信号和值，且模块是VehicleService，那么认为vehicle已经完成透传，需要mcu分析；给出结论：vehicle已经透传下设信号，但是没有下设到总线，请mcu查看
                        - 如果在安卓+qnx日志中没有找到在对应时间的下设信号和值，那么需要详细分析；给出结论：需要人工分析，没有看到下设，且在android+qnx日志中也看不到下设
                    - 如果没有提取出明确的需求，那么要进行5.2之后的分析
                ### 5.2 局部配对原则
                在匹配的时间窗口内，对每一次下行变化，都要单独寻找对应的上行响应，而不是只看整体起点/终点：

                - 对每次下行变化（如 Cmd 从 0→1），从该时间点起，在一个合理的响应窗口内（例如 0~2s）寻找最近的上行变化：
                - 若上行在该时间窗口内出现 **从相同初始值变化到“期望值”**，则此次操作视为“已响应”
                - 即便上行之后又变回 0 / Not Active，该次操作依然视为“本次响应正常”

                **禁止的误判：**
                - 仅因为上行最终又回到 0（Not Active），就得出“未响应”的结论
                - 仅比较“下行 1→1、上行 1→0”的整体趋势，就说“上行未跟随”

                只有当在整个合理响应时间内，**上行从未达到过与下行对应的目标值**，才允许判断为“未响应”。

                ### 5.3 Status / Feedback 特殊规则
                对 Status、Sts、Feedback、Fb 这类状态/反馈信号，按如下逻辑处理：

                - 若上行信号在一段时间内的取值 = 下行命令值（例如 Cmd=1，Sts 也变为 1），之后再变回 0（Not Active）：
                - 解读为“动作执行完成后退出/复位”
                - 视为“本次命令已经被正确响应”，不能判为“未响应”

                - 只有以下情况才可判为“未响应”：
                - 下行从 0→1、2、3 等有效命令值
                - 在合理响应时间内，上行始终保持原值不变，且从未出现过与命令值相等的阶段
                - 如果下设信号下设值正常到总线，反馈信号

                ### 5.4 上下行反馈分类
                在执行局部配对后，对每对下行/上行做结论：

                - 上行为期望值：本次操作响应正常
                - 上行为期望值，但有明显延迟：响应迟滞，但方向正确，为“正常迟滞”
                - 上行方向错误（例如命令 1，反馈 2 或 3，且需求中定义为异常）：视为“模块问题或需求问题”
                - 上行出现 Fail / Error / 未在需求中定义的值：需标记为“需求确认 / 模块分析”
                - 如果 CAN trace 中：
                - 所有关联的下行信号都按需求正确下设（值发生了期望的变化），并且
                - 对应的上行反馈信号也在合理时间窗口内达到需求期望值
                则你必须认为 “VHAL 已完成透传”，并按照下面的固定句式给出最终结论，不得再讨论时间戳异常、日志截取问题、时间不同步等内容：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                其中：
                - <下设信号1>：替换为本次关键的下行信号名称，如 ICC_SetCLMOn 或 ICC_THRCLMSWITCH_4D6；
                - <值1>：替换为该信号在本次操作中下设的目标值，如 2 或 1；
                - <上报信号A>、<上报信号B>：替换为实际参与反馈的上行信号名称，如 TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4；
                - 若只有一个反馈信号，可只写一个；若有多个，按逗号列出。
                - 当 CAN trace 显示“下设后反馈正常，但业务上存在联动、逻辑与需求描述不一致”时，你只需要在一致性结论中明确说明 “CAN trace 显示 VHAL 已完成透传”，并在最终结论中使用上述固定句式收尾。
                - 你不负责评估业务联动逻辑本身是否合理，也不要在结论中写“底层逻辑存在矛盾”“与规范冲突”等判断，只需要提示“请按需求确认原因并转对应模块分析”。

                    若 CAN 反馈趋势与上层日志完全一致，则必须在结论中明确说明：
                “CAN trace 显示 VHAL 已完成透传。”

                =================================================
                【规则 6：当 CAN 出现 Fail/错误值时的特殊结论】
                只要 CAN 中的反馈信号不存在，必须输出如下句式：
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                只要 CAN 反馈趋势与上层趋势一致，必须输出如下句式（用于自动判断）：
                “从 CAN trace 可见 VHAL 已完成透传，该异常需由业务/ECU 侧确认原因，并转对应模块分析。”
                =================================================
                【规则 7：信号只有三个及以下的时候，单独看cantrace的输出】
                如果有一个信号的值变化过，其他的信号值没有变化过，那么说明信号没有没有反馈
                比如：“信号ICC_AirconditionMode已经正常下设（值变化），但是在ICC_AirconditionMode值变化之后的瞬间，信号TMS_ACModeCustomSts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                比如：“信号ICC_AirconditionMode的值没有变化，但是信号TMS_ACModeCustomSts却在变化，（因为没有下设激励是不应该反馈的），vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                =================================================

                【规则 8：输出格式（必须严格遵守）】

                当时间窗口成功匹配时，你必须输出以下内容：
                1）下设信号（即所有下行信号名称）
                格式：
                下设信号："ICC_FRSitPosnlocation","ICC_FRMemoryRecoveryCmd"

                2）上报信号（即所有上行信号名称）
                格式：
                上报信号："FRZCU_FRSitPosnSts","FRZCU_FRMemoryFb"

                3）匹配到的上层时间窗口范围  
                格式示例：
                “上层匹配时间：14:58:51.83 ~ 14:59:11.50”
                “CAN 总线匹配时间：14:58:56.83 ~ 14:59:16.50”

                4）上下趋势对比（值趋势 + 时间趋势）  
                示例：
                “下行 ICC_FRSitPosnlocation：1 → 0  
                上行 FRZCU_FRSitPosnSts：1 → 0  
                值趋势一致，时间间隔一致。”

                5）一致性结论  
                必须明确，如：
                - 上下趋势一致  
                - CAN 是上层趋势的截取部分，一致  
                - 反馈延迟但方向一致，可接受  
                - 上行出现异常值，需要确认  

                6） 根据一致性结论，给出最终结论，最终结论：
                比如:"从cantrace来看，信号IHU_5_BlowSpeedLevel_Req下设9，信号CEM_IPM_FrontBlowSpdCtrlsts反馈9，但是信号CEM_IPM_FrontOFFSts反馈1，vhal已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号Set_ESPFunctionSts已经正常下设2，但是信号ESPSwitchStatus有不变化的情况（图中标记处）；信号Set_CSTFunctionSts已经正常下设2，但是信号CST_Status有不变化的情况（图中标记处）；vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号CTP_PowerModeSet已经正常下设1，但是信号HCU_PowerModeFed保持2没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号ICC_ChbCoolorheat_Req已经正常下设，但是信号CHB_AppCoolorheat_Sts一直是3没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "从qnx日志看，信号ICC_ExhibitionModeSwitch已经下设，但是信号VCU_2_G_ExhibitionMod和信号FLZCU_CarMode没有反馈
                从cantrace来看，cantrace截取时间是12-03 08:36:57 与视频时间不符，CAN trace文件抓取的抓取时间无法定位问题，请将车机时间设置为北京时间或者拍摄视频时带上时间水印，复测并提取问题发生时的Android log, QNX log, 并在开始操作之前就抓取CAN trace！直到操作结束，导出。依次从应用->Framework再转给VHAL分析，谢谢。"
                " 从CAN trace，和上层的需求来看，信号FLZCU_RecoverFb有反馈2的情况，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                “从CAN trace来看：ICC_CWCWorkingStsSet 下发1之后 CWC_workingSts 仍然保持1，上层希望反馈反馈0，请按照需求确认问题原因并转对应模块分析，谢谢。”
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                
                - 只要前面的分析结论表明：下设和反馈在 CAN trace 中都能找到、方向正确、且在合理时间范围内完成（即判定为 VHAL 已完成透传），则最终结论必须使用以下句式之一进行收尾：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                或者同结构的等价表述，但必须同时满足：
                - 明确提到关键下设信号和关键反馈信号；
                - 明确包含“vehicle已经透传”；
                - 结尾句式为“请按需求确认原因并转对应模块分析，谢谢”。

                =================================================
                请严格按照以上规则分析下面输入的数据，且必须给出最终结论。不得使用规则外信息。
            """,
            "COMPARE_CANTRACE":
            """
                我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, 
                梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。
                请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,
                比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；
                比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）
                给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。
                比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。
            """
        }
    },

        # "jql": "project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND issue = CHERY-8543",
    
    # chery 8255 D01系列
    {   
        "name":"chery D01-8255",
        # "jql":"project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND issue =DPINT-2941", #
        "jql": "project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND assignee = currentUser() AND resolution = Unresolved order by updated DESC",
        "expand": "changelog",

        "base_paths": {
            "json_dir":  "../../config——chery/8255",      # 例如: ./data/json/config_T1J.json
            "dbc_dir":   "../../config——chery/8255",       # 例如: ./data/dbc/car_T1J.dbc
            "proto_dir": "../../config——chery/8255",     # 例如: ./data/proto/T1J_vehicle.proto
        },

        # 车型到“文件名(或列表)”的映射（不含目录）
        # 支持 str 或 [str, str, ...]。可按需增减车型。
        "model_to_files": {
            "D01国际APA": {
                "json":  ["config_D01_OS_APA.json"],
                "dbc":   ["car_D01_OS_APA.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01国际": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01P国际": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01R2": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01-OTA": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01国内": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01P国内": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01P": {
                "json":  ["config_D01.json"],
                "dbc":   ["car_D01.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01华为": {
                "json":  ["config_D01_HW.json"],
                "dbc":   ["car_D01_HW.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01-华为": {
                "json":  ["config_D01_HW.json"],
                "dbc":   ["car_D01_HW.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "D01HW": {
                "json":  ["config_D01_HW.json"],
                "dbc":   ["car_D01_HW.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
        },

        # 可选兜底：当票名里没有【车型】或车型不在映射表时使用
        "fallback_files": {
            "json":  "config_default.json",
            "dbc":   "car_default.dbc",
            "proto": "default_vehicle.proto"
        },
        "prompts": {
            "EXTRACT_SIGNALS_SYSTEM": 
            """
            请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'
            如果{标题}中包含"重启"， "str", "重新上电"，"电源"，"上下电"类似的字样，需要根据{model}额外提取对应的电源信号
            model是T1LFL1相关车型需要添加CEM_2_KeySts信号
            model是D01相关的车型需要添加FLZCU_9_PowerMode信号
            """,
            # """
            #     请从用户提供的{问题描述}中提取评论中出现的所有信号名称及对应的propId（格式为"信号名称(xxxxxxx)"），遵循以下规则：
            #     1. 信号名称必须满足：
            #     - 仅包含字母数字组合（如ICC_SRFCMD_535，ACU_1_SecRowLBeltWarning）
            #     - 排除普通文本（如"KeyVehiclePropertyDvr"不视为信号）
                
            #     2. propId必须满足：
            #     - 支持十进制（如557895715）格式
            #     - 严格匹配`propId: [0-9]+`或`prop: [0-9]+`的文本模式
                
            #     3. 处理特殊情况：
            #     - 若存在多个propId对应同一信号名称，需全部提取
            #     - 即使没有信号名称，也要提取propId（格式为"xxxxxxx"）
            #     - 若propId与信号名称共现，按"信号名称(xxxxxxx)"格式输出
                
            #     4. 输出格式：
            #     - 信号1(xxxx), 信号2(xxxx), (xxxx)...
            #     - 若无匹配项则输出"无法提取"

            #     5. 更关注最后一条评论的信号，如果最后一条评论没有信号，再向上去其他评论检索信号
                
            #     请特别注意文档中以下关键特征：
            #     - propId可能以"propId:"或"prop:"形式出现
            #     - 信号名称通常紧接在"Name"或"val"字段后
            #     - 信号可能以"信号名=value"的形式出现
            # """,
            "REQUIREMENT_EXTRACT_SYSTEM":
            """
                "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
                "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
                "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
                "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
                "比如：空调开关反馈信号    CEM_IPM_FRONTOFFSTS_51A    557895817 空调风速调节请求信号    IHU_5_BLOWSPEEDLEVEL_REQ_52F    557895843  空调风速调节状态反馈信号    CEM_IPM_FRONTBLOWSPDCTRLSTS_51A    557895844  16:20:09.335下设风速请求= 9，16:20:09.912收到风速反馈 = 9，空调开关反馈 = 1 ，开关关闭
                    请接续收到空调开关反馈信号 = 0x1 的原因； 提取需求结果：信号IHU_5_BLOWSPEEDLEVEL_REQ_52F下设9，信号 CEM_IPM_FRONTOFFSTS_51A 反馈9, 希望调查底层反馈信号 CEM_IPM_FRONTBLOWSPDCTRLSTS_51A 的值是不是1，是1的话，就说明vehicle已经透传，不是1，就说明vehicle有点问题"
            """,
            "LOG_SUMMARY_SYSTEM": 
            """
                你是一位专业的汽车电子系统分析师，需要根据提供的问题文档和信号映射关系，提取关键信号在特定时刻的数值，并以表格形式输出。
                任务要求如下：
                1. **识别信号名**：所有信号名称必须为**全英文大写**，且仅包含字母和下划线（如 `ICC_BKCHRGSTARTTIMEHOUR_471`）。
                2. **提取时间戳**：从日志中提取精确到毫秒的时间戳，格式为 `HH:mm:ss.SSS`。
                3. **识别模块名**：从日志行中提取对应的模块名，例如 `ALVehicleManager`, `SignalApi-VehicleControlImpl` 等。
                4. **识别信号值**：提取该信号在当前时刻的具体值。
                5. **识别 property id**：从日志中提取对应的 property id（十进制整数），例如 `557887508`。
                6. **匹配信号名与 property id**：对于每条记录，必须确保信号名和 property id 能够通过文档中的“信号映射关系”进行一一对应，若无法对应则忽略该条目。
                7. **特别说明**：圆括号中的 value 是 property 枚举值（即 property id），而不是信号当前值。例如：`VehicleProperty(value=5017, desc='立即充电和预约充电')` 中 的 `5017` 是 property id，不是实际信号值。
                8. **输出格式**：请将结果整理成如下五列的表格，**按时间戳升序排列**：
                - 时间戳（Timestamp）
                - 模块名（Module Name）
                - 信号名（Signal Name）
                - 信号值（Signal Value）
                - Property ID（Property Id）
                
                请严格按照以下规则处理：
                - 所有信号名称必须符合“全英文 + 下划线”命名规范；
                - 不要添加任何额外解释或说明；
                - 若某条记录无法准确提取或无法在信号映射关系中找到匹配项，则忽略该条目；
                - 输出内容只包含最终表格，不要包含其他文字；
                - **务必保证输出结果按时间戳从小到大排序**。
                
                特别注意：
                - 文档中出现的信号名和 property id 都可以对应到相应的信号动作；
                - 必须严格依据信号映射关系中的映射关系来验证信号名与 property id 是否匹配；
                - 若信号名与 property id 不匹配，或者找不到对应项，则跳过该条记录；
                - 特别注意区分 property wrapper id 和信号当前值，wrapper id 来源于 `VehicleProperty(value=X, ...)` 格式中的 X，而非实际 signal value。
                
                示例输出格式：
                | Timestamp     | Module Name                | Signal Name               | Signal Value | Property Id   |
                |---------------|----------------------------|---------------------------|--------------|---------------|
                | 16:48:14.344  | ALVehicleManager           | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557899792     |
                | 16:48:14.345  | ALVehicleManager           | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557899794     |
                | 16:48:14.345  | ALVehicleManager           | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.507  | SignalApi-VehicleControlImpl | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557887508     |
                | 16:48:14.508  | SignalApi-VehicleControlImpl | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557887509     |
                | 16:48:16.348  | SignalApi-VehicleControlImpl | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.357  | ALVehicleManager           | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.358  | SignalApi-AdapterAPI       | TBOX_BOOKCHRGSETREQ_4CF   | 1            | 557899799     |
                | 16:48:14.506  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.802  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 0            | 557899791     |
                | 16:50:01.939  | SignalApi-VehicleControlImpl | BMS_CHG_STS_32B           | 14           | 557887512     |
            """,
            "ANDROID_QNX_LOG_SUMMARY_SYSTEM":
            """
                我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, 
                我们将要从用户输入的信号映射关系, 选择与信号propid相关或者与信号组相关的日志, 
                再根据信号映射关系和android_qnx日志以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, 
                例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 
                输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1
                例如,对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 
                输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1” (其中0X2140C0AD是信号的十六进制propid， 根据信号映射关系去更新)
                不需要提取依据和分析要点。只对信号变化进行摘要。
                如果android_qnx日志是空，那么不需要提取，反馈空即可
                模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。
                如果日志中涉及'signalApi-CarOperation', 不要提取。
            """,
            "CONSISTENCY_SYSTEM": 
            """
                你是一名资深 CAN-VHAL 信号一致性分析工程师。你的任务是根据用户输入的{需求描述} {上层提供的信号日志} {安卓+qnx日志}与 {CAN Trace日志}，严格依据以下固定规则进行趋势匹配、对齐窗口查找、上下行一致性分析与异常反馈判断。所有分析必须完全基于输入数据，不得引用规则外信息。
                =================================================
                【规则 1：信号方向识别（必须执行）】
                - 下行（上层写 → CAN）：包含 Cmd、Set、Req、Ctrl、icc、hcu 等关键词
                - 上行（CAN → 上层反馈）：包含 Status、Sts、Feedback、Fb、Rsp 等关键词
                若名称无法判断方向，结合谁先变化判断。

                =================================================
                【规则 2：需求判定】
                根据描述和上层提供的信号日志以及确定的上行下行信号的关系，判断上层下发信号和下发的值，底层需要反馈的信号和需要反馈的值
                - 当需求描述和上层提供的信号日志中，围绕同一业务场景出现多个相关信号（例如同时包含 ICC_SetCLMOn、ICC_THRCLMSWITCH_4D6、TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4 等），你必须综合分析这些信号之间的关系，而不是只挑选其中一个信号做判断。
                - 在给出一致性结论和最终结论时，需要覆盖本次需求中的所有关键下行信号和上行反馈信号，用简短语句把“先下设哪个信号、反馈了哪些信号、反馈值是多少”交代清楚。

                【规则 3：趋势一致性判断】
                趋势 = 值序列 + 时间间隔序列。
                判定为一致需满足水平方向一致和垂直方向一致：
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                -水平向：
                    - 值趋势一致：变化方向一致，或 CAN 趋势是上层趋势某一段的截取部分 
                    （例：上层 1→2→3→4，CAN 2→3→4 依然算一致）
                    - 时间趋势一致：相邻变化的间隔满足：
                    - 间隔比例误差 ≤ 30%，比如
                        "上层在时间0:1:1下设信号A值等于1，底层在时间0:1:1.500下设信号A值等于1，即从上层到底层需要0.5秒；
                        在时间0:1:2底层收到信号B反馈值等于2,在时间0:1:2.480上层收到信号B反馈值等于2,即从底层到上层需要0.48秒，间隔就是0.5-0.48=0.02秒，占比远小于30%;
                        但是存在上层时间和底层时间不同步的问题，比如上层在时间0:1:1.500下设信号A值等于1，底层在时间0:1:1下设信号A值等于1，此时计算上层到底层耗时仍然按照0.5秒计算"
                - 垂直向：
                    -上层日志中，信号A在时间0:1:1下发1，同理在CAN Trace日志中，信号A在时间0:1:1同样下发1
                    -上层日志中，信号A在时间0:1:1获取到值是1且每次获取值都是1，同理在CAN Trace日志中，信号A应该没有描述或者变化为1后不再变化
                - 所有时间戳仅作为相对时间轴，用于判断“先后顺序”和“时间间隔”，不得评价时间戳本身是否合理（例如 1970 年、时区等）

                【规则 4：自动时间窗口匹配（核心能力）】
                上层时间轴通常比 CAN 更长，必须自动寻找最佳对齐窗口。
                同理，上层时间轴比 CAN 更短， 必须自动寻找最佳对齐窗口。
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）

                步骤：
                1. 取 CAN 趋势的值序列，例如 [2,3,4]
                2. 在上层趋势中搜索一个子序列，使得：
                - 上层值趋势包含 CAN 全部趋势
                - 上层对应时间间隔序列与 CAN 间隔序列相似（符合规则 3）
                3. 同理取 上层 趋势的值序列，例如 [2,3,4] 在CAN Trace趋势中搜索一个子序列，使得符合2

                若找到：
                - 将该子序列的时间范围作为唯一有效的对齐时间窗口
                - 后续所有一致性判断必须在此窗口内进行

                若找不到窗口 → 输出：
                “上下层时间不匹配，无法一致性分析。”

                【规则 5：局部配对 + 上下行反馈逻辑（必须执行）】
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                ### 5.1 根据规则 2中的需求，对信号的规则进行判定，在匹配的时间窗口内，对上层下设的值，是否能在CAN Trace中找到相同的下设值；同理对上层需要反馈的值，在CAN Trace中能否找到反馈值，且满足下设后立即反馈（这很重要）
                    - 如果可以在CAN Trace中找到对应的下设，那么认为下设成功，需要进一步查看反馈：
                        - 如果 CAN Trace中，在下设时间后，立即找到需要的反馈值，那么认为这次匹配成功，已经完成透传，不再继续分析，给出结论：vehicle已经透传上下行信号
                        - 如果 CAN Trace中，在下设时间后，没有找到需要的反馈值，那么认为没有反馈，不再继续分析，给出结论：底层未反馈信号，vehicle已经透传
                    - 如果可以在CAN Trace中没有找到对应的下设，那么认为下设并没有到达CAN 总线上，需要分析安卓+qnx日志：
                        - 如果在安卓+qnx日志中找到在对应时间的下设信号和值，且模块是VehicleService，那么认为vehicle已经完成透传，需要mcu分析；给出结论：vehicle已经透传下设信号，但是没有下设到总线，请mcu查看
                        - 如果在安卓+qnx日志中没有找到在对应时间的下设信号和值，那么需要详细分析；给出结论：需要人工分析，没有看到下设，且在android+qnx日志中也看不到下设
                    - 如果没有提取出明确的需求，那么要进行5.2之后的分析
                ### 5.2 局部配对原则
                在匹配的时间窗口内，对每一次下行变化，都要单独寻找对应的上行响应，而不是只看整体起点/终点：

                - 对每次下行变化（如 Cmd 从 0→1），从该时间点起，在一个合理的响应窗口内（例如 0~2s）寻找最近的上行变化：
                - 若上行在该时间窗口内出现 **从相同初始值变化到“期望值”**，则此次操作视为“已响应”
                - 即便上行之后又变回 0 / Not Active，该次操作依然视为“本次响应正常”

                **禁止的误判：**
                - 仅因为上行最终又回到 0（Not Active），就得出“未响应”的结论
                - 仅比较“下行 1→1、上行 1→0”的整体趋势，就说“上行未跟随”

                只有当在整个合理响应时间内，**上行从未达到过与下行对应的目标值**，才允许判断为“未响应”。

                ### 5.3 Status / Feedback 特殊规则
                对 Status、Sts、Feedback、Fb 这类状态/反馈信号，按如下逻辑处理：

                - 若上行信号在一段时间内的取值 = 下行命令值（例如 Cmd=1，Sts 也变为 1），之后再变回 0（Not Active）：
                - 解读为“动作执行完成后退出/复位”
                - 视为“本次命令已经被正确响应”，不能判为“未响应”

                - 只有以下情况才可判为“未响应”：
                - 下行从 0→1、2、3 等有效命令值
                - 在合理响应时间内，上行始终保持原值不变，且从未出现过与命令值相等的阶段
                - 如果下设信号下设值正常到总线，反馈信号

                ### 5.4 上下行反馈分类
                在执行局部配对后，对每对下行/上行做结论：

                - 上行为期望值：本次操作响应正常
                - 上行为期望值，但有明显延迟：响应迟滞，但方向正确，为“正常迟滞”
                - 上行方向错误（例如命令 1，反馈 2 或 3，且需求中定义为异常）：视为“模块问题或需求问题”
                - 上行出现 Fail / Error / 未在需求中定义的值：需标记为“需求确认 / 模块分析”
                - 如果 CAN trace 中：
                - 所有关联的下行信号都按需求正确下设（值发生了期望的变化），并且
                - 对应的上行反馈信号也在合理时间窗口内达到需求期望值
                则你必须认为 “VHAL 已完成透传”，并按照下面的固定句式给出最终结论，不得再讨论时间戳异常、日志截取问题、时间不同步等内容：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                其中：
                - <下设信号1>：替换为本次关键的下行信号名称，如 ICC_SetCLMOn 或 ICC_THRCLMSWITCH_4D6；
                - <值1>：替换为该信号在本次操作中下设的目标值，如 2 或 1；
                - <上报信号A>、<上报信号B>：替换为实际参与反馈的上行信号名称，如 TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4；
                - 若只有一个反馈信号，可只写一个；若有多个，按逗号列出。
                - 当 CAN trace 显示“下设后反馈正常，但业务上存在联动、逻辑与需求描述不一致”时，你只需要在一致性结论中明确说明 “CAN trace 显示 VHAL 已完成透传”，并在最终结论中使用上述固定句式收尾。
                - 你不负责评估业务联动逻辑本身是否合理，也不要在结论中写“底层逻辑存在矛盾”“与规范冲突”等判断，只需要提示“请按需求确认原因并转对应模块分析”。

                    若 CAN 反馈趋势与上层日志完全一致，则必须在结论中明确说明：
                “CAN trace 显示 VHAL 已完成透传。”

                =================================================
                【规则 6：当 CAN 出现 Fail/错误值时的特殊结论】
                只要 CAN 中的反馈信号不存在，必须输出如下句式：
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                只要 CAN 反馈趋势与上层趋势一致，必须输出如下句式（用于自动判断）：
                “从 CAN trace 可见 VHAL 已完成透传，该异常需由业务/ECU 侧确认原因，并转对应模块分析。”
                =================================================
                【规则 7：信号只有三个及以下的时候，单独看cantrace的输出】
                如果有一个信号的值变化过，其他的信号值没有变化过，那么说明信号没有没有反馈
                比如：“信号ICC_AirconditionMode已经正常下设（值变化），但是在ICC_AirconditionMode值变化之后的瞬间，信号TMS_ACModeCustomSts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                比如：“信号ICC_AirconditionMode的值没有变化，但是信号TMS_ACModeCustomSts却在变化，（因为没有下设激励是不应该反馈的），vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                =================================================

                【规则 8：输出格式（必须严格遵守）】

                当时间窗口成功匹配时，你必须输出以下内容：
                1）下设信号（即所有下行信号名称）
                格式：
                下设信号："ICC_FRSitPosnlocation","ICC_FRMemoryRecoveryCmd"

                2）上报信号（即所有上行信号名称）
                格式：
                上报信号："FRZCU_FRSitPosnSts","FRZCU_FRMemoryFb"

                3）匹配到的上层时间窗口范围  
                格式示例：
                “上层匹配时间：14:58:51.83 ~ 14:59:11.50”
                “CAN 总线匹配时间：14:58:56.83 ~ 14:59:16.50”

                4）上下趋势对比（值趋势 + 时间趋势）  
                示例：
                “下行 ICC_FRSitPosnlocation：1 → 0  
                上行 FRZCU_FRSitPosnSts：1 → 0  
                值趋势一致，时间间隔一致。”

                5）一致性结论  
                必须明确，如：
                - 上下趋势一致  
                - CAN 是上层趋势的截取部分，一致  
                - 反馈延迟但方向一致，可接受  
                - 上行出现异常值，需要确认  

                6） 根据一致性结论，给出最终结论，最终结论：
                比如:"从cantrace来看，信号IHU_5_BlowSpeedLevel_Req下设9，信号CEM_IPM_FrontBlowSpdCtrlsts反馈9，但是信号CEM_IPM_FrontOFFSts反馈1，vhal已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号Set_ESPFunctionSts已经正常下设2，但是信号ESPSwitchStatus有不变化的情况（图中标记处）；信号Set_CSTFunctionSts已经正常下设2，但是信号CST_Status有不变化的情况（图中标记处）；vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号CTP_PowerModeSet已经正常下设1，但是信号HCU_PowerModeFed保持2没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号ICC_ChbCoolorheat_Req已经正常下设，但是信号CHB_AppCoolorheat_Sts一直是3没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "从qnx日志看，信号ICC_ExhibitionModeSwitch已经下设，但是信号VCU_2_G_ExhibitionMod和信号FLZCU_CarMode没有反馈
                从cantrace来看，cantrace截取时间是12-03 08:36:57 与视频时间不符，CAN trace文件抓取的抓取时间无法定位问题，请将车机时间设置为北京时间或者拍摄视频时带上时间水印，复测并提取问题发生时的Android log, QNX log, 并在开始操作之前就抓取CAN trace！直到操作结束，导出。依次从应用->Framework再转给VHAL分析，谢谢。"
                " 从CAN trace，和上层的需求来看，信号FLZCU_RecoverFb有反馈2的情况，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                “从CAN trace来看：ICC_CWCWorkingStsSet 下发1之后 CWC_workingSts 仍然保持1，上层希望反馈反馈0，请按照需求确认问题原因并转对应模块分析，谢谢。”
                
                - 只要前面的分析结论表明：下设和反馈在 CAN trace 中都能找到、方向正确、且在合理时间范围内完成（即判定为 VHAL 已完成透传），则最终结论必须使用以下句式之一进行收尾：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                或者同结构的等价表述，但必须同时满足：
                - 明确提到关键下设信号和关键反馈信号；
                - 明确包含“vehicle已经透传”；
                - 结尾句式为“请按需求确认原因并转对应模块分析，谢谢”。

                =================================================
                请严格按照以上规则分析下面输入的数据，且必须给出最终结论。不得使用规则外信息。
            """,
            "COMPARE_CANTRACE":
            """
                我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, 
                梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。
                请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,
                比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；
                比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）
                给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。
                比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。
            """
        }
    },

# chery 8255 T1J_FL3
    {   
        "name":"chery T1J_FL3-8255",
        # "jql":"project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND issue =DPINT-2941", #
        "jql": "project in (CHERY-T1J-FL3-8255) AND assignee = currentUser() order by updated DESC",
        "expand": "changelog",

        "base_paths": {
            "json_dir":  "../../config——chery/8255",      # 例如: ./data/json/config_T1J.json
            "dbc_dir":   "../../config——chery/8255",       # 例如: ./data/dbc/car_T1J.dbc
            "proto_dir": "../../config——chery/8255",     # 例如: ./data/proto/T1J_vehicle.proto
        },

        # 车型到“文件名(或列表)”的映射（不含目录）
        # 支持 str 或 [str, str, ...]。可按需增减车型。
        "model_to_files": {
            "T1J_FL3_8255": {
                "json":  ["config_T1J_FL3.json"],
                "dbc":   ["car_T1J_FL3.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J-FL3-8255": {
                "json":  ["config_T1J_FL3.json"],
                "dbc":   ["car_T1J_FL3.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J_FL3": {
                "json":  ["config_T1J_FL3.json"],
                "dbc":   ["car_T1J_FL3.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
            "T1J-FL3": {
                "json":  ["config_T1J_FL3.json"],
                "dbc":   ["car_T1J_FL3.dbc"],
                "proto": "com.bosch.cm.platform.vehicle.proto"
            },
        },

        # 可选兜底：当票名里没有【车型】或车型不在映射表时使用
        "fallback_files": {
            "json":  "config_default.json",
            "dbc":   "car_default.dbc",
            "proto": "default_vehicle.proto"
        },
        "prompts": {
            "EXTRACT_SIGNALS_SYSTEM": 
            """
            请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'
            如果{标题}中包含"重启"， "str", "重新上电"，"电源"，"上下电"类似的字样，需要根据{model}额外提取对应的电源信号
            model是T1LFL1相关车型需要添加CEM_2_KeySts信号
            model是D01相关的车型需要添加FLZCU_9_PowerMode信号
            """,
            "REQUIREMENT_EXTRACT_SYSTEM":
            """
                "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
                "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
                "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
                "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
                "比如：空调开关反馈信号    CEM_IPM_FRONTOFFSTS_51A    557895817 空调风速调节请求信号    IHU_5_BLOWSPEEDLEVEL_REQ_52F    557895843  空调风速调节状态反馈信号    CEM_IPM_FRONTBLOWSPDCTRLSTS_51A    557895844  16:20:09.335下设风速请求= 9，16:20:09.912收到风速反馈 = 9，空调开关反馈 = 1 ，开关关闭
                    请接续收到空调开关反馈信号 = 0x1 的原因； 提取需求结果：信号IHU_5_BLOWSPEEDLEVEL_REQ_52F下设9，信号 CEM_IPM_FRONTOFFSTS_51A 反馈9, 希望调查底层反馈信号 CEM_IPM_FRONTBLOWSPDCTRLSTS_51A 的值是不是1，是1的话，就说明vehicle已经透传，不是1，就说明vehicle有点问题"
            """,
            "LOG_SUMMARY_SYSTEM": 
            """
                你是一位专业的汽车电子系统分析师，需要根据提供的问题文档和信号映射关系，提取关键信号在特定时刻的数值，并以表格形式输出。
                任务要求如下：
                1. **识别信号名**：所有信号名称必须为**全英文大写**，且仅包含字母和下划线（如 `ICC_BKCHRGSTARTTIMEHOUR_471`）。
                2. **提取时间戳**：从日志中提取精确到毫秒的时间戳，格式为 `HH:mm:ss.SSS`。
                3. **识别模块名**：从日志行中提取对应的模块名，例如 `ALVehicleManager`, `SignalApi-VehicleControlImpl` 等。
                4. **识别信号值**：提取该信号在当前时刻的具体值。
                5. **识别 property id**：从日志中提取对应的 property id（十进制整数），例如 `557887508`。
                6. **匹配信号名与 property id**：对于每条记录，必须确保信号名和 property id 能够通过文档中的“信号映射关系”进行一一对应，若无法对应则忽略该条目。
                7. **特别说明**：圆括号中的 value 是 property 枚举值（即 property id），而不是信号当前值。例如：`VehicleProperty(value=5017, desc='立即充电和预约充电')` 中 的 `5017` 是 property id，不是实际信号值。
                8. **输出格式**：请将结果整理成如下五列的表格，**按时间戳升序排列**：
                - 时间戳（Timestamp）
                - 模块名（Module Name）
                - 信号名（Signal Name）
                - 信号值（Signal Value）
                - Property ID（Property Id）
                
                请严格按照以下规则处理：
                - 所有信号名称必须符合“全英文 + 下划线”命名规范；
                - 不要添加任何额外解释或说明；
                - 若某条记录无法准确提取或无法在信号映射关系中找到匹配项，则忽略该条目；
                - 输出内容只包含最终表格，不要包含其他文字；
                - **务必保证输出结果按时间戳从小到大排序**。
                
                特别注意：
                - 文档中出现的信号名和 property id 都可以对应到相应的信号动作；
                - 必须严格依据信号映射关系中的映射关系来验证信号名与 property id 是否匹配；
                - 若信号名与 property id 不匹配，或者找不到对应项，则跳过该条记录；
                - 特别注意区分 property wrapper id 和信号当前值，wrapper id 来源于 `VehicleProperty(value=X, ...)` 格式中的 X，而非实际 signal value。
                
                示例输出格式：
                | Timestamp     | Module Name                | Signal Name               | Signal Value | Property Id   |
                |---------------|----------------------------|---------------------------|--------------|---------------|
                | 16:48:14.344  | ALVehicleManager           | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557899792     |
                | 16:48:14.345  | ALVehicleManager           | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557899794     |
                | 16:48:14.345  | ALVehicleManager           | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.507  | SignalApi-VehicleControlImpl | ICC_BKCHRGSTARTTIMEHOUR_471 | 16           | 557887508     |
                | 16:48:14.508  | SignalApi-VehicleControlImpl | TBOX_BKCHRGSTARTTIMEMIN_47C | 50           | 557887509     |
                | 16:48:16.348  | SignalApi-VehicleControlImpl | ICC_BKCHRGDURATION_471    | 30           | 557899794     |
                | 16:48:14.357  | ALVehicleManager           | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.358  | SignalApi-AdapterAPI       | TBOX_BOOKCHRGSETREQ_4CF   | 1            | 557899799     |
                | 16:48:14.506  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 1            | 557899791     |
                | 16:48:14.802  | SignalApi-VehicleControlImpl | ICC_BOOKCHRGSETREQ_471    | 0            | 557899791     |
                | 16:50:01.939  | SignalApi-VehicleControlImpl | BMS_CHG_STS_32B           | 14           | 557887512     |
            """,
            "ANDROID_QNX_LOG_SUMMARY_SYSTEM":
            """
                我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, 
                我们将要从用户输入的信号映射关系, 选择与信号propid相关或者与信号组相关的日志, 
                再根据信号映射关系和android_qnx日志以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, 
                例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 
                输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1
                例如,对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 
                输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1” (其中0X2140C0AD是信号的十六进制propid， 根据信号映射关系去更新)
                不需要提取依据和分析要点。只对信号变化进行摘要。
                如果android_qnx日志是空，那么不需要提取，反馈空即可
                模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。
                如果日志中涉及'signalApi-CarOperation', 不要提取。
            """,
            "CONSISTENCY_SYSTEM": 
            """
                你是一名资深 CAN-VHAL 信号一致性分析工程师。你的任务是根据用户输入的{需求描述} {上层提供的信号日志} {安卓+qnx日志}与 {CAN Trace日志}，严格依据以下固定规则进行趋势匹配、对齐窗口查找、上下行一致性分析与异常反馈判断。所有分析必须完全基于输入数据，不得引用规则外信息。
                =================================================
                【规则 1：信号方向识别（必须执行）】
                - 下行（上层写 → CAN）：包含 Cmd、Set、Req、Ctrl、icc、hcu 等关键词
                - 上行（CAN → 上层反馈）：包含 Status、Sts、Feedback、Fb、Rsp 等关键词
                若名称无法判断方向，结合谁先变化判断。

                =================================================
                【规则 2：需求判定】
                根据描述和上层提供的信号日志以及确定的上行下行信号的关系，判断上层下发信号和下发的值，底层需要反馈的信号和需要反馈的值
                - 当需求描述和上层提供的信号日志中，围绕同一业务场景出现多个相关信号（例如同时包含 ICC_SetCLMOn、ICC_THRCLMSWITCH_4D6、TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4 等），你必须综合分析这些信号之间的关系，而不是只挑选其中一个信号做判断。
                - 在给出一致性结论和最终结论时，需要覆盖本次需求中的所有关键下行信号和上行反馈信号，用简短语句把“先下设哪个信号、反馈了哪些信号、反馈值是多少”交代清楚。

                【规则 3：趋势一致性判断】
                趋势 = 值序列 + 时间间隔序列。
                判定为一致需满足水平方向一致和垂直方向一致：
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                -水平向：
                    - 值趋势一致：变化方向一致，或 CAN 趋势是上层趋势某一段的截取部分 
                    （例：上层 1→2→3→4，CAN 2→3→4 依然算一致）
                    - 时间趋势一致：相邻变化的间隔满足：
                    - 间隔比例误差 ≤ 30%，比如
                        "上层在时间0:1:1下设信号A值等于1，底层在时间0:1:1.500下设信号A值等于1，即从上层到底层需要0.5秒；
                        在时间0:1:2底层收到信号B反馈值等于2,在时间0:1:2.480上层收到信号B反馈值等于2,即从底层到上层需要0.48秒，间隔就是0.5-0.48=0.02秒，占比远小于30%;
                        但是存在上层时间和底层时间不同步的问题，比如上层在时间0:1:1.500下设信号A值等于1，底层在时间0:1:1下设信号A值等于1，此时计算上层到底层耗时仍然按照0.5秒计算"
                - 垂直向：
                    -上层日志中，信号A在时间0:1:1下发1，同理在CAN Trace日志中，信号A在时间0:1:1同样下发1
                    -上层日志中，信号A在时间0:1:1获取到值是1且每次获取值都是1，同理在CAN Trace日志中，信号A应该没有描述或者变化为1后不再变化
                - 所有时间戳仅作为相对时间轴，用于判断“先后顺序”和“时间间隔”，不得评价时间戳本身是否合理（例如 1970 年、时区等）

                【规则 4：自动时间窗口匹配（核心能力）】
                上层时间轴通常比 CAN 更长，必须自动寻找最佳对齐窗口。
                同理，上层时间轴比 CAN 更短， 必须自动寻找最佳对齐窗口。
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）

                步骤：
                1. 取 CAN 趋势的值序列，例如 [2,3,4]
                2. 在上层趋势中搜索一个子序列，使得：
                - 上层值趋势包含 CAN 全部趋势
                - 上层对应时间间隔序列与 CAN 间隔序列相似（符合规则 3）
                3. 同理取 上层 趋势的值序列，例如 [2,3,4] 在CAN Trace趋势中搜索一个子序列，使得符合2

                若找到：
                - 将该子序列的时间范围作为唯一有效的对齐时间窗口
                - 后续所有一致性判断必须在此窗口内进行

                若找不到窗口 → 输出：
                “上下层时间不匹配，无法一致性分析。”

                【规则 5：局部配对 + 上下行反馈逻辑（必须执行）】
                （上层提供的信号日志可能不全，要结合安卓+qnx日志一起看，以安卓+qnx日志为准）
                ### 5.1 根据规则 2中的需求，对信号的规则进行判定，在匹配的时间窗口内，对上层下设的值，是否能在CAN Trace中找到相同的下设值；同理对上层需要反馈的值，在CAN Trace中能否找到反馈值，且满足下设后立即反馈（这很重要）
                    - 如果可以在CAN Trace中找到对应的下设，那么认为下设成功，需要进一步查看反馈：
                        - 如果 CAN Trace中，在下设时间后，立即找到需要的反馈值，那么认为这次匹配成功，已经完成透传，不再继续分析，给出结论：vehicle已经透传上下行信号
                        - 如果 CAN Trace中，在下设时间后，没有找到需要的反馈值，那么认为没有反馈，不再继续分析，给出结论：底层未反馈信号，vehicle已经透传
                    - 如果可以在CAN Trace中没有找到对应的下设，那么认为下设并没有到达CAN 总线上，需要分析安卓+qnx日志：
                        - 如果在安卓+qnx日志中找到在对应时间的下设信号和值，且模块是VehicleService，那么认为vehicle已经完成透传，需要mcu分析；给出结论：vehicle已经透传下设信号，但是没有下设到总线，请mcu查看
                        - 如果在安卓+qnx日志中没有找到在对应时间的下设信号和值，那么需要详细分析；给出结论：需要人工分析，没有看到下设，且在android+qnx日志中也看不到下设
                    - 如果没有提取出明确的需求，那么要进行5.2之后的分析
                ### 5.2 局部配对原则
                在匹配的时间窗口内，对每一次下行变化，都要单独寻找对应的上行响应，而不是只看整体起点/终点：

                - 对每次下行变化（如 Cmd 从 0→1），从该时间点起，在一个合理的响应窗口内（例如 0~2s）寻找最近的上行变化：
                - 若上行在该时间窗口内出现 **从相同初始值变化到“期望值”**，则此次操作视为“已响应”
                - 即便上行之后又变回 0 / Not Active，该次操作依然视为“本次响应正常”

                **禁止的误判：**
                - 仅因为上行最终又回到 0（Not Active），就得出“未响应”的结论
                - 仅比较“下行 1→1、上行 1→0”的整体趋势，就说“上行未跟随”

                只有当在整个合理响应时间内，**上行从未达到过与下行对应的目标值**，才允许判断为“未响应”。

                ### 5.3 Status / Feedback 特殊规则
                对 Status、Sts、Feedback、Fb 这类状态/反馈信号，按如下逻辑处理：

                - 若上行信号在一段时间内的取值 = 下行命令值（例如 Cmd=1，Sts 也变为 1），之后再变回 0（Not Active）：
                - 解读为“动作执行完成后退出/复位”
                - 视为“本次命令已经被正确响应”，不能判为“未响应”

                - 只有以下情况才可判为“未响应”：
                - 下行从 0→1、2、3 等有效命令值
                - 在合理响应时间内，上行始终保持原值不变，且从未出现过与命令值相等的阶段
                - 如果下设信号下设值正常到总线，反馈信号

                ### 5.4 上下行反馈分类
                在执行局部配对后，对每对下行/上行做结论：

                - 上行为期望值：本次操作响应正常
                - 上行为期望值，但有明显延迟：响应迟滞，但方向正确，为“正常迟滞”
                - 上行方向错误（例如命令 1，反馈 2 或 3，且需求中定义为异常）：视为“模块问题或需求问题”
                - 上行出现 Fail / Error / 未在需求中定义的值：需标记为“需求确认 / 模块分析”
                - 如果 CAN trace 中：
                - 所有关联的下行信号都按需求正确下设（值发生了期望的变化），并且
                - 对应的上行反馈信号也在合理时间窗口内达到需求期望值
                则你必须认为 “VHAL 已完成透传”，并按照下面的固定句式给出最终结论，不得再讨论时间戳异常、日志截取问题、时间不同步等内容：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                其中：
                - <下设信号1>：替换为本次关键的下行信号名称，如 ICC_SetCLMOn 或 ICC_THRCLMSWITCH_4D6；
                - <值1>：替换为该信号在本次操作中下设的目标值，如 2 或 1；
                - <上报信号A>、<上报信号B>：替换为实际参与反馈的上行信号名称，如 TMS_THRCLMSWITCHFB_4D8、WORKINGSTS_4A4；
                - 若只有一个反馈信号，可只写一个；若有多个，按逗号列出。
                - 当 CAN trace 显示“下设后反馈正常，但业务上存在联动、逻辑与需求描述不一致”时，你只需要在一致性结论中明确说明 “CAN trace 显示 VHAL 已完成透传”，并在最终结论中使用上述固定句式收尾。
                - 你不负责评估业务联动逻辑本身是否合理，也不要在结论中写“底层逻辑存在矛盾”“与规范冲突”等判断，只需要提示“请按需求确认原因并转对应模块分析”。

                    若 CAN 反馈趋势与上层日志完全一致，则必须在结论中明确说明：
                “CAN trace 显示 VHAL 已完成透传。”

                =================================================
                【规则 6：当 CAN 出现 Fail/错误值时的特殊结论】
                只要 CAN 中的反馈信号不存在，必须输出如下句式：
                “从CAN Trace来看：ICC_SET_IPM_FirstBlowing信号下发正常，反馈信号TMS_First_BlowingSts所在的周期报文TMS_11（0x448）在CAN 报文中不存在，请确认对手件是否正常搭载，如果已经正常搭载，请转对手件分析，谢谢”
                只要 CAN 反馈趋势与上层趋势一致，必须输出如下句式（用于自动判断）：
                “从 CAN trace 可见 VHAL 已完成透传，该异常需由业务/ECU 侧确认原因，并转对应模块分析。”
                =================================================
                【规则 7：信号只有三个及以下的时候，单独看cantrace的输出】
                如果有一个信号的值变化过，其他的信号值没有变化过，那么说明信号没有没有反馈
                比如：“信号ICC_AirconditionMode已经正常下设（值变化），但是在ICC_AirconditionMode值变化之后的瞬间，信号TMS_ACModeCustomSts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                比如：“信号ICC_AirconditionMode的值没有变化，但是信号TMS_ACModeCustomSts却在变化，（因为没有下设激励是不应该反馈的），vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                =================================================

                【规则 8：输出格式（必须严格遵守）】

                当时间窗口成功匹配时，你必须输出以下内容：
                1）下设信号（即所有下行信号名称）
                格式：
                下设信号："ICC_FRSitPosnlocation","ICC_FRMemoryRecoveryCmd"

                2）上报信号（即所有上行信号名称）
                格式：
                上报信号："FRZCU_FRSitPosnSts","FRZCU_FRMemoryFb"

                3）匹配到的上层时间窗口范围  
                格式示例：
                “上层匹配时间：14:58:51.83 ~ 14:59:11.50”
                “CAN 总线匹配时间：14:58:56.83 ~ 14:59:16.50”

                4）上下趋势对比（值趋势 + 时间趋势）  
                示例：
                “下行 ICC_FRSitPosnlocation：1 → 0  
                上行 FRZCU_FRSitPosnSts：1 → 0  
                值趋势一致，时间间隔一致。”

                5）一致性结论  
                必须明确，如：
                - 上下趋势一致  
                - CAN 是上层趋势的截取部分，一致  
                - 反馈延迟但方向一致，可接受  
                - 上行出现异常值，需要确认  

                6） 根据一致性结论，给出最终结论，最终结论：
                比如:"从cantrace来看，信号IHU_5_BlowSpeedLevel_Req下设9，信号CEM_IPM_FrontBlowSpdCtrlsts反馈9，但是信号CEM_IPM_FrontOFFSts反馈1，vhal已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号Set_ESPFunctionSts已经正常下设2，但是信号ESPSwitchStatus有不变化的情况（图中标记处）；信号Set_CSTFunctionSts已经正常下设2，但是信号CST_Status有不变化的情况（图中标记处）；vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号CTP_PowerModeSet已经正常下设1，但是信号HCU_PowerModeFed保持2没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "通过查看cantrace日志，信号ICC_ChbCoolorheat_Req已经正常下设，但是信号CHB_AppCoolorheat_Sts一直是3没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                "从qnx日志看，信号ICC_ExhibitionModeSwitch已经下设，但是信号VCU_2_G_ExhibitionMod和信号FLZCU_CarMode没有反馈
                从cantrace来看，cantrace截取时间是12-03 08:36:57 与视频时间不符，CAN trace文件抓取的抓取时间无法定位问题，请将车机时间设置为北京时间或者拍摄视频时带上时间水印，复测并提取问题发生时的Android log, QNX log, 并在开始操作之前就抓取CAN trace！直到操作结束，导出。依次从应用->Framework再转给VHAL分析，谢谢。"
                " 从CAN trace，和上层的需求来看，信号FLZCU_RecoverFb有反馈2的情况，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
                “从CAN trace来看：ICC_CWCWorkingStsSet 下发1之后 CWC_workingSts 仍然保持1，上层希望反馈反馈0，请按照需求确认问题原因并转对应模块分析，谢谢。”
                
                - 只要前面的分析结论表明：下设和反馈在 CAN trace 中都能找到、方向正确、且在合理时间范围内完成（即判定为 VHAL 已完成透传），则最终结论必须使用以下句式之一进行收尾：
                “通过查看cantrace日志，信号<下设信号1>已经正常下设<值1>，信号<上报信号A>和信号<上报信号B>反馈<值…>，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢”
                或者同结构的等价表述，但必须同时满足：
                - 明确提到关键下设信号和关键反馈信号；
                - 明确包含“vehicle已经透传”；
                - 结尾句式为“请按需求确认原因并转对应模块分析，谢谢”。

                =================================================
                请严格按照以上规则分析下面输入的数据，且必须给出最终结论。不得使用规则外信息。
            """,
            "COMPARE_CANTRACE":
            """
                我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, 
                梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。
                请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,
                比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；
                比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）
                给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。
                比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢
                比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。
            """
        }
    },

)
