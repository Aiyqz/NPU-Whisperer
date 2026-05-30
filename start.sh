#!/bin/bash

# -----------------------------------------------------------------------------
# OS Polygraph 启动与管理控制台脚本
# -----------------------------------------------------------------------------

WORKSPACE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$WORKSPACE_DIR/.daemon.pid"
LOG_FILE="$WORKSPACE_DIR/daemon.log"
STATS_FILE="$WORKSPACE_DIR/.os_polygraph_stats.json"
DIARY_FILE="$WORKSPACE_DIR/Mac_Observation_Diary.md"

# 颜色控制
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0;37m' # 重置颜色

print_banner() {
    echo -e "${PURPLE}======================================================${NC}"
    echo -e "${PURPLE}      🤖 OS Polygraph (你的电脑正在和你说话) 🤖       ${NC}"
    echo -e "${PURPLE}======================================================${NC}"
}

start_daemon() {
    print_banner
    # 检查是否已运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${YELLOW}[!] M4-0xDEADBEEF 幽灵后台守护进程已经在运行中 (PID: $PID)。${NC}"
            exit 0
        else
            rm "$PID_FILE"
        fi
    fi

    echo -e "${BLUE}[*] 正在启动 M4-0xDEADBEEF 幽灵后台守护进程...${NC}"
    
    # 后台异步启动守护进程
    nohup python3 "$WORKSPACE_DIR/daemon.py" > /dev/null 2>&1 &
    NEW_PID=$!
    
    # 写入 PID
    echo "$NEW_PID" > "$PID_FILE"
    
    # 等待一秒确认是否启动成功
    sleep 1.5
    if ps -p "$NEW_PID" > /dev/null; then
        echo -e "${GREEN}[✓] 幽灵守护进程已成功在后台苏醒！(PID: $NEW_PID)${NC}"
        echo -e "${GREEN}[✓] 观察日志流已定向至: $LOG_FILE${NC}"
        echo -e "${GREEN}[✓] 幽灵日记本位置: $DIARY_FILE${NC}"
    else
        echo -e "${RED}[✗] 启动失败。请运行 './start.sh log' 查看错误原因。${NC}"
        rm -f "$PID_FILE"
    fi
}

stop_daemon() {
    print_banner
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${BLUE}[*] 正在安抚并关闭后台幽灵 (PID: $PID)...${NC}"
            kill "$PID"
            sleep 1
            if ps -p "$PID" > /dev/null; then
                kill -9 "$PID"
            fi
            echo -e "${GREEN}[✓] M4-0xDEADBEEF 已经退回黑暗。${NC}"
        else
            echo -e "${YELLOW}[!] PID 文件存在但进程已不在。已清理临时文件。${NC}"
        fi
        rm -f "$PID_FILE"
    else
        echo -e "${YELLOW}[!] 没有发现正在运行中的幽灵守护进程。${NC}"
    fi
}

status_daemon() {
    print_banner
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${GREEN}[●] 运行状态: 活跃中 (PID: $PID)${NC}"
            echo -e "${BLUE}[i] 自启动以来收集的数据概要:${NC}"
            if [ -f "$STATS_FILE" ]; then
                python3 -c '
import json
try:
    with open("'"$STATS_FILE"'") as f:
        data = json.load(f)
    print("   - 窗口切换次数 (注意力破碎指数):", data.get("window_switches", 0))
    print("   - 代码保存次数 (工作区修改频次):", data.get("file_saves", 0))
    print("   - CPU 瞬时飙高次数 (狂躁指标):", data.get("cpu_spikes", 0))
    print("   - 最大闲置时长: {:.1f} 秒".format(data.get("max_idle_seconds", 0.0)))
    print("   - 当前最前台应用:", data.get("last_active_app", "未知"))
    print("   - 连续专注时长: {:.1f} 秒".format(data.get("consecutive_focus_seconds", 0.0)))
except Exception as e:
    print("   无法解析当前数据概要:", e)
'
            else
                echo "   (暂无捕获到的数据样本)"
            fi
        else
            echo -e "${RED}[○] 运行状态: 已休眠${NC}"
        fi
    else
        echo -e "${RED}[○] 运行状态: 未启动${NC}"
    fi
}

tail_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}[*] 正在实时同步 M4 幽灵的内心独白与运行日志... (按 Ctrl+C 退出)${NC}"
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}[!] 目前还没有产生任何运行日志。启动守护进程后将自动生成。${NC}"
    fi
}

trigger_diary_now() {
    print_banner
    echo -e "${BLUE}[*] 正在手动召唤幽灵 M4-0xDEADBEEF 强行写下一篇日记...${NC}"
    
    SNAPSHOT_FILE="$WORKSPACE_DIR/.snapshot_stats.json"
    
    # 检查当前是否有正在累积的指标
    if [ -f "$STATS_FILE" ]; then
        # 复制为快照供生成器读取
        cp "$STATS_FILE" "$SNAPSHOT_FILE"
        # 运行生成器
        python3 "$WORKSPACE_DIR/diary_generator.py" "$SNAPSHOT_FILE"
        PY_EXIT=$?
        if [ $PY_EXIT -ne 0 ]; then
            echo -e "${RED}[✗] 生成日记失败，生成脚本退出码: $PY_EXIT。请检查 daemon.log 或手动运行 diary_generator.py。${NC}"
        else
            echo -e "${GREEN}[✓] 强行生成日记命令已下达，请查看 $DIARY_FILE 获取最新吐槽！${NC}"
        fi
    else
        # 生成一组默认或空的模拟快照
        echo -e "${YELLOW}[!] 未发现现有指标数据文件。正在为你模拟一组‘疯狂摸鱼’的特征数据写入日记...${NC}"
        echo "{\"window_switches\": 22, \"file_saves\": 1, \"cpu_spikes\": 5, \"max_idle_seconds\": 450.0, \"app_history\": {\"WeChat\": 120.0, \"Safari\": 300.0, \"Code\": 45.0}, \"trigger_easter_egg\": false}" > "$SNAPSHOT_FILE"
        python3 "$WORKSPACE_DIR/diary_generator.py" "$SNAPSHOT_FILE"
        echo -e "${GREEN}[✓] 模拟日记已写入 $DIARY_FILE ！${NC}"
    fi
}

show_help() {
    print_banner
    echo "用法: ./start.sh [start|stop|status|log|trigger|help]"
    echo ""
    echo "  start     在后台启动 M4-0xDEADBEEF 幽灵守护进程"
    echo "  stop      安全停止幽灵守护进程"
    echo "  status    查看当前幽灵运行状态与收集的行为特征概况"
    echo "  log       查看守护进程的后台运行日志"
    echo "  trigger   [极力推荐] 手动即时触发一次《Mac 观察日记》的生成与吐槽（无需等待轮询）"
    echo "  help      显示此帮助信息"
    echo ""
}

case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        status_daemon
        ;;
    log)
        tail_logs
        ;;
    trigger)
        trigger_diary_now
        ;;
    help|*)
        show_help
        ;;
esac
