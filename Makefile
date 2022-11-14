

# change user and passwd if you use it

all: 
	python3 draw_pm.py --authname your_host_id --authpasswd your_host_passwd
	# cp total.md ../memo

local: 
	python3 draw_pm.py --authname your_host_id --authpasswd your_host_passwd --local

debug: 
	python3 draw_pm.py --authname your_host_id --authpasswd your_host_passwd  --debug
	# cp total.md ../memo

brief: 
	python3 draw_pm.py --authname your_host_id --authpasswd your_host_passwd  --brief
	# cp total.md ../memo

collab: 
	python3 dashboard_callab.py --authname your_collab_id --authpasswd your_collab_passwd
	# cp total.md ../memo
