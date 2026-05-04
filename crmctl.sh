#!/bin/bash

# CRM System Control Script
# Usage: ./crmctl.sh [start|stop|restart|status|logs|enable|disable]

ACTION=$1
SERVICE=$2

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SUDO_PASS="Pytc@123"

show_help() {
    echo -e "${GREEN}CRM 系统管理脚本${NC}"
    echo ""
    echo "用法：$0 [命令] [服务名]"
    echo ""
    echo "命令:"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看状态"
    echo "  logs        查看日志"
    echo "  enable      开机自启"
    echo "  disable     禁用自启"
    echo ""
    echo "服务名:"
    echo "  backend     后端服务"
    echo "  frontend    前端服务"
    echo "  all         所有服务 (默认)"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动所有服务"
    echo "  $0 stop backend   # 停止后端"
    echo "  $0 logs frontend  # 查看前端日志"
}

run_cmd() {
    if [ -f /etc/systemd/system/crm-$1.service ]; then
        echo "$SUDO_PASS" | sudo -S systemctl $ACTION crm-$1
    else
        echo -e "${RED}服务 crm-$1 不存在${NC}"
        exit 1
    fi
}

case $ACTION in
    start)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            run_cmd "backend"
            sleep 3
            run_cmd "frontend"
        else
            run_cmd "$SERVICE"
        fi
        ;;
    stop)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            run_cmd "frontend"
            run_cmd "backend"
        else
            run_cmd "$SERVICE"
        fi
        ;;
    restart)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            run_cmd "backend"
            sleep 3
            run_cmd "frontend"
        else
            run_cmd "$SERVICE"
        fi
        ;;
    status)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            echo -e "${GREEN}=== 后端服务状态 ===${NC}"
            echo "$SUDO_PASS" | sudo -S systemctl status crm-backend --no-pager -l
            echo ""
            echo -e "${GREEN}=== 前端服务状态 ===${NC}"
            echo "$SUDO_PASS" | sudo -S systemctl status crm-frontend --no-pager -l
        else
            echo "$SUDO_PASS" | sudo -S systemctl status crm-$SERVICE --no-pager -l
        fi
        ;;
    logs)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            echo "$SUDO_PASS" | sudo -S journalctl -u crm-backend -u crm-frontend -f --no-pager
        else
            echo "$SUDO_PASS" | sudo -S journalctl -u crm-$SERVICE -f --no-pager
        fi
        ;;
    enable)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            echo "$SUDO_PASS" | sudo -S systemctl enable crm-backend crm-frontend
        else
            echo "$SUDO_PASS" | sudo -S systemctl enable crm-$SERVICE
        fi
        echo -e "${GREEN}服务已设置为开机自启${NC}"
        ;;
    disable)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            echo "$SUDO_PASS" | sudo -S systemctl disable crm-backend crm-frontend
        else
            echo "$SUDO_PASS" | sudo -S systemctl disable crm-$SERVICE
        fi
        echo -e "${YELLOW}服务已禁用开机自启${NC}"
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit 0
