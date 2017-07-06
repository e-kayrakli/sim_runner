count_lines:
	wc -l *.py platforms/*.py benchmarks/*.py

clean:
	rm -f *.pyc platforms/*.pyc benchmarks/*.pyc jobschedulers/*.pyc *.profile
	rm -rf __pycache__/ platforms/__pycache__ benchmarks/__pycache__ jobschedulers/__pycache__ graphs

