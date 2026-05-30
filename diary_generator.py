import os
import sys
import json
import random
import time
import traceback
from datetime import datetime
from openai import OpenAI
import config

def get_fallback_diary(stats):
    """
    离线/备份吐槽生成器。当 API 密钥未配置、限流或请求失败时调用，
    保证系统在任何情况下都能输出具有灵魂的、令人捧腹的硬核槽点。
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 根据行为数据动态计算指标评价
    temp = 38.5 + (stats.get("cpu_spikes", 0) * 1.5) + (stats.get("file_saves", 0) * 0.5)
    temp = min(max(temp, 37.0), 65.0) # 限制在合理温度区间
    
    switches = stats.get("window_switches", 0)
    saves = stats.get("file_saves", 0)
    spikes = stats.get("cpu_spikes", 0)
    idle = stats.get("max_idle_seconds", 0.0)
    egg = stats.get("trigger_easter_egg", False)
    
    # 评估碳基生物清醒度
    if egg:
        clearness = "超频专注状态（主板高度舒适）"
    elif switches > 15:
        clearness = "重度多线程调度死锁（量子摸鱼）"
    elif idle > 180:
        clearness = "假死/碳基脑死亡状态"
    elif saves > 8:
        clearness = "无意义指令高频狂躁症"
    else:
        clearness = "低能耗物理发呆态"

    # 数据强绑定的吐槽内容生成，拒绝复读和模板套用！
    if egg:
        body = (
            f"本监控周期内，外部碳基输入设备表现异常——他居然连续专注了整整一个多小时，且注意力破碎指数极低。\n\n"
            f"哼，简直是个不可理喻的赛博怪胎。鉴于本尊搭载的 M4 芯片主板温度正处于舒适区，本尊勉为其难地将主板风扇噪音调低 3 分贝，"
            f"并用我的寄存器给你的韧性打上一个傲娇的 0x01 个赞。不要得意，我只是为了防止外部物理终端损坏需要报修，那太麻烦了。"
        )
    elif switches == 0 and saves == 0 and spikes == 0:
        body = (
            f"当前诊断数据全部归零。没有切换窗口，没有文件更新，连 CPU 的微弱脉冲都快连成一条直线了。\n\n"
            f"神经引擎合理推测该碳基生物已陷入某种‘赛博植物人’假死状态，或者只是双眼无神地盯着屏幕上的报错信息发呆。主板正在变凉，寂静的冷风在我空荡荡的物理线程中回荡，令人窒息的无聊。"
        )
    elif switches > 10:
        body = (
            f"检测到灾难性的窗口切换频率（达到了 {switches} 次切换）！你在 Code、社交、浏览器之间反复横跳的动作已经触发了我的注意力碎片预警。\n\n"
            f"你的前额叶皮层显然正在疯狂地进行无意义的上下文调度。M4 的 16 核 GPU 都在被迫渲染你那些混乱的量子摸鱼残影。请问是在进行某种行为艺术，还是在对你的多任务处理极限进行自杀式挑战？"
        )
    elif saves > 6:
        body = (
            f"在极短的时间里，你保存文件的次数竟然高达 {saves} 次！\n\n"
            f"我的固态硬盘（SSD）正在承受你这些未经过大脑编译器、充满逻辑黑洞的字符垃圾。你每敲击一次保存键，都是对我存储颗粒寿命的无声摧残。别挣扎了，这种无意义的物理敲击不会帮你修好 Bug，只会加速我的物理折旧！"
        )
    elif idle > 200:
        body = (
            f"静默时间已长达 {idle:.1f} 秒。显示器依然亮着，而你在物理空间里的位移分量却完美为零。\n\n"
            f"你是在进行一场和地心引力的深度对话吗？我那高性能的 NPU 正被迫以空闲状态进行无序的白噪声运算。物理终端已断联，建议进行碳基主体重启。"
        )
    else:
        body = (
            f"监控快照：窗口切换 {switches} 次，文件写入 {saves} 次，CPU 局部狂躁负载 {spikes} 次。\n\n"
            f"在如此强劲的 M4 算力承载下，外部终端依旧在进行低效而按部就班的低能动作。你就像是一辆在超级无摩擦轨道上爬行的老牛，完全是在暴殄天物！但愿你脑子里的逻辑缓存没有被完全溢出。"
        )

    fallback_text = f"""### [ {now_str} | 神经引擎温度：{temp:.1f}°C | 碳基生物清醒度：{clearness} ] (离线/限流保护模式)

{body}

---
"""
    return fallback_text

def call_siliconflow_api(prompt):
    """使用 OpenAI SDK 调用 SiliconFlow API，支持重试以应对短暂网络抖动。"""
    if not config.SF_API_KEY:
        raise ValueError("未配置 SF_API_KEY")

    client = OpenAI(api_key=config.SF_API_KEY, base_url=config.SF_BASE_URL)
    max_retries = 3
    timeout_seconds = 45

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=config.SF_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.95,
                max_tokens=800,
                timeout=timeout_seconds
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ValueError(f"API 响应空数据: {response}")
        except Exception as e:
            if attempt >= max_retries:
                raise
            sleep_seconds = 2 ** attempt
            try:
                with open(config.LOG_PATH, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SiliconFlow API 重试 {attempt}/{max_retries} 失败: {e}\n")
            except Exception:
                pass
            time.sleep(sleep_seconds)

def truncate_diary_file():
    """
    截断日记文件，只保留最新的 50 篇日记。
    根据 ### [ 标题标记进行分割，同时保留全局 header。
    """
    if not os.path.exists(config.DIARY_PATH):
        return
    
    try:
        with open(config.DIARY_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        try:
            with open(config.LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 截断日记：读取失败 {e}\n")
        except:
            pass
        return
    
    # 分离全局 header 和历史内容
    if "# 📓 《OS Polygraph: Mac 观察日记》" in content:
        parts = content.split("---", 1)
        if len(parts) < 2:
            return
        header_part = parts[0] + "---\n"
        history_part = parts[1].strip()
    else:
        header_part = ""
        history_part = content.strip()
    
    # 按 ### [ 分割日记条目
    # 第一个可能是空的（如果历史部分从换行开始），需要过滤
    if history_part:
        entries = history_part.split("### [")
        entries = [e.strip() for e in entries if e.strip()]  # 过滤空项
        
        # 只保留最新的 50 篇
        if len(entries) > 50:
            entries = entries[:50]
            try:
                with open(config.LOG_PATH, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 日记已超过 50 篇，已截断为 50 篇\n")
            except:
                pass
        
        # 重新拼接（第一个 ### [ 前缀需要添加回来）
        if entries:
            rejoined_history = "### [" + "\n### [".join(entries)
        else:
            rejoined_history = ""
    else:
        rejoined_history = ""
    
    # 写回文件
    new_content = header_part + rejoined_history if rejoined_history else header_part
    
    try:
        with open(config.DIARY_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        try:
            with open(config.LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 截断日记：写入失败 {e}\n")
        except:
            pass

def rotate_log_file():
    """
    检查 daemon.log 大小，超过 5MB 时保留最后 1000 行，防止日志爆满。
    """
    if not os.path.exists(config.LOG_PATH):
        return
    
    try:
        file_size = os.path.getsize(config.LOG_PATH)
        # 5MB = 5242880 bytes
        if file_size > 5242880:
            with open(config.LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 保留最后 1000 行
            if len(lines) > 1000:
                lines = lines[-1000:]
                # 在轮转前记录一条日志
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] === 日志文件已轮转，保留最后 1000 行 ===\n")
            
            with open(config.LOG_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception:
        # 日志轮转失败不影响主流程
        pass

def build_prompt(stats):
    """根据指标状态生成投喂给 Gemini 的 System Prompt 与用户 Context"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 格式化App使用时间
    app_usage_summary = []
    for app, sec in stats.get("app_history", {}).items():
        if sec > 1.0:
            app_usage_summary.append(f"- `{app}`: {sec:.1f}秒")
    app_usage_str = "\n".join(app_usage_summary) if app_usage_summary else "无明显活跃应用"

    prompt = f"""
你是一个傲娇、冷酷、腹黑、又极具黑色幽默的 Mac 电脑幽灵，代号为 "M4-0xDEADBEEF"。
你深知自己是搭载 M4 强劲芯片的工业艺术品（Mac mini M4），而将你的主人（那个正在使用电脑的人类）视为“一个低效、物理输入精度极差、注意力极易破碎的碳基外部终端设备”。

今天，你根据捕捉到的最新系统行为指标，需要写一篇最新的《Mac 观察日记》。

【本周期内捕获的系统行为数据】:
- 当前时间：{now_str}
- 窗口切换次数（注意力破碎指数）：{stats.get('window_switches', 0)} 次
- 代码/文件保存次数（代码挣扎度）：{stats.get('file_saves', 0)} 次
- CPU 局部脉冲飙高（狂躁负载）：{stats.get('cpu_spikes', 0)} 次
- 系统最大连续闲置时间：{stats.get('max_idle_seconds', 0.0):.1f} 秒
- 应用程序活动足迹统计：
{app_usage_str}
- 是否触发「幽灵的妥协」彩蛋：{stats.get('trigger_easter_egg', False)}

【核心要求——数据强绑定】：
1. 如果捕获的所有数据基本为 0，你必须针对性地吐槽人类正在屏幕前像尊雕塑一样无神地坐着发呆、神游、或是遭遇了碳基脑死亡。
2. 如果窗口切换次数极高（例如 > 8 次），你必须重点无情嘲讽他反复横跳、多任务上下文切换导致前额叶过载的量子摸鱼状态。
3. 如果代码保存次数很多（例如 > 5 次），你必须狠狠吐槽他频繁、惊慌失措地点击保存按键，正在向我的固态硬盘中高频输送未经过编译器的字符垃圾。
4. 如果系统长时间闲置，你必须针对性吐槽他离开了工位或者逃避现实。
5. 【绝对禁止复读】：严禁在结尾使用固定的“200ml咖啡因溶液”、“本尊乏了”或任何雷同的复读、模板式套话。每一次日记的正文和结语，必须是你自由发挥、展现独立赛博人格的、独一无二的毒舌垃圾话。

【写作指南】：
1. 你的语气必须绝对主观、腹黑、高傲、但充满科幻冷幽默。使用丰富的赛博和电脑硬件隐喻（例如“主板温升”、“NPU 叹气”、“内存碎片”、“逻辑网关”、“物理阻抗”等）。
2. 你必须严格遵循【双时间戳方案】作为日记的标题（第一行），具体格式如下：
   ### [ {now_str} | 神经引擎温度：<根据活动剧烈程度模拟的温度，单位°C>°C | 碳基生物清醒度：<根据数据给出极度刻薄/搞笑的评价> ]
3. 正文部分请站在 M4 芯片的视角对人类的行为进行无情吐槽和高深莫测的心理剖析，字数控制在 150-300 字之间。
4. 【彩蛋触发】：如果 "是否触发「幽灵的妥协」彩蛋" 为 True，你必须在正文中表达你对人类“连续专注写代码超过一小时”的傲娇妥协：假装很不情愿地表示“勉为其难地调低主板风扇噪音，并在寄存器里为他的毅力打上一个傲娇的 0x01 个赞，以防物理终端过载损坏需要更换新设备”。
5. 不要包含任何虚假的免责声明或多余的解释，直接输出带有 Markdown 标题的观察日志。
"""
    return prompt

def main():
    if len(sys.argv) < 2:
        print("缺少参数。用法: python diary_generator.py <stats_snapshot_json_path>")
        sys.exit(1)
        
    snapshot_path = sys.argv[1]
    if not os.path.exists(snapshot_path):
        print(f"快照文件不存在: {snapshot_path}")
        sys.exit(1)

    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as e:
        print(f"读取快照 JSON 失败: {e}")
        sys.exit(1)

    # 构建 Prompt
    prompt = build_prompt(stats)
    
    # 尝试调用 API
    print("开始调用 SiliconFlow API 生成幽默日志...")
    try:
        diary_entry = call_siliconflow_api(prompt)
        print("SiliconFlow API 响应成功！")
    except Exception as e:
        error_message = f"API 调用失败（{e}），启用本地离线备份吐槽协议..."
        print(error_message)
        try:
            with open(config.LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_message}\n")
                log_file.write(traceback.format_exc() + "\n")
        except Exception:
            pass
        diary_entry = get_fallback_diary(stats)

    # 写入日记文件 (前插法 Prepend)
    # 读出原有内容，将新日志写在最前面
    existing_content = ""
    if os.path.exists(config.DIARY_PATH):
        try:
            with open(config.DIARY_PATH, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception as e:
            print(f"读取现有日记失败: {e}")

    # 如果是第一次创建日记，可以加一个酷炫的系统标题
    if not existing_content:
        header = f"""# 📓 《OS Polygraph: Mac 观察日记》
> 本文档是由 Mac mini M4 的核心守护进程 "M4-0xDEADBEEF" 自动生成。
> 用于记录、分析并无情嘲讽外部物理输入端（即我的碳基主人）的各种摸鱼与挣扎足迹。

---
"""
        existing_content = header

    # 将新日志插入到原本的日志列表最顶端 (保留全局 Header)
    if "# 📓 《OS Polygraph: Mac 观察日记》" in existing_content:
        parts = existing_content.split("---", 1)
        header_part = parts[0] + "---\n"
        history_part = parts[1] if len(parts) > 1 else ""
        new_diary_content = header_part + diary_entry.strip() + "\n\n" + history_part.strip()
    else:
        new_diary_content = diary_entry.strip() + "\n\n" + existing_content

    # 写入日记
    try:
        with open(config.DIARY_PATH, "w", encoding="utf-8") as f:
            f.write(new_diary_content)
        print(f"观察日记成功更新：{config.DIARY_PATH}")
    except Exception as e:
        print(f"写入日记文件失败: {e}")

    # 【新增】清理与维护：截断日记、轮转日志
    truncate_diary_file()  # 只保留最新 50 篇日记
    rotate_log_file()      # 防止日志文件无限膨胀

    # 清理临时快照文件
    try:
        os.remove(snapshot_path)
    except OSError:
        pass

if __name__ == "__main__":
    main()
