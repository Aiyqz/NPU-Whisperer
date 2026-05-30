import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
import config

class OSPolygraphDaemon:
    def __init__(self):
        self.stats_file = config.STATS_PATH
        self.log_file = config.LOG_PATH
        
        # 初始化状态数据
        self.reset_stats()
        
        # 记录上一次轮询的时间
        self.last_poll_time = time.time()
        
        # 维护一个文件修改时间的字典，用于监听工作区
        self.file_mtimes = {}
        self.init_workspace_files()
        
        # 上一次写日志和心跳的时间
        self.log(f"OS Polygraph Daemon 启动。监控工作区：{config.WORKSPACE_DIR}")

    def log(self, message):
        """记录本地守护进程运行日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        sys.stdout.write(log_line)
        sys.stdout.flush()
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            sys.stderr.write(f"写入运行日志失败: {e}\n")

    def reset_stats(self):
        """重置一个日记周期内的行为指标数据"""
        self.stats = {
            "window_switches": 0,
            "file_saves": 0,
            "cpu_spikes": 0,
            "max_idle_seconds": 0.0,
            "app_history": {},         # 每个App停留的秒数
            "consecutive_focus_seconds": 0.0,  # 连续专注秒数
            "start_time": time.time(),
            "last_active_app": "Unknown",
            "last_flush_time": time.time(),
            "trigger_easter_egg": False  # 是否触发「幽灵的妥协」
        }
        self.save_stats()

    def save_stats(self):
        """将当前内存中的状态指标持久化至本地 JSON"""
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            self.log(f"持久化状态数据失败: {e}")

    def load_stats(self):
        """从本地 JSON 加载状态指标（如果存在）"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 仅在数据结构匹配时恢复
                    if "window_switches" in data:
                        self.stats = data
            except Exception as e:
                self.log(f"加载持久化数据失败，已重置: {e}")

    def init_workspace_files(self):
        """递归扫描工作区内的所有文件并记录其修改时间"""
        self.file_mtimes = {}
        self.scan_workspace_files()

    def scan_workspace_files(self):
        """扫描工作区，返回自上次扫描以来被修改的文件数量"""
        modified_count = 0
        current_mtimes = {}
        
        # 需要排除的目录和文件
        exclude_dirs = {".git", ".venv", "venv", "__pycache__"}
        exclude_files = {
            os.path.basename(config.LOG_PATH),
            os.path.basename(config.STATS_PATH),
            os.path.basename(config.DIARY_PATH),
            ".DS_Store"
        }

        try:
            for root, dirs, files in os.walk(config.WORKSPACE_DIR):
                # 排除特定文件夹
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    if file in exclude_files or file.endswith(".tmp") or file.endswith(".swp"):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        current_mtimes[file_path] = mtime
                        
                        # 如果是新文件，或者文件被修改过
                        if file_path in self.file_mtimes:
                            if mtime > self.file_mtimes[file_path]:
                                modified_count += 1
                        else:
                            # 第一次启动后新创建的文件也算修改/保存
                            if self.file_mtimes: # 避免首次初始化全部算作修改
                                modified_count += 1
                    except OSError:
                        continue
        except Exception as e:
            self.log(f"扫描工作区文件失败: {e}")

        self.file_mtimes = current_mtimes
        return modified_count

    def get_active_app(self):
        """通过 AppleScript 获取当前最前台的活动应用程序名称"""
        try:
            cmd = ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return res.stdout.strip()
        except subprocess.TimeoutExpired:
            self.log("osascript 获取活动窗口超时")
        except Exception as e:
            self.log(f"osascript 执行失败: {e}")
        return "Unknown"

    def get_system_idle_time(self):
        """通过 ioreg 获取系统的闲置时间（秒）"""
        try:
            cmd = "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF/1000000000; exit}'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                val = res.stdout.strip()
                return float(val) if val else 0.0
        except Exception as e:
            self.log(f"获取系统闲置时间失败: {e}")
        return 0.0

    def get_cpu_usage(self):
        """获取当前系统总 CPU 占用率的估值"""
        try:
            cmd = "ps -A -o %cpu | awk '{s+=$1} END {print s}'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                val = res.stdout.strip()
                return float(val) if val else 0.0
        except Exception as e:
            pass
        return 0.0

    def poll(self):
        """单次监控轮询逻辑"""
        now = time.time()
        duration = now - self.last_poll_time
        self.last_poll_time = now

        # 1. 捕捉当前活动 App
        current_app = self.get_active_app()
        if current_app != "Unknown":
            # 累加停留时间
            self.stats["app_history"][current_app] = self.stats["app_history"].get(current_app, 0.0) + duration
            
            # 检测窗口切换
            if current_app != self.stats["last_active_app"]:
                if self.stats["last_active_app"] != "Unknown":
                    self.stats["window_switches"] += 1
                    self.log(f"活动窗口切换: {self.stats['last_active_app']} -> {current_app}")
                self.stats["last_active_app"] = current_app

        # 2. 捕捉系统闲置时间（赛博脑死亡检测）
        idle_time = self.get_system_idle_time()
        if idle_time > self.stats["max_idle_seconds"]:
            self.stats["max_idle_seconds"] = idle_time
        
        # 3. 捕捉 CPU 飙高瞬间 (M4 10核，当单核或多核负载飙高，多进程合计数超过 150% 视为一次瞬时飙高)
        cpu_usage = self.get_cpu_usage()
        if cpu_usage > 150.0:
            self.stats["cpu_spikes"] += 1
            self.log(f"检测到 CPU 瞬时负载飙高: {cpu_usage}%")

        # 4. 捕捉代码保存/修改频次
        modified_files = self.scan_workspace_files()
        if modified_files > 0:
            self.stats["file_saves"] += modified_files
            self.log(f"检测到工作区文件保存/修改事件数: {modified_files}")

        # 5. 「幽灵的妥协」：计算连续高强度专注时间
        # 定义专注条件：当前最前台 App 是 Code (或其它终端等开发工具)，且在该周期内没有高频切换窗口
        # 如果最近一段时间内的平均窗口切换频率极低且以 Code 为主，则累加专注时间。
        if current_app == "Code":
            self.stats["consecutive_focus_seconds"] += duration
            # 如果专注时间达到了设定的阈值，标记触发彩蛋
            if self.stats["consecutive_focus_seconds"] >= config.FOCUS_EGG_THRESHOLD:
                if not self.stats["trigger_easter_egg"]:
                    self.stats["trigger_easter_egg"] = True
                    self.log("✨ 达成成就：连续专注编写代码超过1小时！「幽灵的妥协」彩蛋已就绪。")
        else:
            # 如果切到了其他娱乐App（如浏览器、社交App等），且停留时间超过 30 秒，则重置专注时间
            # 我们简化逻辑：如果最前台不是 Code，并且累计在非 Code 应用中超过 30 秒，则重置专注
            non_code_time = sum(time for app, time in self.stats["app_history"].items() if app != "Code")
            if non_code_time > 30.0:
                if self.stats["consecutive_focus_seconds"] > 0:
                    self.log(f"因在非开发窗口（{current_app}）停留过久，重置了连续专注计时器（之前已累计 {self.stats['consecutive_focus_seconds']:.1f} 秒）。")
                    self.stats["consecutive_focus_seconds"] = 0.0

        # 保存最新的状态指标
        self.save_stats()

        # 6. 自动触发日记生成
        time_since_last_flush = now - self.stats["last_flush_time"]
        if time_since_last_flush >= config.FLUSH_INTERVAL:
            self.log(f"已达到生成间隔时间（{config.FLUSH_INTERVAL}秒），开始触发《Mac 观察日记》生成流程...")
            self.trigger_diary_generation()

    def trigger_diary_generation(self):
        """异步触发日记生成脚本，不阻塞监控的主循环"""
        # 保存当前指标，然后重置状态，以便在生成日记时，守护进程能立刻开启下一轮的捕捉
        current_stats_snapshot = self.stats.copy()
        
        # 重置并保存
        self.reset_stats()
        self.stats["last_flush_time"] = time.time()
        self.save_stats()
        
        # 将本次快照暂存一个临时文件，供生成器读取，防止竞争
        snapshot_path = os.path.join(config.WORKSPACE_DIR, ".snapshot_stats.json")
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(current_stats_snapshot, f, indent=2)
            
            # 使用 Subprocess 异步启动写日记的任务
            # 这样即使 API 延迟较高，也不会阻碍我们每 3 秒一次的监控主循环
            generator_path = os.path.join(config.WORKSPACE_DIR, "diary_generator.py")
            cmd = [sys.executable, generator_path, snapshot_path]
            with open(config.LOG_PATH, "a", encoding="utf-8") as log_handle:
                subprocess.Popen(cmd, cwd=config.WORKSPACE_DIR, stdout=log_handle, stderr=log_handle)
            self.log("异步日记生成进程已成功派生（spawned）。")
        except Exception as e:
            self.log(f"触发日记生成失败: {e}")

    def run(self):
        """启动监控主循环"""
        self.load_stats()
        self.stats["last_flush_time"] = time.time()
        self.save_stats()
        
        while True:
            try:
                self.poll()
            except KeyboardInterrupt:
                self.log("收到键盘中断，正在安全退出...")
                break
            except Exception as e:
                self.log(f"主轮询异常: {e}")
            time.sleep(config.MONITOR_INTERVAL)

if __name__ == "__main__":
    daemon = OSPolygraphDaemon()
    daemon.run()
