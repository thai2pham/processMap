

# change user and passwd if you use it

all: 
	python3 draw_pm.py --authname cheoljoo.lee --authpasswd !code123 
	cp total.md ../memo

debug: 
	python3 draw_pm.py --authname cheoljoo.lee --authpasswd !code123  --debug
	cp total.md ../memo