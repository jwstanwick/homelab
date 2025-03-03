deploy:
	docker compose up --build

stop:
	docker compose down

dashboard:
	@echo "Launching system dashboard..."
	@tmux new-session -d -s dashboard "watch -n 1 docker stats"
	@tmux split-window -v "htop"
	@tmux attach-session -t dashboard

install-dashboard:
	@echo "Installing dashboard..."
	sleep 20
	lxterminal --geometry=maximized -e "make -f /path/to/your/Makefile dashboard"